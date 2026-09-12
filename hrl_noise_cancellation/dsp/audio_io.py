"""
Standard library audio I/O, synthetic signal generation, and SNR metrics.
Built with zero external dependencies, with optional NumPy acceleration.
"""

import math
import random
import struct
import wave
from typing import List, Tuple, Union

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class AudioIO:
    """Read and write standard 16-bit PCM WAV files using standard library."""

    @staticmethod
    def read_wav(filepath: str) -> Tuple[List[float], int]:
        """Reads a WAV file and returns normalized float samples in [-1.0, 1.0] and sample rate."""
        with wave.open(filepath, "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw_data = wf.readframes(n_frames)

        if sampwidth != 2:
            raise ValueError(f"Only 16-bit PCM WAV supported, found sampwidth={sampwidth}")

        total_samples = n_frames * n_channels
        fmt = f"<{total_samples}h"
        int16_samples = struct.unpack(fmt, raw_data)

        # Convert to mono if multi-channel by averaging
        if n_channels == 1:
            samples = [s / 32768.0 for s in int16_samples]
        else:
            mono = []
            for i in range(0, total_samples, n_channels):
                avg = sum(int16_samples[i:i + n_channels]) / (n_channels * 32768.0)
                mono.append(avg)
            samples = mono

        return samples, framerate

    @staticmethod
    def write_wav(filepath: str, samples: Union[List[float], "np.ndarray"], sample_rate: int = 16000) -> None:
        """Writes normalized float samples [-1.0, 1.0] to a 16-bit mono PCM WAV file."""
        if HAS_NUMPY and isinstance(samples, np.ndarray):
            clamped = np.clip(samples, -1.0, 1.0)
            int16_data = (clamped * 32767.0).astype(np.int16).tobytes()
        else:
            int16_list = []
            for s in samples:
                val = max(-1.0, min(1.0, float(s)))
                int16_list.append(int(val * 32767.0))
            int16_data = struct.pack(f"<{len(int16_list)}h", *int16_list)

        with wave.open(filepath, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(int16_data)


def generate_synthetic_benchmark(
    sample_rate: int = 16000,
    duration_sec: float = 2.5,
    target_snr_db: float = 3.0,
    seed: int = 42,
) -> Tuple[List[float], List[float], List[float], int]:
    """
    Generates a deterministic synthetic audio benchmark:
    - Clean Speech: Harmonic formant series (f0=220Hz, 440Hz, 880Hz, 1320Hz)
      modulated by a realistic syllabic amplitude envelope.
    - Noise Interference: Stationary Gaussian white noise + 50Hz mains hum.
    Returns:
      (clean_signal, noisy_signal, noise_signal, sample_rate)
    """
    random.seed(seed)
    total_samples = int(sample_rate * duration_sec)
    clean = [0.0] * total_samples
    noise = [0.0] * total_samples

    # 1. Synthesize harmonic voice signal
    f0 = 220.0
    for i in range(total_samples):
        t = i / sample_rate
        # Syllabic envelope: 3 syllables per second with soft pauses
        syllable_env = max(0.0, math.sin(2.0 * math.pi * 1.5 * t)) ** 2
        # Voice harmonics (simulating vocal cord vibrations + formants)
        voice = (
            0.50 * math.sin(2.0 * math.pi * f0 * t)
            + 0.25 * math.sin(2.0 * math.pi * 2 * f0 * t)
            + 0.15 * math.sin(2.0 * math.pi * 4 * f0 * t)
            + 0.10 * math.sin(2.0 * math.pi * 6 * f0 * t)
        )
        clean[i] = voice * syllable_env

    # 2. Synthesize interference (50Hz powerline hum + Gaussian noise)
    hum_freq = 50.0
    for i in range(total_samples):
        t = i / sample_rate
        hum = 0.3 * math.sin(2.0 * math.pi * hum_freq * t) + 0.1 * math.sin(2.0 * math.pi * 2 * hum_freq * t)
        # Box-Muller standard normal random noise
        u1 = max(1e-9, random.random())
        u2 = random.random()
        gauss = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        noise[i] = hum + 0.7 * gauss

    # 3. Scale noise to match exact target SNR
    p_clean = sum(x * x for x in clean) / total_samples
    p_noise = sum(x * x for x in noise) / total_samples

    if p_clean > 0 and p_noise > 0:
        desired_noise_p = p_clean / (10.0 ** (target_snr_db / 10.0))
        scale = math.sqrt(desired_noise_p / p_noise)
        noise = [n * scale for n in noise]

    noisy = [clean[i] + noise[i] for i in range(total_samples)]

    # Normalize clean and noisy to prevent clipping
    max_amp = max(max(abs(x) for x in noisy), 1e-6)
    if max_amp > 0.95:
        norm_factor = 0.90 / max_amp
        clean = [c * norm_factor for c in clean]
        noise = [n * norm_factor for n in noise]
        noisy = [ny * norm_factor for ny in noisy]

    return clean, noisy, noise, sample_rate


def calculate_snr(clean: List[float], processed: List[float]) -> float:
    """
    Computes Signal-to-Noise Ratio (SNR) in decibels (dB):
    SNR = 10 * log10( sum(clean^2) / sum((clean - processed)^2) )
    """
    n = min(len(clean), len(processed))
    if n == 0:
        return 0.0

    p_clean = sum(clean[i] * clean[i] for i in range(n))
    error_p = sum((clean[i] - processed[i]) ** 2 for i in range(n))

    if error_p < 1e-12:
        return 100.0  # Perfect reconstruction
    if p_clean < 1e-12:
        return 0.0

    return 10.0 * math.log10(p_clean / error_p)
