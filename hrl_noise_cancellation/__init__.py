"""
HRL X Noise Cancellation
High-performance Digital Signal Processing & Real-Time Noise Suppression Engine.
Copyright (c) 2026 HRL International.
"""

__version__ = "0.9.0"
__author__ = "HRL International"

from .dsp.spectral import SpectralSubtraction, SpectralGate
from .dsp.adaptive import NLMSFilter
from .dsp.fxlms import FxLMSFilter
from .dsp.adaptive_eq import AdaptiveEQ, PsychoacousticMasker
from .dsp.anti_phase import AntiPhaseInverter
from .dsp.echo_cancellation import AcousticEchoKiller
from .dsp.fan_vacuum import FanNoiseVacuum
from .dsp.boat_rockerz_411 import BoatRockerz411ANC
from .dsp.acoustic_barrier import AcousticBlackoutBarrier
from .dsp.predictive_anc import UltraFastPredictiveANC
from .silicon.h1_chip import H1AudioSilicon
from .dsp.audio_io import AudioIO, generate_synthetic_benchmark, calculate_snr

__all__ = [
    "__version__",
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
    "UltraFastPredictiveANC",
    "H1AudioSilicon",
    "AudioIO",
    "generate_synthetic_benchmark",
    "calculate_snr",
]
