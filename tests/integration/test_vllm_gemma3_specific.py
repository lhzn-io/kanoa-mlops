#!/usr/bin/env python3
"""Model-specific tests for Gemma 3 unique capabilities.

Tests unique features not covered by comparison benchmarks:
- Real-world image understanding
- Multi-turn conversation memory

For apples-to-apples comparisons, use:
- test_vllm_text_comparison.py
- test_vllm_vision_comparison.py
"""

import base64
import io
import json
import platform
import time
from dataclasses import asdict, dataclass
from datetime import datetime

import requests
from PIL import Image

MODEL_NAME = "gemma-3-12b"
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


def query_gemma(prompt, max_tokens=200, temperature=0.7, image_url=None):
    """Query the Gemma model via vLLM OpenAI-compatible API.

    Args:
        prompt: Text prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        image_url: Optional image URL (data URI or HTTP URL) for vision tasks

    Returns:
        tuple: (response_text, usage_dict, duration_s)
    """
    headers = {"Content-Type": "application/json"}

    if image_url:
        # Vision request
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
    else:
        # Text-only request
        content = prompt

    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
        "stream_options": {"include_usage": True},
    }

    print("   Streaming response...", end="", flush=True)
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
                        content_chunk = delta.get("content", "")
                        if content_chunk:
                            print(content_chunk, end="", flush=True)
                            full_content.append(content_chunk)
                except json.JSONDecodeError:
                    continue

    duration_s = time.time() - start_time
    print()  # Newline after stream

    return (
        "".join(full_content),
        usage,
        duration_s,
    )


def test_vision_boardwalk():
    """Test vision capability with a real-world photo."""
    print("\n[TEST] Vision - Real World Photo (Boardwalk)")
    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/960px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"

    # Download image and convert to base64
    print(f"   Downloading image...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    img_resp = requests.get(image_url, headers=headers)
    img_resp.raise_for_status()

    # Convert to Base64
    img = Image.open(io.BytesIO(img_resp.content))
    if max(img.size) > 1024:
        img.thumbnail((1024, 1024))

    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_str = base64.b64encode(buf.getvalue()).decode("utf-8")
    base64_url = f"data:image/jpeg;base64,{img_str}"

    response, usage, duration = query_gemma(
        "Describe this image in detail.",
        max_tokens=200,
        temperature=0.1,
        image_url=base64_url,
    )
    print(f"\n[OK] Response received ({len(response)} chars)")

    # Track metrics
    tokens_generated = usage.get("completion_tokens", 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(
        TestMetrics(
            test_name="Vision - Real World Photo",
            duration_s=duration,
            tokens_generated=tokens_generated,
            tokens_per_second=tokens_per_sec,
            prompt_tokens=usage.get("prompt_tokens", 0),
        )
    )

    print(
        f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s"
    )
    assert len(response) > 50, "Expected substantial description"
    print("[PASS] Real-world vision test passed")


def test_multi_turn_conversation():
    """Test multi-turn conversation memory capability."""
    print("\n[TEST] Multi-turn Conversation Memory")

    headers = {"Content-Type": "application/json"}
    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": "My name is Alice."},
            {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
            {"role": "user", "content": "What's my name?"},
        ],
        "max_tokens": 50,
        "temperature": 0.1,
    }

    start_time = time.time()
    response = requests.post(API_URL, headers=headers, json=data)
    duration = time.time() - start_time

    response.raise_for_status()
    result = response.json()["choices"][0]["message"]["content"]
    usage = response.json().get("usage", {})

    print(f"[OK] Response: {result}")

    # Track metrics
    tokens_generated = usage.get("completion_tokens", 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(
        TestMetrics(
            test_name="Multi-turn Conversation",
            duration_s=duration,
            tokens_generated=tokens_generated,
            tokens_per_second=tokens_per_sec,
            prompt_tokens=usage.get("prompt_tokens", 0),
        )
    )

    print(
        f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s"
    )
    assert "Alice" in result or "alice" in result, (
        "Expected model to remember the name from conversation history"
    )
    print("[PASS] Multi-turn conversation test passed")


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
    print("PERFORMANCE REPORT - GEMMA 3 SPECIFIC TESTS")
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
    """Export results to JSON."""
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
        "test_type": "gemma3_specific",
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
    print("[INFO] Gemma 3 Model-Specific Tests")
    print(f"[INFO] Model: {MODEL_NAME}")
    print(f"[INFO] API URL: {API_URL}")
    print("[INFO] Testing unique capabilities not in comparison benchmarks\n")

    try:
        # API Health
        test_api_health()

        # Unique capability tests
        test_vision_boardwalk()
        test_multi_turn_conversation()

        # Print performance report
        print_performance_report()

        # Export JSON
        export_results_json()

        print("\n" + "=" * 70)
        print("[SUCCESS] All Gemma 3 specific tests passed!")
        print("=" * 70)
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"[FAILURE] Tests failed: {e}")
        print("=" * 70)
        exit(1)
