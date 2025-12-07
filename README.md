# kanoa-mlops

MLOps infrastructure for local LLM hosting with `kanoa`.

## Overview

This repository provides production-ready infrastructure for:

- **vLLM Serving**: Host state-of-the-art local models (Molmo, Gemma 3) with OpenAI-compatible API
- **Ollama Serving**: Host GGUF models easily (Llama 3, Gemma 3) with robust local support.
- **Deployment Patterns**: Docker Compose for local, Terraform for GCP

## Quick Start

### Prerequisites

- Docker and Docker Compose (or `docker compose` plugin)
- **NVIDIA GPU** (required for vLLM - Intel/AMD GPUs not supported)
- Conda (optional, for environment management)

#### WSL2 Users

If running on WSL2, the NVIDIA driver must be installed on **Windows** (not inside WSL).
See [docs/source/wsl2-gpu-setup.md](docs/source/wsl2-gpu-setup.md) for detailed setup.

#### GPU Detection

Verify your GPU is detected:

```bash
make gpu-probe
```

This will display detailed GPU metadata including memory, PCIe bandwidth (important for eGPUs), temperature, and CUDA support.

### 1. Setup Environment

```bash
conda env create -f environment.yml
conda activate kanoa-mlops

# Install GPU dependencies
pip install -r requirements.txt
```

### 2. Download Model

```bash
# Download Molmo 7B (Currently Verified)
./scripts/download-models.sh molmo-7b-d
```

### 3. Start vLLM Server

```bash
# Start Molmo 7B service
docker compose -f docker/vllm/docker-compose.molmo.yml up -d
```

This starts a vLLM server on `http://localhost:8000` serving the Molmo model.

### 4. Use with kanoa

```python
from kanoa.backends import VLLMBackend

# Connect to local vLLM server
backend = VLLMBackend(
    api_base="http://localhost:8000/v1",
    model="allenai/Molmo-7B-D-0924"
)

# Interpret data
result = backend.interpret(
    fig=my_figure,
    data=my_data,
    context="Analysis context",
    focus=None,
    kb_context=None,
    custom_prompt=None
)

print(result.text)
```

## Project Structure

```text
kanoa-mlops/
├── docker/
│   └── vllm/              # Local vLLM Docker Compose setup
├── infrastructure/
│   └── gcp/               # GCP Terraform for cloud GPU instances
├── examples/
│   ├── demo-molmo-7b-egpu.ipynb
│   └── quickstart-gemma3-gcp.ipynb
├── scripts/
│   └── download-models.sh
├── docs/
│   └── source/            # Sphinx documentation source
└── environment.yml        # Conda environment
```

## Deployment Options

### Option 1: Local Docker (NVIDIA GPU Required)

Best for: Development with a local NVIDIA GPU.

```bash
# Molmo 7B
docker compose -f docker/vllm/docker-compose.molmo.yml up -d

# Gemma 3 (Experimental)
docker compose -f docker/vllm/docker-compose.gemma.yml up -d
```

See [docker/vllm/README.md](docker/vllm/README.md) for details.

### Option 2: GCP Cloud GPU (Beta)

Best for: Users without NVIDIA GPUs, or for production workloads.

Features:

- **L4 GPU** (~$0.70/hr) - 24GB VRAM for 7B-13B models
- **Auto-shutdown** after idle timeout (default: 30 min)
- **Firewall** restricted to your IP only

```bash
cd infrastructure/gcp

# Configure (edit with your project_id and IP)
cp terraform.tfvars.example terraform.tfvars

# Deploy
terraform init
terraform apply

# Use the output API endpoint with kanoa
```

See [docs/source/gcp-setup-guide.md](docs/source/gcp-setup-guide.md) for full setup.

### Option 3: Ollama (Local)

Best for: Easy local setup, VSCode integration, broader hardware support (CPU/Apple Silicon/NVIDIA).

```bash
make serve-ollama
```

See [docker/ollama/README.md](docker/ollama/README.md) for details.

## Supported Models

### Vision Language Models (2025-2026)

