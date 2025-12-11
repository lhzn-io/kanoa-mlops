#!/usr/bin/env python3
"""Run multiple benchmark iterations for Molmo and compute statistics."""

import json
import subprocess
import time
from pathlib import Path
from statistics import mean, stdev


def run_single_benchmark():
    """Run a single benchmark and return results."""
    result = subprocess.run(
        ["python3", "test_vllm_molmo_api.py"],
        check=False,
        capture_output=False,
        text=True,
        cwd=Path(__file__).parent,
    )

    if result.returncode != 0:
        print(f"[ERROR] Benchmark failed: {result.stderr}")
        return None

    # Load the results
    results_path = Path(__file__).parent / "benchmark_results.json"
    with open(results_path, "r") as f:
        return json.load(f)


def main():
    num_runs = 10
    results = []

    print(f"Running {num_runs} benchmark iterations for Molmo 7B...\n")

    for i in range(num_runs):
        print(f"[{i + 1}/{num_runs}] Running benchmark...")
        result = run_single_benchmark()

        if result:
            results.append(result)
            print(
                f"  ✓ Completed: {result['summary']['total_tokens']} tokens in {result['summary']['total_duration_s']:.1f}s (Timestamp: {result['timestamp']})"
            )
            print(
                f"    Throughput: {result['summary']['avg_tokens_per_second']:.1f} tok/s\n"
            )
        else:
            print("  ✗ Failed\n")

        # Brief pause between runs
        if i < num_runs - 1:
            time.sleep(2)

    if not results:
        print("[ERROR] No successful runs")
        return

    # Compute statistics
    print("=" * 70)
    print("BENCHMARK STATISTICS - MOLMO 7B")
    print("=" * 70)
    print(f"\nRuns completed: {len(results)}")

    # Overall throughput stats
    throughputs = [r["summary"]["avg_tokens_per_second"] for r in results]
    print("\nOverall Throughput:")
    print(f"  Mean:   {mean(throughputs):.1f} tok/s")
    if len(throughputs) > 1:
        print(f"  StdDev: {stdev(throughputs):.1f} tok/s")
        print(f"  Min:    {min(throughputs):.1f} tok/s")
        print(f"  Max:    {max(throughputs):.1f} tok/s")

    # Per-test statistics
    print("\nPer-Test Statistics:")
    print(f"{'Test':<25} {'Mean (tok/s)':<15} {'StdDev':<10} {'Min':<10} {'Max':<10}")
    print("-" * 70)

    # Collect per-test data
    test_names = [t["test_name"] for t in results[0]["tests"]]

    for test_name in test_names:
        test_throughputs = []
        for result in results:
            for test in result["tests"]:
                if test["test_name"] == test_name:
                    test_throughputs.append(test["tokens_per_second"])
                    break

        if test_throughputs:
            mean_val = mean(test_throughputs)
            if len(test_throughputs) > 1:
                std_val = stdev(test_throughputs)
                min_val = min(test_throughputs)
                max_val = max(test_throughputs)
                print(
                    f"{test_name:<25} {mean_val:>10.1f}      {std_val:>6.1f}     {min_val:>6.1f}     {max_val:>6.1f}"
                )
            else:
                print(
                    f"{test_name:<25} {mean_val:>10.1f}      {'N/A':>6}     {'N/A':>6}     {'N/A':>6}"
                )

    print("=" * 70)

    # Save aggregated results
    aggregated = {
        "num_runs": len(results),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": results[0]["model"],
        "platform": results[0]["platform"],
        "statistics": {
            "overall": {
                "mean_throughput": mean(throughputs),
                "std_throughput": stdev(throughputs) if len(throughputs) > 1 else 0,
                "min_throughput": min(throughputs),
                "max_throughput": max(throughputs),
            },
            "per_test": {},
        },
        "raw_results": results,
    }

    for test_name in test_names:
        test_throughputs = []
        for result in results:
            for test in result["tests"]:
                if test["test_name"] == test_name:
                    test_throughputs.append(test["tokens_per_second"])
                    break

        aggregated["statistics"]["per_test"][test_name] = {
            "mean": mean(test_throughputs),
            "std": stdev(test_throughputs) if len(test_throughputs) > 1 else 0,
            "min": min(test_throughputs),
            "max": max(test_throughputs),
        }

    output_path = Path(__file__).parent / "benchmark_statistics_molmo.json"

    # Load existing results if they exist
    existing_data = []
    if output_path.exists():
        try:
            with open(output_path, "r") as f:
                content = json.load(f)
                if isinstance(content, list):
                    existing_data = content
                elif isinstance(content, dict):
                    existing_data = [content]
        except json.JSONDecodeError:
            pass

    # Remove any existing entry for this platform to avoid duplicates
    existing_data = [
        entry
        for entry in existing_data
        if entry.get("platform") != aggregated["platform"]
    ]

    # Append new results
    existing_data.append(aggregated)

    with open(output_path, "w") as f:
        json.dump(existing_data, f, indent=2)

    print(f"\n[INFO] Statistics saved to: {output_path}")


if __name__ == "__main__":
    main()
