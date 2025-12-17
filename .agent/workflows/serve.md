---
description: Serve local AI backend services (Ollama, vLLM, Monitoring)
---

# Local Service Management

Manage local AI infrastructure (Ollama, Monitoring) using either the `kanoa` CLI or `make` targets.

## Setup

Ensure you have installed the `kanoa-mlops` plugin:

```bash
pip install -e .
```

## Using the CLI

### Start Services

```bash
# // turbo
kanoa mlops serve all         # Start all services

# // turbo
kanoa mlops serve ollama      # Start Ollama only

# // turbo
kanoa mlops serve monitoring  # Start Monitoring only
```

### Stop Services

```bash
# // turbo
kanoa mlops stop              # Stop all services

# // turbo
kanoa mlops stop ollama       # Stop Ollama only

# // turbo
kanoa mlops stop monitoring   # Stop Monitoring only
```

### Restart Services

```bash
# // turbo
kanoa mlops restart ollama      # Restart Ollama

# // turbo
kanoa mlops restart monitoring  # Restart Monitoring
```

## Using Make Targets

Alternatively, use make directly:

```bash
# Start
make serve-ollama
make serve-monitoring

# Stop
make stop-ollama
make stop-monitoring
make stop-all

# Restart
make restart-ollama
make restart-monitoring
```

## Service URLs

After starting services:

| Service | URL | Credentials |
|---------|-----|-------------|
| Ollama | <http://localhost:11434> | N/A |
| Grafana | <http://localhost:3000> | admin/admin |
| Prometheus | <http://localhost:9090> | N/A |

## Architecture

```
CLI (kanoa)          Makefile           Docker Compose
    │                    │                    │
    └──► delegates ──►   │   ──► executes ──► │
                         │                    │
  kanoa mlops serve ollama     │                    │
         │               │                    │
         └───────►  make serve-ollama         │
                         │                    │
                         └──────────► docker compose up -d
```

**Single source of truth**: All logic lives in the Makefile. CLI and workflows just delegate.
