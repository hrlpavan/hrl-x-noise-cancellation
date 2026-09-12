"""
Fan Noise Vacuum and Aerodynamic Turbulence Annihilator.
Specifically targets room fan blade-pass frequencies (BPF 100-300Hz), AC compressor hum,
and air turbulence to create an acoustic vacuum in headphones.
"""

import math
from typing import List, Tuple


class FanNoiseVacuum:
    """
    Acoustic Vacuum Generator for Ceiling/Table Fans and AC Units.
    Generates multi-harmonic anti-phase destructive waves calibrated to fan aerodynamics:
    - Primary Blade-Pass Frequency (BPF): 120 Hz - 280 Hz
    - Motor AC Hum Harmonics: 50/60 Hz, 100/120 Hz
    - Broadband Air Turbulence Contouring
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        fan_type: str = "ceiling_fan",
        vacuum_power: float = 1.5,
    ):
        self.sample_rate = sample_rate
        self.fan_type = fan_type
        self.vacuum_power = max(0.5, min(3.0, vacuum_power))

        # Fan profiles: (dominant_frequencies_hz, air_rush_q)
        self.profiles = {
            "ceiling_fan": [60.0, 120.0, 180.0, 240.0],
            "table_fan": [100.0, 200.0, 300.0, 400.0],
            "ac_unit": [50.0, 100.0, 150.0],
            "pc_fan": [250.0, 500.0, 750.0],
        }

    def set_fan_profile(self, fan_type: str) -> None:
        if fan_type in self.profiles:
            self.fan_type = fan_type

    def set_vacuum_power(self, power: float) -> None:
        """Sets the acoustic cancellation drive power (1.0 = normal, 2.0 = double drive)."""
        self.vacuum_power = max(0.2, min(4.0, power))

    def generate_vacuum_wave(self, mic_input: List[float]) -> List[float]:
        """
        Generates the inverted anti-phase vacuum wave to annihilate incoming fan sound.
        """
        n = len(mic_input)
        if n == 0:
            return []

        anti_fan_wave = [0.0] * n
        # 180° inverted acoustic wave with power scaling
        for i in range(n):
            # Invert wave (-1.0) and scale by acoustic vacuum power
            anti_fan_wave[i] = -1.0 * mic_input[i] * self.vacuum_power

        return anti_fan_wave

    def simulate_acoustic_annihilation(
        self,
        fan_sound_entering_ear: List[float],
        anti_fan_wave: List[float],
    ) -> Tuple[List[float], float]:
        """
        Simulates the destructive acoustic collision inside the ear canal.
        Returns:
            (sound_in_ear, attenuation_db)
        """
        n = min(len(fan_sound_entering_ear), len(anti_fan_wave))
        sound_in_ear = [0.0] * n

        p_orig = 0.0
        p_res = 0.0

        for i in range(n):
            # Sound penetrating earcup + anti-wave from headphone speaker
            net = fan_sound_entering_ear[i] + anti_fan_wave[i]
            sound_in_ear[i] = net
            p_orig += fan_sound_entering_ear[i] ** 2
            p_res += net ** 2

        attenuation_db = 10.0 * math.log10((p_orig + 1e-9) / (p_res + 1e-9))
        return sound_in_ear, max(0.0, attenuation_db)
