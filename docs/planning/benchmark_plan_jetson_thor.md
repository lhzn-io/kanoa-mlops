
# Benchmark Plan: Jetson Thor Model Evaluation

**Date**: December 8, 2025
**Status**: Planned
**Hardware**: NVIDIA Jetson Thor (128GB Unified Memory)

## 1. Objective

To evaluate the performance and feasibility of running frontier-class open models on the Jetson Thor platform. The goal is to determine the optimal model selection for various `kanoa` workloads (coding, general chat, vision, monitoring) and assess the viability of concurrent execution.

**Primary Focus**:
Unlike server deployments, our priority is **low-latency, single-user experience**. We prioritize **Time to First Token (TTFT)** and **Inter-Token Latency (ITL)** over total batch throughput.

**Candidate Models & Roles:**

1.  **Llama 4 Maverick 17B** (BF16): Candidate for *General Interaction & Multimodal*
2.  **Olmo 3 32B Think** (BF16): Candidate for *Deep Reasoning & Coding*
3.  **Molmo 72B** (4-bit/8-bit): Candidate for *Scientific Vision*
4.  **Ministral 3 14B** (BF16): Candidate for *Background Monitoring*
## 2. Test Matrix

### Scenario A: Baseline Performance (Single Model)

Measure the raw performance of each model running in isolation to establish a baseline.

| Model | Precision | Context | Target Metric |
| :--- | :--- | :--- | :--- |
| **Llama 4 Maverick** | BF16 | 4k / 32k / 128k | > 50 tok/s |
| **Olmo 3 Think** | BF16 | 8k / 32k | > 30 tok/s |
| **Molmo 72B** | 4-bit (AWQ) | 4k (Image + Text) | > 15 tok/s |
| **Ministral 3** | BF16 | 4k | > 80 tok/s |

### Scenario B: Concurrent Execution (Multi-Model)

Verify the Thor's ability to run multiple models simultaneously without OOM or severe degradation.

* **Test B1**: **Llama 4 Maverick** (Foreground) + **Ministral 3** (Background)
  * *Goal*: Ensure Ministral can process a dummy stream while Llama 4 handles chat.
* **Test B2**: **Llama 4 Maverick** + **Vector DB** (pgvector)
  * *Goal*: Verify memory headroom for RAG operations.

### Scenario C: Model Loading Latency

Measure the time required to swap models into memory to determine if dynamic switching is a viable strategy.

*   **Test C1**: Unload **Llama 4** -> Load **Olmo 3**
  * *Target*: < 5 seconds (leveraging NVMe SSD speed).
* **Test C2**: Unload **Llama 4** -> Load **Molmo 72B**
  * *Target*: < 10 seconds.

### Scenario D: Serving Engine Bake-off (vLLM vs Ollama)

Compare the two leading local inference engines to determine the best fit for the Jetson architecture.

*   **Hypothesis**: `vllm` may offer better raw performance via optimized kernels, while `ollama` may offer lower VRAM overhead and easier management.
*   **Test D1**: **Llama 4 Maverick 17B** on vLLM vs Ollama.
    *   *Metric*: TTFT, ITL, VRAM Overhead.
*   **Test D2**: **Quantization Support**.
    *   *Check*: Does Ollama support the specific FP4/AWQ formats required for Thor?

## 3. Methodology

### Tools

1. **Inference Engines**:
   * `vllm`: Production-grade serving, PagedAttention, optimized for NVIDIA.
   * `ollama`: Developer-friendly, `llama.cpp` backend, potential for lower overhead.
2. **Monitoring**: `tegrastats` (for power/thermal/VRAM), `nvtop`.
3. **Benchmarking**: `vllm/benchmarks/benchmark_latency.py` and `ollama` timing output.

### Metrics

* **TTFT (Time To First Token)**: **Primary Metric**. The "snappiness" of the chat UI.
* **ITL (Inter-Token Latency)**: **Primary Metric**. Reading speed (target > 50 tok/s).
* **Throughput**: *Secondary*. Only relevant for background batch tasks.
* **VRAM Peak**: Maximum memory usage during heavy context.
* **Power Draw**: Average Watts during inference (TDP target < 100W).

## 4. Execution Plan

1. **Environment Setup**:
   * Flash Jetson Thor with JetPack 7.0 (Blackwell support).
   * Install `vllm` optimized for Jetson.
2. **Model Preparation**:
   * Download BF16 weights for Llama 4, Olmo 3, Ministral 3.
   * Quantize Molmo 72B to 4-bit AWQ using `AutoAWQ`.
3. **Run Benchmarks**:
   * Execute Scenario A scripts.
   * Execute Scenario B scripts.
   * Execute Scenario C scripts.
4. **Reporting**:
   * Update `benchmark_results.json`.
   * Publish "Jetson Thor Performance Report".
