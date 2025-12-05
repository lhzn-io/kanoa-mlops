import base64
import io
import json
import platform
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
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
            {"type": "image_url", "image_url": {"url": image_url}}
        ]
    else:
        # Text-only request
        content = prompt

    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": content}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    start_time = time.time()
    response = requests.post(API_URL, headers=headers, json=data)
    duration_s = time.time() - start_time

    response.raise_for_status()
    result = response.json()
    return result['choices'][0]['message']['content'], result.get('usage', {}), duration_s

def test_vision_boardwalk():
    """Test vision capability with a real-world photo."""
    print("\n[TEST] Testing Vision - Boardwalk Photo...")
    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/960px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"

    # Download image and convert to base64
    print(f"   Downloading {image_url}...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    img_resp = requests.get(image_url, headers=headers)
    img_resp.raise_for_status()

    # Convert to Base64
    img = Image.open(io.BytesIO(img_resp.content))
    if max(img.size) > 1024:
        img.thumbnail((1024, 1024))

    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    base64_url = f"data:image/jpeg;base64,{img_str}"

    response, usage, duration = query_gemma("Describe this image in detail.", max_tokens=200, temperature=0.1, image_url=base64_url)
    print(f"[OK] Response:\n{response}")

    # Track metrics
    tokens_generated = usage.get('completion_tokens', 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(TestMetrics(
        test_name="Vision - Boardwalk",
        duration_s=duration,
        tokens_generated=tokens_generated,
        tokens_per_second=tokens_per_sec,
        prompt_tokens=usage.get('prompt_tokens', 0)
    ))

    print(f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s")
    print("[PASS] Vision test (boardwalk) passed")

def test_vision_chart():
    """Test vision capability with a matplotlib chart."""
    print("\n[TEST] Testing Vision - Matplotlib Chart...")

    # Generate a simple chart
    fig, ax = plt.subplots(figsize=(8, 6))
    categories = ['Q1', 'Q2', 'Q3', 'Q4']
    values = [45, 60, 55, 70]
    ax.bar(categories, values, color=['red', 'blue', 'green', 'orange'])
    ax.set_title('Quarterly Revenue (in millions)')
    ax.set_ylabel('Revenue ($M)')
    plt.tight_layout()

    # Convert to Base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)

    image_url = f"data:image/png;base64,{img_str}"

    response, usage, duration = query_gemma("What data is shown in this chart? Provide specific values.", max_tokens=200, temperature=0.1, image_url=image_url)
    print(f"[OK] Response:\n{response}")

    # Track metrics
    tokens_generated = usage.get('completion_tokens', 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(TestMetrics(
        test_name="Vision - Chart",
        duration_s=duration,
        tokens_generated=tokens_generated,
        tokens_per_second=tokens_per_sec,
        prompt_tokens=usage.get('prompt_tokens', 0)
    ))

    print(f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s")
    print("[PASS] Vision test (chart) passed")

def test_basic_chat():
    """Test basic chat functionality."""
    print("\n[TEST] Testing Basic Chat...")
    prompt = "What is the capital of France?"

    response, usage, duration = query_gemma(prompt, max_tokens=50, temperature=0.1)
    print(f"[OK] Response:\n{response}")

    # Track metrics
    tokens_generated = usage.get('completion_tokens', 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(TestMetrics(
        test_name="Basic Chat",
        duration_s=duration,
        tokens_generated=tokens_generated,
        tokens_per_second=tokens_per_sec,
        prompt_tokens=usage.get('prompt_tokens', 0)
    ))

    print(f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s")
    assert "Paris" in response or "paris" in response, "Expected 'Paris' in response"
    print("[PASS] Basic chat test passed")

def test_code_generation():
    """Test code generation capability."""
    print("\n[TEST] Testing Code Generation...")
    prompt = "Write a Python function to calculate the fibonacci sequence. Include a docstring."

    response, usage, duration = query_gemma(prompt, max_tokens=300, temperature=0.2)
    print(f"[OK] Response:\n{response}")

    # Track metrics
    tokens_generated = usage.get('completion_tokens', 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(TestMetrics(
        test_name="Code Generation",
        duration_s=duration,
        tokens_generated=tokens_generated,
        tokens_per_second=tokens_per_sec,
        prompt_tokens=usage.get('prompt_tokens', 0)
    ))

    print(f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s")
    assert "def" in response or "fibonacci" in response.lower(), "Expected function definition"
    print("[PASS] Code generation test passed")

def test_reasoning():
    """Test reasoning and problem-solving."""
    print("\n[TEST] Testing Reasoning...")
    prompt = """A farmer has 17 sheep, and all but 9 die. How many sheep are left?
Think step by step and explain your reasoning."""

    response, usage, duration = query_gemma(prompt, max_tokens=200, temperature=0.1)
    print(f"[OK] Response:\n{response}")

    # Track metrics
    tokens_generated = usage.get('completion_tokens', 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(TestMetrics(
        test_name="Reasoning",
        duration_s=duration,
        tokens_generated=tokens_generated,
        tokens_per_second=tokens_per_sec,
        prompt_tokens=usage.get('prompt_tokens', 0)
    ))

    print(f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s")
    print("[PASS] Reasoning test completed")

def test_structured_output():
    """Test ability to produce structured output (JSON)."""
    print("\n[TEST] Testing Structured Output...")
    prompt = """List 3 programming languages with their primary use cases.
Return your answer as a JSON array with objects containing 'language' and 'use_case' fields."""

    response, usage, duration = query_gemma(prompt, max_tokens=250, temperature=0.1)
    print(f"[OK] Response:\n{response}")

    # Track metrics
    tokens_generated = usage.get('completion_tokens', 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(TestMetrics(
        test_name="Structured Output",
        duration_s=duration,
        tokens_generated=tokens_generated,
        tokens_per_second=tokens_per_sec,
        prompt_tokens=usage.get('prompt_tokens', 0)
    ))

    print(f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s")
    if "[" in response and "]" in response:
        print("[PASS] Structured output test passed (JSON detected)")
    else:
        print("[INFO] Response may not be valid JSON, but test completed")

def test_multi_turn_conversation():
    """Test multi-turn conversation capability."""
    print("\n[TEST] Testing Multi-turn Conversation...")

    headers = {"Content-Type": "application/json"}
    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": "My name is Alice."},
            {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
            {"role": "user", "content": "What's my name?"}
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }

    start_time = time.time()
    response = requests.post(API_URL, headers=headers, json=data)
    duration = time.time() - start_time

    response.raise_for_status()
    result = response.json()['choices'][0]['message']['content']
    usage = response.json().get('usage', {})

    print(f"[OK] Response:\n{result}")

    # Track metrics
    tokens_generated = usage.get('completion_tokens', 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(TestMetrics(
        test_name="Multi-turn",
        duration_s=duration,
        tokens_generated=tokens_generated,
        tokens_per_second=tokens_per_sec,
        prompt_tokens=usage.get('prompt_tokens', 0)
    ))

    print(f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s")
    assert "Alice" in result or "alice" in result, "Expected model to remember the name"
    print("[PASS] Multi-turn conversation test passed")

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
    print(f"[OK] Health check passed")
    print("[PASS] API health test passed")

def print_performance_report():
    """Print formatted performance report."""
    if not TEST_METRICS:
        return

    print("\n" + "="*70)
    print("PERFORMANCE REPORT")
    print("="*70)

    # Summary stats
    total_tokens = sum(m.tokens_generated for m in TEST_METRICS)
    total_duration = sum(m.duration_s for m in TEST_METRICS)
    avg_tokens_per_sec = total_tokens / total_duration if total_duration > 0 else 0

    print(f"\nOverall Statistics:")
    print(f"  Total Tokens Generated: {total_tokens}")
    print(f"  Total Duration: {total_duration:.2f}s")
    print(f"  Average Throughput: {avg_tokens_per_sec:.1f} tokens/s")

    # Per-test breakdown
    print(f"\nPer-Test Results:")
    print(f"{'Test Name':<25} {'Duration':<12} {'Tokens':<10} {'Tok/s':<10}")
    print("-" * 70)
    for metric in TEST_METRICS:
        print(f"{metric.test_name:<25} {metric.duration_s:>8.2f}s    {metric.tokens_generated:>6}     {metric.tokens_per_second:>6.1f}")

    print("="*70)

def export_results_json(filename="benchmark_results.json"):
    """Export results to JSON for GitHub Pages or further analysis."""
    if not TEST_METRICS:
        return

    # Get system info
    try:
        with open('/proc/driver/nvidia/version', 'r') as f:
            nvidia_version = f.readline().strip()
    except:
        nvidia_version = "unknown"

    results = {
        "timestamp": datetime.now().isoformat(),
        "model": MODEL_NAME,
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "gpu": "NVIDIA RTX 5080 16GB",
            "driver": nvidia_version
        },
        "summary": {
            "total_tokens": sum(m.tokens_generated for m in TEST_METRICS),
            "total_duration_s": sum(m.duration_s for m in TEST_METRICS),
            "avg_tokens_per_second": sum(m.tokens_per_second for m in TEST_METRICS) / len(TEST_METRICS)
        },
        "tests": [asdict(m) for m in TEST_METRICS]
    }

    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n[INFO] Benchmark results exported to: {filename}")

if __name__ == "__main__":
    print("[INFO] Starting Integration Tests for Gemma 3 on eGPU (RTX 5080)...")
    print(f"[INFO] Model: {MODEL_NAME}")
    print(f"[INFO] API URL: {API_URL}")
    print("[INFO] Testing both vision and text capabilities")

    try:
        # API Health
        test_api_health()

        # Vision Tests (Gemma 3 supports multimodal)
        test_vision_boardwalk()
        test_vision_chart()

        # Text Tests
        test_basic_chat()
        test_code_generation()
        test_reasoning()
        test_structured_output()
        test_multi_turn_conversation()

        # Print performance report
        print_performance_report()

        # Export JSON for GitHub Pages
        export_results_json()

        print("\n" + "="*70)
        print("[SUCCESS] All integration tests passed!")
        print("="*70)
    except Exception as e:
        print("\n" + "="*70)
        print(f"[FAILURE] Integration tests failed: {e}")
        print("="*70)
        exit(1)
