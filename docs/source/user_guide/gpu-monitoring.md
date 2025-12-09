# GPU Monitoring Tools

Real-time GPU monitoring is essential for understanding model performance, memory usage, and identifying bottlenecks during development and benchmarking.

## Recommended Tools

### nvitop (Primary Recommendation)

**nvitop** provides an interactive, htop-style interface for NVIDIA GPUs.

**Installation:**
```bash
# Already included in requirements-dev.txt
conda activate kanoa-mlops
pip install -r requirements-dev.txt
```

**Usage:**
```bash
# Interactive mode (like htop)
nvitop

# Single snapshot
nvitop --once

# Compact mode
nvitop --compact
```

**Features:**
- Real-time GPU utilization, memory, temperature, power
- Per-process GPU memory usage
- Color-coded resource bars
- Interactive process management
- Multi-GPU support

### gpustat (Quick View)

**gpustat** provides a clean, compact summary of GPU status.

**Usage:**
```bash
# Single snapshot
gpustat --color

# Watch mode (updates every 1 second)
watch -n 1 gpustat --color
```

**Features:**
- Clean, single-line output per GPU
- Good for quick checks or scripting
- Lightweight and fast

### nvidia-smi (Built-in)

The standard NVIDIA tool, always available but less user-friendly.

**Useful Commands:**
```bash
# Basic status
nvidia-smi

# Continuous monitoring (updates every 1s)
nvidia-smi dmon

# Custom query
nvidia-smi --query-gpu=timestamp,utilization.gpu,memory.used,temperature.gpu --format=csv
```

## Monitoring During Benchmarks

When running performance benchmarks, monitor these key metrics:

### 1. GPU Utilization
- **Target**: 80-100% during inference
- **Low utilization** (<50%): Possible CPU bottleneck or inefficient batching

### 2. Memory Usage
- **For 16GB RTX 5080**:
  - Gemma 3 4B: ~8-10GB (with 4-bit quantization)
  - Gemma 3 12B: ~12-15GB (with 4-bit quantization)
- **High memory** (>95%): Risk of OOM errors or cache eviction

### 3. Temperature
- **Normal**: 40-80°C
- **Warning**: >80°C (check cooling/airflow)

### 4. Power Draw
- **RTX 5080**: Up to 360W max
- **Typical load**: 100-300W during inference

## Prometheus & Grafana Monitoring Stack

For production-grade monitoring with dashboards and historical metrics, use the included Prometheus + Grafana stack.

### Quick Start

```bash
# From kanoa-mlops root directory
docker compose -f docker/monitoring/docker-compose.yml up -d
```

**Access:**

- Grafana: <http://localhost:3000> (admin/admin)
- Prometheus: <http://localhost:9090>

The stack includes:

- Auto-provisioned Grafana dashboards for vLLM metrics
- 30-day metric retention
- Real-time GPU cache, throughput, and latency monitoring
- Support for remote endpoints (GCP, Azure, on-prem)

For full documentation, see the [Monitoring Stack README](../../../monitoring/README.md).

### vLLM Metrics Reference

vLLM exposes Prometheus metrics at `/metrics`:

**Key Metrics:**

| Metric | Type | Description |
|--------|------|-------------|
| `vllm:gpu_cache_usage_perc` | Gauge | GPU KV cache utilization (0-100%) |
| `vllm:num_requests_running` | Gauge | Currently executing requests |
| `vllm:avg_generation_throughput_toks_per_s` | Gauge | Output token speed |
| `vllm:time_to_first_token_seconds` | Gauge | Latency to first token |
| `vllm:num_preemptions_total` | Counter | Total cache evictions |

**Quick Check:**

```bash
# View raw metrics
curl http://localhost:8000/metrics

# Watch cache usage
watch -n 1 'curl -s http://localhost:8000/metrics | grep cache_usage_perc'
```

### Example: Calculate Cache Hit Rate

```python
import requests

def get_cache_hit_rate():
    metrics = requests.get("http://localhost:8000/metrics").text

    hits = 0
    queries = 0

    for line in metrics.split('\n'):
        if 'vllm:prefix_cache_hits' in line and not line.startswith('#'):
            hits = float(line.split()[-1])
        elif 'vllm:prefix_cache_queries' in line and not line.startswith('#'):
            queries = float(line.split()[-1])

    return (hits / queries * 100) if queries > 0 else 0

print(f"Prefix cache hit rate: {get_cache_hit_rate():.1f}%")
```

