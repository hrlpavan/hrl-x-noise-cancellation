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

            # Quantization error tolerance for 16-bit PCM (1 / 32767 ≈ 3e-5)
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

        # Ensure that noise was significantly suppressed (gain >= 3 dB)
        self.assertGreater(snr_gain, 3.0, f"Expected SNR gain > 3dB, got {snr_gain:.2f}dB")

    def test_nlms_adaptive_filter(self):
        """Validates that NLMS adaptive filter converges on reference noise and enhances SNR."""
        initial_snr = calculate_snr(self.clean, self.noisy)

        nlms = NLMSFilter(filter_length=64, mu=0.2)
        cleaned = nlms.process(self.noisy, reference_audio=self.noise)

        cleaned_snr = calculate_snr(self.clean, cleaned)
        snr_gain = cleaned_snr - initial_snr

        # Dual-channel reference cancellation should achieve > 5 dB gain
        self.assertGreater(snr_gain, 5.0, f"Expected NLMS gain > 5dB, got {snr_gain:.2f}dB")

    def test_spectral_gate(self):
        """Validates that SpectralGate processes audio and preserves signal length."""
        gate = SpectralGate(frame_size=512, hop_size=256, threshold_db=-36.0, attenuation_db=-24.0)
        output = gate.process(self.noisy)
        self.assertEqual(len(output), len(self.noisy))


if __name__ == "__main__":
    unittest.main()
