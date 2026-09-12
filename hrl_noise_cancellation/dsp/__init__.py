"""
DSP algorithms and audio signal utilities for HRL X Noise Cancellation.
Includes Boll Spectral Subtraction, NLMS, Filtered-X LMS (FxLMS), and Adaptive EQ.
"""

from .spectral import SpectralSubtraction, SpectralGate
from .adaptive import NLMSFilter
from .fxlms import FxLMSFilter
from .adaptive_eq import AdaptiveEQ, PsychoacousticMasker
from .audio_io import AudioIO, generate_synthetic_benchmark, calculate_snr

__all__ = [
    "SpectralSubtraction",
    "SpectralGate",
    "NLMSFilter",
    "FxLMSFilter",
    "AdaptiveEQ",
    "PsychoacousticMasker",
    "AudioIO",
    "generate_synthetic_benchmark",
    "calculate_snr",
]
