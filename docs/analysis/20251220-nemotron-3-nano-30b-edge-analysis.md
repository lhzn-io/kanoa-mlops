# Nemotron 3 Nano 30B Edge Analysis

**Quick Take:** Best open-source model for edge devices like Jetson Thor according to NVIDIA Jetson AI Lab Research Group community feedback (Dec 2025).

## Overview

NVIDIA Nemotron-3-Nano-30B-A3B is a hybrid MoE (Mixture-of-Experts) language model optimized for edge deployment. It achieves near-32B model performance while using only ~10% of parameters per token, making it exceptionally efficient for resource-constrained environments.

**Model ID:** `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16`

## Architecture

### Hybrid Design
- **Total Parameters:** 31.6B
- **Active Parameters per Token:** 3B (~10% activation)
- **Layer Composition:**
  - 23 Mamba-2 + MoE layers
  - 6 Attention layers
- **MoE Configuration:**
  - 128 experts + 1 shared expert per layer
  - 6 experts activated per token

### Context Window
- **1M tokens** - particularly valuable for:
  - Long transcript analysis
  - Multi-sensor data fusion
  - Extended monitoring sessions

## Performance Characteristics

### Throughput
- **3.3x faster** than Qwen3-30B on identical hardware (single H200)
- **2.2x faster** than GPT-OSS-20B
- Benchmark config: 8K input / 16K output on H200

### Memory Requirements
- **BF16:** Runs on GPUs with 24GB VRAM (e.g., RTX 4090)
- **FP8:** Lower memory footprint with ~99% accuracy retention
- **Jetson Thor (128GB):** Comfortable headroom for model + multi-sensor data

### Quantization Options
| Format | Accuracy vs BF16 | Use Case |
|--------|------------------|----------|
| BF16 | 100% (baseline) | Maximum accuracy |
| FP8 | ~99% | Production edge deployment |
| GGUF | Varies by quant | Ultra-low memory scenarios |

**FP8 Strategy:** Selective quantization keeps attention layers and critical Mamba layers in BF16, while quantizing MoE layers and KV cache to FP8.

## Edge Deployment Scenarios

### Low-Power Edge (AGX Orin / Thor)
**Advantages:**
- Sparse activation (3B active vs 30B total) = lower power draw
- Fits power constraints better than dense 27B/32B models
- 1M context handles extended monitoring sessions

**Recommended Config:**
- FP8 quantization for power efficiency
- Priority: Real-time inference with minimal latency

### Multi-Node Cluster (2-4x Thor SoCs)
**Power Budget:** 400-800W

**Advantages:**
- Can run multiple Nemotron instances for specialized tasks
- 3.3x throughput advantage enables real-time multi-modal processing
- Distributed inference across Thor nodes

**Recommended Config:**
- BF16 for maximum accuracy (power less constrained)
- Task-specialized instances

### Distributed Edge + Aggregation
**Deployment:** Edge devices with central aggregation

**Edge Side (Power Constrained):**
- FP8 quantization
- Lightweight real-time processing
- Offload heavy reasoning to aggregation point

**Aggregation Side:**
- BF16 for deep analysis
- Process aggregated data from multiple edge nodes
- 1M context for pattern recognition across deployment

## Comparison to Common Edge Models

| Model | Total Params | Active Params | Context | Multi-Modal | Notes |
|-------|--------------|---------------|---------|-------------|-------|
| **Gemma 3 (12B)** | 12B | 12B (dense) | 128K | No | Baseline efficiency |
| **Gemma 3 (27B)** | 27B | 27B (dense) | 128K | No | Higher capability, dense |
| **Molmo 7B** | 7B | 7B | N/A | Yes | Vision + language |
| **OLMo 3 (32B)** | 32B | 32B (dense) | 128K | No | Max capability, dense |
| **Nemotron-3-Nano-30B** | 31.6B | 3B (sparse) | **1M** | No | Best efficiency/capability ratio |

**Key Insight:** Nemotron-3-Nano offers near-32B reasoning capability with ~12B-level resource usage due to sparse activation.

