# vLLM Molmo Server

Docker Compose setup for serving Molmo models with vLLM.

## Prerequisites

1. **NVIDIA GPU** with CUDA support
2. **NVIDIA Container Toolkit** installed:

   ```bash
   # Ubuntu/Debian
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
     sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
   sudo systemctl restart docker
   ```

3. **Molmo Model** downloaded locally:

   ```bash
   # Run from kanoa-mlops root
   ./scripts/download-models.sh molmo-7b-d
   ```

## Quick Start

```bash
# Start the server
docker-compose up -d

# Check logs
docker-compose logs -f

# Test the server
curl http://localhost:8000/v1/models

# Stop the server
docker-compose down
```

## Configuration

### Environment Variables

Create a `.env` file in this directory:

```bash
# Path to downloaded Molmo model
MOLMO_MODEL_PATH=/path/to/molmo/model

# Hugging Face cache (for tokenizers, etc.)
HF_HOME=~/.cache/huggingface

# GPU to use (default: 0)
CUDA_VISIBLE_DEVICES=0
```

### Model Parameters

Edit `docker-compose.yml` to adjust:

- `--max-model-len`: Maximum sequence length (default: 4096)
- `--gpu-memory-utilization`: GPU memory fraction (default: 0.9)
- `--tensor-parallel-size`: Number of GPUs for model parallelism

## Usage with kanoa

```python
from kanoa.backends import VLLMBackend

backend = VLLMBackend(
    api_base="http://localhost:8000/v1",
    model="allenai/Molmo-7B-D-0924"
)

result = backend.interpret(
    fig=my_figure,
    data=my_data,
    context="Analyze this plot",
    focus=None,
    kb_context=None,
    custom_prompt=None
)

print(result.text)
```

## Troubleshooting

### GPU Not Detected

```bash
# Verify NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# Check Docker daemon config
cat /etc/docker/daemon.json
# Should contain:
# {
#   "runtimes": {
#     "nvidia": {
#       "path": "nvidia-container-runtime",
#       "runtimeArgs": []
#     }
#   }
# }
```

### Out of Memory

Reduce `--gpu-memory-utilization` or `--max-model-len` in `docker-compose.yml`.

### Model Not Found

Ensure `MOLMO_MODEL_PATH` points to the directory containing:

- `config.json`
- `model.safetensors` (or `pytorch_model.bin`)
- `tokenizer.json`
- Other model files

## Performance

Expected performance on NVIDIA A100 (40GB):

- **Throughput**: ~50-100 tokens/sec
- **Latency**: ~2-5 seconds for first token
- **Batch Size**: Up to 8-16 concurrent requests

## Advanced Configuration

### Multi-GPU Setup

```yaml
environment:
  - CUDA_VISIBLE_DEVICES=0,1
command:
  - --tensor-parallel-size
  - "2"
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 2  # Use 2 GPUs
          capabilities: [gpu]
```

### Custom Port

```yaml
ports:
  - "8001:8000"  # Map to different host port
```

## Monitoring

View real-time metrics:

```bash
# GPU usage
watch -n 1 nvidia-smi

# Container stats
docker stats kanoa-vllm-molmo

# API metrics (if enabled)
curl http://localhost:8000/metrics
```
