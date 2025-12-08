# Jetson Thor Performance Analysis

**Date**: December 8, 2025
**Device**: NVIDIA Jetson Thor (Blackwell sm_110)
**Model**: Molmo-7B-D-0924 (Vision-Language Model)

## Executive Summary

We successfully deployed and benchmarked the Molmo-7B vision-language model on the NVIDIA Jetson Thor platform using vLLM. This represents the first successful local inference of a modern VLM on the Blackwell architecture within the `kanoa` ecosystem.

**Key Metrics:**
- **Throughput**: ~8.2 tokens/second (avg)
- **Latency**: First token latency is negligible for interactive use.
- **Stability**: 100% success rate across benchmark suite.

## Benchmark Results

Tests were conducted using `kanoa-mlops` integration suite with 3 iterations.

| Test Case | Mean Speed (tok/s) | Max Speed (tok/s) | Description |
|-----------|-------------------|-------------------|-------------|
| **Boardwalk Photo** | 7.7 | 7.7 | Dense captioning of a nature scene |
| **Complex Plot** | 8.1 | 8.8 | Multi-panel matplotlib chart analysis |
| **Data Interpretation** | 9.7 | 13.7 | Reading values from a line chart |

### Configuration

- **Container**: `ghcr.io/nvidia-ai-iot/vllm:latest-jetson-thor`
- **Quantization**: FP8 KV Cache
- **Tensor Parallelism**: 1
- **Framework**: vLLM 0.6.3.post1 (Custom Build)

## Observations

1. **Stability**: The initial deployment faced issues with missing `tensorflow` dependencies required by the Molmo HF processor. This was resolved by extending the base image.
2. **Performance**: The Jetson Thor demonstrates capable inference speeds for 7B parameter models, making it suitable for real-time edge AI applications.
3. **Architecture**: The `sm_110` architecture requires specific vLLM builds. Standard x86/CUDA images are not compatible.

## Next Steps

- Evaluate **Gemma 3** performance on Thor.
- Optimize **KV Cache** settings for higher concurrency.
- Investigate **TensorRT-LLM** backend for potential speedups.
