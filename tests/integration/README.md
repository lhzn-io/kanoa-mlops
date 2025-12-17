# Benchmarking Suite

Performance benchmarking tools for local LLM inference servers (vLLM, Ollama).

## Overview

Two types of benchmarks:

1. **Model-Specific Benchmarks**: Test unique capabilities of each model (vision, reasoning, code generation)
2. **Comparison Benchmarks**: Standardized tests with identical prompts for apples-to-apples comparisons

## Quick Start

```bash
cd tests/integration

# 1. Start your inference server (e.g., via kanoa)
kanoa mlops serve vllm olmo3

# 2. Run a single test
python3 test_vllm_olmo3_specific.py

# 3. Run statistical benchmark (multiple iterations)
python3 run_benchmark_suite.py --model olmo3 --runs 5
```

## Model-Specific Benchmarks

These tests showcase each model's unique capabilities not covered by comparison benchmarks.

### Gemma 3 (12B)

**Unique Capabilities**: Real-world vision understanding, multi-turn conversation memory

```bash
# Single run (2 unique tests)
python3 test_vllm_gemma3_specific.py

# Statistical benchmark
python3 run_benchmark_suite.py --model gemma3 --runs 5
```

**Tests**: Real-world photo description (boardwalk), multi-turn conversation memory

### Molmo (7B)

**Unique Capabilities**: Vision-specialized with complex plot interpretation

```bash
# Single run (3 vision-focused tests)
python3 test_vllm_molmo_specific.py

# Statistical benchmark
python3 run_benchmark_suite.py --model molmo --runs 5
```

**Tests**: Real-world photo (boardwalk), complex matplotlib plots, data visualization analysis

### OLMo 3 (7B Instruct)

**Unique Capabilities**: System prompt handling, code generation specialization

```bash
# Single run (5 code/reasoning tests)
python3 test_vllm_olmo3_specific.py

# Statistical benchmark
python3 run_benchmark_suite.py --model olmo3 --runs 5
```

**Tests**: Python/SQL code generation (with system prompts), multi-step reasoning, scientific structured output, algorithm design

### Ollama (Gemma 3 4B)

**Capabilities**: Lightweight text model

```bash
# Single run
python3 test_ollama_gemma3.py

# Statistical benchmark
python3 run_benchmark_suite.py --model ollama --runs 3
```

**Tests**: Basic chat with automatic model pull

## Comparison Benchmarks

Standardized tests for fair model comparisons using **identical prompts and inputs**.

### Text Comparison

Compare text-only capabilities across models (Gemma 3, OLMo 3).

**Tests**:

- Code generation (Python with type hints)
- Logical reasoning (logic puzzle)
- Text summarization
- Creative writing
- Structured JSON output

**Usage**:

```bash
# Single run - Gemma 3
MODEL_NAME=gemma-3-12b python3 test_vllm_text_comparison.py

# Single run - OLMo 3
MODEL_NAME=allenai/Olmo-3-7B-Instruct python3 test_vllm_text_comparison.py

# Statistical benchmark - Gemma 3
MODEL_NAME=gemma-3-12b python3 run_benchmark_suite.py --model text-comparison --runs 5

# Statistical benchmark - OLMo 3
MODEL_NAME=allenai/Olmo-3-7B-Instruct python3 run_benchmark_suite.py --model text-comparison --runs 5
```

**Comparing Results**:

```bash
# Run both models
MODEL_NAME=gemma-3-12b python3 run_benchmark_suite.py --model text-comparison --runs 5 --output benchmark_statistics_text_gemma3.json
MODEL_NAME=allenai/Olmo-3-7B-Instruct python3 run_benchmark_suite.py --model text-comparison --runs 5 --output benchmark_statistics_text_olmo3.json

# Compare the JSON outputs side by side
```

### Vision Comparison

Compare vision capabilities across models (Gemma 3, Molmo).

**Tests**:

- Chart analysis (synthetic bar chart)
- Color identification (3x3 color grid)
- Visual counting

**Usage**:

```bash
# Single run - Gemma 3
MODEL_NAME=gemma-3-12b python3 test_vllm_vision_comparison.py

# Single run - Molmo
MODEL_NAME=allenai/Molmo-7B-D-0924 python3 test_vllm_vision_comparison.py

# Statistical benchmark - Gemma 3
MODEL_NAME=gemma-3-12b python3 run_benchmark_suite.py --model vision-comparison --runs 5

# Statistical benchmark - Molmo
MODEL_NAME=allenai/Molmo-7B-D-0924 python3 run_benchmark_suite.py --model vision-comparison --runs 5
```

