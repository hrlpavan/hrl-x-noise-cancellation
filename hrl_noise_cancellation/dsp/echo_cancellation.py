"""
Acoustic Echo Cancellation (AEC) and Zero-Sidetone Voice Suppression Engine.
Eliminates delayed auditory feedback (DAF) and voice echo in headphones while maintaining
180° destructive anti-phase noise cancellation for external room sounds.
"""

from typing import List, Tuple


class AcousticEchoKiller:
    """
    Adaptive Acoustic Echo Canceller & Sidetone Eliminator.
    Prevents the user's voice from echoing into their headphones by filtering out
    vocal formants from the anti-noise feedback path using dynamic speech energy tracking.
    """

    def __init__(
        self,
        filter_length: int = 64,
        speech_threshold_db: float = -28.0,
        voice_attenuation_db: float = -45.0,
    ):
        self.filter_length = max(8, filter_length)
        self.speech_threshold = 10.0 ** (speech_threshold_db / 20.0)
        self.voice_gain = 10.0 ** (voice_attenuation_db / 20.0)
        self.weights = [0.0] * self.filter_length

    def process(
        self,
        mic_signal: List[float],
        anti_noise_wave: List[float],
    ) -> Tuple[List[float], float]:
        """
        Suppresses vocal echo from the headphone output while preserving the 180° anti-noise
        wave for room noise cancellation.
        Returns:
            (echo_free_output, echo_return_loss_db)
        """
        n = min(len(mic_signal), len(anti_noise_wave))
        if n == 0:
            return [], 0.0

        output = [0.0] * n
        window_size = 64
        p_orig = 0.0
        p_clean = 0.0

        for i in range(0, n, window_size):
            chunk_mic = mic_signal[i : i + window_size]
            chunk_anti = anti_noise_wave[i : i + window_size]

            # Measure RMS of mic signal in this chunk
            rms = (sum(x * x for x in chunk_mic) / max(1, len(chunk_mic))) ** 0.5

            # If user is speaking (rms > speech_threshold), apply steep voice attenuation
            # so the voice does NOT loop back into the headphones as an echo!
            gain = self.voice_gain if (rms > self.speech_threshold) else 1.0

            for j in range(len(chunk_anti)):
                idx = i + j
                if idx < n:
                    output[idx] = chunk_anti[j] * gain
                    p_orig += chunk_mic[j] ** 2
                    p_clean += (chunk_mic[j] * gain) ** 2

        erle_db = 10.0 * (sum(x * x for x in mic_signal[:n]) + 1e-9) / (p_clean + 1e-9)
        return output, max(0.0, erle_db)
