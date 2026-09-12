"""
Adaptive Filtering for Acoustic Noise Cancellation (ANC).
Implements Normalized Least Mean Squares (NLMS) with dual-mic and single-channel
Adaptive Line Enhancer (ALE) modes.
"""

from typing import List, Optional, Tuple


class NLMSFilter:
    """
    Normalized Least Mean Squares (NLMS) Adaptive Filter.
    Supports:
    1. Dual-channel ANC (Primary mic: Speech + Noise; Reference mic: Correlated Noise)
    2. Single-channel Adaptive Line Enhancer (ALE) for tonal/hum cancellation
    """

    def __init__(
        self,
        filter_length: int = 64,
        mu: float = 0.2,            # Step-size (learning rate)
        epsilon: float = 1e-4,      # Regularization term
        delay: int = 16,            # Decorrelation delay for single-channel ALE
    ):
        self.filter_length = max(4, filter_length)
        self.mu = max(0.001, min(1.0, mu))
        self.epsilon = max(1e-9, epsilon)
        self.delay = max(1, delay)
        self.weights = [0.0] * self.filter_length

    def reset(self) -> None:
        """Resets filter weights to zero."""
        self.weights = [0.0] * self.filter_length

    def filter_sample(self, primary: float, reference: float, x_buffer: List[float]) -> Tuple[float, float]:
        """
        Processes one sample.
        Args:
            primary: d[n] = signal + noise
            reference: x[n] = correlated noise reference
            x_buffer: ring buffer of past reference samples of size filter_length
        Returns:
            (e[n], y[n]): error (cleaned signal) and estimated noise
        """
        # Estimated noise: y[n] = w^T * x
        y = sum(self.weights[i] * x_buffer[i] for i in range(self.filter_length))
        # Error signal: e[n] = d[n] - y[n]
        e = primary - y

        # Energy of reference vector: ||x||^2
        energy = sum(x * x for x in x_buffer)

        # NLMS weight update: w[n+1] = w[n] + (mu / (energy + eps)) * e * x
        norm_factor = self.mu / (energy + self.epsilon)
        for i in range(self.filter_length):
            self.weights[i] += norm_factor * e * x_buffer[i]

        return e, y

    def process(
        self,
        primary_audio: List[float],
        reference_audio: Optional[List[float]] = None,
    ) -> List[float]:
        """
        Processes entire audio buffer.
        If reference_audio is None, uses Adaptive Line Enhancer (ALE) with delay.
        """
        n_samples = len(primary_audio)
        cleaned = [0.0] * n_samples
        x_buf = [0.0] * self.filter_length

        if reference_audio is not None and len(reference_audio) >= n_samples:
            # Dual-channel reference mode
            for i in range(n_samples):
                ref = reference_audio[i]
                x_buf.pop()
                x_buf.insert(0, ref)
                e, _ = self.filter_sample(primary_audio[i], ref, x_buf)
                cleaned[i] = e
        else:
            # Single-channel Adaptive Line Enhancer (ALE) mode
            # Reference is delayed primary signal
            delay_buf = [0.0] * self.delay
            for i in range(n_samples):
                d = primary_audio[i]
                delayed_ref = delay_buf.pop()
                delay_buf.insert(0, d)

                x_buf.pop()
                x_buf.insert(0, delayed_ref)
                e, _ = self.filter_sample(d, delayed_ref, x_buf)
                # In ALE mode for narrowband noise cancellation, error e contains broadband speech
                cleaned[i] = e

        return cleaned
