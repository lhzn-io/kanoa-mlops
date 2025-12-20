# Local AI Coding Assistant Setup & Reference

Replace cloud-based GitHub Copilot with fully local LLM + Continue.dev. All code stays on your machine—zero cloud API calls.

---

## Quick Start (5 Minutes)

### Option A: vLLM (x86/CUDA GPUs)

```bash
docker run -d --gpus all -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:v0.6.3.post1 \
  --model meta-llama/Llama-4-Scout-17B-16E-Instruct \
  --gpu-memory-utilization 0.7 \
  --max-model-len 32768

# Verify: curl http://localhost:8000/v1/models
```

### Option B: Ollama (ARM64/Thor or lighter quantization)

```bash
# Start Ollama
kanoa mlops serve ollama

# Pull quantized Scout (65GB vs 203GB)
docker exec kanoa-ollama ollama pull ingu627/llama4-scout-q4:109b

# Verify: docker exec kanoa-ollama ollama list
```

### 2. Start Ollama Embeddings

```bash
ollama serve &
ollama pull nomic-embed-text

# Verify: curl http://localhost:11434/api/tags
```

### 3. Install & Configure Continue.dev

**For vLLM (Option A):**

```bash
# VSCode: Cmd/Shift+X → Search "Continue" → Install

# Create ~/.continue/config.json:
mkdir -p ~/.continue
cat > ~/.continue/config.json << 'EOF'
{
  "models": [{
    "title": "Llama-Scout-17B",
    "provider": "openai",
    "model": "meta-llama/Llama-4-Scout-17B-16E-Instruct",
    "apiBase": "http://localhost:8000/v1",
    "contextLength": 32768,
    "completionOptions": {"temperature": 0.5, "maxTokens": 256}
  }],
  "embeddingsProvider": {"provider": "ollama", "model": "nomic-embed-text"},
  "contextProviders": [{"name": "codebase", "params": {}}]
}
EOF
```

**For Ollama (Option B):**

```bash
cat > ~/.continue/config.json << 'EOF'
{
  "models": [{
    "title": "Llama-Scout-Q4",
    "provider": "ollama",
    "model": "ingu627/llama4-scout-q4:109b",
    "apiBase": "http://localhost:11434",
    "contextLength": 8192,
    "completionOptions": {"temperature": 0.5, "maxTokens": 256}
  }],
  "embeddingsProvider": {"provider": "ollama", "model": "nomic-embed-text"},
  "contextProviders": [{"name": "codebase", "params": {}}]
}
EOF
```

### 4. Test It

- Open VSCode in your project
- Type code → autocomplete in <300ms ✓
- Press `Cmd/Ctrl+L` → ask `@codebase` something ✓

---

## Hardware & Configuration

| GPU | VRAM | Model | Runtime | Memory | Latency |
|-----|------|-------|---------|--------|------|
| Jetson Thor | 64GB | Scout Q4 | Ollama | ~14GB | 250-350ms ✓ |
| RTX 5080 | 16GB | Scout 4-bit | vLLM | ~14GB | 150-200ms ✓ |
| RTX 4090 | 24GB | CodeLlama-70B | vLLM | ~21GB | 250-350ms ✓ |
| RTX 5090 | 24GB | CodeLlama-70B | vLLM | ~21GB | 200ms ✓ |

**Recommended: Scout 17B with vLLM (x86/CUDA):**

```bash
docker run -d --gpus all --ipc=host -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:v0.6.3.post1 \
  --model meta-llama/Llama-4-Scout-17B-16E-Instruct \
  --gpu-memory-utilization 0.7 \
  --max-model-len 32768 \
  --kv-cache-dtype fp8 \
  --enable-chunked-prefill
```

**Recommended: Scout 17B Q4 with Ollama (ARM64/Thor):**

```bash
# Start Ollama service
kanoa mlops serve ollama

# Pull Q4 quantized model (65GB)
docker exec kanoa-ollama ollama pull ingu627/llama4-scout-q4:109b

# Run inference
docker exec -it kanoa-ollama ollama run ingu627/llama4-scout-q4:109b
```

**Alternative: CodeLlama-70B (24GB+ GPUs only):**

```bash
docker run -d --gpus all --ipc=host -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:v0.6.3.post1 \
  --model codellama/CodeLlama-70b-Instruct-hf \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.9 \
  --max-model-len 16384 \
  --enable-prefix-caching
```

---

## Troubleshooting

### Autocomplete Not Appearing

```bash
# 1. Check vLLM
curl http://localhost:8000/v1/models

# 2. Check embedding service
curl http://localhost:11434/api/tags

# 3. Reload VSCode: Cmd/Ctrl+Shift+P → "Reload Window"
```

