# Anush X HRL

> **High-Performance Acoustic Noise Suppression & Real-Time DSP Audio Processing Engine**  
> Engineered by Anush & HRL International. Built with zero required third-party dependencies, mathematical spectral subtraction, normalized adaptive filtering (NLMS/ALE), dynamic multi-band spectral gating, ultra-fast predictive lookahead noise cancellation, and an interactive real-time Web Audio visualizer.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![DSP: Spectral Subtraction](https://img.shields.io/badge/DSP-Spectral_Subtraction-purple.svg)]()
[![ANC: Adaptive NLMS](https://img.shields.io/badge/ANC-Normalized_LMS-green.svg)]()
[![Latency: Real-Time](https://img.shields.io/badge/RTF-%3C_0.10x-brightgreen.svg)]()
[![Web Visualizer](https://img.shields.io/badge/UI-Interactive_Dashboard-cyan.svg)]()

> **Full Technical Documentation**: For the complete architectural specification, physical acoustic derivations ($c=343\text{ m/s}$, wave superposition), H1 silicon MMIO registers, Swift 6 Accelerate vDSP SIMD benchmarks, boAt Rockerz 411 hardware calibration, Apple HIG principles, and complete API reference, see [DOCUMENTATION.md](DOCUMENTATION.md).

---

## Architecture Overview

```
                         [ Audio Input Stream ]
                 (Microphone / WAV File / Synthetic Generator)
                                   |
                                   v
             +-------------------------------------------+
             |    Acoustic Pre-Conditioning Filters      |
             |   - 85 Hz Highpass (Rumble / Handling)    |
             |   - 50/60 Hz Dual-Notch (Mains AC Hum)    |
             +---------------------+---------------------+
                                   |
                   +---------------+---------------+
                   |                               |
                   v                               v
    +------------------------------+   +------------------------------+
    |   Spectral Subtraction       |   |   NLMS Adaptive Filter       |
    |   (Boll Formulation)         |   |   (Dual-Mic ANC / ALE)       |
    |   - Hann-Windowed STFT       |   |   - Adaptive Weight Vector w |
    |   - Over-Subtraction (α)     |   |   - Gradient Normalization   |
    |   - Spectral Floor (β)       |   |   - Error Cancellation       |
    +--------------+---------------+   +--------------+---------------+
                   |                               |
                   +---------------+---------------+
                                   |
                                   v
             +-------------------------------------------+
             |     Dynamic Multi-Band Spectral Gate      |
             |   - Adaptive Energy Envelope Tracking     |
             |   - Musical Noise Suppression             |
             +---------------------+---------------------+
                                   |
                   +---------------+---------------+
                   |                               |
                   v                               v
    +------------------------------+   +------------------------------+
    |      Clean Audio Output      |   |   60 FPS Web Visualizer      |
    |  - 16-bit PCM WAV Exporter   |   |   - Dual FFT Spectrum Canvas |
    |  - Real-Time Audio Player    |   |   - Oscilloscope & SNR HUD   |
    +------------------------------+   +------------------------------+
```

---

## Mathematical Foundations

### 1. Spectral Subtraction (Boll, 1979)
For a degraded speech signal $y[n] = s[n] + d[n]$, the Short-Time Fourier Transform (STFT) frame is represented as:
$$Y_k(m) = |Y_k(m)| e^{j \phi_k(m)}$$

The clean speech magnitude estimate $|\hat{S}_k(m)|$ is obtained via parametric over-subtraction with an attenuation spectral floor:
$$|\hat{S}_k(m)| = \max\left( |Y_k(m)|^\gamma - \alpha |\hat{D}_k|^\gamma, \beta |Y_k(m)|^\gamma \right)^{1/\gamma}$$

- **$\alpha \ge 1.0$ (Over-subtraction factor)**: Compensates for spectral peaks in residual noise.
- **$\beta \approx 0.04$ (Spectral floor)**: Prevents zero-energy voids that cause perceptual "musical noise".
- **$\gamma = 1.0$**: Magnitude subtraction; $\gamma = 2.0$: Power spectral density subtraction.
- **Reconstruction**: Overlap-Add (OLA) synthesis with Hann window normalization:
  $$\hat{s}[n] = \frac{\sum_m \hat{s}_m[n - mR] \cdot w[n - mR]}{\sum_m w^2[n - mR]}$$

### 2. Normalized Least Mean Squares (NLMS) Filter
For active noise cancellation with a reference noise sensor $x[n]$:
$$y[n] = \mathbf{w}^T[n] \mathbf{x}[n]$$
$$e[n] = d[n] - y[n]$$
$$\mathbf{w}[n+1] = \mathbf{w}[n] + \frac{\mu}{\|\mathbf{x}[n]\|^2 + \epsilon} e[n] \mathbf{x}[n]$$

Where:
- $\mu \in (0, 1)$ is the normalized adaptation rate.
- $\epsilon$ is a regularization parameter protecting against energy attenuation singularities.
- In single-channel mode, an **Adaptive Line Enhancer (ALE)** decorrelates speech from stationary harmonic interference using a delay line $x[n] = d[n - \Delta]$.

---

## Quickstart

### 1. Run the Synthetic Benchmark Demo
Instantly validates noise cancellation performance using synthetic speech formants corrupted with Gaussian white noise and 50Hz mains hum:
```bash
python3 -m hrl_noise_cancellation demo
```
Output:
```
====================================================================
      ANUSH X HRL // SYNTHETIC DSP BENCHMARK
====================================================================
[*] Generating synthetic test stream: 2.5s @ 16000Hz...
[*] Base Degraded Input SNR: +3.00 dB
--------------------------------------------------------------------
Algorithm                | Elapsed    | Output SNR   | SNR Gain (Δ)
--------------------------------------------------------------------
Spectral Subtraction     |  243.19 ms |    +14.66 dB |    +11.66 dB
NLMS Adaptive (Dual-Mic) |  252.90 ms |     +8.00 dB |     +5.00 dB
====================================================================
```

### 2. Process an Audio File via CLI
Denoise any standard 16-bit PCM WAV file:
```bash
# Using Spectral Subtraction
python3 -m hrl_noise_cancellation process --input noisy_recording.wav --output cleaned_speech.wav --algorithm spectral

# Using Single-Channel Adaptive Filter
python3 -m hrl_noise_cancellation process --input noisy_recording.wav --output cleaned_speech.wav --algorithm nlms

# Customizing over-subtraction aggressiveness (alpha) and spectral floor (beta)
python3 -m hrl_noise_cancellation process -i input.wav -o output.wav --alpha 2.5 --beta 0.03
```

### 3. Launch the Interactive Web Dashboard
Launch the zero-dependency browser visualizer with live microphone support and real-time canvas spectrum analyzers:
```bash
python3 -m hrl_noise_cancellation web --port 8080
```
Open **[http://localhost:8080](http://localhost:8080)** to:
- Test live microphone audio with real-time noise suppression.
- Experiment with the built-in synthetic audio mixer (Voice / White Noise / 50Hz Hum).
- View live 60 FPS dual FFT spectrum overlays (Raw Noisy vs. Clean Filtered).
- Inspect live SNR, peak level, and latency telemetry in real-time.

### 4. Throughput & RTF Benchmark
Measure processing latency and Real-Time Factor (RTF):
```bash
python3 -m hrl_noise_cancellation benchmark
```
- **RTF < 0.10x**: Audio is processed more than **10x faster than real-time** even in pure standard-library Python, and >100x faster with NumPy acceleration.

---

## Verification & Testing

Run the automated test suite verifying sample precision, SNR improvement, NLMS convergence, and boundary overlap-add preservation:
```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

---

## Directory Structure

```
hrl-x-noise-cancellation/
├── LICENSE                                # MIT License
├── README.md                              # Technical specifications & documentation
├── .gitignore                             # Git ignore rules
├── hrl_noise_cancellation/                # Core Python DSP engine
│   ├── __init__.py                        # Package exports & versioning
│   ├── __main__.py                        # CLI module entry point
│   ├── cli.py                             # Unified CLI runner (demo, process, benchmark, web)
│   ├── server.py                          # Zero-dependency HTTP visualizer server
│   └── dsp/
│       ├── __init__.py                    # DSP subpackage exports
│       ├── audio_io.py                    # 16-bit WAV I/O, synthetic generator, SNR calculation
│       ├── spectral.py                    # Spectral Subtraction & Multi-Band Spectral Gate
│       └── adaptive.py                    # NLMS Adaptive Filter & ALE engine
├── web/
│   └── index.html                         # Interactive 60 FPS Web Audio Visualizer
└── tests/
    └── test_dsp.py                        # Automated DSP validation suite
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.  
Copyright &copy; 2026 HRL International.
