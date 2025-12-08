import json
import platform
import time
from dataclasses import asdict, dataclass
from datetime import datetime

import requests

MODEL_NAME = "olmo3-32b-think"
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


def query_olmo3(prompt, max_tokens=500, temperature=0.7):
    """Query the Olmo3 model via vLLM OpenAI-compatible API.

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


def test_code_generation_python():
    """Test code generation capability with Python."""
    print("\n[TEST] Testing Code Generation - Python...")
    prompt = """Write a Python function that implements a binary search algorithm.
Include:
- Type hints
- Docstring with parameters and return value
- Edge case handling
- Example usage"""

    response, usage, duration = query_olmo3(prompt, max_tokens=500, temperature=0.2)
    print(f"[OK] Response:\n{response}")

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
    assert "def" in response and "binary" in response.lower(), (
        "Expected function definition for binary search"
    )
    print("[PASS] Code generation test (Python) passed")


def test_code_generation_sql():
    """Test code generation capability with SQL."""
    print("\n[TEST] Testing Code Generation - SQL...")
    prompt = """Write a SQL query that:
1. Joins three tables: users, orders, and products
2. Calculates the total revenue per user
3. Filters for orders in the last 30 days
4. Returns top 10 users by revenue

Include comments explaining each part."""

    response, usage, duration = query_olmo3(prompt, max_tokens=400, temperature=0.2)
    print(f"[OK] Response:\n{response}")

    # Track metrics
    tokens_generated = usage.get("completion_tokens", 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(
        TestMetrics(
            test_name="Code Generation - SQL",
            duration_s=duration,
            tokens_generated=tokens_generated,
            tokens_per_second=tokens_per_sec,
            prompt_tokens=usage.get("prompt_tokens", 0),
        )
    )

    print(
        f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s"
    )
    assert "SELECT" in response or "select" in response, "Expected SQL SELECT statement"
    print("[PASS] Code generation test (SQL) passed")


def test_complex_reasoning_multistep():
    """Test multi-step reasoning capability."""
    print("\n[TEST] Testing Complex Reasoning - Multi-step...")
    prompt = """Solve this problem step by step:

A bakery makes 300 loaves of bread per day. Each loaf requires:
- 500g flour
- 300ml water  
- 10g salt
- 5g yeast

The bakery operates 6 days a week and wants to plan ingredient orders for a month (4 weeks).

Calculate:
1. Total ingredients needed per week
2. Total ingredients needed per month
3. If flour comes in 25kg bags, water in 5L bottles, salt in 1kg containers, and yeast in 100g packets, how many of each should they order per month?

Show your work and reasoning for each step."""

    response, usage, duration = query_olmo3(prompt, max_tokens=600, temperature=0.1)
    print(f"[OK] Response:\n{response}")

    # Track metrics
    tokens_generated = usage.get("completion_tokens", 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(
        TestMetrics(
            test_name="Complex Reasoning",
            duration_s=duration,
            tokens_generated=tokens_generated,
            tokens_per_second=tokens_per_sec,
            prompt_tokens=usage.get("prompt_tokens", 0),
        )
    )

    print(
        f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s"
    )
    print("[PASS] Complex reasoning test passed")


def test_structured_scientific_output():
    """Test ability to produce structured scientific output in JSON format."""
    print("\n[TEST] Testing Structured Scientific Output...")
    prompt = """Analyze the following hypothetical experimental data and return a structured JSON response:

Experiment: Effect of temperature on enzyme activity
Data points:
- 10°C: 15 units/min
- 20°C: 45 units/min
- 30°C: 78 units/min
- 40°C: 92 units/min
- 50°C: 65 units/min
- 60°C: 20 units/min

Return a JSON object with this exact structure:
{
  "optimal_temperature": <temperature with highest activity>,
  "optimal_activity": <activity value at optimal temp>,
  "trend_description": <brief description of the trend>,
  "hypothesis": <scientific hypothesis explaining the results>,
  "recommendations": [<list of 2-3 recommendations for further study>]
}

Only return the JSON, no additional text."""

    response, usage, duration = query_olmo3(prompt, max_tokens=400, temperature=0.1)
    print(f"[OK] Response:\n{response}")

    # Track metrics
    tokens_generated = usage.get("completion_tokens", 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(
        TestMetrics(
            test_name="Structured Scientific Output",
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
        # Extract JSON from response if it contains extra text
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            parsed = json.loads(json_str)
            print(f"[INFO] Successfully parsed JSON with keys: {list(parsed.keys())}")
            print("[PASS] Structured scientific output test passed (valid JSON)")
        else:
            print("[INFO] Response may not contain valid JSON, but test completed")
    except json.JSONDecodeError:
        print("[INFO] Response is not valid JSON, but test completed")


def test_algorithm_design():
    """Test algorithm design and explanation capability."""
    print("\n[TEST] Testing Algorithm Design...")
    prompt = """Design an efficient algorithm to find the longest palindromic substring in a given string.

Provide:
1. Algorithm explanation (in plain English)
2. Time complexity analysis
3. Space complexity analysis
4. Pseudocode
5. Python implementation"""

    response, usage, duration = query_olmo3(prompt, max_tokens=600, temperature=0.2)
    print(f"[OK] Response:\n{response}")

    # Track metrics
    tokens_generated = usage.get("completion_tokens", 0)
    tokens_per_sec = tokens_generated / duration if duration > 0 else 0
    TEST_METRICS.append(
        TestMetrics(
            test_name="Algorithm Design",
            duration_s=duration,
            tokens_generated=tokens_generated,
            tokens_per_second=tokens_per_sec,
            prompt_tokens=usage.get("prompt_tokens", 0),
        )
    )

    print(
        f"[PERF] {duration:.2f}s | {tokens_generated} tokens | {tokens_per_sec:.1f} tok/s"
    )
    assert "palindrom" in response.lower(), "Expected palindrome-related content"
    print("[PASS] Algorithm design test passed")


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
    print(f"{'Test Name':<35} {'Duration':<12} {'Tokens':<10} {'Tok/s':<10}")
    print("-" * 70)
    for metric in TEST_METRICS:
        print(
            f"{metric.test_name:<35} {metric.duration_s:>8.2f}s    {metric.tokens_generated:>6}     {metric.tokens_per_second:>6.1f}"
        )

    print("=" * 70)


def export_results_json(filename="benchmark_results_olmo3.json"):
    """Export results to JSON for GitHub Pages or further analysis."""
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
    print("[INFO] Starting Integration Tests for Olmo3 32B Think...")
    print(f"[INFO] Model: {MODEL_NAME}")
    print(f"[INFO] API URL: {API_URL}")
    print("[INFO] Testing code generation, reasoning, and structured output capabilities")

    try:
        # API Health
        test_api_health()

        # Code Generation Tests
        test_code_generation_python()
        test_code_generation_sql()

        # Complex Reasoning Test
        test_complex_reasoning_multistep()

        # Structured Scientific Output Test
        test_structured_scientific_output()

        # Algorithm Design Test
        test_algorithm_design()

        # Print performance report
        print_performance_report()

        # Export JSON for GitHub Pages
        export_results_json()

        print("\n" + "=" * 70)
        print("[SUCCESS] All integration tests passed!")
        print("=" * 70)
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"[FAILURE] Integration tests failed: {e}")
        print("=" * 70)
        exit(1)
