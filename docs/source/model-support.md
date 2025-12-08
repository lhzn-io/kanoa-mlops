# Adding Support for New Models

This guide walks through adding support for a new model to kanoa-mlops, using **allenai/OLMo-3-32B-Think** on NVIDIA Jetson Thor as an example.

## Overview

Adding a new model involves:

1. Testing the model locally
2. Creating integration tests
3. Adding benchmark suite
4. Documenting results
5. Submitting a pull request

## Step 1: Test Model Locally

### For Ollama

```bash
# Start Ollama
make serve-ollama

# Pull the model (if available in Ollama registry)
docker compose -f docker/ollama/docker-compose.ollama.yml exec ollama \
  ollama pull olmo3:32b

# Test manually
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "olmo3:32b",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'
```

### For vLLM

```bash
# Download model from Hugging Face
huggingface-cli download allenai/OLMo-3-32B-Think \
  --local-dir ~/.cache/huggingface/hub/models--allenai--OLMo-3-32B-Think

# Start vLLM server
vllm serve allenai/OLMo-3-32B-Think \
  --port 8000 \
  --gpu-memory-utilization 0.85 \
  --max-model-len 4096

# Test
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "allenai/OLMo-3-32B-Think",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'
```

## Step 2: Create Integration Test

Create `tests/integration/test_<platform>_<model>.py` based on existing templates.

### Example: `test_ollama_olmo3.py`

```python
import time
from dataclasses import dataclass, asdict
import json
import platform
from datetime import datetime
import requests

# Configuration
MODEL_NAME = "olmo3:32b"  # Ollama model tag
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

def query_ollama(prompt, max_tokens=200, temperature=0.7):
    """Query the Ollama model via OpenAI-compatible API."""
    headers = {"Content-Type": "application/json"}
    
    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    start_time = time.time()
    response = requests.post(API_URL, headers=headers, json=data)
    duration_s = time.time() - start_time
    
    response.raise_for_status()
    result = response.json()
    return result['choices'][0]['message']['content'], result.get('usage', {}), duration_s

def test_api_health():
    """Test that the Ollama API is healthy."""
    print("\\n[TEST] Testing API Health...")
    try:
        resp = requests.get(OLLAMA_BASE_URL)
        if resp.status_code == 200:
            print("[OK] Ollama is running.")
        
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        resp.raise_for_status()
        print("[PASS] API health test passed")
    except Exception as e:
        print(f"[FAIL] API health check failed: {e}")
        raise

def test_basic_chat():
    """Test basic chat functionality."""
    print("\\n[TEST] Testing Basic Chat...")
    prompt = "What is the capital of France?"
    
    response, usage, duration = query_ollama(prompt, max_tokens=50, temperature=0.1)
    print(f"[OK] Response:\\n{response}")
    
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

def test_reasoning():
    """Test reasoning capability."""
    print("\\n[TEST] Testing Reasoning...")
    prompt = """A farmer has 17 sheep, and all but 9 die. How many sheep are left?
Think step by step."""
    
    response, usage, duration = query_ollama(prompt, max_tokens=200, temperature=0.1)
    print(f"[OK] Response:\\n{response}")
    
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
    print("[PASS] Reasoning test passed")

def print_performance_report():
    """Print formatted performance report."""
    if not TEST_METRICS:
        return
    
    print("\\n" + "="*70)
    print("PERFORMANCE REPORT")
    print("="*70)
    
    total_tokens = sum(m.tokens_generated for m in TEST_METRICS)
    total_duration = sum(m.duration_s for m in TEST_METRICS)
    avg_tokens_per_sec = total_tokens / total_duration if total_duration > 0 else 0
    
    print(f"\\nOverall Statistics:")
    print(f"  Total Tokens Generated: {total_tokens}")
    print(f"  Total Duration: {total_duration:.2f}s")
    print(f"  Average Throughput: {avg_tokens_per_sec:.1f} tokens/s")
    
    print(f"\\nPer-Test Results:")
    print(f"{'Test Name':<25} {'Duration':<12} {'Tokens':<10} {'Tok/s':<10}")
    print("-" * 70)
    for metric in TEST_METRICS:
        print(f"{metric.test_name:<25} {metric.duration_s:>8.2f}s    {metric.tokens_generated:>6}     {metric.tokens_per_second:>6.1f}")
    
    print("="*70)

def export_results_json(filename="benchmark_results_olmo3.json"):
    """Export results to JSON for further analysis."""
    if not TEST_METRICS:
        return
    
    try:
        with open('/proc/driver/nvidia/version', 'r') as f:
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
            "gpu": "NVIDIA Jetson Thor",  # Update for your hardware
            "driver": nvidia_version,
            "runtime": "ollama"
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
    
    print(f"\\n[INFO] Benchmark results exported to: {filename}")

if __name__ == "__main__":
    print(f"[INFO] Starting Integration Tests for {MODEL_NAME} on Ollama...")
    print(f"[INFO] API URL: {API_URL}")
    
    try:
        test_api_health()
        test_basic_chat()
        test_reasoning()
        
        print_performance_report()
        export_results_json()
        
        print("\\n" + "="*70)
        print("[SUCCESS] All integration tests passed!")
        print("="*70)
    except Exception as e:
        print("\\n" + "="*70)
        print(f"[FAILURE] Integration tests failed: {e}")
        print("="*70)
        exit(1)
```

