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

## Architecture-Aware Templating System

`kanoa-mlops` uses a hybrid templating system to support multiple hardware platforms (x86_64, Jetson Orin, Jetson Thor) while keeping architecture-agnostic services simple.

### Platform-Specific Considerations

#### Jetson Thor Limitations

When adding models for Jetson Thor (ARM64/Blackwell):

- **vLLM Thor image**: Pre-built by NVIDIA but has limited quantization support
  - ✅ Works: FP16, FP8, INT8
  - ❌ Missing: bitsandbytes (affects Scout, some LLaMA models)
  - Workaround: Use Ollama for models requiring bitsandbytes

- **Memory constraints**: Thor has 64GB unified memory
  - Large models (>100B params) may OOM without quantization
  - Use conservative `--gpu-memory-utilization` (0.5-0.7)
  - Reduce `--max-model-len` and `--max-num-seqs` if needed

- **Ollama alternative**: Better for Thor in many cases
  - Handles quantization automatically (Q4, Q5, Q6, Q8)
  - Simpler setup, no manual quantization flags
  - Example: Scout 17B reduces from 203GB → 65GB with Q4

#### When to Use Ollama vs vLLM

| Scenario | Recommended Runtime | Reason |
|----------|-------------------|--------|
| Thor + quantization needed | Ollama | Thor vLLM lacks bitsandbytes |
| x86/CUDA + production | vLLM | More control, better throughput |
| Quick prototyping | Ollama | Simpler setup, auto quantization |
| Custom inference params | vLLM | Fine-grained control |

### When to Use Jinja2 Templates (`.yml.j2`)

Use Jinja2 templates when your service needs **architecture-specific configuration**:

- **Different Docker images** per platform (e.g., `ghcr.io/nvidia-ai-iot/vllm:latest-jetson-thor` vs `vllm/vllm-openai:latest`)
- **Platform-specific flags** (e.g., quantization only on non-Thor platforms)
- **Hardware-dependent settings** (CUDA compute capability, memory limits)

**Example**: vLLM services use `.yml.j2` templates because Jetson Thor requires a special pre-built image and different command flags.

### When to Use Static YAML (`.yml`)

Use plain `.yml` files when your service is **architecture-agnostic**:

- Works identically across all platforms
- Uses the same Docker image everywhere
- No conditional configuration needed

**Examples**:

- **Ollama** - `ollama/ollama:latest` works on all platforms
- **Monitoring** - Prometheus, Grafana, DCGM exporter are standard containers

### Available Template Context

In `.j2` templates, the `arch_config` object provides:

```jinja
{% if arch_config.platform_name == "jetson-thor" %}
    image: {{ arch_config.vllm_image }}
{% else %}
    image: vllm/vllm-openai:latest
{% endif %}
```

**Properties**:

- `arch_config.platform_name` - `"jetson-thor"`, `"jetson-orin"`, or `"x86-cuda"`
- `arch_config.arch` - `"aarch64"` or `"x86_64"`
- `arch_config.vllm_image` - Recommended vLLM image for this platform
- `arch_config.cuda_arch` - CUDA compute capability (e.g., `"sm_110"`)
- `arch_config.description` - Human-readable platform description

### How Templates Are Processed

During `kanoa mlops init`:

1. **Static files** (`.yml`) are copied as-is using `shutil.copytree()`
2. **Jinja2 templates** (`.yml.j2`) are:
   - Excluded from the copy operation via `_ignore_jinja_templates()`
   - Rendered with `_render_templates()` using detected `arch_config`
   - Written to the target directory with `.j2` extension removed

See `kanoa_mlops/plugin.py` lines 237-270 for implementation details.

### Step 4: Update Templates (for pip users)

If your model is **architecture-agnostic**, copy as static `.yml`:

```bash
cp docker/ollama/docker-compose.mymodel.yml \
   kanoa_mlops/templates/docker/ollama/
```

If your model needs **architecture-specific configuration**, create a Jinja2 template (`.yml.j2`):

```bash
# 1. Convert to template with arch-specific logic
cp docker/vllm/docker-compose.gemma3.yml.j2 \
   kanoa_mlops/templates/docker/vllm/docker-compose.mymodel.yml.j2

# 2. Edit the template to add conditional logic
vim kanoa_mlops/templates/docker/vllm/docker-compose.mymodel.yml.j2
```

**Example architecture-aware template**:

```yaml
services:
  vllm-mymodel:
{% if arch_config.platform_name == "jetson-thor" %}
    image: {{ arch_config.vllm_image }}
{% else %}
    image: vllm/vllm-openai:latest
{% endif %}
    # ... rest of config
    command: >
      vllm serve
      --model myorg/mymodel
{% if arch_config.platform_name != "jetson-thor" %}
      --quantization bitsandbytes
      --load-format bitsandbytes
{% endif %}
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