## Benchmark Suite Options

The unified `run_benchmark_suite.py` supports all benchmark types:

```bash
python3 run_benchmark_suite.py --model <MODEL> [OPTIONS]
```

**Models**:

- `gemma3` - Model-specific Gemma 3 tests
- `molmo` - Model-specific Molmo tests
- `olmo3` - Model-specific OLMo 3 tests
- `ollama` - Model-specific Ollama tests
- `text-comparison` - Standardized text tests (requires `MODEL_NAME` env var)
- `vision-comparison` - Standardized vision tests (requires `MODEL_NAME` env var)

**Options**:

- `--runs N` - Number of iterations (default: 3)
- `--test-script FILE` - Override test script
- `--results-file FILE` - Override input results file
- `--output FILE` - Override output statistics file

**Examples**:

```bash
# Run 10 iterations for OLMo 3
python3 run_benchmark_suite.py --model olmo3 --runs 10

# Custom output filename
python3 run_benchmark_suite.py --model gemma3 --runs 5 --output my_gemma3_results.json

# Text comparison with custom runs
MODEL_NAME=gemma-3-12b python3 run_benchmark_suite.py --model text-comparison --runs 10
```

## Output Files

All benchmark results are **gitignored** (generated artifacts):

### Single Run Output

- `benchmark_results.json` - Most model-specific tests
- `benchmark_results_ollama.json` - Ollama tests

**Format**:

```json
{
  "timestamp": "2025-12-11T19:00:00",
  "model": "allenai/Olmo-3-7B-Instruct",
  "test_type": "text_comparison",  // For comparison tests only
  "platform": { "system": "Linux", "gpu": "..." },
  "summary": {
    "total_tokens": 1234,
    "total_duration_s": 45.6,
    "avg_tokens_per_second": 27.1
  },
  "tests": [
    {
      "test_name": "Code Generation - Python",
      "duration_s": 12.3,
      "tokens_generated": 456,
      "tokens_per_second": 37.1,
      "prompt_tokens": 89
    }
  ]
}
```

### Multi-Run Statistics Output

- `benchmark_statistics_{model}.json` - Aggregated statistics

**Format**:

```json
{
  "num_runs": 5,
  "timestamp": "2025-12-11T19:30:00",
  "model": "allenai/Olmo-3-7B-Instruct",
  "platform": { "system": "Linux", "gpu": "..." },
  "statistics": {
    "overall": {
      "mean_throughput": 27.3,
      "std_throughput": 1.2,
      "min_throughput": 25.8,
      "max_throughput": 29.1
    },
    "per_test": {
      "Code Generation - Python": {
        "mean": 35.2,
        "std": 2.1,
        "min": 32.5,
        "max": 37.8
      }
    }
  },
  "raw_results": [ /* all individual run results */ ]
}
```

## Interpreting Results

### Throughput (tokens/sec)

- **First run**: Often 10-20% slower due to model loading and JIT compilation
- **Subsequent runs**: More representative of steady-state performance
- **Variance**: High variance (>10% std dev) may indicate:
  - Thermal throttling
  - System load from other processes
  - Cache misses

### Comparing Models

When comparing models using the standardized benchmarks:

1. **Run equal iterations**: Use same `--runs` value for fair comparison
2. **Note model size**: Larger models typically have lower throughput but better quality
3. **Check per-test results**: Some models excel at specific tasks (code vs creative writing)
4. **Consider use case**: Text-only models may be faster for non-vision tasks

### Typical Performance (Jetson Thor, 128GB Unified Memory)

| Model | Size | Text Throughput | Vision Throughput | Notes |
|-------|------|-----------------|-------------------|-------|
| Gemma 3 | 12B | ~25-35 tok/s | ~20-30 tok/s | Multimodal, lower throughput |
| OLMo 3 | 7B | ~40-50 tok/s | N/A | Text-only, optimized for code |
| Molmo | 7B | ~30-40 tok/s | ~25-35 tok/s | Vision-focused |
| Ollama Gemma 3 | 4B | ~55-65 tok/s | N/A | Lightweight, faster |

