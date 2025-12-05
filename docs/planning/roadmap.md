# kanoa-mlops Roadmap & Design

**Status**: Active
**Last Updated**: 2025-12-03

## 1. Vision & Scope

`kanoa-mlops` provides the "brawn" (compute, storage, serving) for local AI interpretation, complementing the lightweight `kanoa` client library ("brain").

### Core Objectives

1. **Local Sovereignty**: Enable high-performance inference on consumer hardware (eGPUs, gaming laptops).
2. **Cloud Flexibility**: Provide seamless "burst to cloud" paths (GCP L4/A100) when local hardware is insufficient.
3. **Grounding Integration**: Connect with external frameworks (hosted or local) for grounded analysis, avoiding custom RAG implementation where possible.

## 2. Target Feature Set

### Phase 1: Inference Infrastructure (Current)

- **vLLM Serving**: Docker-based inference for open-source models.
  - [x] **Molmo 7B**: Vision-language model for chart/plot analysis.
  - [x] **Gemma 3**: Multimodal reasoning (4B, 12B, 27B).
  - [ ] **GPT-OSS 20B**: OpenAI's open-weight reasoning model (fits in 16GB).
  - [ ] **GPT-OSS 120B**: Via free hosted providers (HuggingFace Inference, [gpt-oss.com](https://gpt-oss.com/)).
- **Ollama Integration** (Issue #1):
  - [ ] **Llama 3.2 Vision 11B**: Test OpenAI-compatible API with kanoa
  - [ ] **Setup Documentation**: Quick start guide for Ollama + kanoa
  - [ ] **Example Notebooks**: Demonstrate usage with popular Ollama models
  - [ ] **Model Recommendations**: Document tested models (Qwen3-VL, LLaVA)
  - **Benefits**: Easier setup than vLLM, works on CPU/Apple Silicon/NVIDIA
- **Hardware Support**:
  - [x] **NVIDIA eGPU**: Verified on RTX 5080 (16GB) via Thunderbolt/OCulink.
  - [x] **GCP Cloud**: Terraform modules for L4/A100 instances with auto-shutdown.
  - [ ] **Jetson/Orin**: Edge deployment support.
  - [ ] **Jetson Thor**: Next-gen edge deployment support.

### Phase 2: Grounding Integration (Q1 2026)

- **Strategy**: Prioritize integration with existing Grounding/RAG frameworks over building custom infrastructure.
- **Analysis**:
  - [ ] **Framework Survey**: Identify hosted or local frameworks that provide robust Grounding (e.g., LangChain, LlamaIndex, or specialized vector providers).
- **Implementation**:
  - [ ] **Connectors**: Build adapters for selected Grounding providers.
  - [ ] **Fallback**: Minimal local vector store (e.g., pgvector) only if no suitable external integration exists.

### Phase 3: Production Hardening (Q2 2026)

- **Orchestration**:
  - [ ] **Kubernetes**: Helm charts for GKE/EKS deployment.
  - [ ] **Observability**: Prometheus/Grafana dashboards for GPU metrics.
- **Optimization**:
  - [ ] **Model Caching**: Shared volumes for model weights to reduce startup time.
  - [ ] **Auto-scaling**: KEDA scalers based on queue depth.

## 3. Architecture Design

```mermaid
graph TD
    subgraph "Client Layer (kanoa)"
        Client[Python Client]
    end

    subgraph "Inference Layer (kanoa-mlops)"
        LB[Load Balancer / Traefik]
        vLLM[vLLM (Molmo/Gemma/LLaVa)]
    end

    subgraph "Grounding Layer (External/Integrated)"
        Grounding[Grounding Provider / Vector Store]
    end

    Client -->|Chat Completion API| LB
    LB -->|/v1/chat/completions| vLLM
    Client -->|Context/Retrieval| Grounding
```

## 4. Hardware Compatibility Matrix

| Platform | GPU Memory | Target Models | Status |
| :--- | :--- | :--- | :--- |
| **NVIDIA RTX 5080 (eGPU)** | 16GB | Molmo 7B (4-bit), Gemma 3 12B (4-bit), GPT-OSS 20B | [✓] Verified |
| **NVIDIA RTX 4090** | 24GB | Gemma 3 27B (4-bit), GPT-OSS 20B (FP16) | [ ] Planned |
| **GCP L4** | 24GB | Molmo 7B, Gemma 3 12B (FP16), GPT-OSS 20B | [ ] Planned |
| **GCP H100 / AMD MI300X** | 80GB | GPT-OSS 120B | [ ] Planned |
| **NVIDIA Jetson Orin** | 64GB | Molmo 7B, Gemma 3 27B (Quantized) | [ ] Planned |
| **NVIDIA Jetson Thor** | 128GB | Blackwell GPU, 1000 TFLOPS (FP8) | [ ] Planned |
| **Free Hosted** | — | GPT-OSS 120B via HuggingFace Inference / gpt-oss.com | [ ] Planned |

## 5. Development Guidelines

- **Infrastructure as Code**: All cloud resources must be defined in Terraform.
- **Containerization**: All services must be Dockerized with pinned versions.
- **Idempotency**: Setup scripts must be safe to run multiple times.
- **Documentation**: Every hardware config must have a setup guide (e.g., `docs/source/egpu-setup-guide.md`).
