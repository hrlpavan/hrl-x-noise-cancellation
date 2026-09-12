"""
DSP algorithms and audio signal utilities for HRL X Noise Cancellation.
Includes Boll Spectral Subtraction, NLMS, Filtered-X LMS (FxLMS), Adaptive EQ,
180° Anti-Phase Destructive Wave Cancellation, Acoustic Echo Cancellation (AEC),
and Fan Noise Vacuum Annihilation.
"""

from .spectral import SpectralSubtraction, SpectralGate
from .adaptive import NLMSFilter
from .fxlms import FxLMSFilter
from .adaptive_eq import AdaptiveEQ, PsychoacousticMasker
from .anti_phase import AntiPhaseInverter
from .echo_cancellation import AcousticEchoKiller
from .fan_vacuum import FanNoiseVacuum
from .boat_rockerz_411 import BoatRockerz411ANC
from .acoustic_barrier import AcousticBlackoutBarrier
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
    "FanNoiseVacuum",
    "BoatRockerz411ANC",
    "AcousticBlackoutBarrier",
    "AudioIO",
    "generate_synthetic_benchmark",
    "calculate_snr",
]
