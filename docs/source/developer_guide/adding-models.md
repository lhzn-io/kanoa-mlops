# Adding New Model Support

Guide for contributors adding support for new vision-language or text models.

## Overview

Adding a new model involves:
1. Creating a docker-compose configuration
2. Testing the model locally
3. Adding Makefile targets (optional)
4. Updating documentation

## Quick Start: Add a New vLLM Model

### Step 1: Create Docker Compose File

Copy an existing config as a starting point:

```bash
cd docker/vllm/
cp docker-compose.gemma.yml docker-compose.olmo3.yml
```

### Step 2: Configure the Model

Edit `docker-compose.olmo3.yml`:

```yaml
services:
  vllm-olmo3:
    image: vllm/vllm-openai:latest
    container_name: kanoa-vllm-olmo3
    ports:
      - "8000:8000"  # Use 8001:8000 if running alongside another model
    volumes:
      - ${HF_HOME:-~/.cache/huggingface}:/root/.cache/huggingface:rw
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - HF_HOME=/root/.cache/huggingface
    command:
      - --model
      - allenai/OLMo-3-32B-Think-1125  # HuggingFace model ID
      - --host
      - 0.0.0.0
      - --port
      - "8000"
      - --served-model-name
      - olmo3-32b-think
      - --trust-remote-code
      # Memory optimization for large models
      - --max-model-len
      - "8192"
      - --gpu-memory-utilization
      - "0.9"
      # Quantization (recommended for 32B+ models on consumer GPUs)
      - --quantization
      - bitsandbytes
      - --load-format
      - bitsandbytes
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

networks:
  default:
    name: kanoa-mlops
```

### Step 3: Test the Model

```bash
# Start the server
docker compose -f docker-compose.olmo3.yml up

# In another terminal, test the endpoint
curl http://localhost:8000/v1/models

curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "olmo3-32b-think",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

### Step 4: Update Templates (for pip users)

Copy to bundled templates:

```bash
cp docker/vllm/docker-compose.olmo3.yml \
   kanoa_mlops/templates/docker/vllm/
```

### Step 5: Add Makefile Target (optional)

In `Makefile`:

```makefile
serve-olmo3:
	@echo "Starting Olmo 3 32B Think server..."
	@docker compose -f docker/vllm/docker-compose.olmo3.yml up -d
	@echo "Olmo 3 running at http://localhost:8000"
```

## Configuration Reference

### Key vLLM Parameters

| Parameter | Description | Recommendation |
|-----------|-------------|----------------|
| `--max-model-len` | Max context length | Start with 4096-8192 |
| `--gpu-memory-utilization` | VRAM fraction | 0.8-0.9 for single user |
| `--quantization` | Weight quantization | `bitsandbytes` for large models |
| `--tensor-parallel-size` | Multi-GPU | Set to GPU count |
| `--trust-remote-code` | Model custom code | Required for most models |

### Memory Requirements

| Model Size | Precision | VRAM (approx) |
|------------|-----------|---------------|
| 7B | FP16 | 14GB |
| 7B | 4-bit | 4-6GB |
| 12B | FP16 | 24GB |
| 12B | 4-bit | 8-10GB |
| 32B | FP16 | 64GB+ |
| 32B | 4-bit | 20-24GB |

### Quantization Options

```yaml
# 4-bit quantization (recommended for large models)
- --quantization
- bitsandbytes
- --load-format
- bitsandbytes

# FP8 KV cache (reduces memory, good for context length)
- --kv-cache-dtype
- fp8
```

## Adding Ollama Models

For Ollama, no config changes needed — just pull the model:

```bash
# Start Ollama
kanoa mlops serve ollama

# Pull a new model
docker exec kanoa-ollama ollama pull olmo3:32b

# Use it
curl http://localhost:11434/api/generate \
  -d '{"model": "olmo3:32b", "prompt": "Hello!"}'
```

## Testing Checklist

Before submitting a PR:

- [ ] Model starts without errors
- [ ] `/health` endpoint responds
- [ ] `/v1/chat/completions` works
- [ ] Memory usage is reasonable
- [ ] Documented in README

## Troubleshooting

### Model fails to load

```bash
# Check logs
docker compose -f docker-compose.olmo3.yml logs

# Common issues:
# - OOM: Reduce --max-model-len or add quantization
# - Trust: Add --trust-remote-code
# - Download: Check HF_TOKEN if model is gated
```

### Slow inference

Try FP8 KV cache:
```yaml
- --kv-cache-dtype
- fp8
- --enable-chunked-prefill
```

### Need HuggingFace token

For gated models (Llama, Gemma):

```bash
export HF_TOKEN=hf_your_token_here
docker compose -f docker-compose.model.yml up
```

Or add to docker-compose:
```yaml
environment:
  - HF_TOKEN=${HF_TOKEN}
```
