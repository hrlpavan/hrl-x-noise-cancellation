"""
HRL X Noise Cancellation
High-performance Digital Signal Processing & Real-Time Noise Suppression Engine.
Copyright (c) 2026 HRL International.
"""

__version__ = "0.1.0"
__author__ = "HRL International"

from .dsp.spectral import SpectralSubtraction, SpectralGate
from .dsp.adaptive import NLMSFilter
from .dsp.audio_io import AudioIO, generate_synthetic_benchmark, calculate_snr

__all__ = [
    "__version__",
    "SpectralSubtraction",
    "SpectralGate",
    "NLMSFilter",
    "AudioIO",
    "generate_synthetic_benchmark",
    "calculate_snr",
]
