#!/usr/bin/env python3
"""Integration tests for Molmo 7B vLLM API with performance metrics."""

import base64
import io
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

# Add project root to path to allow imports
sys.path.append(str(Path(__file__).parents[2]))

try:
    from kanoa_mlops.arch_detect import detect_architecture
except ImportError:
    from typing import Any

    def detect_architecture() -> Any:  # type: ignore[misc]
        """Fallback if import fails."""

        class MockConfig:
            description = "Unknown Platform"

        return MockConfig()


import matplotlib.pyplot as plt
import numpy as np
import requests
from PIL import Image

MODEL_NAME = "allenai/Molmo-7B-D-0924"
API_URL = "http://localhost:8000/v1/chat/completions"


@dataclass
class TestMetrics:
    """Store performance metrics for a test."""

    test_name: str
    duration_s: float
    tokens_generated: int
    tokens_per_second: float
    prompt_tokens: int = 0


# Global metrics collection
TEST_METRICS: list[TestMetrics] = []


def query_molmo(prompt, image_url, max_tokens=200, temperature=0.1):
    """
    Query Molmo API with vision support.

    Returns:
        tuple: (response_text, usage_dict, duration_s)
    """
    headers = {"Content-Type": "application/json"}
    data = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    start_time = time.time()
    response = requests.post(API_URL, headers=headers, json=data)
    duration_s = time.time() - start_time

    response.raise_for_status()
    result = response.json()

    return (
        result["choices"][0]["message"]["content"],
        result.get("usage", {}),
        duration_s,
    )


def test_boardwalk_photo():
    """Test vision capabilities with real-world photo."""
    print("\n[TEST] Testing Boardwalk Photo (URL -> Base64)...")
    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/960px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"

    try:
        # Download image locally first to avoid container networking issues
        print(f"   Downloading {image_url}...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        img_resp = requests.get(image_url, headers=headers)
        img_resp.raise_for_status()

        # Convert to Base64
        img = Image.open(io.BytesIO(img_resp.content))
        # Resize if too large (Molmo handles large images well, but let's be safe and fast)
        if max(img.size) > 1024:
            img.thumbnail((1024, 1024))

        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        img_str = base64.b64encode(buf.getvalue()).decode("utf-8")
        base64_url = f"data:image/jpeg;base64,{img_str}"

        description, usage, duration_s = query_molmo(
            "Describe this image in detail.", base64_url
        )

        # Record metrics
        tokens_generated = usage.get("completion_tokens", 0)
        prompt_tokens = usage.get("prompt_tokens", 0)
        tokens_per_sec = tokens_generated / duration_s if duration_s > 0 else 0

        TEST_METRICS.append(
            TestMetrics(
                test_name="Boardwalk Photo",
                duration_s=duration_s,
                tokens_generated=tokens_generated,
                tokens_per_second=tokens_per_sec,
                prompt_tokens=prompt_tokens,
            )
        )

        print(f"[OK] Response:\n{description}")
        print(
            f"[PERF] Duration: {duration_s:.2f}s | Tokens: {tokens_generated} | Speed: {tokens_per_sec:.1f} tok/s"
        )
        print("[PASS] Boardwalk photo test passed")
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        raise


def test_complex_plot():
    """Test vision with complex matplotlib multi-panel plot."""
    print("\n[TEST] Testing Complex Matplotlib Plot (Base64)...")

    # Generate Plot
    fig, axs = plt.subplots(2, 2, figsize=(10, 8))

    # 1. Sine Wave
    x = np.linspace(0, 10, 100)
    axs[0, 0].plot(x, np.sin(x), "r-", linewidth=2)
    axs[0, 0].set_title("Sine Wave")
    axs[0, 0].grid(True)

    # 2. Scatter Plot
    np.random.seed(42)
    axs[0, 1].scatter(
        np.random.rand(50), np.random.rand(50), c=np.random.rand(50), cmap="viridis"
    )
    axs[0, 1].set_title("Random Scatter")

    # 3. Histogram
    axs[1, 0].hist(np.random.randn(1000), bins=30, color="green", alpha=0.7)
    axs[1, 0].set_title("Normal Distribution")

    # 4. Bar Chart
    categories = ["A", "B", "C", "D"]
    values = [15, 30, 45, 10]
    axs[1, 1].bar(categories, values, color="purple")
    axs[1, 1].set_title("Category Values")

    plt.tight_layout()

    # Convert to Base64
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    img_str = base64.b64encode(buf.getvalue()).decode("utf-8")
    plt.close(fig)

    image_url = f"data:image/png;base64,{img_str}"

    try:
        description, usage, duration_s = query_molmo(
            "Analyze this multi-panel plot. What does each subplot show?",
            image_url,
            max_tokens=300,
        )

        # Record metrics
        tokens_generated = usage.get("completion_tokens", 0)
        prompt_tokens = usage.get("prompt_tokens", 0)
        tokens_per_sec = tokens_generated / duration_s if duration_s > 0 else 0

        TEST_METRICS.append(
            TestMetrics(
                test_name="Complex Plot",
                duration_s=duration_s,
                tokens_generated=tokens_generated,
                tokens_per_second=tokens_per_sec,
                prompt_tokens=prompt_tokens,
            )
        )

        print(f"[OK] Response:\n{description}")
        print(
            f"[PERF] Duration: {duration_s:.2f}s | Tokens: {tokens_generated} | Speed: {tokens_per_sec:.1f} tok/s"
        )
        print("[PASS] Complex plot test passed")
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        raise


def test_data_interpretation():
    """Test interpreting a data visualization with quantitative details."""
    print("\n[TEST] Testing Data Interpretation...")

    # Create a plot with clear data
    fig, ax = plt.subplots(figsize=(10, 6))
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    revenue = [45000, 52000, 48000, 61000, 58000, 65000]

    ax.plot(months, revenue, marker="o", linewidth=2, markersize=8)
    ax.set_title("Monthly Revenue (USD)", fontsize=14)
    ax.set_ylabel("Revenue ($)", fontsize=12)
    ax.grid(True, alpha=0.3)

    # Convert to base64
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=100)
    buf.seek(0)
    img_str = base64.b64encode(buf.getvalue()).decode("utf-8")
    plt.close(fig)

    image_url = f"data:image/png;base64,{img_str}"

    try:
        result, usage, duration_s = query_molmo(
            "What is the trend in this revenue chart? Which month had the highest revenue?",
            image_url,
            max_tokens=200,
        )

        # Record metrics
        tokens_generated = usage.get("completion_tokens", 0)
        prompt_tokens = usage.get("prompt_tokens", 0)
        tokens_per_sec = tokens_generated / duration_s if duration_s > 0 else 0

        TEST_METRICS.append(
            TestMetrics(
                test_name="Data Interpretation",
                duration_s=duration_s,
                tokens_generated=tokens_generated,
                tokens_per_second=tokens_per_sec,
                prompt_tokens=prompt_tokens,
            )
        )

        print(f"[OK] Response:\n{result}")
        print(
            f"[PERF] Duration: {duration_s:.2f}s | Tokens: {tokens_generated} | Speed: {tokens_per_sec:.1f} tok/s"
        )

        # Verify it understood the trend
        assert (
            "increase" in result.lower()
            or "trend" in result.lower()
            or "june" in result.lower()
            or "jun" in result.lower()
        ), "Expected model to identify upward trend or highest month"
        print("[PASS] Data interpretation test passed")
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        raise


