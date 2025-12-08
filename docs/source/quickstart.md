# Quickstart Guide

This guide will help you get started with kanoa-mlops on your local GPU system.

## Prerequisites

- **NVIDIA GPU** with CUDA support (tested on RTX 5080, Jetson Thor, etc.)
- **Docker** with NVIDIA Container Toolkit
- **Conda** (recommended) or Python 3.11+
- **Git**

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/lhzn-io/kanoa-mlops.git
cd kanoa-mlops
```

### 2. Set Up Environment

#### Option A: Using Conda (Recommended)

```bash
# Create and activate environment
conda env create -f environment.yml
conda activate kanoa-mlops

# Install development dependencies
pip install -r requirements-dev.txt
```

#### Option B: Using venv

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Verify GPU Access

```bash
# Check NVIDIA driver
nvidia-smi

# Verify Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

## Quick Start: Running Your First Model

### Option 1: Ollama (Easiest)

Ollama is the simplest way to get started with local inference.

#### Start Ollama Server

```bash
make serve-ollama
```

This will:

- Start Ollama with GPU support
- Expose API on `http://localhost:11434`
- Mount your Hugging Face cache for model access

#### Pull a Model

```bash
# Pull Gemma 3 4B (recommended for getting started)
docker compose -f docker/ollama/docker-compose.ollama.yml exec ollama ollama pull gemma3:4b

# Or pull a larger model
docker compose -f docker/ollama/docker-compose.ollama.yml exec ollama ollama pull gemma3:12b
```

#### Test the Model

```bash
# Run integration test
make test-ollama

# Or test manually
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:4b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Option 2: vLLM (Advanced)

vLLM provides higher throughput for production workloads.

#### Download a Model

First, download a model from Hugging Face:

```bash
# Set your Hugging Face token (optional, for gated models)
export HF_TOKEN=your_token_here

# Download Gemma 3 12B
huggingface-cli download google/gemma-3-12b-it \
  --local-dir ~/.cache/huggingface/hub/models--google--gemma-3-12b-it
```

#### Serve with vLLM

```bash
# For local development (uses native vLLM)
make serve-molmo  # Serves Molmo 7B on port 8000

# Or manually start vLLM
vllm serve google/gemma-3-12b-it \
  --port 8000 \
  --gpu-memory-utilization 0.9
```

#### Test vLLM

```bash
# Run integration test
python3 tests/integration/test_vllm_gemma3_api.py
```

## Monitoring Your Models

Start the monitoring stack to track GPU usage and performance:

```bash
make serve-monitoring
```

Access dashboards:

- **Grafana**: <http://localhost:3000> (admin/admin)
- **Prometheus**: <http://localhost:9090>

## Benchmarking

Run performance benchmarks to measure throughput:

```bash
# Benchmark Ollama
cd tests/integration
python3 run_benchmark_suite_ollama.py

# Benchmark vLLM
python3 run_benchmark_suite.py
```

See [Benchmarking Guide](../tests/integration/README.md) for detailed usage.

## Stopping Services

```bash
# Stop Ollama
docker compose -f docker/ollama/docker-compose.ollama.yml down

# Stop monitoring
docker compose -f docker-compose.monitoring.yml down
```

## Next Steps

- **[Model Support Guide](model-support.md)**: Add support for new models
- **[Contributing Guide](contributing.md)**: Contribute your benchmark results
- **[Performance Analysis](performance-analysis.md)**: Optimize your setup
- **[GPU Monitoring](gpu-monitoring.md)**: Deep dive into metrics

## Troubleshooting

### "CUDA out of memory"

- Reduce `--gpu-memory-utilization` (default: 0.9)
- Use a smaller model (e.g., 4B instead of 12B)
- Close other GPU applications

### "Connection refused"

- Ensure the service is running: `docker ps`
- Check port availability: `netstat -tuln | grep 11434`

### "Model not found"

For Ollama:

```bash
# List available models
docker compose -f docker/ollama/docker-compose.ollama.yml exec ollama ollama list

# Pull the model
docker compose -f docker/ollama/docker-compose.ollama.yml exec ollama ollama pull <model>
```

For vLLM:

```bash
# Verify model path
ls -la ~/.cache/huggingface/hub/
```

## Platform-Specific Notes

### NVIDIA Jetson Thor

- Use Ollama for best compatibility
- Reduce batch sizes for memory constraints
- Monitor temperature: `tegrastats`

### WSL2

See [WSL2 GPU Setup Guide](wsl2-gpu-setup.md)

### eGPU (Thunderbolt)

See [eGPU Setup Guide](egpu-setup-guide.md)
