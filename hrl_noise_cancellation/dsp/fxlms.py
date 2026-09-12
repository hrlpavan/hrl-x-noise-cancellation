"""
Filtered-X Least Mean Squares (FxLMS) Adaptive Filter.
Implements Apple's core active noise cancellation algorithm with secondary path
estimation (S(z)) and HRL's normalized leaky weight update for guaranteed stability.
"""

from typing import List, Optional, Tuple


class FxLMSFilter:
    """
    Normalized Leaky Filtered-X Least Mean Squares (FxLMS) Engine.
    Models primary acoustic path P(z) and secondary speaker-to-earpath S(z).
    """

    def __init__(
        self,
        filter_length: int = 64,
        secondary_path_length: int = 16,
        mu: float = 0.15,          # Learning rate
        leakage: float = 1e-4,     # Leakage factor (guarantees loop stability)
        epsilon: float = 1e-4,     # Regularization term
    ):
        self.filter_length = max(8, filter_length)
        self.sec_length = max(4, secondary_path_length)
        self.mu = max(0.001, min(1.0, mu))
        self.leakage = max(0.0, min(0.01, leakage))
        self.epsilon = max(1e-9, epsilon)

        # Primary anti-noise adaptive weights W(z)
        self.weights = [0.0] * self.filter_length

        # Secondary path model S_hat(z) (speaker -> ear canal -> error mic)
        # Default: delayed impulse response approximating earbud cavity resonance
        self.s_hat = [0.0] * self.sec_length
        self.s_hat[0] = 0.85
        if self.sec_length > 1:
            self.s_hat[1] = -0.35
        if self.sec_length > 2:
            self.s_hat[2] = 0.15

        # Ring buffers
        self.x_buf = [0.0] * self.filter_length      # Raw reference noise
        self.x_filt_buf = [0.0] * self.filter_length # Filtered reference x'(n) = S_hat * x
        self.sec_in_buf = [0.0] * self.sec_length    # Buffer for S_hat filtering

    def set_secondary_path(self, impulse_response: List[float]) -> None:
        """Configures the estimated secondary acoustic path transfer function S_hat(z)."""
        n = min(len(impulse_response), self.sec_length)
        for i in range(n):
            self.s_hat[i] = float(impulse_response[i])

    def filter_sample(self, ref_sample: float, error_sample: float) -> Tuple[float, float]:
        """
        Processes one time step.
        Args:
            ref_sample: External feedforward mic input x(n)
            error_sample: Inward-facing error mic input e(n) = d(n) - y'(n)
        Returns:
            (anti_noise, cleaned_error): Output driver signal y(n) and residual error e(n)
        """
        # 1. Update raw reference buffer
        self.x_buf.pop()
        self.x_buf.insert(0, ref_sample)

        # 2. Compute anti-noise driver output: y(n) = w^T * x
        anti_noise = sum(self.weights[i] * self.x_buf[i] for i in range(self.filter_length))

        # 3. Compute filtered reference x'(n) = S_hat * x
        self.sec_in_buf.pop()
        self.sec_in_buf.insert(0, ref_sample)
        filtered_ref = sum(self.s_hat[j] * self.sec_in_buf[j] for j in range(self.sec_length))

        self.x_filt_buf.pop()
        self.x_filt_buf.insert(0, filtered_ref)

        # 4. Energy of filtered reference: ||x'||^2
        energy = sum(x * x for x in self.x_filt_buf)

        # 5. Normalized Leaky FxLMS weight update:
        # w(n+1) = (1 - mu * leakage) * w(n) + (mu / (||x'||^2 + eps)) * e(n) * x'(n)
        leak_factor = 1.0 - (self.mu * self.leakage)
        norm_factor = self.mu / (energy + self.epsilon)

        for i in range(self.filter_length):
            self.weights[i] = (self.weights[i] * leak_factor) + (norm_factor * error_sample * self.x_filt_buf[i])

        return anti_noise, error_sample

    def process(
        self,
        primary_audio: List[float],
        reference_noise: List[float],
    ) -> Tuple[List[float], List[float]]:
        """
        Batch processes a block of audio.
        Returns:
            (anti_noise_stream, residual_error_stream)
        """
        n_samples = min(len(primary_audio), len(reference_noise))
        anti_noise_out = [0.0] * n_samples
        residual_error_out = [0.0] * n_samples

        # Simulation of acoustic secondary path for validation
        plant_buf = [0.0] * self.sec_length

        for i in range(n_samples):
            x = reference_noise[i]
            d = primary_audio[i]

            # In acoustic physics: e(n) = d(n) - S(z)*y(n)
            # Compute past driver sound arriving at error mic
            s_arrived = sum(self.s_hat[j] * plant_buf[j] for j in range(self.sec_length))
            e_measured = d - s_arrived

            y, _ = self.filter_sample(x, e_measured)
            anti_noise_out[i] = y
            residual_error_out[i] = e_measured

            plant_buf.pop()
            plant_buf.insert(0, y)

        return anti_noise_out, residual_error_out
