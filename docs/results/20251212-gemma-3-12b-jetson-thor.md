# Benchmark Results: Gemma 3 (12B) on NVIDIA Jetson Thor

**Date:** December 12, 2025
**Model:** `google/gemma-3-12b-it`
**Platform:** NVIDIA Jetson Thor (Blackwell sm_110)

## Summary

| Metric | Value |
| :--- | :--- |
| **Mean Throughput** | 4.9 tok/s |
| **Std Dev** | 1.5 tok/s |
| **Min Throughput** | 4.1 tok/s |
| **Max Throughput** | 7.6 tok/s |
| **Total Runs** | 5 (after 5 warmup runs) |

## Test Breakdown (Model-Specific)

| Test Case | Mean Speed (tok/s) | Min (tok/s) | Max (tok/s) |
| :--- | :--- | :--- | :--- |
| **Vision - Real World Photo** | 4.5 | 4.1 | 5.4 |
| **Multi-turn Conversation** | 5.3 | 4.0 | 9.9 |

## Comparison Benchmarks

### Vision Comparison (Apples-to-Apples)

Standardized vision prompts for comparing against other multimodal models (e.g., Molmo 7B).

| Test Case | Speed (tok/s) | Tokens | Duration (s) |
| :--- | :--- | :--- | :--- |
| **Chart Analysis** | 4.3 | 195 | 45.30 |
| **Color Identification** | 4.2 | 75 | 17.73 |
| **Visual Counting** | 4.3 | 110 | 25.56 |
| **Overall** | **4.3** | **380** | **88.60** |

### Text Comparison (Apples-to-Apples)

Standardized text prompts for comparing against text-only models (e.g., OLMo 3).

| Test Case | Speed (tok/s) | Tokens | Duration (s) |
| :--- | :--- | :--- | :--- |
| **Code Generation** | 4.4 | 500 | 114.12 |
| **Logical Reasoning** | 4.3 | 500 | 115.54 |
| **Text Summarization** | 4.4 | 75 | 17.23 |
| **Creative Writing** | 4.3 | 289 | 67.20 |
| **Structured JSON** | 4.3 | 76 | 17.52 |
| **Overall** | **4.3** | **1440** | **331.61** |

## Notes

- **Performance**: Gemma 3 (12B) is significantly slower (~4.3 tok/s) than Molmo 7B (~7.3 tok/s) on this hardware, which is expected given the larger parameter count (12B vs 7B).
- **Stability**: Performance is very consistent across all tasks, with a slight jump in the final benchmark run (7.6 tok/s), suggesting potential for further optimization or longer warm-up periods.
- **Hardware**: Running on NVIDIA Jetson Thor (Blackwell architecture).

## Raw Data

```json
{
  "overall": {
    "mean_throughput": 4.9,
    "std_throughput": 1.5,
    "min_throughput": 4.1,
    "max_throughput": 7.6
  }
}
```
