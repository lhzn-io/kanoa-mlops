# kanoa-mlops

MLOps infrastructure for local LLM hosting and RAG with `kanoa`.

## Overview

This repository provides production-ready infrastructure for:

- **vLLM Serving**: Host state-of-the-art local models (Gemma 3, Molmo, Llama 3.1) with OpenAI-compatible API
- **RAG Infrastructure**: PostgreSQL + pgvector for knowledge base grounding
- **Deployment Patterns**: Docker Compose for local, Kubernetes for production

## Quick Start

### Prerequisites

- Docker and Docker Compose
- NVIDIA GPU with CUDA support (for vLLM)
- Conda (optional, for environment management)

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
│   ├── vllm/              # vLLM serving containers
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile
│   │   └── README.md
│   ├── pgvector/          # PostgreSQL + pgvector (future)
│   └── embeddings/        # Embedding models (future)
├── kubernetes/            # K8s manifests (future)
├── examples/
│   ├── quickstart-gemma3.py
│   └── quickstart-molmo.py
├── scripts/
│   └── download-models.sh
├── environment.yml        # Conda environment
└── README.md
```

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
