# Benchmark Results: Molmo 7B on NVIDIA Jetson Thor

**Date:** December 12, 2025
**Model:** `allenai/Molmo-7B-D-0924`
**Platform:** NVIDIA Jetson Thor (Blackwell sm_110)

## Summary

| Metric | Value |
| :--- | :--- |
| **Mean Throughput** | 9.3 tok/s |
| **Std Dev** | 3.2 tok/s |
| **Min Throughput** | 7.2 tok/s |
| **Max Throughput** | 14.9 tok/s |
| **Total Runs** | 10 (10 successful) |

## Test Breakdown (Model-Specific)

| Test Case | Mean Speed (tok/s) | Min (tok/s) | Max (tok/s) |
| :--- | :--- | :--- | :--- |
| **Boardwalk Photo** | 8.8 | 7.0 | 14.9 |
| **Complex Plot** | 9.6 | 7.1 | 15.7 |
| **Data Interpretation** | 9.5 | 7.1 | 15.4 |

## Comparison Benchmarks

### Vision Comparison (Apples-to-Apples)

Standardized vision prompts for comparing against other multimodal models (e.g., Gemma 3).

| Test Case | Speed (tok/s) | Tokens | Duration (s) |
| :--- | :--- | :--- | :--- |
| **Chart Analysis** | 6.9 | 93 | 13.42 |
| **Color Identification** | 7.0 | 70 | 9.98 |
| **Visual Counting** | 7.0 | 69 | 9.79 |
| **Overall** | **7.0** | **232** | **33.20** |

### Text Comparison (Apples-to-Apples)

Standardized text prompts for comparing against text-only models (e.g., OLMo 3).

| Test Case | Speed (tok/s) | Tokens | Duration (s) |
| :--- | :--- | :--- | :--- |
| **Code Generation** | 7.3 | 347 | 47.55 |
| **Logical Reasoning** | 7.2 | 123 | 17.02 |
| **Text Summarization** | 7.3 | 85 | 11.60 |
| **Creative Writing** | 7.2 | 240 | 33.32 |
| **Structured JSON** | 7.3 | 58 | 7.99 |
| **Overall** | **7.3** | **853** | **117.48** |

## Notes

- **Performance Jump**: Throughput significantly increased (doubled to ~14-15 tok/s) in the last 3 runs, likely due to vLLM internal caching or system warm-up.
- **Caching**: Implemented local image caching to resolve DNS issues with `upload.wikimedia.org`.
- **Hardware**: Running on NVIDIA Jetson Thor (Blackwell architecture).

## Raw Data

```json
{
  "overall": {
    "mean_throughput": 9.3,
    "std_throughput": 3.2,
    "min_throughput": 7.2,
    "max_throughput": 14.9
  }
}
```