## Step 3: Create Benchmark Suite

Create `tests/integration/run_benchmark_suite_<model>.py`:

```python
#!/usr/bin/env python3
"""Run multiple benchmark iterations and compute statistics for OLMo-3."""

import json
import subprocess
import time
from pathlib import Path
from statistics import mean, stdev


def run_single_benchmark():
    """Run a single benchmark and return results."""
    result = subprocess.run(
        ["python3", "test_ollama_olmo3.py"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )
    
    if result.returncode != 0:
        print(f"[ERROR] Benchmark failed: {result.stderr}")
        return None
    
    try:
        with open(Path(__file__).parent / "benchmark_results_olmo3.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[ERROR] benchmark_results_olmo3.json not found")
        return None

def main():
    num_runs = 3
    results = []
    
    print(f"Running {num_runs} benchmark iterations for OLMo-3...\\n")
    
    for i in range(num_runs):
        print(f"[{i+1}/{num_runs}] Running benchmark...")
        result = run_single_benchmark()
        
        if result:
            results.append(result)
            print(f"  ✓ Completed: {result['summary']['total_tokens']} tokens in {result['summary']['total_duration_s']:.1f}s")
            print(f"    Throughput: {result['summary']['avg_tokens_per_second']:.1f} tok/s\\n")
        else:
            print("  ✗ Failed\\n")
        
        if i < num_runs - 1:
            time.sleep(2)
    
    if not results:
        print("[ERROR] No successful runs")
        return
    
    # Compute statistics
    print("="*70)
    print("OLMO-3 BENCHMARK STATISTICS")
    print("="*70)
    print(f"\\nRuns completed: {len(results)}")
    
    throughputs = [r['summary']['avg_tokens_per_second'] for r in results]
    print("\\nOverall Throughput:")
    print(f"  Mean:   {mean(throughputs):.1f} tok/s")
    if len(throughputs) > 1:
        print(f"  StdDev: {stdev(throughputs):.1f} tok/s")
        print(f"  Min:    {min(throughputs):.1f} tok/s")
        print(f"  Max:    {max(throughputs):.1f} tok/s")
    
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
            }
        },
        "raw_results": results
    }
    
    with open("benchmark_statistics_olmo3.json", "w") as f:
        json.dump(aggregated, f, indent=2)
    
    print("\\n[INFO] Statistics saved to: benchmark_statistics_olmo3.json")

if __name__ == "__main__":
    main()
```