## Troubleshooting Performance Issues

### High Variance in Benchmark Results

If you see inconsistent performance across test runs:

1. **Check GPU contention**: Use `nvitop` to verify only one model is loaded
2. **Monitor memory pressure**: High memory usage (>95%) can cause cache eviction
3. **Verify thermal throttling**: Temperature >80°C may trigger performance reduction
4. **Check KV cache utilization**: Low hit rates indicate poor caching

### Example Investigation:

```bash
# Terminal 1: Monitor GPU in real-time
nvitop

# Terminal 2: Run benchmark with verbose logging
cd tests/integration
python3 test_vllm_gemma3_api.py

# Terminal 3: Watch vLLM metrics
watch -n 1 'curl -s http://localhost:8000/metrics | grep -E "(cache|memory|token)"'
```

## Best Practices

1. **Always monitor during development**: Catch memory leaks and performance regressions early
2. **Baseline before optimization**: Record metrics before making changes
3. **Use consistent load**: Keep GPU warm (previous inference) for fair comparisons
4. **Document your setup**: GPU driver version, CUDA version, model config
5. **Multiple runs**: Use the benchmark suite (`run_benchmark_suite_gemma3.py`) to measure variance

## Integration with Benchmark Suite

Our benchmark suite automatically collects performance metrics. For GPU monitoring integration:

```bash
# Run benchmark suite for Gemma 3 12B (3 iterations)
cd tests/integration
python3 run_benchmark_suite_gemma3.py

# Run benchmark suite for Molmo 7B (3 iterations)
python3 run_benchmark_suite_molmo.py
```

Each suite includes:

- Per-test timing and token throughput
- Statistical analysis (mean, stddev, min, max)
- JSON output with full results

Results are saved to:

- `benchmark_statistics_gemma3.json` - Gemma 3 12B results
- `benchmark_statistics_molmo.json` - Molmo 7B results

### Benchmark Results (RTX 5080 16GB eGPU)

Real-world performance with 4-bit quantization + FP8 KV cache:

| Model | Mean Throughput | Std Dev | Range | Relative Speed |
| :--- | :--- | :--- | :--- | :--- |
| **Molmo 7B** | **31.1 tok/s** | 5.9 tok/s | 24.2 - 34.5 tok/s | **3.02x faster** |
| Gemma 3 12B | 10.3 tok/s | 3.5 tok/s | 8.1 - 14.4 tok/s | Baseline |

**Per-Test Breakdown (Molmo 7B)**:

- Boardwalk Photo: 29.3 ± 5.8 tok/s
- Complex Plot: 32.7 ± 6.3 tok/s
- Data Interpretation: 28.8 ± 8.8 tok/s

**Key Observations**:

1. **Molmo 7B is 3x faster** despite being smaller (7B vs 12B parameters)
2. **Similar variance** across both models (~19-34% coefficient of variation)
3. **First inference penalty**: Cold cache results in slower initial requests (prefix caching helps)
4. **Task complexity matters**: Data interpretation shows highest variance (18.8-35.4 tok/s)

### Benchmark Methodology

Each benchmark suite runs 3 iterations of:

1. **API Health Check**: Verify server responsiveness
2. **Vision Tests** (Molmo):
   - Real-world photo interpretation
   - Complex multi-panel matplotlib plots
   - Data visualization analysis
3. **Vision + Text Tests** (Gemma 3):
   - Chart interpretation
   - Code generation from visual input
   - Reasoning tasks
   - Structured output (JSON)
   - Multi-turn conversations

**Metrics Collected**:

- Total tokens generated
- Total duration (seconds)
- Tokens per second (throughput)
- Per-test timing and variance

**Hardware Configuration**:

- GPU: NVIDIA RTX 5080 16GB (eGPU via Thunderbolt 5)
- Quantization: 4-bit BitsAndBytes
- KV Cache: FP8 dtype
- GPU Memory Utilization: 80%
- Max Sequences: 5
- Chunked Prefill: Enabled (2048 tokens)

## References

- [nvitop GitHub](https://github.com/XuehaiPan/nvitop)
- [gpustat GitHub](https://github.com/wookayin/gpustat)
- [vLLM Metrics Documentation](https://docs.vllm.ai/en/latest/serving/metrics.html)
- [NVIDIA-SMI Reference](https://developer.nvidia.com/nvidia-system-management-interface)