- **Molmo (7B)**: Excellent for vision tasks. 31.1 tok/s on RTX 5080. (Verified)
- **Gemma 3 (12B)**: Strong text reasoning, vision support. 10.3 tok/s on RTX 5080. (Verified)
- **Gemma 3 (4B, 27B)**: Additional model sizes. (Planned)

### Text-Only Models

- Llama 3.1 (8B, 70B) (Planned)
- Mistral (7B) (Planned)

## Architecture

### vLLM Server

- **OpenAI-compatible API**: Drop-in replacement for OpenAI endpoints
- **GPU Acceleration**: Optimized inference with CUDA
- **Batching**: Efficient request batching for throughput
- **Streaming**: Support for streaming responses

### Integration with kanoa

- Use `VLLMBackend` from `kanoa` package
- Configure `api_base` to point to local vLLM server
- Specify model name matching vLLM server config

## Performance

### Benchmark Results (RTX 5080 16GB eGPU)

Real-world performance with 4-bit quantization + FP8 KV cache:

| Model | Mean Throughput | Variance | Notes |
| :--- | :--- | :--- | :--- |
| **Molmo 7B** | **31.1 tok/s** | ±5.9 tok/s | Best for vision tasks, 3x faster |
| Gemma 3 12B | 10.3 tok/s | ±3.5 tok/s | More stable, better text reasoning |

**Key Findings**:

- **Molmo 7B** delivers 3x higher throughput than Gemma 3 12B despite being smaller
- Both models show similar variance (~19-34% coefficient of variation)
- First inference is slower due to cold cache; subsequent requests benefit from prefix caching
- Performance varies by task complexity (18-38 tok/s range observed)

See [docs/source/gpu-monitoring.md](docs/source/gpu-monitoring.md) for benchmarking methodology and detailed performance analysis.

### vLLM Advantages

vLLM provides significantly faster inference compared to direct transformers:

- **Throughput**: 10-20x improvement with batching
- **Latency**: 2-3x faster for single requests
- **Memory**: More efficient GPU memory usage

## Hardware Testing Roadmap

We are actively testing and optimizing `kanoa-mlops` for various edge AI hardware platforms.

| Hardware Platform | GPU Memory | Target Models | Performance | Status |
| :--- | :--- | :--- | :--- | :--- |
| **NVIDIA RTX 5080 (eGPU)** | 16GB | Molmo 7B (4-bit) | 31.1 tok/s | [✓] Verified |
| **NVIDIA RTX 5080 (eGPU)** | 16GB | Gemma 3 12B (4-bit) | 10.3 tok/s | [✓] Verified |
| **GCP L4 GPU** | 24GB | Molmo 7B, Gemma 3 12B | TBD | [ ] Planned |
| **NVIDIA Jetson Thor** | TBD | Gemma 3 27B | TBD | [ ] Planned |
| **NVIDIA Orin AGX** | 32GB / 64GB | Molmo 7B | TBD | [ ] Planned |

## Future Roadmap

- **RAG Infrastructure**: PostgreSQL + pgvector for knowledge base grounding.
- **LLaVa Models**: Evaluate LLaVa-Next and LLaVa-OneVision for specialized vision tasks.
- **Ollama Integration**: [✓] Implemented (Dec 2025).
- **Production Hardening**: Kubernetes manifests and Helm charts.

## GPU Monitoring

Real-time GPU monitoring tools are included in the development environment:

```bash
# Interactive htop-style GPU monitor
nvitop

# Quick snapshot
gpustat --color

# Watch mode (updates every 1s)
watch -n 1 gpustat --color
```

See [docs/source/gpu-monitoring.md](docs/source/gpu-monitoring.md) for detailed monitoring guides, including:

- vLLM Prometheus metrics (`/metrics` endpoint)
- Prefix cache hit rate monitoring
- Performance troubleshooting
- Benchmark analysis

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

> **Pro Tip**: We find **Claude Code** to be an excellent "DevOps Buddy" for this project. It handles Docker configurations and bash scripting particularly well. If you use it, just remember our [Human-in-the-Loop policy](CONTRIBUTING.md#4-ai-contribution-policy)!

## License

MIT License - see `kanoa` repository for details.
