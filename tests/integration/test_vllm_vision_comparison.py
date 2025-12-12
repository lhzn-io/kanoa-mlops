#!/usr/bin/env python3
"""Apples-to-apples vision comparison across vLLM models (Gemma3, Molmo).

This test runs identical vision prompts on different models to enable fair
performance and quality comparisons.
"""

import base64
import io
import json
import os
import platform
import time
from dataclasses import asdict, dataclass
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import requests
from PIL import Image

# Model to test (set via environment variable)
MODEL_NAME = os.getenv("MODEL_NAME", "gemma-3-12b")
API_URL = "http://localhost:8000/v1/chat/completions"


@dataclass
class TestMetrics:
    """Store performance metrics for a test."""

    test_name: str
    duration_s: float
    tokens_generated: int
    tokens_per_second: float
    prompt_tokens: int = 0


# Global list to store test metrics
TEST_METRICS = []


def create_test_chart():
    """Create a simple bar chart for testing."""
    categories = ["Q1", "Q2", "Q3", "Q4"]
    values = [45, 62, 58, 71]

    plt.figure(figsize=(8, 6))
    plt.bar(categories, values, color=["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A"])
    plt.title("Quarterly Revenue (in thousands)")
    plt.xlabel("Quarter")
    plt.ylabel("Revenue ($K)")
    plt.grid(axis="y", alpha=0.3)

    # Save to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close()
    buf.seek(0)

    # Encode as base64 data URI
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"


def create_color_grid():
    """Create a simple colored grid for testing."""
    # Create 3x3 colored grid
    colors = np.array(
        [
            [[255, 0, 0], [0, 255, 0], [0, 0, 255]],  # Red, Green, Blue
            [[255, 255, 0], [255, 0, 255], [0, 255, 255]],  # Yellow, Magenta, Cyan
            [[128, 128, 128], [255, 255, 255], [0, 0, 0]],  # Gray, White, Black
        ],
        dtype=np.uint8,
    )

    # Scale up to make it visible
    colors = np.repeat(np.repeat(colors, 50, axis=0), 50, axis=1)

    img = Image.fromarray(colors)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"


def query_vision_model(prompt, image_url, max_tokens=300, temperature=0.7):
    """Query vision model via vLLM OpenAI-compatible API.

    Args:
        prompt: Text prompt
        image_url: Image data URI
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature

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
        "stream": True,
        "stream_options": {"include_usage": True},
    }

    print("[INFO] Streaming response...")
    start_time = time.time()
    response = requests.post(API_URL, headers=headers, json=data, stream=True)

    response.raise_for_status()

    full_content = []
    usage = {}

    for line in response.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    if chunk.get("usage"):
                        usage = chunk["usage"]

                    if "choices" in chunk and len(chunk["choices"]) > 0:
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            print(content, end="", flush=True)
                            full_content.append(content)
                except json.JSONDecodeError:
                    pass

    print()  # Newline after stream
    duration_s = time.time() - start_time

    full_response_text = "".join(full_content)
    return (
        full_response_text,
        usage,
        duration_s,
    )


def test_chart_analysis():
    """Test chart interpretation - identical across vision models."""
    print("\n[TEST] Chart Analysis")
    image_url = create_test_chart()

    prompt = """Analyze this chart and provide:
1. What type of chart is this?
2. What does it show?
3. What is the trend across quarters?
4. Which quarter had the highest value?"""

    response, usage, duration = query_vision_model(
        prompt, image_url, max_tokens=300, temperature=0.1
    )
    print(f"\n[OK] Response received ({len(response)} chars)")

    # Track metrics
    tokens_generated = usage.get("completion_tokens", 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(
        TestMetrics(
            test_name="Chart Analysis",
            duration_s=duration,
            tokens_generated=tokens_generated,
            tokens_per_second=tokens_per_sec,
            prompt_tokens=usage.get("prompt_tokens", 0),
        )
    )

    print(
        f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s"
    )
    assert "q4" in response.lower() or "quarter 4" in response.lower() or "71" in response, (
        "Expected mention of Q4 or highest value"
    )
    print("[PASS] Chart analysis test passed")


def test_color_identification():
    """Test color identification - identical across vision models."""
    print("\n[TEST] Color Identification")
    image_url = create_color_grid()

    prompt = """Describe the colors you see in this image.
