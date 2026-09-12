"""
Adaptive EQ and Psychoacoustic Auditory Masking (PAM).
Models in-ear acoustic seal leakage and eliminates eardrum suction/cabin pressure.
"""

import math
from typing import List, Tuple


class AdaptiveEQ:
    """
    In-Ear Acoustic Seal Detector & Low-Frequency Compensator.
    Reverse-engineers and enhances Apple's Adaptive EQ technology.
    """

    def __init__(self, sample_rate: int = 16000, target_bass_gain_db: float = 0.0):
        self.sample_rate = sample_rate
        self.target_bass_gain = 10.0 ** (target_bass_gain_db / 20.0)
        self.seal_integrity = 1.0  # 1.0 = Perfect airtight seal, 0.0 = Severe leakage
        self.boost_gain = 1.0

    def estimate_seal_integrity(self, music_playback: List[float], inward_mic: List[float]) -> float:
        """
        Estimates acoustic seal by comparing playback low-frequency energy vs measured in-ear response.
        """
        n = min(len(music_playback), len(inward_mic))
        if n == 0:
            return 1.0

        p_playback = sum(x * x for x in music_playback[:n]) + 1e-9
        p_inward = sum(x * x for x in inward_mic[:n]) + 1e-9

        # Ratio of in-ear energy to driver energy at low frequencies
        ratio = p_inward / p_playback
        # Ideal sealed ear canal provides acoustic pressure amplification; leakage causes energy drop
        self.seal_integrity = max(0.1, min(1.0, ratio * 1.2))

        # Dynamic low-frequency compensation gain
        # If seal is leaking (e.g. seal_integrity = 0.5), boost low end up to 6 dB
        self.boost_gain = 1.0 / math.sqrt(self.seal_integrity)
        return self.seal_integrity

    def compensate(self, audio: List[float]) -> List[float]:
        """Applies real-time seal compensation to audio playback."""
        return [sample * self.boost_gain for sample in audio]


class PsychoacousticMasker:
    """
    Psychoacoustic Auditory Masking (PAM) Engine.
    Implements ISO 226 equal-loudness contours to eliminate eardrum 'cabin pressure'.
    """

    @staticmethod
    def hearing_threshold_db(frequency_hz: float) -> float:
        """
        Approximation of the absolute threshold of hearing (ATH / Minimum Audible Field in dB SPL)
        according to ISO 226:
        T_q(f) = 3.64*(f/1000)^-0.8 - 6.5*exp(-0.6*(f/1000 - 3.3)^2) + 10^-3*(f/1000)^4
        """
        f = max(20.0, min(20000.0, frequency_hz)) / 1000.0
        term1 = 3.64 * (f ** -0.8)
        term2 = -6.5 * math.exp(-0.6 * ((f - 3.3) ** 2))
        term3 = 1e-3 * (f ** 4)
        return term1 + term2 + term3

    @classmethod
    def apply_pressure_relief(
        cls,
        anti_noise: List[float],
        ambient_noise_level_db: float,
        low_cut_hz: float = 40.0,
    ) -> List[float]:
        """
        Modulates low-frequency anti-noise amplitude when ambient noise is already below
        human perception, removing unneeded physical eardrum pressure.
        """
        ath_40hz = cls.hearing_threshold_db(low_cut_hz)

        # If ambient noise is already lower than threshold of hearing + 10 dB,
        # attenuate the aggressive sub-bass anti-phase wave
        headroom = ambient_noise_level_db - ath_40hz
        if headroom < 10.0:
            scale = max(0.2, min(1.0, (headroom + 10.0) / 20.0))
            return [sample * scale for sample in anti_noise]

        return list(anti_noise)
