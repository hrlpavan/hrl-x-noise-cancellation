"""
Unified CLI for HRL X Noise Cancellation.
Supports:
- demo: Synthesizes noisy test audio and demonstrates spectral/adaptive denoising.
- process: Cleans an external WAV audio file.
- benchmark: Measures processing latency and Real-Time Factor (RTF).
- web: Launches local interactive real-time visualizer dashboard.
"""

import argparse
import os
import sys
import time
from .dsp.audio_io import AudioIO, generate_synthetic_benchmark, calculate_snr
from .dsp.spectral import SpectralSubtraction, SpectralGate
from .dsp.adaptive import NLMSFilter


def run_demo() -> int:
    """Runs end-to-end synthetic audio denoising benchmark and prints SNR gain."""
    print("=" * 68)
    print("      HRL X NOISE CANCELLATION // SYNTHETIC DSP BENCHMARK")
    print("=" * 68)

    sample_rate = 16000
    duration_sec = 2.5
    print(f"[*] Generating synthetic test stream: {duration_sec}s @ {sample_rate}Hz...")
    clean, noisy, noise, sr = generate_synthetic_benchmark(
        sample_rate=sample_rate,
        duration_sec=duration_sec,
        target_snr_db=3.0,
    )

    initial_snr = calculate_snr(clean, noisy)
    print(f"[*] Base Degraded Input SNR: {initial_snr:+.2f} dB")

    # 1. Spectral Subtraction
    t0 = time.perf_counter()
    spectral = SpectralSubtraction(alpha=2.2, beta=0.04)
    cleaned_spectral = spectral.process(noisy, noise_reference=noise[:sample_rate // 2])
    t_spectral = (time.perf_counter() - t0) * 1000
    spectral_snr = calculate_snr(clean, cleaned_spectral)
    spectral_gain = spectral_snr - initial_snr

    # 2. NLMS Adaptive Filter
    t0 = time.perf_counter()
    nlms = NLMSFilter(filter_length=64, mu=0.2)
    cleaned_nlms = nlms.process(noisy, reference_audio=noise)
    t_nlms = (time.perf_counter() - t0) * 1000
    nlms_snr = calculate_snr(clean, cleaned_nlms)
    nlms_gain = nlms_snr - initial_snr

    # Export demo audio files
    AudioIO.write_wav("demo_clean.wav", clean, sr)
    AudioIO.write_wav("demo_noisy.wav", noisy, sr)
    AudioIO.write_wav("demo_cleaned_spectral.wav", cleaned_spectral, sr)
    AudioIO.write_wav("demo_cleaned_nlms.wav", cleaned_nlms, sr)

    print("-" * 68)
    print(f"{'Algorithm':<24} | {'Elapsed':<10} | {'Output SNR':<12} | {'SNR Gain (Δ)':<12}")
    print("-" * 68)
    print(f"{'Spectral Subtraction':<24} | {t_spectral:>7.2f} ms | {spectral_snr:>+9.2f} dB | {spectral_gain:>+9.2f} dB")
    print(f"{'NLMS Adaptive (Dual-Mic)':<24} | {t_nlms:>7.2f} ms | {nlms_snr:>+9.2f} dB | {nlms_gain:>+9.2f} dB")
    print("=" * 68)
    print("[+] Saved demo audio artifacts:")
    print("    - demo_clean.wav")
    print("    - demo_noisy.wav")
    print("    - demo_cleaned_spectral.wav")
    print("    - demo_cleaned_nlms.wav")
    print("[✓] Benchmark completed successfully.")
    return 0


def run_process(args: argparse.Namespace) -> int:
    """Processes an input WAV file and writes the cleaned output."""
    if not os.path.exists(args.input):
        print(f"[!] Error: Input file not found: {args.input}", file=sys.stderr)
        return 1

    print(f"[*] Reading '{args.input}'...")
    samples, sr = AudioIO.read_wav(args.input)
    duration = len(samples) / sr
    print(f"[*] Loaded {len(samples)} samples ({duration:.2f}s @ {sr}Hz)")

    t0 = time.perf_counter()
    if args.algorithm == "spectral":
        algo = SpectralSubtraction(alpha=args.alpha, beta=args.beta)
        cleaned = algo.process(samples)
    elif args.algorithm == "nlms":
        algo = NLMSFilter(filter_length=64, mu=0.2)
        cleaned = algo.process(samples)
    elif args.algorithm == "gate":
        algo = SpectralGate(threshold_db=-36.0, attenuation_db=-24.0)
        cleaned = algo.process(samples)
    else:
        print(f"[!] Unknown algorithm '{args.algorithm}'", file=sys.stderr)
        return 1

    elapsed = time.perf_counter() - t0
    rtf = elapsed / max(duration, 1e-6)

    print(f"[*] Processed in {elapsed*1000:.2f}ms (RTF: {rtf:.3f}x)")
    print(f"[*] Saving cleaned audio to '{args.output}'...")
    AudioIO.write_wav(args.output, cleaned, sr)
    print("[✓] Audio processing complete.")
    return 0


def run_benchmark(args: argparse.Namespace) -> int:
    """Measures processing speed, throughput, and Real-Time Factor (RTF)."""
    sr = 16000
    duration_sec = 5.0
    _, noisy, noise, _ = generate_synthetic_benchmark(sample_rate=sr, duration_sec=duration_sec)

    print(f"[*] Benchmarking on {duration_sec}s audio stream ({len(noisy)} samples)...")

    # Benchmark Spectral Subtraction
    t0 = time.perf_counter()
    SpectralSubtraction().process(noisy)
    t_spectral = time.perf_counter() - t0
    rtf_spectral = t_spectral / duration_sec

    # Benchmark NLMS
    t0 = time.perf_counter()
    NLMSFilter().process(noisy, reference_audio=noise)
    t_nlms = time.perf_counter() - t0
    rtf_nlms = t_nlms / duration_sec

    print("-" * 55)
    print(f"{'Engine':<24} | {'Compute Time':<12} | {'RTF (x)':<10}")
    print("-" * 55)
    print(f"{'Spectral Subtraction':<24} | {t_spectral*1000:>9.2f} ms | {rtf_spectral:>8.4f}x")
    print(f"{'NLMS Adaptive Filter':<24} | {t_nlms*1000:>9.2f} ms | {rtf_nlms:>8.4f}x")
    print("-" * 55)
    print(f"[✓] Real-time capability: {'PASS' if max(rtf_spectral, rtf_nlms) < 1.0 else 'WARN'}")
    return 0


def run_web(args: argparse.Namespace) -> int:
    """Launches the interactive web visualizer dashboard."""
    from .server import start_server
    return start_server(port=args.port, open_browser=not args.no_browser)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="hrl_noise_cancellation",
        description="HRL X Noise Cancellation: High-performance audio noise suppression engine.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Demo command
    subparsers.add_parser("demo", help="Run synthetic audio noise cancellation demo")

    # Process command
    proc_parser = subparsers.add_parser("process", help="Denoise an audio file")
    proc_parser.add_argument("--input", "-i", required=True, help="Path to input WAV file")
    proc_parser.add_argument("--output", "-o", required=True, help="Path to output WAV file")
    proc_parser.add_argument(
        "--algorithm", "-a",
        choices=["spectral", "nlms", "gate"],
        default="spectral",
        help="Denoising algorithm (default: spectral)",
    )
    proc_parser.add_argument("--alpha", type=float, default=2.0, help="Over-subtraction factor")
    proc_parser.add_argument("--beta", type=float, default=0.05, help="Spectral floor")

    # Benchmark command
    subparsers.add_parser("benchmark", help="Measure RTF and processing throughput")

    # Web dashboard command
    web_parser = subparsers.add_parser("web", help="Launch interactive browser dashboard")
    web_parser.add_argument("--port", "-p", type=int, default=8080, help="Server port (default: 8080)")
    web_parser.add_argument("--no-browser", action="store_true", help="Do not automatically open browser")

    args = parser.parse_args()

    if args.command == "demo":
        sys.exit(run_demo())
    elif args.command == "process":
        sys.exit(run_process(args))
    elif args.command == "benchmark":
        sys.exit(run_benchmark(args))
    elif args.command == "web":
        sys.exit(run_web(args))
    else:
        # Default behavior: run demo if no args provided
        sys.exit(run_demo())


if __name__ == "__main__":
    main()