List the colors in the grid from left to right, top to bottom."""

    response, usage, duration = query_vision_model(
        prompt, image_url, max_tokens=200, temperature=0.1
    )
    print(f"\n[OK] Response received ({len(response)} chars)")

    # Track metrics
    tokens_generated = usage.get("completion_tokens", 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(
        TestMetrics(
            test_name="Color Identification",
            duration_s=duration,
            tokens_generated=tokens_generated,
            tokens_per_second=tokens_per_sec,
            prompt_tokens=usage.get("prompt_tokens", 0),
        )
    )

    print(
        f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s"
    )
    # Check if primary colors are mentioned
    response_lower = response.lower()
    color_mentions = sum(
        1 for color in ["red", "green", "blue"] if color in response_lower
    )
    assert color_mentions >= 2, "Expected mention of primary colors"
    print("[PASS] Color identification test passed")


def test_visual_counting():
    """Test visual counting - identical across vision models."""
    print("\n[TEST] Visual Counting")
    image_url = create_color_grid()

    prompt = """How many distinct colors are visible in this image?
Count them and list each color."""

    response, usage, duration = query_vision_model(
        prompt, image_url, max_tokens=200, temperature=0.1
    )
    print(f"\n[OK] Response received ({len(response)} chars)")

    # Track metrics
    tokens_generated = usage.get("completion_tokens", 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(
        TestMetrics(
            test_name="Visual Counting",
            duration_s=duration,
            tokens_generated=tokens_generated,
            tokens_per_second=tokens_per_sec,
            prompt_tokens=usage.get("prompt_tokens", 0),
        )
    )

    print(
        f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s"
    )
    # Should identify approximately 9 colors (might group similar ones)
    assert any(str(num) in response for num in [6, 7, 8, 9]), (
        "Expected reasonable color count"
    )
    print("[PASS] Visual counting test passed")


def test_api_health():
    """Test that the vLLM API is healthy and responsive."""
    print("\n[TEST] API Health")

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
        return

    print("\n" + "=" * 70)
    print(f"VISION PERFORMANCE REPORT - {MODEL_NAME}")
    print("=" * 70)

    # Summary stats
    total_tokens = sum(m.tokens_generated for m in TEST_METRICS)
    total_duration = sum(m.duration_s for m in TEST_METRICS)
    avg_tokens_per_sec = total_tokens / total_duration if total_duration > 0 else 0

    print("\nOverall Statistics:")
    print(f"  Total Tokens Generated: {total_tokens}")
    print(f"  Total Duration: {total_duration:.2f}s")
    print(f"  Average Throughput: {avg_tokens_per_sec:.1f} tokens/s")

    # Per-test breakdown
    print("\nPer-Test Results:")
    print(f"{'Test Name':<30} {'Duration':<12} {'Tokens':<10} {'Tok/s':<10}")
    print("-" * 70)
    for metric in TEST_METRICS:
        print(
            f"{metric.test_name:<30} {metric.duration_s:>8.2f}s    {metric.tokens_generated:>6}     {metric.tokens_per_second:>6.1f}"
        )

    print("=" * 70)


def export_results_json(filename="benchmark_results.json"):
    """Export results to JSON for comparison."""
    if not TEST_METRICS:
        return

    # Get system info
    try:
        with open("/proc/driver/nvidia/version", "r") as f:
            nvidia_version = f.readline().strip()
    except Exception:
        nvidia_version = "unknown"

    results = {
        "timestamp": datetime.now().isoformat(),
        "model": MODEL_NAME,
        "test_type": "vision_comparison",
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "gpu": "NVIDIA Jetson Thor (128GB Unified Memory)",
            "driver": nvidia_version,
        },
        "summary": {
            "total_tokens": sum(m.tokens_generated for m in TEST_METRICS),
            "total_duration_s": sum(m.duration_s for m in TEST_METRICS),
            "avg_tokens_per_second": sum(m.tokens_per_second for m in TEST_METRICS)
            / len(TEST_METRICS),
        },
        "tests": [asdict(m) for m in TEST_METRICS],
    }

    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n[INFO] Benchmark results exported to: {filename}")


if __name__ == "__main__":
    print("[INFO] Vision Comparison Benchmark")
    print(f"[INFO] Model: {MODEL_NAME}")
    print(f"[INFO] API URL: {API_URL}")
    print("[INFO] Running standardized vision tests across models\n")

    try:
        # API Health
        test_api_health()

        # Standardized vision tests
        test_chart_analysis()
        test_color_identification()
        test_visual_counting()

        # Print performance report
        print_performance_report()

        # Export JSON
        export_results_json()

        print("\n" + "=" * 70)
        print("[SUCCESS] All vision comparison tests passed!")
        print("=" * 70)
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"[FAILURE] Vision comparison tests failed: {e}")
        print("=" * 70)
        exit(1)
