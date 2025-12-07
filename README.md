# kanoa-mlops

**The infrastructure backbone for privacy-first AI interpretation.**

`kanoa-mlops` provides the local compute layer for the [`kanoa`](https://github.com/lhzn-io/kanoa) library — enabling you to interpret data science outputs (plots, tables, models) using state-of-the-art vision-language models, all running on your own hardware.

- 🔒 **Privacy First** — Your data never leaves your machine
- 🎯 **Multiple Backends** — Choose Ollama (easy), vLLM (fast), or cloud GPU (scalable)
- 📊 **Full Observability** — Prometheus + Grafana + NVIDIA DCGM monitoring stack
- 🔌 **Seamless Integration** — Extends `kanoa` CLI with `serve` and `stop` commands

## Quick Start

### The Fast Path (Ollama)

Get running in under 2 minutes with Ollama — no model downloads required:

```bash
# Install kanoa-mlops as a plugin
pip install -e .

# Start Ollama (pulls model on first run)
kanoa serve ollama

# That's it! Use with kanoa
```

### The Performance Path (vLLM)

For maximum throughput on NVIDIA GPUs:

```bash
# Download model (~14GB)
./scripts/download-models.sh molmo-7b-d

# Start vLLM server
docker compose -f docker/vllm/docker-compose.molmo.yml up -d

# Verify
curl http://localhost:8000/health
```

## Choose Your Backend

| Backend | Best For | Hardware | Throughput | Setup |
| :--- | :--- | :--- | :--- | :--- |
| **Ollama** | Getting started, CPU/Apple Silicon | Any | ~15 tok/s | `kanoa serve ollama` |
| **vLLM** | Production, maximum speed | NVIDIA GPU | ~31 tok/s | Docker Compose |
| **GCP L4** | No local GPU, team sharing | Cloud | ~25 tok/s | Terraform |

### Ollama (Easiest)

Perfect for development, VSCode integration, and broader hardware support.

```bash
kanoa serve ollama
# → Ollama running at http://localhost:11434
```

Supports: Gemma 3 (4B/12B), Llama 3, Mistral, and [many more](https://ollama.com/library).

### vLLM (Fastest)

Optimized inference with CUDA, batching, and OpenAI-compatible API.

```bash
# Molmo 7B (best for vision)
docker compose -f docker/vllm/docker-compose.molmo.yml up -d

# Gemma 3 12B (best for reasoning)
docker compose -f docker/vllm/docker-compose.gemma.yml up -d
```

Endpoints: `http://localhost:8000/v1/chat/completions`

### GCP Cloud GPU (Scalable)

For users without local GPUs or production workloads.

```bash
cd infrastructure/gcp
cp terraform.tfvars.example terraform.tfvars  # Configure
terraform apply
```

Features: L4 GPU (~$0.70/hr), auto-shutdown, IP-restricted firewall.

## Using with kanoa

Once a backend is running, `kanoa` automatically detects it:

```python
from kanoa import Interpreter

# Uses local backend (Ollama or vLLM) automatically
interpreter = Interpreter(backend="local")

# Interpret your matplotlib figure
result = interpreter.interpret(fig)
print(result.text)
```

Or explicitly configure:

```python
from kanoa.backends import VLLMBackend

backend = VLLMBackend(
    api_base="http://localhost:8000/v1",
    model="allenai/Molmo-7B-D-0924"
)
```

## CLI Integration

`kanoa-mlops` extends the `kanoa` CLI with infrastructure commands:

```bash
# Start services
kanoa serve ollama      # Start Ollama
kanoa serve monitoring  # Start Prometheus + Grafana
kanoa serve all         # Start everything

# Stop all services
kanoa stop
```

## Monitoring Stack

Real-time observability for your inference workloads:

```bash
kanoa serve monitoring
# → Grafana:    http://localhost:3000 (admin/admin)
# → Prometheus: http://localhost:9090
```

**Dashboard Features:**

| Section | Metrics |
| :--- | :--- |
| Token Odometers | Cumulative prompt/generated tokens, request counts |
| Latency | TTFT and TPOT percentiles (p50, p90, p95, p99) |
| GPU Hardware | Temperature, power, utilization, memory (via NVIDIA DCGM) |
| vLLM Performance | KV cache usage, request queue, throughput |

See [monitoring/README.md](monitoring/README.md) for full documentation.

## Project Structure

```text
kanoa-mlops/
├── kanoa_mlops/           # CLI plugin (serve, stop commands)
│   └── plugin.py
├── docker/
│   ├── vllm/              # vLLM Docker Compose configs
│   └── ollama/            # Ollama Docker Compose config
├── monitoring/
│   ├── grafana/           # Dashboards and provisioning
│   └── prometheus/        # Scrape configs
├── infrastructure/
│   └── gcp/               # Terraform for cloud GPU
├── examples/              # Jupyter notebooks
├── scripts/               # Model download utilities
└── tests/integration/     # Backend integration tests
```

## Performance

### Benchmark Results (RTX 5080 16GB eGPU)

| Model | Backend | Throughput | Notes |
| :--- | :--- | :--- | :--- |
| **Molmo 7B** | vLLM | **31.1 tok/s** | Best for vision tasks |
| Gemma 3 12B | vLLM | 10.3 tok/s | Strong text reasoning |
| Gemma 3 4B | Ollama | ~15 tok/s | Good balance |

**Why vLLM is faster:**

- Continuous batching for concurrent requests
- PagedAttention for efficient KV cache
- FP8 quantization support

## Supported Models

### Vision-Language Models

| Model | Size | vLLM | Ollama | Notes |
| :--- | :--- | :--- | :--- | :--- |
| Molmo 7B | 14GB | [✓] | — | Best vision performance |
| Gemma 3 | 4B-27B | [✓] | [✓] | Excellent all-rounder |
| LLaVa-Next | 7B-34B | [ ] | [✓] | Planned for vLLM |

### Text-Only Models (via Ollama)

Llama 3.1, Mistral, Qwen 2.5, and [100+ more](https://ollama.com/library).

## Hardware Compatibility

| Platform | Status | Notes |
| :--- | :--- | :--- |
| NVIDIA RTX (Desktop/Laptop) | [✓] Verified | RTX 3080+ recommended |
| NVIDIA RTX (eGPU) | [✓] Verified | TB3/TB4 bandwidth sufficient |
| Apple Silicon | [✓] Ollama | M1/M2/M3 via Ollama |
| GCP L4 GPU | [✓] Verified | 24GB VRAM, ~$0.70/hr |
| Intel/AMD GPU | — | Not supported |

## Prerequisites

- **Docker** and Docker Compose
- **NVIDIA GPU + Drivers** (for vLLM)
- **Python 3.11+**

**WSL2 Users**: Install NVIDIA drivers on Windows, not inside WSL. See [docs/source/wsl2-gpu-setup.md](docs/source/wsl2-gpu-setup.md).

## Roadmap

- [✓] Ollama integration (Dec 2025)
- [✓] CLI plugin system (Dec 2025)
- [✓] NVIDIA DCGM monitoring (Dec 2025)
- [ ] PostgreSQL + pgvector for RAG
- [ ] Kubernetes / Helm charts
- [ ] NVIDIA Jetson support

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

> **Pro Tip**: We find **Claude Code** to be an excellent DevOps buddy for this project. If you use AI tools, just remember our [Human-in-the-Loop policy](CONTRIBUTING.md#4-ai-contribution-policy).

## License

MIT License — see [LICENSE](LICENSE) for details.
