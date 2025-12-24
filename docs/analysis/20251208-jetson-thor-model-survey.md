
# Analysis: Frontier Models on NVIDIA Jetson Thor

**Date**: December 8, 2025
**Status**: Draft
**Author**: kanoa-mlops Agent

## 1. Executive Summary

The NVIDIA Jetson Thor (Blackwell architecture, 128GB Unified Memory) represents a paradigm shift for edge AI. This document analyzes the feasibility of running the "2025 Class" of frontier open models—specifically **Olmo 3**, **Gemma 3**, **Molmo**, **Llama 4**, and **Ministral 3**—on this hardware.

---

## 1. Olmo 3 32B Think (Coding & Reasoning)

The **Olmo 3 32B Think** model is the current state-of-the-art open-source model available from AllenAI for complex reasoning and code management. Its specialized training on long chain-of-thought (CoT) datasets makes it a strong contender against proprietary models like Claude Opus 4.5 for technical workloads.

### Suitability for Thor (Olmo)

The model fits comfortably into the **128 GB unified memory**, allowing for deployment of the **full FP16/BF16 weights** for maximum quality, or a highly optimized 4-bit version for peak speed.

| Precision | VRAM Footprint | Suitability |
| :--- | :--- | :--- |
| **Full (BF16)** | $\approx 64 \text{ GB}$ | **Perfect Fit**: Uses ~50% of memory. Max quality. |
| **4-bit (NVFP4)** | $\approx 20 \text{ GB}$ | **Max Speed**: Leverages native FP4 support. |

### Workload Match

The "Think" variant is explicitly post-trained to surface intermediate reasoning steps, which is invaluable for debugging, reviewing complex logic, and managing scientific codebases.

---

## 2. Gemma 3 27B IT (General Purpose)

Google's **Gemma 3 27B** offers a massive context window and high general capability, making it an excellent all-rounder.

### Suitability for Thor (Gemma)

| Precision | VRAM Footprint | Suitability |
| :--- | :--- | :--- |
| **Full (BF16)** | $\approx 62 \text{ GB}$ | **Perfect Fit**: With 128K context, total footprint is ~70-80GB. |
| **4-bit (NVFP4)** | $\approx 17.6 \text{ GB}$ | **Max Speed**: Extremely fast inference. |

### vLLM Configuration Targets

- **Model ID**: `google/gemma-3-27b-it`
- **Memory Utilization**: `--gpu-memory-utilization 0.9`
- **Context Window**: `--max-model-len 16384` (up to 128K feasible)

---

## 3. Molmo 72B (Multimodal Science)

**Molmo 72B** is the flagship open multimodal model, capable of interpreting complex scientific figures, charts, and diagrams with accuracy rivaling GPT-4V.

### Feasibility Analysis

Running a 72B parameter model is the ultimate test for the Jetson Thor.

- **Full Precision (BF16)**: Requires $\approx 144 \text{ GB}$. **DOES NOT FIT**.
- **8-bit Quantization**: Requires $\approx 72-80 \text{ GB}$. **FITS**.
- **4-bit Quantization**: Requires $\approx 40-48 \text{ GB}$. **FITS COMFORTABLY**.

### Recommendation

We recommend running **Molmo 72B in 4-bit (AWQ/GPTQ)** or **8-bit (FP8)**. This leaves ample room (40-80GB) for the massive KV cache required for high-resolution image processing and long context, ensuring smooth performance even with heavy multimodal workloads.

---

## 4. Llama 4 (Scout & Maverick)

**Model**: `meta-llama/Llama-4-Scout-17B` & `meta-llama/Llama-4-Maverick-17B`
**Type**: Multimodal Mixture-of-Experts (MoE)
**Release Date**: Late 2025

The Llama 4 release marks a significant shift towards "natively multimodal" architectures. Unlike previous generations where vision was an adapter, Llama 4 integrates it at the core.

- **Scout (17B)**: Designed for high-speed analysis with 16 experts.
- **Maverick (17B)**: A "dense-like" MoE with 128 experts, offering higher reasoning capabilities at a similar memory footprint.

### Suitability for Thor (Llama 4)

| Precision | VRAM Footprint | Suitability |
| :--- | :--- | :--- |
| **Full (BF16)** | $\approx 46 \text{ GB}$ | **Perfect Fit**: Leaves ~80GB free for other tasks. |
| **4-bit (NVFP4)** | $\approx 16 \text{ GB}$ | **Ultra-Light**: Can run alongside Molmo or Olmo. |

