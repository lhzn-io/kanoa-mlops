# Benchmark Results: Gemma 3 4B on Mac Studio (M4 Max)

**Date:** 2026-01-06
**Contributor:** @lhzn
**Hardware:** Mac Studio (Mac16,9)

- **Chip:** Apple M4 Max
- **Memory:** 128 GB Unified Memory
- **OS:** macOS (Darwin arm64)

## Configuration

- **Model:** `gemma3:4b`
- **Runtime:** Native Ollama (v0.13.5)
- **Quantization:** Q4_K_M (Default)
- **Interface:** HTTP API (OpenAI-compatible)

## Performance Metrics

### Text Generation (15 Iterations)

*Profile: 5 Warmup + 10 Measurement Runs*

| Task Category | Mean Throughput (tok/s) | Min | Max | StdDev |
| :--- | :--- | :--- | :--- | :--- |
| **Overall Text** | **92.6** | **92.4** | **93.4** | **0.3** |
| Code Generation | 99.3 | 99.0 | 99.9 | 0.3 |
| Logical Reasoning | 98.7 | 98.0 | 100.0 | 0.6 |
| Creative Writing | 98.0 | 97.4 | 98.7 | 0.5 |
| Summarization | 85.2 | 84.4 | 85.9 | 0.4 |
| Structured JSON | 82.0 | 81.3 | 83.0 | 0.5 |

### Vision Capabilities (15 Iterations)

*Profile: 5 Warmup + 10 Measurement Runs*

| Task Category | Mean Throughput (tok/s) | Min | Max | StdDev |
| :--- | :--- | :--- | :--- | :--- |
| **Overall Vision** | **55.4** | **53.9** | **56.2** | **0.6** |
| Chart Analysis | 68.7 | 66.0 | 70.2 | 1.2 |
| Color ID | 53.3 | 48.8 | 54.7 | 1.6 |
| Visual Counting | 44.3 | 43.9 | 44.8 | 0.3 |

## Raw Benchmark Summary

```json
{
  "text_benchmark": {
    "runs": 10,
    "warmup": 5,
    "mean_throughput": 92.6,
    "std_dev": 0.3,
    "min_throughput": 92.4,
    "max_throughput": 93.4
  },
  "vision_benchmark": {
    "runs": 10,
    "warmup": 5,
    "mean_throughput": 55.4,
    "std_dev": 0.6
  }
}
```

## Observations

- **Performance**: The 4B model demonstrates exceptional speed on the M4 Max, achieving **~93 tok/s** for text generation. This is roughly **2.1x faster** than the 12B variant (~43 tok/s), scaling almost linearly with parameter count reduction.
- **Vision Efficiency**: Multi-modal queries run comfortably at **~55 tok/s**, making this model viable for real-time video frame analysis or responsive VQA applications.
- **Stability**: The spread between minimum and maximum throughput is negligible (< 1.5%), confirming that the native Ollama Metal backend handles the M4's unified memory bandwidth efficiently without throttling.
- **Task Variance**: Logic and Code tasks perform slightly better (~99 tok/s) than dense summarization (~85 tok/s), likely due to token prediction probabilities or KV cache dynamics for longer contexts.
- **Setup**: Native Ollama installation via Homebrew is seamless.
- **Compatibility**: Metal acceleration works out of the box.
- **Integration**: `kanoa-mlops` CLI correctly detects the native instance.