## Language Support

- English
- German
- Spanish
- French
- Italian
- Japanese

## Training Data Cutoff

**June 25, 2025** - Current as of deployment date.

## Integration Recommendations

### Priority 1: Add to kanoa-mlops Model Registry
Create vLLM configuration for easy deployment alongside existing models.

### Priority 2: Benchmark Against Current Stack
- Compare FP8 Nemotron vs BF16 Gemma 3 (27B) on domain-specific tasks
- Evaluate throughput vs accuracy tradeoffs
- Profile power consumption

### Priority 3: Test Multi-Instance Deployment
- Evaluate running 2x FP8 Nemotron instances vs 1x dense 32B model
- Hypothesis: Better task specialization with comparable total compute

## Potential Limitations

### 1. No Native Multi-Modal Support
- Would need separate vision model (e.g., Molmo) for camera integration
- Consider pipeline: Vision model → Nemotron (reasoning)

### 2. Hardware Validation Needed
- Community feedback positive but lacks public Thor benchmarks
- Recommend platform-specific profiling before production deployment

### 3. vLLM Version Requirements
**Confirmed:** vLLM officially supports Nemotron 3 Nano as of December 15, 2025
- Mamba-2 + MoE hybrid architecture fully supported
- Minimum version: Unknown (support announced Dec 2025, likely ≥0.6.x)
- Recommended: vLLM 0.13.0+ for latest MoE optimizations
- See "Testing Requirements" section below for details

## Testing Requirements

### vLLM Version Compatibility

**Official Support:** Announced December 15, 2025 on vLLM blog

**Minimum Requirements:**
- vLLM version with Mamba-2 + MoE hybrid support (likely ≥0.6.x based on kanoa-mlops baseline)
- `--trust-remote-code` flag required for model loading
- `--mamba_ssm_cache_dtype float32` flag recommended for accurate quality

