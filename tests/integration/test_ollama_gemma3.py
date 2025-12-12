import json
import platform
import time
from dataclasses import asdict, dataclass
from datetime import datetime

import requests

# Configuration
MODEL_NAME = "gemma3:4b"  # Ollama model tag
OLLAMA_BASE_URL = "http://localhost:11434"
API_URL = f"{OLLAMA_BASE_URL}/v1/chat/completions"


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


def ensure_model_pulled():
    """Ensure the model is pulled in Ollama."""
    print(f"\n[SETUP] Checking if model '{MODEL_NAME}' is available...")
    try:
        # Check if model exists
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        resp.raise_for_status()
        models = [m["name"] for m in resp.json()["models"]]
        if MODEL_NAME in models:
            print(f"[OK] Model '{MODEL_NAME}' is already available.")
            return

        print(
            f"[INFO] Model '{MODEL_NAME}' not found. Pulling (this may take a while)..."
        )
        # Pull model (streaming)
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/pull", json={"name": MODEL_NAME, "stream": False}
        )
        resp.raise_for_status()
        print(f"[OK] Model '{MODEL_NAME}' pulled successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to check/pull model: {e}")
        raise


def query_ollama(prompt, max_tokens=200, temperature=0.7, image_url=None):
    """Query the Ollama model via OpenAI-compatible API.

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
    }

    print("   Streaming response...", end="", flush=True)
    start_time = time.time()
    response = requests.post(API_URL, headers=headers, json=data, stream=True)

    response.raise_for_status()

    full_content = []
    usage = {}

    for line in response.iter_lines():
        if line:
            decoded_line = line.decode("utf-8")
            if decoded_line.startswith("data: "):
                data_str = decoded_line[6:]
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


def test_api_health():
    """Test that the Ollama API is healthy."""
    print("\n[TEST] Testing API Health...")
    try:
        resp = requests.get(OLLAMA_BASE_URL)
        if resp.status_code == 200:
            print("[OK] Ollama is running.")
        else:
            print(f"[WARN] Ollama root endpoint returned {resp.status_code}")

        # Check tags endpoint
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        resp.raise_for_status()
        print("[PASS] API health test passed")
    except Exception as e:
        print(f"[FAIL] API health check failed: {e}")
        raise


def test_basic_chat():
    """Test basic chat functionality."""
    print("\n[TEST] Testing Basic Chat...")
    prompt = "What is the capital of France?"

    response, usage, duration = query_ollama(prompt, max_tokens=50, temperature=0.1)
    print(f"[OK] Response:\n{response}")

    # Track metrics (Ollama usage format might differ slightly but OpenAI shim should normalize)
    tokens_generated = usage.get("completion_tokens", 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(
        TestMetrics(
            test_name="Basic Chat",
            duration_s=duration,
            tokens_generated=tokens_generated,
            tokens_per_second=tokens_per_sec,
            prompt_tokens=usage.get("prompt_tokens", 0),
        )
    )

    print(
        f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s"
    )
    assert "Paris" in response or "paris" in response, "Expected 'Paris' in response"
    print("[PASS] Basic chat test passed")


def print_performance_report():
    """Print formatted performance report."""
    if not TEST_METRICS:
        return

    print("\n" + "=" * 70)
    print("PERFORMANCE REPORT")
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
    print(f"{'Test Name':<25} {'Duration':<12} {'Tokens':<10} {'Tok/s':<10}")
    print("-" * 70)
    for metric in TEST_METRICS:
        print(
            f"{metric.test_name:<25} {metric.duration_s:>8.2f}s    {metric.tokens_generated:>6}     {metric.tokens_per_second:>6.1f}"
        )

    print("=" * 70)


def export_results_json(filename="benchmark_results_ollama.json"):
    """Export results to JSON for further analysis."""
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
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "gpu": "NVIDIA RTX 5080 16GB",
            "driver": nvidia_version,
            "runtime": "ollama",
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
    print(f"[INFO] Starting Integration Tests for {MODEL_NAME} on Ollama...")
    print(f"[INFO] API URL: {API_URL}")

    try:
        # Prerequisites
        test_api_health()
        ensure_model_pulled()

        # Text Tests
        test_basic_chat()

        # Add more tests here similar to Gemma vLLM if needed,
        # but starting simple to verify integration.

        # Print performance report
        print_performance_report()

        # Export JSON
        export_results_json()

        print("\n" + "=" * 70)
        print("[SUCCESS] All integration tests passed!")
        print("=" * 70)
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"[FAILURE] Integration tests failed: {e}")
        print("=" * 70)
        exit(1)
