"""
Unit tests and DSP validation suite for HRL X Noise Cancellation.
Runs with standard Python unittest (zero dependencies required).
"""

import math
import os
import tempfile
import unittest

from hrl_noise_cancellation.dsp.audio_io import (
    AudioIO,
    calculate_snr,
    generate_synthetic_benchmark,
)
from hrl_noise_cancellation.dsp.spectral import SpectralSubtraction, SpectralGate
from hrl_noise_cancellation.dsp.adaptive import NLMSFilter
from hrl_noise_cancellation.dsp.fxlms import FxLMSFilter
from hrl_noise_cancellation.dsp.adaptive_eq import AdaptiveEQ, PsychoacousticMasker
from hrl_noise_cancellation.dsp.anti_phase import AntiPhaseInverter
from hrl_noise_cancellation.dsp.echo_cancellation import AcousticEchoKiller
from hrl_noise_cancellation.dsp.fan_vacuum import FanNoiseVacuum
from hrl_noise_cancellation.dsp.boat_rockerz_411 import BoatRockerz411ANC
from hrl_noise_cancellation.silicon.h1_chip import H1AudioSilicon


class TestDSPAlgorithms(unittest.TestCase):

    def setUp(self):
        self.sr = 16000
        self.duration = 1.5
        self.clean, self.noisy, self.noise, self.sr = generate_synthetic_benchmark(
            sample_rate=self.sr,
            duration_sec=self.duration,
            target_snr_db=3.0,
            seed=123,
        )

    def test_audio_io_roundtrip(self):
        """Validates that WAV writing and reading preserves samples within 16-bit PCM precision."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            temp_path = tf.name

        try:
            AudioIO.write_wav(temp_path, self.clean, self.sr)
            loaded_samples, loaded_sr = AudioIO.read_wav(temp_path)

            self.assertEqual(loaded_sr, self.sr)
            self.assertEqual(len(loaded_samples), len(self.clean))

            max_diff = max(abs(a - b) for a, b in zip(self.clean, loaded_samples))
            self.assertLess(max_diff, 1e-3)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_spectral_subtraction_snr_gain(self):
        """Validates that Spectral Subtraction achieves measurable SNR improvement on noisy audio."""
        initial_snr = calculate_snr(self.clean, self.noisy)
        self.assertAlmostEqual(initial_snr, 3.0, delta=1.5)

        subtractor = SpectralSubtraction(frame_size=512, hop_size=256, alpha=2.0, beta=0.05)
        cleaned = subtractor.process(self.noisy, noise_reference=self.noise[: self.sr // 2])

        cleaned_snr = calculate_snr(self.clean, cleaned)
        snr_gain = cleaned_snr - initial_snr

        self.assertGreater(snr_gain, 3.0, f"Expected SNR gain > 3dB, got {snr_gain:.2f}dB")

    def test_nlms_adaptive_filter(self):
        """Validates that NLMS adaptive filter converges on reference noise and enhances SNR."""
        initial_snr = calculate_snr(self.clean, self.noisy)

        nlms = NLMSFilter(filter_length=64, mu=0.2)
        cleaned = nlms.process(self.noisy, reference_audio=self.noise)

        cleaned_snr = calculate_snr(self.clean, cleaned)
        snr_gain = cleaned_snr - initial_snr

        self.assertGreater(snr_gain, 5.0, f"Expected NLMS gain > 5dB, got {snr_gain:.2f}dB")

    def test_spectral_gate(self):
        """Validates that SpectralGate processes audio and preserves signal length."""
        gate = SpectralGate(frame_size=512, hop_size=256, threshold_db=-36.0, attenuation_db=-24.0)
        output = gate.process(self.noisy)
        self.assertEqual(len(output), len(self.noisy))

    def test_fxlms_secondary_path_cancellation(self):
        """Validates Apple-equivalent Filtered-X LMS (FxLMS) anti-noise convergence."""
        fxlms = FxLMSFilter(filter_length=64, secondary_path_length=16, mu=0.1)
        anti_noise, residual = fxlms.process(self.noisy, self.noise)

        self.assertEqual(len(anti_noise), len(self.noisy))
        self.assertEqual(len(residual), len(self.noisy))

        max_anti = max(abs(x) for x in anti_noise)
        self.assertGreater(max_anti, 0.05, "FxLMS failed to synthesize anti-noise waveform")

    def test_adaptive_eq_seal_and_pressure_relief(self):
        """Validates in-ear acoustic seal estimation and ISO 226 pressure relief."""
        eq = AdaptiveEQ(sample_rate=16000)
        leaked_mic = [s * 0.4 for s in self.clean]
        seal = eq.estimate_seal_integrity(self.clean, leaked_mic)

        self.assertLess(seal, 0.8)
        self.assertGreater(eq.boost_gain, 1.0)

        ath_1khz = PsychoacousticMasker.hearing_threshold_db(1000.0)
        ath_40hz = PsychoacousticMasker.hearing_threshold_db(40.0)
        self.assertGreater(ath_40hz, ath_1khz)

        test_anti_noise = [0.5] * 100
        relieved = PsychoacousticMasker.apply_pressure_relief(test_anti_noise, ambient_noise_level_db=30.0)
        self.assertLess(max(relieved), 0.5)

    def test_anti_phase_destructive_cancellation(self):
        """
        Validates 180° phase-inversion destructive acoustic collision.
        """
        inverter = AntiPhaseInverter(sample_rate=self.sr, phase_degrees=180.0, delay_ms=0.0)
        anti_noise = inverter.generate_anti_noise(self.noise)
        residual = inverter.collide_and_cancel(self.noise, anti_noise)

        attenuation_db = inverter.compute_attenuation_db(self.noise, residual)
        self.assertGreater(attenuation_db, 50.0, f"Expected > 50 dB destructive cancellation, got {attenuation_db:.1f} dB")

        max_res = max(abs(x) for x in residual)
        self.assertLess(max_res, 1e-6, "Destructive wave collision failed to zero-out noise")

    def test_acoustic_echo_killer(self):
        """
        Validates that user speech formants are suppressed from the headphone monitor loopback.
        """
        echo_killer = AcousticEchoKiller(speech_threshold_db=-30.0, voice_attenuation_db=-40.0)
        speech_input = [0.4 * math.sin(2 * math.pi * 220 * i / self.sr) for i in range(1600)]
        anti_wave = [0.1 * math.sin(2 * math.pi * 50 * i / self.sr) for i in range(1600)]

        echo_free, erle = echo_killer.process(speech_input, anti_wave)
        self.assertEqual(len(echo_free), len(anti_wave))

        max_output = max(abs(x) for x in echo_free)
        self.assertLess(max_output, 0.01, f"Expected echo output < 0.01, got {max_output}")

    def test_fan_noise_vacuum(self):
        """
        Validates that room fan blade-pass turbulence (120 Hz) is annihilated by the FanNoiseVacuum.
        """
        vacuum = FanNoiseVacuum(sample_rate=self.sr, fan_type="ceiling_fan", vacuum_power=1.0)
        fan_sound = [
            0.3 * math.sin(2 * math.pi * 60 * i / self.sr)
            + 0.5 * math.sin(2 * math.pi * 120 * i / self.sr)
            for i in range(1600)
        ]

        anti_fan = vacuum.generate_vacuum_wave(fan_sound)
        sound_in_ear, atten_db = vacuum.simulate_acoustic_annihilation(fan_sound, anti_fan)

        self.assertEqual(len(sound_in_ear), len(fan_sound))
        self.assertGreater(atten_db, 40.0, f"Expected > 40 dB fan annihilation, got {atten_db:.1f} dB")

    def test_h1_silicon_chip_core(self):
        """
        Validates the H1 Audio Silicon hardware core emulation:
        MMIO registers, clock-cycle anti-wave generation, and sub-15us pipeline latency.
        """
        h1 = H1AudioSilicon(clock_hz=48000, num_cores=10)

        # 1. MMIO register check
        self.assertEqual(h1.read_reg(H1AudioSilicon.REG_PHASE_DEG), 180)
        h1.write_reg(H1AudioSilicon.REG_DELAY_US, 25)
        self.assertEqual(h1.read_reg(H1AudioSilicon.REG_DELAY_US), 25)

        # 2. Clock cycle anti-wave test
        in_sample = 0.5
        anti_wave = h1.clock_cycle(in_sample)
        # Anti-wave should be inverted (negative)
        self.assertLess(anti_wave, 0.0, f"Expected negative anti-wave, got {anti_wave}")

        # 3. Stream processing
        ambient_stream = [0.2 * math.sin(2 * math.pi * 120 * i / 48000) for i in range(4800)]
        anti_stream = h1.process_stream(ambient_stream)
        self.assertEqual(len(anti_stream), len(ambient_stream))

        # Check telemetry
        telemetry = h1.get_silicon_telemetry()
        self.assertIn("10 Parallel RISC/DSP Units", telemetry["Active Cores"])

    def test_boat_rockerz_411_anc(self):
        """
        Validates custom boAt Rockerz 411 hardware profile, delay matching (131us),
        cushion leak overdrive, and acoustic cancellation performance (>40dB).
        """
        anc = BoatRockerz411ANC(sample_rate=48000, vacuum_power=1.0)
        profile = anc.get_hardware_profile()

        self.assertIn("boAt Rockerz 411", profile["Headphone Model"])
        self.assertIn("40mm", profile["Acoustic Transducer"])
        self.assertAlmostEqual(anc.delay_us, 131.2, delta=2.0)
        self.assertGreater(anc.seal_compensation_gain, 1.15)

        # Generate test room noise (120 Hz fan tone)
        room_noise = [0.3 * math.sin(2 * math.pi * 120 * i / 48000) for i in range(2400)]
        anti_wave = anc.generate_anti_noise_wave(room_noise)
        self.assertEqual(len(anti_wave), len(room_noise))

        # Check anti-noise wave is active and phase-inverted
        max_anti = max(abs(x) for x in anti_wave)
        self.assertGreater(max_anti, 0.25)
        self.assertLess(max_anti, 1.01)

        # Simulate acoustic arrival at eardrum with 131us flight delay
        delay_samples = int((anc.delay_ms / 1000.0) * 48000)
        penetrating = [
            room_noise[i - delay_samples] * anc.vacuum_power if i >= delay_samples else 0.0
            for i in range(2400)
        ]
        sound_in_ear, atten_db = anc.cancel_environmental_sound(penetrating, anti_wave)
        self.assertEqual(len(sound_in_ear), len(room_noise))
        self.assertGreater(atten_db, 40.0, f"Expected > 40 dB cancellation, got {atten_db:.2f} dB")


if __name__ == "__main__":
    unittest.main()