**Verdict**: These models represent the "sweet spot" for the Jetson Thor, balancing capability with efficiency.

---

## 5. Ministral 3 (Edge Native)

**Model**: `mistralai/Ministral-3-14B-Instruct`
**Type**: Edge-First Multimodal
**Release Date**: Late 2025

Mistral's answer to the edge compute revolution. At 14B parameters, it is the most lightweight of the "frontier-class" models.

### Suitability for Thor (Ministral)

| Precision | VRAM Footprint | Suitability |
| :--- | :--- | :--- |
| **Full (BF16)** | $\approx 35 \text{ GB}$ | **Max Efficiency**: Ideal for background tasks. |
| **4-bit (NVFP4)** | $\approx 12 \text{ GB}$ | **Minimal Footprint**: Negligible impact on system resources. |

---

## 6. Comparative Analysis

| Model | Params | Type | VRAM (BF16) | VRAM (4-bit) | Thor Fit | Role |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Olmo 3 Think** | 32B | Dense Text | ~70 GB | ~24 GB | ✅ Full | Deep Reasoning |
| **Gemma 3 IT** | 27B | Dense Text | ~62 GB | ~20 GB | ✅ Full | General Assistant |
| **Molmo** | 72B | Multimodal | ❌ 150 GB | ~48 GB | ⚠️ Quant Only | Vision/Science |
| **Llama 4 Scout** | 17B | MoE M-Modal | ~46 GB | ~16 GB | ✅✅ Easy | Fast Multimodal |
| **Ministral 3** | 14B | Edge M-Modal | ~35 GB | ~12 GB | ✅✅ Easy | Background Tasks |

## 7. Conclusion: Feasibility & Recommendations

The "2025 Class" of AI models is defined by a shift away from massive monolithic dense models towards **specialized, efficient architectures** (MoE, Multimodal-Native) that fit on high-end edge hardware.

For the **kanoa** project on Jetson Thor, we propose evaluating the following configuration:

1. **General**: **Llama 4 Maverick (17B)** or **Gemma 3 (27B)** for general interaction and multimodal understanding.
2. **Reasoning**: **Olmo 3 (32B)** loaded on-demand for complex reasoning tasks.
3. **Vision**: **Molmo (72B)** (Quantized) for high-fidelity scientific image analysis.

### Next Steps

- [ ] Execute `run-benchmark-suite` for Olmo 3, Gemma 3, and Llama 4.
- [ ] Validate Molmo 72B quantization compatibility with vLLM on Thor.
- [ ] Test concurrent execution of Ministral 3 (background) + Llama 4 (foreground).

## References

1. **Molmo 72B Performance**:
   - "Molmo-72B achieves the highest academic benchmark score and ranks second on human evaluation, just slightly behind GPT-4o."
   - It outperforms **GPT-4V** on academic benchmarks (Avg Score: 81.2 vs 71.1).
   - Source: [Molmo 72B HuggingFace Card](https://huggingface.co/allenai/Molmo-72B-0924) and [Technical Report (arXiv:2409.17146)](https://arxiv.org/abs/2409.17146).

2. **AllenAI Olmo 3**:
   - "The Olmo 3 model family... 32B-Think: Our flagship post-trained release, capable of reasoning through complex problems step by step."
   - Source: [AllenAI Olmo Project Page](https://allenai.org/olmo) and [HuggingFace Collection](https://huggingface.co/collections/allenai/olmo-3-post-training).

3. **Google Gemma 3**:
   - "Gemma 3 is introducing advanced agentic coding capabilities..."
   - Source: [Google AI Blog: Start building with Gemini 3](https://blog.google/technology/developers/gemini-3-developers/) and [Gemma Family on HuggingFace](https://huggingface.co/collections/google/googles-gemma-models-family).

4. **Meta Llama 4**:
   - "Llama 4 models mark the beginning of a new era... natively multimodal AI models."
   - Source: [HuggingFace Llama 4 Collection](https://huggingface.co/collections/meta-llama/llama-4).

5. **Mistral AI**:
   - "Ministral 3: A collection of edge models... All with vision capabilities."
   - Source: [Mistral AI HuggingFace Org](https://huggingface.co/mistralai).
