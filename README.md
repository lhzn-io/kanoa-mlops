# kanoa-mlops

**The infrastructure backbone for privacy-first AI interpretation.**

[![Tests](https://github.com/lhzn-io/kanoa-mlops/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/lhzn-io/kanoa-mlops/actions/workflows/pre-commit.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

`kanoa-mlops` provides the local compute layer for the [`kanoa`](https://github.com/lhzn-io/kanoa) library — enabling you to interpret data science outputs (plots, tables, models) using state-of-the-art vision-language models, all running on your own hardware.

- **Privacy First** — Your data never leaves your machine
- **Multiple Backends** — Choose Ollama (easy), vLLM (fast), or cloud GPU (scalable)
- **Full Observability** — Prometheus + Grafana + NVIDIA DCGM monitoring stack
- **Seamless Integration** — Extends `kanoa` CLI with `serve` and `stop` commands

## Installation

### For Users (add to your project)

```bash
# Base install (local inference with Ollama/vLLM)
pip install kanoa-mlops

# With GCP support (for cloud deployment)
pip install kanoa-mlops[gcp]

# Everything (GCP + dev tools)
pip install kanoa-mlops[all]
```

### For Contributors

```bash
# Clone and install in editable mode
git clone https://github.com/lhzn-io/kanoa-mlops.git
cd kanoa-mlops

# Base environment (no GCP tools)
conda env create -f environment.yml
conda activate kanoa-mlops

# Or with GCP infrastructure tools (terraform, gcloud)
conda env create -f environment-gcp.yml
conda activate kanoa-mlops-gcp
```

## Quick Start

### Option A: Add to Existing Project (pip)

For users adding local AI to a science project:

```bash
# Install the package
pip install kanoa-mlops

# Initialize docker templates in your project
kanoa init mlops --dir .

# Start Ollama
kanoa serve ollama

# Done! Your project now has local AI
```

### Option B: Clone Repository (full setup)

For contributors or those wanting the full monitoring stack:

```bash
# Clone the repo
git clone https://github.com/lhzn-io/kanoa-mlops.git
cd kanoa-mlops

# Start Ollama (pulls model on first run)
kanoa serve ollama

# Start monitoring (optional)
kanoa serve monitoring
```

### The Performance Path (vLLM)

For maximum throughput on NVIDIA GPUs:

```bash
# Download model (~14GB)
huggingface-cli download allenai/Molmo-7B-D-0924

# Start vLLM server
docker compose -f docker/vllm/docker-compose.molmo.yml up -d

# Verify
curl http://localhost:8000/health
```

#### Advanced Models

For the Olmo3 32B Think model (requires significant GPU memory):

```bash
# Download model (~32GB) - requires Hugging Face authentication for gated models
huggingface-cli download allenai/Olmo-3-32B-Think

# Start vLLM server (optimized for Jetson Thor with 128GB Unified Memory)
make serve-olmo3-32b

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
# Initialize (for pip users)
kanoa init mlops --dir .  # Scaffold docker templates

# Start services
kanoa serve ollama       # Start Ollama
kanoa serve monitoring   # Start Prometheus + Grafana
kanoa serve all          # Start everything

# Stop services
kanoa stop               # Stop all services
kanoa stop ollama        # Stop specific service

# Status
kanoa status             # Show config and running services

# Restart services
kanoa restart ollama     # Restart Ollama
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
| Olmo 3 32B Think | 32GB | [✓] | — | Advanced reasoning, code generation |
| LLaVa-Next | 7B-34B | [ ] | [✓] | Planned for vLLM |

### Text-Only Models (via Ollama)

Llama 3.1, Mistral, Qwen 2.5, and [100+ more](https://ollama.com/library).

## Hardware Compatibility

| Platform | Status | Notes |
| :--- | :--- | :--- |
| NVIDIA RTX (Desktop/Laptop) | [✓] Verified | RTX 3080+ recommended |
| NVIDIA RTX (eGPU) | [✓] Verified | TB3/TB4 bandwidth sufficient |
| NVIDIA Jetson Thor | [✓] Verified | 128GB Unified Memory, Blackwell GPU |
| Apple Silicon | [✓] Ollama | M1/M2/M3 via Ollama |
| GCP L4 GPU | [✓] Verified | 24GB VRAM, ~$0.70/hr |
| Intel/AMD GPU | — | Not supported |

## Development Setup

### Plugin Architecture

`kanoa-mlops` is a **plugin** for the `kanoa` CLI. The `kanoa` package provides the CLI framework, and `kanoa-mlops` registers additional commands (`serve`, `stop`, `restart`) via Python entry points.

```text
kanoa (CLI)  ──loads──►  kanoa-mlops (plugin)
     │                        │
     └── entry points ◄───────┘
```

### Co-Development Setup

To develop both packages simultaneously, install both in **editable mode**:

```bash
# Clone both repos
git clone https://github.com/lhzn-io/kanoa.git
git clone https://github.com/lhzn-io/kanoa-mlops.git

# Create and activate environment
conda env create -f kanoa-mlops/environment.yml
conda activate kanoa-mlops

# Install BOTH packages in editable mode
pip install -e ./kanoa           # Provides 'kanoa' CLI
pip install -e ./kanoa-mlops     # Registers plugin commands

# Verify
kanoa --help  # Should show: serve, stop, restart
```

> **Why both?** The `kanoa` package provides the CLI entry point. The `kanoa-mlops` package registers its commands as plugins. Both must be installed for the full CLI to work.

### Quick Reinstall

If you switch conda environments or commands are missing:

```bash
pip install -e /path/to/kanoa -e /path/to/kanoa-mlops
```

## Prerequisites

- **Docker** and Docker Compose
- **NVIDIA GPU + Drivers** (for vLLM)
- **Python 3.11+**

**WSL2/eGPU Users**: See the [Local GPU Setup Guide](docs/source/local-gpu-setup.md) for platform-specific instructions.

## Roadmap

- [✓] Ollama integration (Dec 2025)
- [✓] CLI plugin system (Dec 2025)
- [✓] NVIDIA DCGM monitoring (Dec 2025)
- [✓] NVIDIA Jetson Thor support (Dec 2025)
- [ ] PostgreSQL + pgvector for RAG
- [ ] Kubernetes / Helm charts
- [ ] NVIDIA Jetson Orin support

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

- **Adding New Models?** Check out the [Model Contribution Guide](docs/adding-models.md).

> **Pro Tip**: We find **Claude Code** to be an excellent DevOps buddy for this project. If you use AI tools, just remember our [Human-in-the-Loop policy](CONTRIBUTING.md#4-ai-contribution-policy).

## License

MIT License — see [LICENSE](LICENSE) for details.