def test_api_health():
    """Test that the vLLM API is healthy and responsive."""
    print("\n[TEST] Testing API Health...")

    # Check models endpoint
    models_url = "http://localhost:8000/v1/models"
    response = requests.get(models_url)
    response.raise_for_status()
    models = response.json()
    print(f"[OK] Available models: {[m['id'] for m in models['data']]}")

    # Check health endpoint
    health_url = "http://localhost:8000/health"
    response = requests.get(health_url)
    response.raise_for_status()
    print("[OK] Health check passed")
    print("[PASS] API health test passed")


def print_performance_report():
    """Print formatted performance report."""
    if not TEST_METRICS:
        print("\n[WARNING] No performance metrics collected")
        return

    total_tokens = sum(m.tokens_generated for m in TEST_METRICS)
    total_duration = sum(m.duration_s for m in TEST_METRICS)
    avg_tokens_per_sec = total_tokens / total_duration if total_duration > 0 else 0

    print("\n" + "=" * 70)
    print("PERFORMANCE SUMMARY")
    print("=" * 70)
    print(f"Model: {MODEL_NAME}")
    print(f"Total Tests: {len(TEST_METRICS)}")
    print(f"Total Tokens Generated: {total_tokens}")
    print(f"Total Duration: {total_duration:.2f}s")
    print(f"Average Throughput: {avg_tokens_per_sec:.1f} tokens/second")
    print("\nPer-Test Breakdown:")
    print(
        f"{'Test Name':<25} {'Duration (s)':<15} {'Tokens':<10} {'Speed (tok/s)':<15}"
    )
    print("-" * 70)

    for metric in TEST_METRICS:
        print(
            f"{metric.test_name:<25} {metric.duration_s:>10.2f}      {metric.tokens_generated:>6}     {metric.tokens_per_second:>10.1f}"
        )

    print("=" * 70)


def save_benchmark_results():
    """Save benchmark results to JSON file."""
    try:
        platform_desc = detect_architecture().description
    except Exception:
        platform_desc = "Unknown Platform"

    results = {
        "timestamp": datetime.now().isoformat(),
        "model": MODEL_NAME,
        "platform": platform_desc,
        "summary": {
            "total_tests": len(TEST_METRICS),
            "total_tokens": sum(m.tokens_generated for m in TEST_METRICS),
            "total_duration_s": sum(m.duration_s for m in TEST_METRICS),
            "avg_tokens_per_second": sum(m.tokens_generated for m in TEST_METRICS)
            / sum(m.duration_s for m in TEST_METRICS),
        },
        "tests": [asdict(m) for m in TEST_METRICS],
    }

    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n[INFO] Benchmark results saved to: benchmark_results.json")


if __name__ == "__main__":
    print("[INFO] Starting Integration Tests for Molmo 7B Vision...")
    print(f"[INFO] Testing against: {API_URL}")
    print(f"[INFO] Model: {MODEL_NAME}")

    try:
        test_api_health()
        test_boardwalk_photo()
        test_complex_plot()
        test_data_interpretation()

        print_performance_report()
        save_benchmark_results()

        print("\n[SUCCESS] All tests passed!")
    except Exception as e:
        print(f"\n[FAILURE] Tests failed: {e}")
        raise
