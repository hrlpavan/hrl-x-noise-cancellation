"""
DSP algorithms and audio signal utilities for HRL X Noise Cancellation.
Includes Boll Spectral Subtraction, NLMS, Filtered-X LMS (FxLMS), Adaptive EQ,
180° Anti-Phase Destructive Wave Cancellation, and Acoustic Echo Cancellation (AEC).
"""

from .spectral import SpectralSubtraction, SpectralGate
from .adaptive import NLMSFilter
from .fxlms import FxLMSFilter
from .adaptive_eq import AdaptiveEQ, PsychoacousticMasker
from .anti_phase import AntiPhaseInverter
from .echo_cancellation import AcousticEchoKiller
from .audio_io import AudioIO, generate_synthetic_benchmark, calculate_snr

__all__ = [
    "SpectralSubtraction",
    "SpectralGate",
    "NLMSFilter",
    "FxLMSFilter",
    "AdaptiveEQ",
    "PsychoacousticMasker",
    "AntiPhaseInverter",
    "AcousticEchoKiller",
    "AudioIO",
    "generate_synthetic_benchmark",
    "calculate_snr",
]
