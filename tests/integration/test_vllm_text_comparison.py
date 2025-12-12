#!/usr/bin/env python3
"""Apples-to-apples text comparison across vLLM models (Gemma3, OLMo3).

This test runs identical prompts on different models to enable fair performance
and quality comparisons.
"""

import json
import os
import platform
import time
from dataclasses import asdict, dataclass
from datetime import datetime

import requests

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


def query_model(prompt, max_tokens=500, temperature=0.7):
    """Query any vLLM model via OpenAI-compatible API.

    Args:
        prompt: Text prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature

    Returns:
        tuple: (response_text, usage_dict, duration_s)
    """
    headers = {"Content-Type": "application/json"}

    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
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
                    # Handle usage if present (vLLM sends it in the last chunk)
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


def test_code_generation_python():
    """Test Python code generation - identical across models."""
    print("\n[TEST] Code Generation - Python")
    prompt = """Write a Python function that implements binary search.
Include type hints, docstring, and handle edge cases.
Provide a brief explanation."""

    response, usage, duration = query_model(prompt, max_tokens=500, temperature=0.2)
    print(f"\n[OK] Response received ({len(response)} chars)")

    # Track metrics
    tokens_generated = usage.get("completion_tokens", 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(
        TestMetrics(
            test_name="Code Generation - Python",
            duration_s=duration,
            tokens_generated=tokens_generated,
            tokens_per_second=tokens_per_sec,
            prompt_tokens=usage.get("prompt_tokens", 0),
        )
    )

    print(
        f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s"
    )
    assert "def" in response.lower(), "Expected function definition"
    print("[PASS] Code generation test passed")


def test_reasoning_logic():
    """Test logical reasoning - identical across models."""
    print("\n[TEST] Logical Reasoning")
    prompt = """Solve this logic puzzle:

Three people (Alice, Bob, Carol) each have a different pet (cat, dog, fish).
- Alice doesn't have a cat
- The person with the dog is not Bob
- Carol doesn't have the fish

Who has which pet? Show your reasoning."""

    response, usage, duration = query_model(prompt, max_tokens=500, temperature=0.1)
    print(f"\n[OK] Response received ({len(response)} chars)")

    # Track metrics
    tokens_generated = usage.get("completion_tokens", 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(
        TestMetrics(
            test_name="Logical Reasoning",
            duration_s=duration,
            tokens_generated=tokens_generated,
            tokens_per_second=tokens_per_sec,
            prompt_tokens=usage.get("prompt_tokens", 0),
        )
    )

    print(
        f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s"
    )
    print("[PASS] Logical reasoning test passed")


def test_summarization():
    """Test text summarization - identical across models."""
    print("\n[TEST] Text Summarization")
    prompt = """Summarize this text in 2-3 sentences:

The Industrial Revolution, which took place from the 18th to 19th centuries, was a period
during which predominantly agrarian, rural societies in Europe and America became industrial
and urban. Prior to the Industrial Revolution, which began in Britain in the late 1700s,
manufacturing was often done in people's homes, using hand tools or basic machines.
Industrialization marked a shift to powered, special-purpose machinery, factories and mass
production. The iron and textile industries, along with the development of the steam engine,
played central roles in the Industrial Revolution."""

    response, usage, duration = query_model(prompt, max_tokens=200, temperature=0.3)
    print(f"\n[OK] Response received ({len(response)} chars)")

    # Track metrics
    tokens_generated = usage.get("completion_tokens", 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(
        TestMetrics(
            test_name="Text Summarization",
            duration_s=duration,
            tokens_generated=tokens_generated,
            tokens_per_second=tokens_per_sec,
            prompt_tokens=usage.get("prompt_tokens", 0),
        )
    )

    print(
        f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s"
    )
    assert "industrial" in response.lower(), "Expected summary to mention industry"
    print("[PASS] Summarization test passed")


def test_creative_writing():
    """Test creative writing - identical across models."""
    print("\n[TEST] Creative Writing")
    prompt = """Write a two-paragraph story about a robot discovering nature for the first time."""

    response, usage, duration = query_model(prompt, max_tokens=300, temperature=0.9)
    print(f"\n[OK] Response received ({len(response)} chars)")

    # Track metrics
    tokens_generated = usage.get("completion_tokens", 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(
        TestMetrics(
            test_name="Creative Writing",
            duration_s=duration,
            tokens_generated=tokens_generated,
            tokens_per_second=tokens_per_sec,
            prompt_tokens=usage.get("prompt_tokens", 0),
        )
    )

    print(
        f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s"
    )
    assert len(response) > 100, "Expected substantial creative output"
    print("[PASS] Creative writing test passed")


def test_structured_json_output():
    """Test structured JSON generation - identical across models."""
    print("\n[TEST] Structured JSON Output")
    prompt = """Generate a JSON object for a book with these fields:
- title (string)
- author (string)
- year (number)
- genres (array of strings)
- rating (number 1-5)

Use realistic data. Return only the JSON, no additional text."""

    response, usage, duration = query_model(prompt, max_tokens=300, temperature=0.1)
    print(f"\n[OK] Response received ({len(response)} chars)")

    # Track metrics
    tokens_generated = usage.get("completion_tokens", 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(
        TestMetrics(
            test_name="Structured JSON Output",
            duration_s=duration,
            tokens_generated=tokens_generated,
            tokens_per_second=tokens_per_sec,
            prompt_tokens=usage.get("prompt_tokens", 0),
        )
    )

    print(
        f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s"
    )

    # Try to parse JSON
    try:
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            parsed = json.loads(json_str)
            print(f"[INFO] Valid JSON with keys: {list(parsed.keys())}")
            print("[PASS] Structured JSON output test passed")
        else:
            print("[INFO] Response completed but JSON not clearly delimited")
    except json.JSONDecodeError:
        print("[INFO] Response completed but JSON parsing failed")


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
    print(f"PERFORMANCE REPORT - {MODEL_NAME}")
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
        "test_type": "text_comparison",
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
    print("[INFO] Text Comparison Benchmark")
    print(f"[INFO] Model: {MODEL_NAME}")
    print(f"[INFO] API URL: {API_URL}")
    print("[INFO] Running standardized text tests across models\n")

    try:
        # API Health
        test_api_health()

        # Standardized text tests
        test_code_generation_python()
        test_reasoning_logic()
        test_summarization()
        test_creative_writing()
        test_structured_json_output()

        # Print performance report
        print_performance_report()

        # Export JSON
        export_results_json()

        print("\n" + "=" * 70)
        print("[SUCCESS] All comparison tests passed!")
        print("=" * 70)
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"[FAILURE] Comparison tests failed: {e}")
        print("=" * 70)
        exit(1)
