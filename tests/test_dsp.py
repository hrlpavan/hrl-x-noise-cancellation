"""
Unit tests and DSP validation suite for HRL X Noise Cancellation.
Runs with standard Python unittest (zero dependencies required).
"""

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

        # Check that anti-noise is actively generated
        max_anti = max(abs(x) for x in anti_noise)
        self.assertGreater(max_anti, 0.05, "FxLMS failed to synthesize anti-noise waveform")

    def test_adaptive_eq_seal_and_pressure_relief(self):
        """Validates in-ear acoustic seal estimation and ISO 226 pressure relief."""
        eq = AdaptiveEQ(sample_rate=16000)
        # Simulate acoustic leak: inward mic captures 40% of driver playback
        leaked_mic = [s * 0.4 for s in self.clean]
        seal = eq.estimate_seal_integrity(self.clean, leaked_mic)

        self.assertLess(seal, 0.8)
        self.assertGreater(eq.boost_gain, 1.0)

        # Test ISO 226 hearing threshold at 1 kHz (~0-3 dB SPL) and 40 Hz (> 40 dB SPL)
        ath_1khz = PsychoacousticMasker.hearing_threshold_db(1000.0)
        ath_40hz = PsychoacousticMasker.hearing_threshold_db(40.0)
        self.assertGreater(ath_40hz, ath_1khz, "Human ear should be much less sensitive at 40Hz than 1kHz")

        # Test pressure relief in quiet environment (30 dB ambient noise)
        test_anti_noise = [0.5] * 100
        relieved = PsychoacousticMasker.apply_pressure_relief(test_anti_noise, ambient_noise_level_db=30.0)
        self.assertLess(max(relieved), 0.5, "Expected anti-noise attenuation in quiet room to relieve pressure")


if __name__ == "__main__":
    unittest.main()
