"""
Acoustic Phase Inversion and Destructive Interference Engine.
Captures ambient environmental noise, rotates phase by 180 degrees (anti-phase wave),
applies fractional acoustic delay matching, and creates destructive wave cancellation.
"""

import math
from typing import List, Tuple


class AntiPhaseInverter:
    """
    180° Phase-Rotation Anti-Noise Engine.
    Generates destructive acoustic interference wave:
        x_anti(t) = -A * x(t - tau) = A * sin(omega*t + phi + pi)
    When mixed with incoming environmental noise, both sound waves collide
    destructively and sum to zero:
        x_net(t) = x(t) + x_anti(t) = 0
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        phase_degrees: float = 180.0,
        delay_ms: float = 0.0,
        amplitude_gain: float = 1.0,
    ):
        self.sample_rate = sample_rate
        self.phase_degrees = phase_degrees
        self.delay_ms = max(0.0, delay_ms)
        self.amplitude_gain = max(0.0, amplitude_gain)

    def set_delay_ms(self, delay_ms: float) -> None:
        """Sets acoustic propagation delay in milliseconds (distance from mic to ear canal)."""
        self.delay_ms = max(0.0, delay_ms)

    def set_phase_angle(self, degrees: float) -> None:
        """Sets phase rotation angle (default 180° for complete destructive cancellation)."""
        self.phase_degrees = degrees % 360.0

    def generate_anti_noise(self, mic_noise: List[float]) -> List[float]:
        """
        Generates the 180° phase-inverted anti-noise wave with delay matching.
        """
        n_samples = len(mic_noise)
        if n_samples == 0:
            return []

        # Phase multiplier: 180° is -1.0 (exact destructive inversion)
        rad = math.radians(self.phase_degrees)
        phase_cos = math.cos(rad)

        # Fractional sample delay
        delay_samples = (self.delay_ms / 1000.0) * self.sample_rate
        int_delay = int(math.floor(delay_samples))
        frac_delay = delay_samples - int_delay

        anti_noise = [0.0] * n_samples

        for i in range(n_samples):
            # Delayed sample interpolation
            src_idx = i - int_delay
            if src_idx < 0:
                s0 = 0.0
                s1 = 0.0
            elif src_idx >= n_samples - 1:
                s0 = mic_noise[src_idx] if src_idx < n_samples else 0.0
                s1 = 0.0
            else:
                s0 = mic_noise[src_idx]
                s1 = mic_noise[src_idx + 1]

            # Linear interpolation for fractional sample acoustic distance
            delayed_sample = s0 + frac_delay * (s1 - s0)

            # Invert wave (rotate 180°) and apply calibration gain
            anti_noise[i] = delayed_sample * phase_cos * self.amplitude_gain

        return anti_noise

    def collide_and_cancel(self, environmental_noise: List[float], anti_noise: List[float]) -> List[float]:
        """
        Acoustic collision of original ambient noise and 180° anti-noise wave.
        Returns the residual cancelled sound wave arriving at the listener's eardrum.
        """
        n = min(len(environmental_noise), len(anti_noise))
        return [environmental_noise[i] + anti_noise[i] for i in range(n)]

    def compute_attenuation_db(self, original_noise: List[float], residual_noise: List[float]) -> float:
        """
        Computes the decibel attenuation achieved through destructive wave interference.
        """
        n = min(len(original_noise), len(residual_noise))
        if n == 0:
            return 0.0

        p_orig = sum(x * x for x in original_noise[:n]) + 1e-12
        p_res = sum(x * x for x in residual_noise[:n]) + 1e-12

        attenuation = 10.0 * math.log10(p_orig / p_res)
        return max(0.0, attenuation)
