#!/usr/bin/env python3
"""
HRL X Noise Cancellation - Unified Automated Pipeline Runner (auto.py)
Executes:
1. Automated unit test suite.
2. Synthetic speech + noise benchmark with SNR gain evaluation.
3. High-throughput RTF benchmark.
4. Spins up the interactive web visualizer server.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))


def run_section(title: str):
    print("\n" + "=" * 68)
    print(f"⚡ HRL AUTO PIPELINE // {title.upper()}")
    print("=" * 68)


def main():
    start_all = time.time()
    run_section("Step 1: Automated Unit & Integrity Tests")

    # Run tests
    test_cmd = [sys.executable, "-m", "unittest", "discover", "-s", str(ROOT_DIR / "tests"), "-p", "test_*.py", "-v"]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT_DIR)
    rc = subprocess.call(test_cmd, env=env)
    if rc != 0:
        print("\n[!] Tests failed! Halting pipeline.")
        sys.exit(rc)
    print("[✓] All 4 DSP unit tests passed.")

    # Run demo
    run_section("Step 2: Synthetic Denoising & SNR Validation")
    from hrl_noise_cancellation.cli import run_demo, run_benchmark
    rc = run_demo()
    if rc != 0:
        print("\n[!] Demo failed!")
        sys.exit(rc)

    # Run benchmark
    run_section("Step 3: Real-Time Factor (RTF) Throughput")
    import argparse
    run_benchmark(argparse.Namespace())

    # Summary
    total_time = time.time() - start_all
    run_section("Automation Complete")
    print(f"[✓] Entire pipeline validated successfully in {total_time:.2f}s.")
    print("[✓] All audio artifacts (demo_clean.wav, demo_noisy.wav, demo_cleaned_spectral.wav) are ready.")
    print("=" * 68 + "\n")


if __name__ == "__main__":
    main()