### Autocomplete Too Slow (>500ms)

```bash
# Reduce context length in docker run:
--max-model-len 2048  # Was 4096

# Or switch to smaller model (34B instead of 70B)
```

### No Codebase Search Results

```bash
# Verify Ollama model installed
ollama list

# Force re-index:
# Continue sidebar → Settings ⚙️ → "Reindex Codebase"

# Or manual:
rm -rf ~/.continue/index/
# Reopen VSCode (auto-reindexes)
```

### Out of Memory

```bash
# Reduce GPU memory utilization:
--gpu-memory-utilization 0.75  # Was 0.9

# Or reduce batch size:
--max-num-batched-tokens 4096  # Was 8192

# Or use smaller model (34B instead of 70B)
```

### "Failed to Connect to Embedding Service"

```bash
# Start Ollama
ollama serve &

# Pull model if missing
ollama pull nomic-embed-text

# Verify it's running
curl http://localhost:11434/api/tags
```

---

## Integration with kanoa-mlops

```bash
# Use kanoa to serve vLLM (Scout 17B)
conda activate kanoa-mlops

kanoa mlops serve vllm-llama-scout

# Or with custom model:
kanoa serve --backend vllm \
  --model meta-llama/Llama-4-Scout-17B-16E-Instruct \
  --port 8000 \
  --gpu-memory-utilization 0.7

# Continue auto-detects on localhost:8000
```

---

## Airgapped Deployment (No Internet)

**Phase 1: Prepare (Internet Machine)**

```bash
# Download models (~35GB for Scout 17B)
huggingface-cli download meta-llama/Llama-4-Scout-17B-16E-Instruct \
  --local-dir ~/models/llama-scout

# Download Docker images
docker pull vllm/vllm-openai:v0.6.3.post1
docker save vllm/vllm-openai:v0.6.3.post1 -o ~/vllm.tar

# Download Ollama embeddings
ollama pull nomic-embed-text
# Copy ~/.ollama/models to transfer storage

# Download VSCode extension
# Browser: marketplace.visualstudio.com → Continue.continue → Download
```

**Phase 2: Transfer**

```bash
# Copy to external USB drive:
# - Models (~35GB Scout, or ~140GB for CodeLlama-70B)
# - Docker images (~5GB)
# - Ollama models (~1GB)
# Total: ~45GB (Scout) or ~150GB (CodeLlama-70B)
```

**Phase 3: Setup Offline**

```bash
# On airgapped machine:
cp -r /usb/models ~/.cache/huggingface
docker load -i /usb/vllm.tar
cp -r /usb/ollama ~/.ollama

# Start services
docker run -d --gpus all -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -e HF_HUB_OFFLINE=1 \
  vllm/vllm-openai:v0.6.3.post1 \
  --model meta-llama/Llama-4-Scout-17B-16E-Instruct \
  --gpu-memory-utilization 0.7 \
  --max-model-len 32768

ollama serve &

# Install Continue from VSIX (if needed)
code --install-extension ~/continue-latest.vsix
```

**Phase 4: Verify (No Network!)**

```bash
# Ensure network disconnected
ping google.com  # Should timeout

# Test all services
curl http://localhost:8000/v1/models
curl http://localhost:11434/api/tags

# Monitor: No external traffic should appear
sudo tcpdump -i any -nn 'not (dst 127.0.0.1 or dst 192.168.0.0/16)' -c 10
# Should capture 0 packets
```

---

## Performance Benchmarks

**Jetson Thor + Scout 17B:**

- Autocomplete (128 tokens): 200-300ms
- Chat throughput: 18 tok/s
- Codebase search: 100-150ms
- GPU memory: ~14GB / 64GB unified

**RTX 5080 + Scout 17B:**

- Autocomplete (128 tokens): 150-200ms
- Chat throughput: 28 tok/s
- Codebase search: 80-120ms
- GPU memory: 14GB / 16GB

**RTX 4090 + CodeLlama-70B AWQ:**

- Autocomplete (128 tokens): 250-350ms
- Chat throughput: 22 tok/s
- Codebase search: 100-150ms
- GPU memory: 21GB / 24GB

---

## Common Commands

| Action | Command |
|--------|---------|
| Open chat | `Cmd/Ctrl+L` |
| Inline edit | `Cmd/Ctrl+I` |
| Accept autocomplete | `Tab` |
| View logs | `tail -f ~/.continue/continue.log` |
| Check vLLM | `curl http://localhost:8000/v1/models` |
| Monitor GPU | `watch -n 1 nvidia-smi` |
| Stop vLLM | `docker stop $(docker ps -q --filter ancestor=vllm/vllm-openai)` |
| Stop Ollama | `killall ollama` |

