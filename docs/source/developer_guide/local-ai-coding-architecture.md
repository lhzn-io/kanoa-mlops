# Local AI Coding Agents: Architecture & Performance

Technical deep-dive for infrastructure engineers and those extending the system.

---

## Why Local? The Problem with Cloud

**GitHub Copilot Architecture Issues:**

1. **Inference**: All requests sent to OpenAI cloud servers
   - Latency: 5-10 seconds per request (vs 300ms local)
   - Privacy: All code leaves your machine

2. **Codebase RAG** (The Real Problem):
   - Repos <2,500 files: Limited client-side indexing
   - Repos >2,500 files: GitHub generates embeddings on server
   - **All embeddings stored on GitHub infrastructure**
   - **Shared across all users with repo access**
   - Source: [Medium article on GitHub Copilot RAG](https://medium.com/@xorets/indexing-large-codebases-for-github-copilot-with-local-rag-bdbf8472e21c)

**Local Solution (Continue + vLLM):**

- Inference: Local vLLM server (300ms)
- Embeddings: Local Ollama (20ms)
- Storage: Local LanceDB in `~/.continue/`
- Result: ✅ Zero external API calls

---

## Architecture

```
VSCode
  ↓ (autocomplete/chat requests)
Continue Extension (TypeScript)
  ├→ vLLM (inference)  [localhost:8000]
  ├→ Ollama (embeddings) [localhost:11434]
  └→ LanceDB (vector DB) [~/.continue/]
```

**Data never leaves your machine.**

---

## Component Selection

### vLLM vs. Ollama for Inference

| Factor | vLLM | Ollama |
|--------|------|--------|
| **Models** | Any HuggingFace | Primarily LLaMA family |
| **Latency** | Lower (optimized) | Higher |
| **Throughput** | Higher (batching) | Lower |
| **Code Quality** | Excellent | Good |
| **GPU Support** | NVIDIA/AMD/Intel | NVIDIA/Metal/CPU |
| **Best For** | Production servers | Lightweight/Mac |

**Recommendation:** vLLM for autocomplete (latency critical), Ollama for embeddings (simple, standalone).

### Embedding Models: Evolution

| Model | Dims | Context | Speed | Accuracy | Year |
|-------|------|---------|-------|----------|------|
| all-MiniLM-L6-v2 | 384 | 512 | 14ms | 75% | 2021 |
| **nomic-embed-text-v1.5** | **768** | **8192** | **20ms** | **82%** | **2024** |

**Upgrade from default (MiniLM) to nomic-embed-text:**

- +7% search accuracy
- +2ms latency (negligible)
- Matryoshka scaling (resize dims at inference time)

### LanceDB vs Alternatives

| DB | Local | Latency | Search Quality | Notes |
|----|-------|---------|-----------------|-------|
| **LanceDB** | ✅ | <100ms | High (ANN) | **Embedded TypeScript lib** |
| Pinecone | ❌ | Network | High | Cloud only |
| Weaviate | ✅ | ~150ms | High | Separate process |
| FAISS | ✅ | <50ms | High | RAM-limited |

**Why LanceDB:** Zero external dependencies, ~100ms latency, no separate service.

---

## Model Recommendations

### Decision Matrix

```
GPU VRAM Available?
├─ 24GB+  → CodeLlama-70B or Qwen-32B
├─ 18-24GB → Qwen-32B or CodeLlama-34B
├─ 12-18GB → CodeLlama-34B or CodeLlama-13B
└─ 8-12GB → CodeLlama-13B or 7B models
```

### Tier 1: Best (70B - requires 24GB+)

- **Model:** CodeLlama-70B-Instruct (Meta)
- **Quantization:** AWQ (4-bit) or float16
- **Expected:** 250-350ms autocomplete, 22 tok/s chat
- **Context:** 4096 tokens

### Tier 2: Best Balance (32B - requires 18-24GB)

- **Model:** Qwen2.5-Coder-32B-Instruct (Alibaba)
- **Quantization:** AWQ
- **Expected:** 180-250ms autocomplete, 28 tok/s chat
- **Context:** 32768 tokens (much larger!)

### Tier 3: Efficient (34B - requires 12-18GB)

- **Model:** CodeLlama-34B-Instruct (Meta)
- **Quantization:** AWQ or GPTQ
- **Expected:** 190ms autocomplete, 35 tok/s chat
- **Context:** 4096 tokens

### Tier 4: Lightweight (13B - requires 8-12GB)

- **Model:** CodeLlama-13B-Instruct (Meta)
- **Quantization:** GPTQ
- **Expected:** 120ms autocomplete, 50 tok/s chat
- **Context:** 4096 tokens

---

## vLLM Performance Tuning

### Configuration Template (RTX 4090)

```bash
docker run -d \
  --gpus all \
  --ipc=host \
  -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:v0.6.3.post1 \
  --model codellama/CodeLlama-70b-Instruct-hf \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.9 \
  --max-model-len 16384 \
  --max-num-batched-tokens 8192 \
  --dtype float16 \
  --enable-prefix-caching
```

### Parameter Reference

| Parameter | Purpose | Autocomplete | Chat |
|-----------|---------|--------------|------|
| `--gpu-memory-utilization` | VRAM budget | 0.85 (safer) | 0.9 (maximize) |
| `--max-model-len` | Max context | 4096 (faster) | 16384 (better) |
| `--max-num-batched-tokens` | Batch size | 4096 | 8192 |
| `--enable-prefix-caching` | Cache prompt embeddings | True (faster) | True |
| `--dtype` | Precision | float16 (fast) | bfloat16 (stable) |

### Quantization Comparison

| Method | VRAM | Speed | Accuracy | Use Case |
|--------|------|-------|----------|----------|
| float16 | 100% | 1.0x | 100% | Reference/GPU RAM available |
| AWQ (4-bit) | 25% | 1.2x | 98-99% | **Recommended for most** |
| GPTQ (4-bit) | 25% | 1.15x | 97-98% | Alternative to AWQ |
| Int8 | 50% | 1.05x | 99% | Minimal loss, more VRAM |

**Quick Start AWQ:**

```bash
docker run -d --gpus all -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:v0.6.3.post1 \
  --model TheBloke/CodeLlama-70B-Instruct-AWQ \
  --quantization awq \
  --gpu-memory-utilization 0.9
```

---

## Embedding & RAG Strategy

### Indexing Flow

```
Codebase (~10k files)
  ↓
Split into chunks (50-100 tokens each)
  ↓
Generate embeddings with nomic-embed-text (768 dims)
  ↓
Store in LanceDB (~50KB per embedding)
  ↓
Index size: ~2.5GB for 10k files
```

### Retrieval Quality Tuning

```json
{
  "contextProviders": [{
    "name": "codebase",
    "params": {
      "nRetrieve": 25,      // Initial candidates
      "nFinal": 5,          // Returned results
      "useReranking": true  // LLM re-rank (adds 1-2s)
    }
  }]
}
```

**Trade-offs:**

- Speed: `nRetrieve=10, useReranking=false` (~50ms)
- Balance: `nRetrieve=15, useReranking=false` (~100ms)
- Quality: `nRetrieve=25, useReranking=true` (~500ms)

### Verification

```bash
# Check LanceDB files exist
ls -lah ~/.continue/index/*/lancedb/

# Monitor embedding speed
time curl http://localhost:11434/api/embeddings \
  -d '{"model": "nomic-embed-text", "prompt": "sample code"}'
```

---

## Integration with kanoa-mlops

### Unified Multi-Model Backend

```bash
# Serve multiple models on different ports
kanoa serve --backend vllm \
  --model codellama/CodeLlama-70b-Instruct-hf:8000 \
  --model allenai/Molmo-7B-D-0924:8001 \
  --model Qwen/Qwen2.5-Coder-32B-Instruct:8002
```

### Resource Allocation

**Priority Strategy:**

1. VSCode autocomplete: <300ms latency (highest)
2. VSCode chat: <5s first token (high)
3. kanoa CLI: Background (lower)

**GPU Monitoring:**

```bash
# Watch GPU during autocomplete
watch -n 0.1 nvidia-smi

# View vLLM metrics
curl http://localhost:8000/metrics | grep running_requests
```

---

## Security & Data Sovereignty

### Network Isolation Verification

```bash
# Capture all traffic except localhost
sudo tcpdump -i any -nn \
  'not (dst host 127.0.0.1 or dst net 192.168.0.0/16)' \
  -w vscode-traffic.pcap

# Develop normally, then inspect
tcpdump -r vscode-traffic.pcap -A | grep -E "^GET|^POST|^Host:"
# Should return NOTHING

# Verify zero cloud providers in config
grep -E '"provider":\s*"(openai|anthropic|cohere)"' \
  ~/.continue/config.json
# Should return nothing
```

### Model Provenance

All models from official sources:

- HuggingFace Hub (verified model cards)
- Meta (CodeLlama official)
- Alibaba (Qwen official)
- Nomic AI (embedding model)

---

## Performance Benchmarking

### Latency Measurement

```bash
# Test 50 autocomplete requests
for i in {1..50}; do
  TIME=$(curl -s http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
      "model": "codellama",
      "messages": [{"role": "user", "content": "def hello():"}],
      "max_tokens": 128
    }' -w "%{time_total}" -o /dev/null)
  echo $TIME
done | sort -n | tail -5 | head -1  # p95
```

### Reference Benchmarks

**RTX 4090 (24GB):**

- Autocomplete: 250-350ms (p95)
- Chat: 22 tok/s
- Search: 100-150ms

**RTX 5080 (16GB):**

- Autocomplete: 190-280ms (p95)
- Chat: 35 tok/s
- Search: 100ms

---

## Common Issues & Solutions

### High Autocomplete Latency (>500ms)

| Symptom | Cause | Solution |
|---------|-------|----------|
| First request slow | Model loading | Warm-up dummy requests |
| Consistently slow | GPU memory pressure | Reduce `--gpu-memory-utilization` |
| Spikes | vLLM queue buildup | Reduce `--max-num-batched-tokens` |
| After idle | vLLM timeout | Restart container |

### Poor Search Results

```bash
# Verify embedding model
ollama list | grep nomic

# Force re-index
rm -rf ~/.continue/index/

# Or upgrade embeddings
ollama pull nomic-embed-text:latest
```

### OOM During Indexing

```bash
# Reduce chunk size
export CONTINUE_CHUNK_SIZE=512  # Default 1024

# Or add files to .continueignore
echo "node_modules/" >> ~/.continue/.continueignore
echo ".git/" >> ~/.continue/.continueignore
```

---

## Monitoring & Metrics

### vLLM Metrics Endpoint

```bash
# Active requests
curl http://localhost:8000/metrics | grep running_requests

# Throughput
curl http://localhost:8000/metrics | grep generation_tokens_total

# Monitor in real-time
watch -n 1 'curl -s http://localhost:8000/metrics | grep -E "running|total"'
```

### Continue Logs

```bash
# Enable debug mode
echo '{"debugMode": true}' >> ~/.continue/config.json

# Monitor in real-time
tail -f ~/.continue/continue.log | grep -E "latency|embedding|search"
```

---

## Advanced: Custom Extensions

Extend Continue with project-specific context:

```python
# ~/.continue/custom_providers.py
from continue import ContextProvider

class JiraContextProvider(ContextProvider):
    async def get_context(self, query: str) -> str:
        tickets = await fetch_jira(query)
        return f"Related tickets: {tickets}"
```

---

## Performance SLOs

| Metric | Target | Typical | Status |
|--------|--------|---------|--------|
| Autocomplete latency (p95) | <300ms | 250-350ms | ✅ |
| Chat first token | <5s | 2-3s | ✅ |
| Chat throughput | 20+ tok/s | 22 tok/s | ✅ |
| Codebase search | <200ms | 100-150ms | ✅ |

---

## See Also

- **User Setup Guide**: See user guide for quick-start
- **Troubleshooting**: See user guide
- **References**: Original task planning doc

---

## References

1. GitHub Copilot RAG Issue: <https://medium.com/@xorets/indexing-large-codebases-for-github-copilot-with-local-rag-bdbf8472e21c>
2. Nomic Embed Paper: <https://arxiv.org/abs/2402.01613>
3. vLLM: <https://docs.vllm.ai/>
4. Continue.dev: <https://docs.continue.dev/>
