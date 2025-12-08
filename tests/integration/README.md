# Benchmarking Suite

This directory contains performance benchmarking tools for testing local inference servers (vLLM, Ollama, Molmo).

## Overview

The benchmarking suite provides:

- **Single-run tests**: Quick validation of model performance
- **Multi-run benchmarks**: Statistical analysis across multiple iterations
- **JSON output**: Machine-readable results for tracking over time

## Available Benchmarks

### vLLM (Gemma 3)

- **Single run**: `python3 test_vllm_gemma3_api.py`
- **Benchmark suite**: `python3 run_benchmark_suite.py`
- **Model**: Gemma 3 12B
- **Port**: 8000

### Ollama (Gemma 3 4B)

- **Single run**: `python3 test_ollama_gemma3.py`
- **Benchmark suite**: `python3 run_benchmark_suite_ollama.py`
- **Model**: Gemma 3 4B
- **Port**: 11434

### Molmo (7B)

- **Single run**: `python3 test_vllm_molmo_api.py`
- **Benchmark suite**: `python3 run_benchmark_suite_molmo.py`
- **Model**: Molmo 7B
- **Port**: 8000

## Usage

### Running a Single Test

```bash
cd tests/integration

# Start your inference server first (e.g., make serve-ollama)
python3 test_ollama_gemma3.py
```

This will:

1. Check API health
2. Pull the model if needed (Ollama only)
3. Run test queries
4. Display performance metrics
5. Export results to `benchmark_results_<platform>.json`

### Running a Benchmark Suite

For statistical analysis across multiple runs:

```bash
cd tests/integration
python3 run_benchmark_suite_ollama.py
```

**Default**: 3 iterations with 2-second pauses between runs.

**Output**:

- Console: Mean, StdDev, Min, Max throughput
- `benchmark_statistics_ollama.json`: Aggregated results

### Customizing Benchmark Runs

Edit the benchmark suite script to change:

- `num_runs`: Number of iterations (default: 3)
- Test parameters in the underlying test file

## Output Files

All benchmark result files are **gitignored** as they are generated artifacts:

- `benchmark_results_*.json`: Single-run results
- `benchmark_statistics_*.json`: Multi-run aggregated statistics
- `benchmark_runs.txt`: Legacy text output (deprecated)

## Interpreting Results

### Throughput (tokens/sec)

- **First run**: Often slower due to model loading, JIT compilation
- **Subsequent runs**: More representative of steady-state performance
- **Variance**: High variance may indicate thermal throttling or system load

### Typical Performance (RTX 5080 16GB)

| Model | Platform | Throughput |
|-------|----------|------------|
| Gemma 3 12B | vLLM | ~80-100 tok/s |
| Gemma 3 4B | Ollama | ~55-65 tok/s |
| Molmo 7B | vLLM | ~60-80 tok/s |

## Makefile Integration

For convenience, use the root Makefile:

```bash
# From kanoa-mlops root
make test-ollama  # Runs Ollama integration test
```

## Troubleshooting

### "Connection refused"

- Ensure the inference server is running (`make serve-ollama`, etc.)
- Check the correct port is exposed

### "Model not found" (Ollama)

- The test will automatically pull the model
- First run will be slower due to download

### Low throughput

- **First run**: Normal, model is loading
- **Persistent**: Check GPU utilization (`nvidia-smi`), thermal throttling

## Adding New Benchmarks

To add a benchmark for a new model:

1. Create `test_<platform>_<model>.py` based on existing templates
2. Implement test cases with `TestMetrics` tracking
3. Add `export_results_json()` function
4. Create `run_benchmark_suite_<platform>.py` wrapper
5. Update this README

## See Also

- [Ollama Docker Setup](../../docker/ollama/README.md)
- [Monitoring Guide](../../monitoring/README.md) (if exists)
- Root [README](../../README.md)