---

## Model Selection

Choose based on your GPU VRAM:

| VRAM | Model | Type | Command |
|------|-------|------|------|
| 12-16GB | **Llama-Scout-17B** ⭐ | MoE | Default (see above) - Recommended |
| 24GB+ | CodeLlama-70B | Dense | `--model codellama/CodeLlama-70b-Instruct-hf` |
| 18-24GB | Qwen2.5-Coder-32B | Dense | `--model Qwen/Qwen2.5-Coder-32B-Instruct` |
| 12-18GB | CodeLlama-34B | Dense | `--model codellama/CodeLlama-34b-Instruct-hf` |
| 8-12GB | CodeLlama-13B | Dense | `--model codellama/CodeLlama-13b-Instruct-hf` |

**Why Scout?**

- ✅ MoE efficiency: Only ~4B active params per token (17B total, 16 experts)
- ✅ Llama 4 generation: Smarter base architecture than CodeLlama (Llama 2)
- ✅ General purpose: Not code-specialized but excellent for coding tasks
- ✅ Long context: 32k tokens (2x CodeLlama's 16k)
- ✅ Quantization-friendly: Q4 reduces size from 203GB to 65GB

All models from HuggingFace (Meta, Alibaba, etc.). No proprietary models required.

---

## kanoa mlops CLI Integration

The `kanoa mlops serve` command provides a unified interface for both vLLM and Ollama:

### Ollama with Model Selection

```bash
# Interactive: Shows menu to select from locally pulled models
kanoa mlops serve ollama scout

# Non-interactive: Start Ollama server only
kanoa mlops serve ollama
```

**First time setup:**

```bash
# Start Ollama
kanoa mlops serve ollama

# Pull Scout (Q4 quantized)
docker exec kanoa-ollama ollama pull ingu627/llama4-scout-q4:109b

# List models
docker exec kanoa-ollama ollama list
```

### vLLM with Model Selection

```bash
# Interactive: Shows cached HuggingFace models
kanoa mlops serve vllm llama-scout

# Non-interactive: Specify model directly
kanoa mlops serve vllm llama-scout --model meta-llama/Llama-4-Scout-17B-16E-Instruct
```

### Consistent Pattern

Both runtimes follow the same pattern:

```bash
kanoa mlops serve <runtime> [family] [--model <specific-model>]

# Examples:
kanoa mlops serve ollama scout          # Ollama Scout selector
kanoa mlops serve vllm llama-scout      # vLLM Scout selector
kanoa mlops serve ollama                # Start Ollama server
kanoa mlops serve vllm gemma3           # vLLM Gemma selector
```

---

## Verification Checklist

After setup:

- [ ] Runtime responds:
  - vLLM: `curl http://localhost:8000/v1/models`
  - Ollama: `docker exec kanoa-ollama ollama list`
- [ ] Embeddings installed: `ollama list | grep nomic`
- [ ] Continue extension: `code --list-extensions | grep Continue`
- [ ] config.json exists: `cat ~/.continue/config.json`
- [ ] Autocomplete appears in <300ms
- [ ] `@codebase` returns search results
- [ ] Monitor tab shows NO external API calls

---

## Getting Help

- **Continue Discord**: <https://discord.gg/vapESyrFmJ>
- **vLLM Issues**: <https://github.com/vllm-project/vllm/issues>
- **Ollama GitHub**: <https://github.com/ollama/ollama>

---

## Key Concepts

**What's Running:**

- vLLM: Code completion server (local inference)
- Ollama: Embedding model server (semantic search)
- LanceDB: Vector database (stored in ~/.continue/)
- Continue: VSCode extension integrating all 3

**Data Flow:**

1. Type code → Continue sends to vLLM (localhost:8000)
2. vLLM infers locally, returns suggestion
3. For @codebase: Continue generates embeddings with Ollama (localhost:11434)
4. Searches local LanceDB index in ~/.continue/
5. ✅ ZERO external calls

**Why Local:**

- GitHub Copilot sends code to OpenAI servers
- GitHub Copilot stores codebase embeddings server-side
- Local version: all code stays on your machine
- Full data sovereignty for government/healthcare/proprietary work

---

## See Also

- **Architecture Deep-Dive**: See developer guide
- **Performance Tuning**: Benchmark your setup for your GPU
- **Kanoa Integration**: Run unified multi-model inference backend
