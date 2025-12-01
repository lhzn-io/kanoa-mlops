# Local Inference Hardware Compatibility

Research findings on running vLLM and vision-language models locally.

**Date**: November 2025
**Status**: Findings archived

---

## Summary

| Platform | vLLM Support | Molmo/Gemma 3 | Recommendation |
|----------|--------------|---------------|----------------|
| **NVIDIA GPU** | ✅ Full | ✅ Full | Primary target |
| **Intel Arc GPU** | ❌ No | ⚠️ Partial (Ollama) | Not recommended for vLLM |
| **CPU-only** | ⚠️ Limited | ❌ Failed | Too slow, unstable |

---

## NVIDIA GPU (CUDA)

### Status: ✅ Fully Supported

vLLM is built primarily for NVIDIA GPUs with CUDA support.

**Requirements:**

- NVIDIA GPU with 16GB+ VRAM (24GB recommended for 7B+ models)
- CUDA 12.1+ drivers
- NVIDIA Container Toolkit for Docker

**Tested Configurations:**

- RTX 4090 (24GB): Excellent performance
- L4 (24GB, cloud): Good performance, cost-effective
- T4 (16GB, cloud): Works for 7B models with reduced context

**Recommendation:** Use NVIDIA GPU locally or via cloud (GCP, AWS, etc.)

---

## Intel Arc GPU (Xe)

### Status: ❌ Not Supported by vLLM

**Test Hardware:** Intel Arc 140V (16GB VRAM, Lunar Lake integrated)

### Findings

1. **vLLM**: No Intel GPU support
   - vLLM is CUDA-only (NVIDIA)
   - No XPU/oneAPI backend

2. **IPEX (Intel Extension for PyTorch)**:
   - Does NOT support Gemma 3 models
   - Supported models: Llama, Qwen, Phi, Mistral, DeepSeek
   - ⚠️ **Being retired** - EOL March 2026
   - Intel is upstreaming optimizations to native PyTorch

3. **Ollama**:
   - Has Gemma 3 (4B, 12B, 27B) - multimodal with vision
   - Intel Arc GPU support is **experimental**
   - May work for smaller models but not production-ready

### Available Gemma 3 Models in Ollama

| Model | Size | VRAM Needed | Context |
|-------|------|-------------|---------|
| gemma3:4b | 3.3GB | ~6GB | 128K |
| gemma3:12b | 8.1GB | ~12GB | 128K |
| gemma3:27b | 17GB | ~24GB | 128K |

### Potential Future Options

- **Ollama + Intel Arc**: Experimental, may improve over time
- **Native PyTorch XPU**: As IPEX features are upstreamed
- **IPEX-LLM**: Fork focused on Intel GPUs, but also sunsetting

**Recommendation:** Do not rely on Intel Arc for vLLM workloads. Use GCP/cloud GPUs instead.

---

## CPU-Only Inference

### Status: ❌ Not Viable for vLLM + Multimodal

**Test Configuration:**

- vLLM v0.6.3.post1
- Model: allenai/Molmo-7B-D-0924
- Device: CPU (Intel Lunar Lake)
- RAM: 16GB

### Results

```bash
docker run ... --device cpu ...
```

**Outcome:** ❌ Failed

- Model loading started but crashed during weight initialization
- vLLM's CPU backend doesn't properly support multimodal models with `trust-remote-code`
- Error: `RuntimeError: Engine process failed to start`

### Why CPU Fails

1. **Memory**: 7B model in float32 requires ~28GB RAM (model weights + KV cache)
2. **Custom Code**: Molmo uses `trust-remote-code` which has limited CPU support
3. **Performance**: Even if it worked, expect ~1-5 tokens/sec (10-50x slower than GPU)

### Alternatives for CPU

| Tool | Multimodal | Performance | Notes |
|------|------------|-------------|-------|
| **llama.cpp** | Limited | Better | Requires GGUF conversion |
| **Ollama** | Yes | Moderate | Easier setup, CPU fallback |
| **transformers** | Yes | Slow | Direct inference, no optimization |

**Recommendation:** CPU-only is not viable for vLLM. Use cloud GPU or Ollama for local CPU inference.

---

## WSL2 Considerations

For Windows users running WSL2:

1. **NVIDIA GPUs**: Work with WSL2
   - Install NVIDIA driver on **Windows** (not inside WSL)
   - Driver 470+ includes WSL support automatically
   - Run `nvidia-smi` inside WSL to verify

2. **Intel Arc GPUs**: Limited WSL support
   - DirectX 12 passthrough works for some workloads
   - CUDA emulation not available
   - Ollama may work with CPU fallback

3. **Docker**: Use Docker Desktop with WSL2 backend or install Docker inside WSL

---

## Cloud GPU Recommendation

For users without NVIDIA GPUs, cloud is the most reliable option:

### GCP (Recommended)

| GPU | VRAM | Cost/hr | Best For |
|-----|------|---------|----------|
| T4 | 16GB | ~$0.35 | 7B models, budget |
| **L4** | 24GB | ~$0.70 | 7B-13B models |
| A100 | 40GB | ~$3.00 | 70B models |

See `infrastructure/gcp/` for Terraform setup with auto-shutdown.

### AWS

- g4dn.xlarge (T4): ~$0.53/hr
- g5.xlarge (A10G 24GB): ~$1.00/hr

### Azure

- NC4as_T4_v3: ~$0.53/hr
- NC6s_v3 (V100): ~$3.00/hr

---

## Conclusions

1. **Primary Path**: NVIDIA GPU (local or cloud)
2. **Fallback**: GCP with L4 GPU (~$0.70/hr with auto-shutdown)
3. **Not Viable**: Intel Arc + vLLM, CPU-only + vLLM
4. **Future Watch**: Ollama Intel Arc support, PyTorch native XPU

---

## References

- [vLLM Documentation](https://docs.vllm.ai/)
- [Intel Extension for PyTorch (retiring)](https://github.com/intel/intel-extension-for-pytorch)
- [Ollama Gemma 3](https://ollama.com/library/gemma3)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)
