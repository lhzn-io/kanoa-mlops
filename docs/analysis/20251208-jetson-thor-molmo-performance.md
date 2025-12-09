# Jetson Thor Performance Analysis

**Date**: December 8, 2025
**Device**: NVIDIA Jetson Thor (Blackwell sm_110)
**Model**: Molmo-7B-D-0924 (Vision-Language Model)

## Executive Summary

We successfully deployed and benchmarked the Molmo-7B vision-language model on the NVIDIA Jetson Thor platform using vLLM, comparing it against a desktop RTX 5080 (eGPU). This represents the first successful local inference of a modern VLM on the Blackwell architecture within the `kanoa` ecosystem.

**Key Metrics:**
- **Throughput (Steady State)**: ~14.0 tokens/second (Thor) vs ~103.8 tokens/second (RTX 5080)
- **Throughput (Cold Start)**: ~7.6 tokens/second (Thor)
- **Latency**: First token latency is negligible for interactive use on both platforms.
- **Stability**: 100% success rate across benchmark suite.

## Benchmark Results

Tests were conducted using `kanoa-mlops` integration suite with 10 iterations per platform.

### Comparative Performance

| Metric | RTX 5080 (eGPU) | Jetson Thor (Edge) | Difference |
| :--- | :--- | :--- | :--- |
| **Mean Throughput** | **103.8 tok/s** | 11.1 tok/s | ~9.3x |
| **Max Throughput** | **108.3 tok/s** | 14.0 tok/s | ~7.7x |
| **Consistency (Std Dev)** | 5.0 | 3.1 | - |

### Jetson Thor Detailed Breakdown

| Test Case | Mean Speed (tok/s) | Max Speed (tok/s) | Description |
|-----------|-------------------|-------------------|-------------|
| **Boardwalk Photo** | 10.7 | 13.9 | Dense captioning of a nature scene |
| **Complex Plot** | 11.3 | 14.2 | Multi-panel matplotlib chart analysis |
| **Data Interpretation** | 11.3 | 14.2 | Reading values from a line chart |

### Configuration

- **Container**: `ghcr.io/nvidia-ai-iot/vllm:latest-jetson-thor`
- **Quantization**: FP8 KV Cache
- **Tensor Parallelism**: 1
- **Framework**: vLLM 0.6.3.post1 (Custom Build)

## Observations

1. **The "Thor Warm-up" Phenomenon**: The Jetson Thor exhibits a distinct warm-up phase. Runs 1-4 averaged ~7.6 tok/s, while runs 6-10 stabilized at ~13.9 tok/s. This suggests JIT compilation or clock boosting plays a significant role in initial performance.
2. **Edge Viability**: While the RTX 5080 is ~7.5x faster, the Thor's steady-state performance of **14 tok/s** is comfortably above the threshold for real-time conversational interfaces (faster than human reading speed).
3. **Stability**: The initial deployment faced issues with missing `tensorflow` dependencies required by the Molmo HF processor. This was resolved by extending the base image.
4. **Architecture**: The `sm_110` architecture requires specific vLLM builds. Standard x86/CUDA images are not compatible.

## Next Steps

- Evaluate **Gemma 3** performance on Thor.
- Optimize **KV Cache** settings for higher concurrency.
- Investigate **TensorRT-LLM** backend for potential speedups.