*Note: Actual performance varies based on prompt length, temperature, and system load.*

## Workflow Examples

### Example 1: Benchmark a New Model Deployment

```bash
# 1. Start the server
kanoa mlops serve vllm olmo3

# 2. Quick validation (tests unique OLMo3 capabilities)
python3 test_vllm_olmo3_specific.py

# 3. Statistical benchmark
python3 run_benchmark_suite.py --model olmo3 --runs 10

# 4. Check results
cat benchmark_statistics_olmo3.json
```

### Example 2: Compare Text Capabilities

```bash
# Benchmark Gemma 3 on text tasks
kanoa mlops serve vllm gemma3
MODEL_NAME=gemma-3-12b python3 run_benchmark_suite.py --model text-comparison --runs 5 --output stats_text_gemma3.json

# Switch to OLMo 3
kanoa mlops stop vllm gemma3
kanoa mlops serve vllm olmo3
MODEL_NAME=allenai/Olmo-3-7B-Instruct python3 run_benchmark_suite.py --model text-comparison --runs 5 --output stats_text_olmo3.json

# Compare
diff <(jq '.statistics.overall' stats_text_gemma3.json) <(jq '.statistics.overall' stats_text_olmo3.json)
```

### Example 3: Compare Vision Capabilities

```bash
# Benchmark Gemma 3 vision
kanoa mlops serve vllm gemma3
MODEL_NAME=gemma-3-12b python3 run_benchmark_suite.py --model vision-comparison --runs 5 --output stats_vision_gemma3.json

# Switch to Molmo
kanoa mlops stop vllm gemma3
kanoa mlops serve vllm molmo
MODEL_NAME=allenai/Molmo-7B-D-0924 python3 run_benchmark_suite.py --model vision-comparison --runs 5 --output stats_vision_molmo.json

# Molmo is vision-specialized, should outperform in these tests
```

## Troubleshooting

### "Connection refused"

**Cause**: Inference server not running or wrong port

**Fix**:

```bash
# Check if server is running
kanoa status

# Start server if needed
kanoa mlops serve vllm olmo3

# Verify port (should be 8000 for vLLM, 11434 for Ollama)
curl http://localhost:8000/health  # vLLM
curl http://localhost:11434/api/tags  # Ollama
```

### "Model not found" (Ollama)

**Cause**: Model not pulled yet

**Fix**: The test automatically pulls the model on first run. First run will be slower.

### Low throughput

**First run**: Normal - model loading, JIT compilation, cache warming

**Persistent low throughput**:

```bash
# Check GPU utilization
nvidia-smi

# Check thermal throttling (Jetson)
sudo tegrastats

# Check system load
top

# Free cache if needed
sync && echo 3 | sudo tee /proc/sys/vm/drop_caches
```

### High variance in results

**Causes**:

- Thermal throttling (check temps with `tegrastats`)
- Background processes (check with `top`)
- Different prompt lengths in tests
- First few runs still warming up

**Fix**:

```bash
# Increase number of runs to smooth out variance
python3 run_benchmark_suite.py --model olmo3 --runs 10

# Check for background processes
top
```

## Adding New Benchmarks

To add a benchmark for a new model:

1. **Create test file**: `test_vllm_<model>_specific.py`
   - Copy an existing specific test as template
   - Only include tests for **unique capabilities** not in comparison benchmarks
   - Implement test functions with `TestMetrics` tracking
   - Add `export_results_json()` that outputs to `benchmark_results.json`
   - Add clear docstring explaining what's unique about these tests

2. **Update benchmark suite**: Add model to `run_benchmark_suite.py` choices list

3. **Test it**:

   ```bash
   python3 test_vllm_<model>_specific.py
   python3 run_benchmark_suite.py --model <model> --runs 3
   ```

4. **Update this README**: Add model to the appropriate section

**Note**: For standard comparisons (code, reasoning, vision basics), use the comparison test files instead.

### Creating Comparison Tests

To add new standardized comparison tests:

1. Identify the capability to test (e.g., translation, math, etc.)
2. Create test file with identical prompts for all models
3. Use `MODEL_NAME` environment variable for model selection
4. Add to `run_benchmark_suite.py` choices
5. Document in this README

## See Also

- [kanoa-mlops Documentation](../../README.md)
- [Docker Setup](../../docker/)
- [Monitoring](../../monitoring/)
