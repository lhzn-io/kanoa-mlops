#!/usr/bin/env python3
"""Run multiple benchmark iterations and compute statistics for Ollama."""

import json
import subprocess
import time
from pathlib import Path
from statistics import mean, stdev

def run_single_benchmark():
    """Run a single benchmark and return results."""
    result = subprocess.run(
        ["python3", "test_ollama_gemma3.py"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )

    if result.returncode != 0:
        print(f"[ERROR] Benchmark failed: {result.stderr}")
        return None

    # Load the results
    try:
        with open(Path(__file__).parent / "benchmark_results_ollama.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[ERROR] benchmark_results_ollama.json not found")
        return None

def main():
    num_runs = 3
    results = []

    print(f"Running {num_runs} benchmark iterations for Ollama...\n")

    for i in range(num_runs):
        print(f"[{i+1}/{num_runs}] Running benchmark...")
        result = run_single_benchmark()

        if result:
            results.append(result)
            print(f"  ✓ Completed: {result['summary']['total_tokens']} tokens in {result['summary']['total_duration_s']:.1f}s")
            print(f"    Throughput: {result['summary']['avg_tokens_per_second']:.1f} tok/s\n")
        else:
            print(f"  ✗ Failed\n")

        # Brief pause between runs
        if i < num_runs - 1:
            time.sleep(2)

    if not results:
        print("[ERROR] No successful runs")
        return

    # Compute statistics
    print("="*70)
    print("OLLAMA BENCHMARK STATISTICS")
    print("="*70)
    print(f"\nRuns completed: {len(results)}")

    # Overall throughput stats
    throughputs = [r['summary']['avg_tokens_per_second'] for r in results]
    print(f"\nOverall Throughput:")
    print(f"  Mean:   {mean(throughputs):.1f} tok/s")
    if len(throughputs) > 1:
        print(f"  StdDev: {stdev(throughputs):.1f} tok/s")
        print(f"  Min:    {min(throughputs):.1f} tok/s")
        print(f"  Max:    {max(throughputs):.1f} tok/s")

    # Per-test statistics (Ollama test currently only has 'Basic Chat')
    print(f"\nPer-Test Statistics:")
    print(f"{'Test':<25} {'Mean (tok/s)':<15} {'StdDev':<10} {'Min':<10} {'Max':<10}")
    print("-" * 70)

    # Collect per-test data
    test_names = [t['test_name'] for t in results[0]['tests']]

    for test_name in test_names:
        test_throughputs = []
        for result in results:
            for test in result['tests']:
                if test['test_name'] == test_name:
                    test_throughputs.append(test['tokens_per_second'])
                    break

        if test_throughputs:
            mean_val = mean(test_throughputs)
            if len(test_throughputs) > 1:
                std_val = stdev(test_throughputs)
                min_val = min(test_throughputs)
                max_val = max(test_throughputs)
                print(f"{test_name:<25} {mean_val:>10.1f}      {std_val:>6.1f}     {min_val:>6.1f}     {max_val:>6.1f}")
            else:
                print(f"{test_name:<25} {mean_val:>10.1f}      {'N/A':>6}     {'N/A':>6}     {'N/A':>6}")

    print("="*70)

    # Save aggregated results
    aggregated = {
        "num_runs": len(results),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": results[0]['model'],
        "platform": results[0]['platform'],
        "statistics": {
            "overall": {
                "mean_throughput": mean(throughputs),
                "std_throughput": stdev(throughputs) if len(throughputs) > 1 else 0,
                "min_throughput": min(throughputs),
                "max_throughput": max(throughputs)
            },
            "per_test": {}
        },
        "raw_results": results
    }

    for test_name in test_names:
        test_throughputs = []
        for result in results:
            for test in result['tests']:
                if test['test_name'] == test_name:
                    test_throughputs.append(test['tokens_per_second'])
                    break

        aggregated["statistics"]["per_test"][test_name] = {
            "mean": mean(test_throughputs),
            "std": stdev(test_throughputs) if len(test_throughputs) > 1 else 0,
            "min": min(test_throughputs),
            "max": max(test_throughputs)
        }

    with open("benchmark_statistics_ollama.json", "w") as f:
        json.dump(aggregated, f, indent=2)

    print(f"\n[INFO] Statistics saved to: benchmark_statistics_ollama.json")

if __name__ == "__main__":
    main()