## Step 4: Run and Document Results

### Run Benchmarks

```bash
cd tests/integration

# Single run
python3 test_ollama_olmo3.py

# Benchmark suite (3 iterations)
python3 run_benchmark_suite_olmo3.py
```

### Document Results

Create a results file documenting your findings:

**`docs/results/olmo3-jetson-thor.md`**:

```markdown
# OLMo-3-32B-Think on NVIDIA Jetson Thor

## Hardware

- **Platform**: NVIDIA Jetson Thor
- **GPU**: [Specs]
- **RAM**: [Amount]
- **Storage**: [Type and size]

## Software

- **OS**: Ubuntu 22.04 (JetPack 6.0)
- **CUDA**: 12.2
- **Docker**: 24.0.7
- **Ollama**: 0.13.1

## Model Configuration

- **Model**: allenai/OLMo-3-32B-Think
- **Quantization**: None (FP16)
- **Context Length**: 4096
- **Batch Size**: 1

## Performance Results

### Throughput

| Metric | Value |
|--------|-------|
| Mean | XX.X tok/s |
| StdDev | X.X tok/s |
| Min | XX.X tok/s |
| Max | XX.X tok/s |

### Memory Usage

- **GPU Memory**: XX GB / XX GB
- **System RAM**: XX GB / XX GB

### Latency

- **Time to First Token**: XXX ms
- **Per-Token Latency**: XX ms

## Observations

- [Any notable behaviors, issues, or optimizations]
- [Thermal performance]
- [Stability over long runs]

## Recommendations

- [Optimal batch size]
- [Memory configuration]
- [Use cases this setup is good for]
```

## Step 5: Submit Pull Request

### 1. Create a Branch

```bash
git checkout -b add-olmo3-support
```

### 2. Stage Your Changes

```bash
git add tests/integration/test_ollama_olmo3.py
git add tests/integration/run_benchmark_suite_olmo3.py
git add docs/results/olmo3-jetson-thor.md
```

### 3. Commit

```bash
git commit -m "feat: add OLMo-3-32B-Think support for Jetson Thor

- Add integration test for OLMo-3 on Ollama
- Add benchmark suite for statistical analysis
- Document performance results on Jetson Thor
- Tested on Jetson Thor with XX GB GPU memory"
```

### 4. Push and Create PR

```bash
git push origin add-olmo3-support
```

Then create a pull request on GitHub with:

- **Title**: `feat: Add OLMo-3-32B-Think support for Jetson Thor`
- **Description**: Summary of changes, performance results, and any notable findings

## Best Practices

### Test Coverage

Include tests for:

- ✅ Basic chat completion
- ✅ Reasoning tasks
- ✅ Code generation (if applicable)
- ✅ Long context (if model supports it)
- ✅ Multi-turn conversations

### Performance Metrics

Always report:

- ✅ Throughput (tokens/sec)
- ✅ Memory usage
- ✅ First token latency
- ✅ Hardware specifications
- ✅ Software versions

### Documentation

- ✅ Clear hardware specs
- ✅ Reproducible setup instructions
- ✅ Known limitations
- ✅ Recommended configurations

## Troubleshooting

### Model Won't Load

```bash
# Check available memory
free -h
nvidia-smi

# Try with reduced memory utilization
vllm serve <model> --gpu-memory-utilization 0.7
```

### Out of Memory

- Use quantization (INT8, INT4)
- Reduce context length: `--max-model-len 2048`
- Enable CPU offloading (if supported)

### Slow Performance

- Check thermal throttling: `nvidia-smi dmon`
- Verify GPU utilization: `nvidia-smi`
- Ensure no other processes using GPU

## See Also

- [Quickstart Guide](quickstart.md)
- [Benchmarking Guide](../tests/integration/README.md)
- [Contributing Guide](contributing.md)