**Recommended for Testing:**
- **x86/Development:** vLLM 0.13.0+ (latest MoE optimizations, December 2025 release)
- **Jetson Thor/Production:** `ghcr.io/nvidia-ai-iot/vllm:latest-jetson-thor` (NVIDIA's monthly-updated image)

### Two-Track Testing Strategy

#### Track 1: x86 Development Environment
**Purpose:** Validate model compatibility and benchmark performance before Thor deployment

**Setup:**
```bash
# Update kanoa-mlops
pip install vllm>=0.13.0

# Serve Nemotron 3 Nano
vllm serve nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16 \
  --trust-remote-code \
  --mamba_ssm_cache_dtype float32
```

**Tests:**
- [ ] Model loads successfully with BF16
- [ ] Model loads with FP8 quantization
- [ ] Inference throughput benchmarking (8K input / 16K output)
- [ ] Accuracy validation on test prompts
- [ ] Memory usage profiling

#### Track 2: Jetson Thor Production Environment
**Purpose:** Validate edge deployment and measure actual power/performance

**Setup:**
```bash
# Use NVIDIA's official Jetson vLLM image
docker pull ghcr.io/nvidia-ai-iot/vllm:latest-jetson-thor

# Serve via kanoa-mlops docker-compose
kanoa mlops serve vllm nemotron3-nano
```

**Tests:**
- [ ] Model loads on Thor hardware
- [ ] FP8 quantization performance vs BF16
- [ ] Power consumption measurement (target: <400W for single instance)
- [ ] Thermal profiling under sustained load
- [ ] Throughput comparison vs Gemma 3 (27B) and OLMo 3 (32B)

### Known Configuration Requirements

**Required Flags:**
- `--trust-remote-code` - Enable custom model code execution
- `--mamba_ssm_cache_dtype float32` - Ensure accurate quality for Mamba-2 layers

**Optional Flags for Testing:**
- `--dtype bfloat16` - Force BF16 precision
- `--quantization fp8` - Enable FP8 quantization (vLLM 0.13.0+)
- `--max-model-len 1048576` - Specify 1M context window (may require adjustment based on VRAM)

### Jetson-Specific Considerations

**NVIDIA Jetson vLLM Container:**
- Updated monthly with Jetson-specific optimizations
- Includes NVFP4 support (Blackwell-specific 4-bit format)
- May lag behind upstream vLLM releases but includes Thor-optimized kernels
- As of Dec 2025: Delivers 3.5x performance improvement vs launch (Aug 2025)

**When to Use Each:**
- **Upstream vLLM 0.13.0:** Development, testing, x86 benchmarking
- **NVIDIA Jetson Image:** Production Thor deployment, power-optimized inference

### Version Migration Notes (vLLM 0.13.0)

If upgrading from kanoa-mlops baseline (vllm>=0.6.3) to 0.13.0:

**Breaking Changes:**
- Attention backend configuration: environment variables → CLI arguments
- PassConfig flag renames (if using custom compilation)
- Deprecated `-O.xx` flag removed

**New Features Relevant to Nemotron:**
- MoE LoRA loading optimization
- Fused blockwise quantization improvements
- Latent MoE architecture support
- Blackwell GPU optimizations (including Thor)

## Action Items

### Phase 1: x86 Development Testing
- [ ] Upgrade kanoa-mlops to vLLM 0.13.0
- [ ] Create docker-compose.nemotron3-nano.yml for x86
- [ ] Test model loading with BF16 and FP8
- [ ] Benchmark inference throughput
- [ ] Validate accuracy on representative tasks

### Phase 2: Jetson Thor Deployment
- [ ] Pull latest `ghcr.io/nvidia-ai-iot/vllm:latest-jetson-thor`
- [ ] Create Thor-specific docker-compose configuration
- [ ] Profile memory usage during multi-task inference
- [ ] Measure power consumption (target: <400W)
- [ ] Compare against Gemma 3 (27B) and OLMo 3 (32B)

### Phase 3: Production Validation
- [ ] Thermal profiling under sustained load
- [ ] Multi-instance testing (2x FP8 vs 1x BF16)
- [ ] Integration with chatty-buoy sensor pipeline
- [ ] Document production deployment guide

## References

### Model Documentation
- [Nemotron 3 Nano Technical Report (PDF)](https://research.nvidia.com/labs/nemotron/files/NVIDIA-Nemotron-3-Nano-Technical-Report.pdf)
- [Hugging Face Model Card (BF16)](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16)
- [Hugging Face Model Card (FP8)](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8)
- [NVIDIA Research Page](https://research.nvidia.com/labs/nemotron/Nemotron-3/)

### vLLM Support
- [vLLM Blog: Run NVIDIA Nemotron 3 Nano (Dec 15, 2025)](https://blog.vllm.ai/2025/12/15/run-nvidia-nemotron-3-nano.html)
- [vLLM v0.13.0 Release Notes](https://github.com/vllm-project/vllm/releases/tag/v0.13.0)
- [vLLM Blog: Now Serving NVIDIA Nemotron (Oct 23, 2025)](https://blog.vllm.ai/2025/10/23/now_serving_nvidia_nemotron_with_vllm.html)

### Jetson Thor Platform
- [Jetson Thor Performance Blog](https://developer.nvidia.com/blog/unlock-faster-smarter-edge-models-with-7x-gen-ai-performance-on-nvidia-jetson-agx-thor/)
- [NVIDIA Jetson vLLM Container Announcement (3.5x Performance Boost)](https://forums.developer.nvidia.com/t/announcing-new-vllm-container-3-5x-increase-in-gen-ai-performance-in-just-5-weeks-of-jetson-agx-thor-launch/346634)
- [vLLM Release 25.09 - NVIDIA Docs](https://docs.nvidia.com/deeplearning/frameworks/vllm-release-notes/rel-25-09.html)

### Analysis
- [Technical Review on Medium](https://medium.com/@leucopsis/a-technical-review-of-nvidias-nemotron-3-nano-30b-a3b-e91673f22df4)

---

**Source:** NVIDIA Jetson AI Lab Research Group Discord recommendation (Dec 19, 2025)
**Analysis Date:** December 20, 2025
