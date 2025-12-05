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

## vLLM-Specific Metrics

For more detailed performance analysis, vLLM exposes Prometheus metrics at `/metrics`:

### Key Metrics to Monitor:

```python
import requests

metrics = requests.get("http://localhost:8000/metrics").text

# Prefix cache hit rate (higher is better)
# vllm:prefix_cache_hits / vllm:prefix_cache_queries

# KV cache utilization (target: 85-95%)
# vllm:gpu_cache_usage_perc

# Latency (Time to First Token)
# vllm:time_to_first_token_seconds
```

### Example: Calculate Cache Hit Rate

```python
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
5. **Multiple runs**: Use the benchmark suite (`run_benchmark_suite.py`) to measure variance

## Integration with Benchmark Suite

Our benchmark suite automatically collects performance metrics. For GPU monitoring integration:

```python
# tests/integration/run_benchmark_suite.py includes:
# - Per-test timing
# - Token throughput
# - Statistical analysis (mean, stddev, min, max)

# Run multiple iterations to measure variance
python3 tests/integration/run_benchmark_suite.py
```

Results are saved to `benchmark_statistics.json` with full statistics.

## References

- [nvitop GitHub](https://github.com/XuehaiPan/nvitop)
- [gpustat GitHub](https://github.com/wookayin/gpustat)
- [vLLM Metrics Documentation](https://docs.vllm.ai/en/latest/serving/metrics.html)
- [NVIDIA-SMI Reference](https://developer.nvidia.com/nvidia-system-management-interface)
