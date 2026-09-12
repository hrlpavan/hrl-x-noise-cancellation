"""
Branch Education Acoustic Physics & Superposition Blueprint Engine.
Implements the core physical and acoustic laws of Active Noise Cancellation:
1. Compressions & Rarefactions: Air molecule longitudinal pressure oscillations (ΔP).
2. Wavelength vs Frequency: λ = c / f, spatial phase alignment tolerance.
3. Constructive vs Destructive Interference Boundary: 4*sin^2(Δθ/2).
4. High-Frequency Anti-Constructive Safety Guard (crossover to passive foam damping).
5. Linear Superposition Principle: s_speaker = s_music - x_noise => p_ear = s_music.
"""

import math
from typing import Any, Dict, List, Tuple


class BranchAcousticPhysics:
    """
    Mathematical and physical acoustics model based on the Branch Education
    Noise Cancellation engineering blueprint.
    """

    SPEED_OF_SOUND_M_S: float = 343.0  # Speed of sound in dry room air at 20°C
    ATMOSPHERIC_PRESSURE_PA: float = 101325.0  # Standard ambient pressure P0
    AIR_DENSITY_KG_M3: float = 1.2041  # Air density rho_0 at 20°C

    @classmethod
    def calculate_wavelength(cls, freq_hz: float) -> float:
        """
        Calculates physical acoustic wavelength λ = c / f (in meters).
        Example: 100 Hz => 3.43 m, 1000 Hz => 0.343 m (34.3 cm).
        """
        f = max(float(freq_hz), 1e-6)
        return cls.SPEED_OF_SOUND_M_S / f

    @classmethod
    def calculate_phase_error(cls, freq_hz: float, delay_seconds: float) -> float:
        """
        Calculates spatial/temporal phase alignment error in radians:
        Δθ = 2 * π * f * Δt
        """
        return 2.0 * math.pi * float(freq_hz) * float(delay_seconds)

    @classmethod
    def calculate_interference_power(
        cls, freq_hz: float, delay_seconds: float
    ) -> Tuple[str, float, float]:
        """
        Computes the acoustic interference result when an anti-phase wave (180°)
        collides with incoming noise having a timing offset Δt:
        
        Residual Power Ratio: P_ratio = 4 * sin^2(Δθ / 2)
        - Δθ < 60° (π/3)  => DESTRUCTIVE (Noise reduced, P_ratio < 1.0, attenuation < 0 dB)
        - Δθ = 60° (π/3)  => NEUTRAL (0 dB, cancellation limit)
        - Δθ > 60°        => CONSTRUCTIVE (Noise amplified up to +6 dB / 2x pressure, +2P)
        
        Returns:
            Tuple of (regime_name, power_ratio, attenuation_db)
        """
        d_theta = cls.calculate_phase_error(freq_hz, delay_seconds)
        # Power ratio between residual acoustic wave and incoming noise wave
        p_ratio = 4.0 * (math.sin(d_theta / 2.0) ** 2)

        if p_ratio < 0.999:
            regime = "DESTRUCTIVE"
        elif p_ratio <= 1.001:
            regime = "BOUNDARY"
        else:
            regime = "CONSTRUCTIVE"

        # Limit to -60 dB floor for clean logging
        db = 10.0 * math.log10(max(p_ratio, 1e-6))
        return regime, p_ratio, db

    @classmethod
    def calculate_coherence_limit(
        cls, delay_seconds: float, max_phase_error_deg: float = 60.0
    ) -> float:
        """
        Calculates the maximum safe operational frequency f_crit where Active
        Noise Cancellation remains destructive before risk of constructive amplification:
        f_crit = (max_phase_error_rad) / (2 * π * Δt)
        
        For boAt Rockerz 411 (131.2 μs delay) and 60° phase error:
        f_crit = (π / 3) / (2 * π * 131.2e-6) ≈ 1,270 Hz.
        """
        max_error_rad = math.radians(max_phase_error_deg)
        dt = max(float(delay_seconds), 1e-9)
        return max_error_rad / (2.0 * math.pi * dt)

    @classmethod
    def anti_constructive_filter(
        cls, samples: List[float], sample_rate: int, cutoff_hz: float = 1200.0
    ) -> List[float]:
        """
        2nd-order Butterworth IIR Lowpass filter designed to attenuate anti-noise
        above the spatial coherence limit (e.g. 1,200 Hz).
        Prevents constructive interference (+2P doubling) and high-frequency hiss.
        """
        n = len(samples)
        if n == 0:
            return []

        # Biquad Butterworth low-pass coefficients
        omega = 2.0 * math.pi * cutoff_hz / sample_rate
        sn = math.sin(omega)
        cs = math.cos(omega)
        alpha = sn / (2.0 * math.sqrt(2.0))

        b0 = (1.0 - cs) / 2.0
        b1 = 1.0 - cs
        b2 = (1.0 - cs) / 2.0
        a0 = 1.0 + alpha
        a1 = -2.0 * cs
        a2 = 1.0 - alpha

        # Normalize by a0
        b0 /= a0
        b1 /= a0
        b2 /= a0
        a1 /= a0
        a2 /= a0

        out = [0.0] * n
        x1 = x2 = y1 = y2 = 0.0

        for i in range(n):
            x0 = samples[i]
            y0 = b0 * x0 + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            out[i] = y0
            x2 = x1
            x1 = x0
            y2 = y1
            y1 = y0

        return out

    @classmethod
    def superposition_audio_mix(
        cls,
        music_samples: List[float],
        ambient_noise_samples: List[float],
        anti_noise_samples: List[float],
    ) -> Dict[str, Any]:
        """
        Demonstrates the Linear Superposition Principle from Branch Education:
        
        1. Headphone Speaker Output (Electrical -> Acoustic):
           s_speaker(t) = s_music(t) + s_anti_noise(t)
           where s_anti_noise(t) = -x_noise(t)
        
        2. Acoustic Summation in the Ear Canal (Physical Air):
           p_ear(t) = s_speaker(t) + x_ambient_noise(t)
                    = [s_music(t) + s_anti_noise(t)] + x_ambient_noise(t)
                    = s_music(t) + [x_ambient_noise(t) - x_noise(t)]
                    = s_music(t)  (Prism of Silence + Pure Music)
        
        Returns:
            Dict containing:
            - 'speaker_signal': Composite driver signal
            - 'ear_pressure': Net acoustic pressure at eardrum
            - 'residual_noise': p_ear - s_music
            - 'ambient_noise_attenuation_db': Net attenuation of ambient noise
            - 'music_fidelity_snr_db': Signal-to-Distortion of music reproduction
        """
        length = min(len(music_samples), len(ambient_noise_samples), len(anti_noise_samples))
        if length == 0:
            return {
                "speaker_signal": [],
                "ear_pressure": [],
                "residual_noise": [],
                "ambient_noise_attenuation_db": 0.0,
                "music_fidelity_snr_db": 100.0,
            }

        speaker_signal = [0.0] * length
        ear_pressure = [0.0] * length
        residual_noise = [0.0] * length

        p_noise_in = 0.0
        p_noise_res = 0.0
        p_music = 0.0
        p_distortion = 0.0

        for i in range(length):
            m = music_samples[i]
            n = ambient_noise_samples[i]
            a = anti_noise_samples[i]

            # Speaker transmits both music and anti-noise wave
            spk = m + a
            speaker_signal[i] = spk

            # At the eardrum, speaker wave collides with physical incoming noise wave
            p = spk + n
            ear_pressure[i] = p

            # Residual noise is whatever deviates from intended music
            res = p - m
            residual_noise[i] = res

            p_noise_in += n * n
            p_noise_res += res * res
            p_music += m * m
            p_distortion += (p - m) * (p - m)

        p_noise_in = max(p_noise_in, 1e-12)
        p_noise_res = max(p_noise_res, 1e-12)
        p_music = max(p_music, 1e-12)
        p_distortion = max(p_distortion, 1e-12)

        attenuation_db = 10.0 * math.log10(p_noise_res / p_noise_in)
        music_snr_db = 10.0 * math.log10(p_music / p_distortion)

        return {
            "speaker_signal": speaker_signal,
            "ear_pressure": ear_pressure,
            "residual_noise": residual_noise,
            "ambient_noise_attenuation_db": attenuation_db,
            "music_fidelity_snr_db": music_snr_db,
        }
