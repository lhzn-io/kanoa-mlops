# kanoa-mlops

MLOps infrastructure for local LLM hosting and RAG with `kanoa`.

## Overview

This repository provides production-ready infrastructure for:

- **vLLM Serving**: Host state-of-the-art local models (Gemma 3, Molmo, Llama 3.1) with OpenAI-compatible API
- **RAG Infrastructure**: PostgreSQL + pgvector for knowledge base grounding
- **Deployment Patterns**: Docker Compose for local, Kubernetes for production

## Quick Start

### Prerequisites

- Docker and Docker Compose (or `docker compose` plugin)
- **NVIDIA GPU** (required for vLLM - Intel/AMD GPUs not supported)
- Conda (optional, for environment management)

#### WSL2 Users

⚠️ If running on WSL2, the NVIDIA driver must be installed on **Windows** (not inside WSL).
See [docker/vllm/README.md](docker/vllm/README.md#wsl2-windows-subsystem-for-linux) for detailed setup.

### 1. Setup Environment

```bash
conda env create -f environment.yml
conda activate kanoa-mlops
```

### 2. Download Model

```bash
# Download Gemma 3 12B (Recommended for 2025/2026)
./scripts/download-models.sh gemma-3-12b
```

### 3. Start vLLM Server

```bash
cd docker/vllm
# Set model environment variables
export MODEL_NAME=gemma-3-12b
export SERVED_MODEL_NAME=google/gemma-3-12b-it
docker-compose up
```

This starts a vLLM server on `http://localhost:8000` serving the Gemma 3 model.

### 4. Use with kanoa

```python
from kanoa.backends import VLLMBackend

# Connect to local vLLM server
backend = VLLMBackend(
    api_base="http://localhost:8000/v1",
    model="google/gemma-3-12b-it"
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

## Repository Structure

```text
kanoa-mlops/
├── docker/
│   └── vllm/              # Local vLLM Docker Compose setup
├── infrastructure/
│   └── gcp/               # GCP Terraform for cloud GPU instances
├── examples/
│   ├── quickstart-gemma3.py
│   └── quickstart-molmo.py
├── scripts/
│   └── download-models.sh
├── docs/
│   └── planning/          # Architecture and planning docs
└── environment.yml        # Conda environment
```

## Deployment Options

### Option 1: Local Docker (NVIDIA GPU Required)

Best for: Development with a local NVIDIA GPU.

```bash
cd docker/vllm
docker-compose up -d
```

See [docker/vllm/README.md](docker/vllm/README.md) for details.

### Option 2: GCP Cloud GPU (Recommended)

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

See [infrastructure/gcp/README.md](infrastructure/gcp/README.md) for full setup.

## Supported Models

### Vision Language Models (2025-2026)

- **Gemma 3 (4B, 12B, 27B)**: Google's latest open-weight multimodal models. State-of-the-art performance for local deployment.
- **Molmo (7B, 1B)**: Excellent alternative for specific vision tasks.

### Text-Only Models

- Llama 3.1 (8B, 70B)
- Mistral (7B)

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

vLLM provides significantly faster inference compared to direct transformers:

- **Throughput**: 10-20x improvement with batching
- **Latency**: 2-3x faster for single requests
- **Memory**: More efficient GPU memory usage

## Deployment Patterns

### Local Development

- Docker Compose (this repo)
- Single GPU, local model storage

### Production (Future)

- Kubernetes with GPU node pools
- Model caching and replication
- Load balancing and autoscaling
- Monitoring with Prometheus/Grafana

## Contributing

See `kanoa` repository for contribution guidelines.

## License

MIT License - see `kanoa` repository for details.
