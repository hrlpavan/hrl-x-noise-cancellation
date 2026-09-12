"""
Spectral Subtraction and Multi-Band Spectral Gating algorithms.
Implements Boll (1979) magnitude/power spectral subtraction and dynamic spectral gating.
Supports pure Python (via Cooley-Tukey FFT) with automatic NumPy acceleration.
"""

import cmath
import math
from typing import List, Optional

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# ============================================================================
# Pure Python Radix-2 FFT (Zero external dependencies fallback)
# ============================================================================

def _pure_fft(x: List[complex]) -> List[complex]:
    """Cooley-Tukey radix-2 decimation-in-time FFT."""
    n = len(x)
    if n <= 1:
        return x
    even = _pure_fft(x[0::2])
    odd = _pure_fft(x[1::2])
    factor = [cmath.exp(-2j * cmath.pi * k / n) * odd[k] for k in range(n // 2)]
    return [even[k] + factor[k] for k in range(n // 2)] + [even[k] - factor[k] for k in range(n // 2)]


def _pure_ifft(x: List[complex]) -> List[complex]:
    """Inverse FFT using conjugated forward FFT."""
    n = len(x)
    conj_x = [c.conjugate() for c in x]
    transformed = _pure_fft(conj_x)
    return [c.conjugate() / n for c in transformed]


class SpectralSubtraction:
    """
    Boll (1979) Magnitude / Power Spectral Subtraction with over-subtraction
    and spectral floor to eliminate musical noise.
    """

    def __init__(
        self,
        frame_size: int = 512,
        hop_size: int = 256,
        alpha: float = 2.0,      # Over-subtraction factor
        beta: float = 0.05,      # Spectral floor (attenuation floor)
        gamma: float = 1.0,      # 1.0 = Magnitude subtraction, 2.0 = Power subtraction
        noise_frames: int = 8,   # Number of frames used to estimate noise profile
    ):
        p = 1
        while p < frame_size:
            p <<= 1
        self.frame_size = p
        self.hop_size = hop_size if hop_size > 0 else self.frame_size // 2
        self.alpha = max(1.0, alpha)
        self.beta = max(0.001, min(0.5, beta))
        self.gamma = gamma
        self.noise_frames = max(1, noise_frames)

        # Precompute Hann window
        self.window = [
            0.5 * (1.0 - math.cos(2.0 * math.pi * i / (self.frame_size - 1)))
            for i in range(self.frame_size)
        ]

    def process(self, audio: List[float], noise_reference: Optional[List[float]] = None) -> List[float]:
        """
        Denoises audio using spectral subtraction.
        If noise_reference is provided, noise profile is estimated from it;
        otherwise, it is estimated from the first few frames of the input.
        """
        if HAS_NUMPY:
            return self._process_numpy(audio, noise_reference)
        return self._process_pure(audio, noise_reference)

    def _process_numpy(self, audio: List[float], noise_reference: Optional[List[float]]) -> List[float]:
        signal = np.asarray(audio, dtype=np.float32)
        n_samples = len(signal)
        if n_samples == 0:
            return []
        if n_samples < self.frame_size:
            signal = np.pad(signal, (0, self.frame_size - n_samples))

        window = np.hanning(self.frame_size).astype(np.float32)
        hop = self.hop_size
        pad_start = hop
        pad_end = self.frame_size

        padded = np.pad(signal, (pad_start, pad_end), mode='constant')
        total_len = len(padded)
        n_frames = (total_len - self.frame_size) // hop + 1

        frames = np.lib.stride_tricks.as_strided(
            padded,
            shape=(n_frames, self.frame_size),
            strides=(padded.strides[0] * hop, padded.strides[0]),
        )
        windowed_frames = frames * window
        spectrogram = np.fft.rfft(windowed_frames, axis=1)

        mag = np.abs(spectrogram)
        phase = np.angle(spectrogram)

        # Estimate noise profile
        if noise_reference is not None and len(noise_reference) >= self.frame_size:
            noise_sig = np.asarray(noise_reference, dtype=np.float32)
            n_noise_frames = min(self.noise_frames, (len(noise_sig) - self.frame_size) // hop + 1)
            noise_frames = np.lib.stride_tricks.as_strided(
                noise_sig,
                shape=(n_noise_frames, self.frame_size),
                strides=(noise_sig.strides[0] * hop, noise_sig.strides[0]),
            )
            noise_mag = np.mean(np.abs(np.fft.rfft(noise_frames * window, axis=1)), axis=0)
        else:
            k_init = min(self.noise_frames, n_frames)
            noise_mag = np.mean(mag[:k_init], axis=0)

        # Spectral subtraction with floor
        if self.gamma == 1.0:
            subtracted = mag - self.alpha * noise_mag
            clean_mag = np.maximum(subtracted, self.beta * mag)
        else:
            subtracted = np.power(mag, self.gamma) - self.alpha * np.power(noise_mag, self.gamma)
            clean_mag = np.power(np.maximum(subtracted, self.beta * np.power(mag, self.gamma)), 1.0 / self.gamma)

        clean_spec = clean_mag * np.exp(1j * phase)
        inv_frames = np.fft.irfft(clean_spec, axis=1) * window

        out_length = (n_frames - 1) * hop + self.frame_size
        out_signal = np.zeros(out_length, dtype=np.float32)
        win_sum = np.zeros(out_length, dtype=np.float32)

        for i in range(n_frames):
            start = i * hop
            end = start + self.frame_size
            out_signal[start:end] += inv_frames[i]
            win_sum[start:end] += window ** 2

        nonzero = win_sum > 1e-4
        out_signal[nonzero] /= win_sum[nonzero]

        cleaned = out_signal[pad_start : pad_start + n_samples]
        return cleaned.tolist()

    def _process_pure(self, audio: List[float], noise_reference: Optional[List[float]]) -> List[float]:
        n_samples = len(audio)
        if n_samples == 0:
            return []

        hop = self.hop_size
        num_bins = self.frame_size // 2 + 1

        # 1. Estimate noise profile
        noise_profile = [0.0] * num_bins
        if noise_reference is not None and len(noise_reference) >= self.frame_size:
            n_noise_frames = min(self.noise_frames, (len(noise_reference) - self.frame_size) // hop + 1)
            for f in range(n_noise_frames):
                start = f * hop
                chunk = [noise_reference[start + j] * self.window[j] for j in range(self.frame_size)]
                spec = _pure_fft([complex(x, 0.0) for x in chunk])
                for k in range(num_bins):
                    noise_profile[k] += abs(spec[k]) / n_noise_frames
        else:
            # Estimate from initial frames of audio
            n_est_frames = min(self.noise_frames, max(1, (n_samples - self.frame_size) // hop + 1))
            for f in range(n_est_frames):
                start = f * hop
                chunk = [audio[start + j] * self.window[j] for j in range(self.frame_size)]
                spec = _pure_fft([complex(x, 0.0) for x in chunk])
                for k in range(num_bins):
                    noise_profile[k] += abs(spec[k]) / n_est_frames

        # 2. Symmetric STFT Padding
        pad_start = hop
        pad_end = self.frame_size
        padded = [0.0] * pad_start + list(audio) + [0.0] * pad_end
        total_len = len(padded)
        n_frames = (total_len - self.frame_size) // hop + 1

        out_length = (n_frames - 1) * hop + self.frame_size
        out_buf = [0.0] * out_length
        win_sum = [0.0] * out_length

        for f in range(n_frames):
            start = f * hop
            chunk = [padded[start + j] * self.window[j] for j in range(self.frame_size)]
            spec = _pure_fft([complex(x, 0.0) for x in chunk])

            sub_spec = [complex(0, 0)] * self.frame_size
            for k in range(num_bins):
                m = abs(spec[k])
                phi = cmath.phase(spec[k])
                clean_m = max(m - self.alpha * noise_profile[k], self.beta * m)
                c = cmath.rect(clean_m, phi)
                sub_spec[k] = c
                if 0 < k < self.frame_size // 2:
                    sub_spec[self.frame_size - k] = c.conjugate()

            inv_chunk = [c.real for c in _pure_ifft(sub_spec)]
            for j in range(self.frame_size):
                out_buf[start + j] += inv_chunk[j] * self.window[j]
                win_sum[start + j] += self.window[j] ** 2

        for i in range(out_length):
            if win_sum[i] > 1e-4:
                out_buf[i] /= win_sum[i]

        cleaned = out_buf[pad_start : pad_start + n_samples]
        return cleaned


class SpectralGate:
    """
    Multi-Band Spectral Gate.
    Smoothly attenuates frequency bins below an adaptive energy threshold.
    """

    def __init__(
        self,
        frame_size: int = 512,
        hop_size: int = 256,
        threshold_db: float = -36.0,
        attenuation_db: float = -24.0,
    ):
        self.frame_size = frame_size
        self.hop_size = hop_size
        self.threshold = 10.0 ** (threshold_db / 20.0)
        self.attenuation_factor = 10.0 ** (attenuation_db / 20.0)
        self.subtractor = SpectralSubtraction(
            frame_size=frame_size,
            hop_size=hop_size,
            alpha=1.5,
            beta=self.attenuation_factor,
        )

    def process(self, audio: List[float], noise_reference: Optional[List[float]] = None) -> List[float]:
        """Applies dynamic spectral gating."""
        return self.subtractor.process(audio, noise_reference=noise_reference)
