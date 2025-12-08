# Quick Start: Adding kanoa-mlops to Your Project

This guide is for data scientists adding local AI capabilities to an existing project.

## Prerequisites

- Python 3.11+
- Docker (with GPU support for NVIDIA)
- ~10GB disk space for models

## Installation

```bash
pip install kanoa-mlops
```

Or with optional dependencies:

```bash
# For GCP cloud deployment
pip install kanoa-mlops[gcp]

# For development (linting, testing)
pip install kanoa-mlops[dev]

# Everything
pip install kanoa-mlops[all]
```

## Initialize Your Project

Scaffold the docker templates into your project:

```bash
cd your-project/
kanoa init mlops --dir .
```

This creates:
```
your-project/
└── docker/
    ├── ollama/           # Ollama server config
    ├── vllm/             # vLLM configs (Molmo, Gemma)
    └── monitoring/       # Prometheus + Grafana
```

## Start Local Inference

### Ollama (Easiest)

```bash
kanoa serve ollama
# → Ollama running at http://localhost:11434
```

### vLLM (Fastest)

For maximum performance on NVIDIA GPUs:

```bash
cd docker/vllm
docker compose -f docker-compose.molmo.yml up -d
# → vLLM running at http://localhost:8000
```

## Use with kanoa

```python
from kanoa import Interpreter

# Auto-detects local backend
interpreter = Interpreter(backend="local")

# Interpret your plot
result = interpreter.interpret(fig)
print(result.text)
```

## Monitoring (Optional)

```bash
kanoa serve monitoring
# → Grafana: http://localhost:3000 (admin/admin)
# → Prometheus: http://localhost:9090
```

## CLI Commands Reference

| Command | Description |
|---------|-------------|
| `kanoa init mlops --dir .` | Scaffold docker templates |
| `kanoa serve ollama` | Start Ollama server |
| `kanoa serve monitoring` | Start monitoring stack |
| `kanoa stop` | Stop all services |
| `kanoa status` | Show config and service status |

## Next Steps

- [Local GPU Setup Guide](local-gpu-setup.md) — Platform-specific instructions
- [Monitoring Guide](../monitoring/README.md) — Dashboard deep-dive
- [vLLM Tuning](../docker/vllm/README.md) — Model configuration

## Troubleshooting

### "kanoa-mlops not initialized"

Run `kanoa init mlops --dir .` first.

### Docker GPU not detected

Ensure NVIDIA Container Toolkit is installed:
```bash
nvidia-smi  # Should show your GPU
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi  # Should work
```

### Port already in use

Stop existing services: `kanoa stop` or check with `docker ps`.
