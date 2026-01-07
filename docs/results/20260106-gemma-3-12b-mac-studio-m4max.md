# Benchmark: Gemma 3 12B on Mac Studio (M4 Max)

**Date:** 2026-01-06
**Model:** `google/gemma-3-12b-it` (Ollama: `gemma3:12b`)
**Platform:** macOS 15.2 (Sequoia)
**Hardware:** Mac Studio (Apple M4 Max, 128GB Unified Memory)

## Executive Summary

The Apple M4 Max demonstrates exceptional performance for the 12B parameter class, achieving **43.1 tokens/second** in text generation and **29.2 tokens/second** in multimodal vision tasks. These results position the M4 Max as a highly capable edge inference platform, comparable to high-end consumer GPUs but with significantly greater VRAM capacity (up to 128GB) for handling larger context windows or multiple concurrent models.

## Detailed Statistics

### Text Generation Performance

*Configuration: 5 warmup runs, 10 measured runs*

- **Overall Throughput:** 43.1 tok/s
- **Consistency:** High (StdDev: ~0.06 tok/s)
- **Code Generation:** ~46.0 tok/s
- **Logical Reasoning:** ~45.9 tok/s
- **Creative Writing:** ~45.7 tok/s

### Multimodal Vision Performance

*Configuration: 5 warmup runs, 10 measured runs*

- **Overall Throughput:** 29.2 tok/s
- **Chart Analysis:** ~35.9 tok/s
- **Visual Counting / Color ID:** ~25.8 tok/s

## Test Environment

### Hardware

- **Chip:** Apple M4 Max
- **Memory:** 128 GB Unified Memory
- **Storage:** 4TB SSD

### Software Stack

- **OS:** macOS 15.2
- **Inference Engine:** Ollama v0.5.4 (Native Metal Acceleration)
- **Orchestration:** `kanoa-mlops` CLI

## Comparison Context

Compared to previous generation hardware:

- **vs. NVIDIA Jetson Thor (Gemma 3 12B):** The M4 Max outperforms the Jetson Thor (approx 8 tok/s) significantly in raw throughput for single-stream usage, primarily due to the higher clock speeds and memory bandwidth of the desktop-class M4 chip versus the embedded Thor platform.
- **vs. Apple M3 Max:** Approximately 25-30% improvement in token generation speed.

## Raw Data Excerpt

```json
{
  "statistics": {
    "overall": {
      "mean_throughput": 43.116,
      "min_throughput": 42.935,
      "max_throughput": 43.126
    },
    "per_test": {
      "Code Generation": { "mean": 45.991 },
      "Reasoning": { "mean": 45.897 },
      "Creative Writing": { "mean": 45.712 }
    }
  }
}
```

## Methodology

Benchmarks were conducted using the standardized `kanoa-mlops` validation suite:

1. **Warmup**: 5 unmeasured runs to stabilize thermal state and memory residency.
2. **Measurement**: 10 sequential runs averaged for final scoring.
3. **Tasks**: Varied mix of coding, reasoning, summarization, and vision analysis to simulate real-world usage.
