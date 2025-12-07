---
description: Serve local AI backend services (Ollama, vLLM, Monitoring)
---

# Serving Local Infrastructure

You can manage the local AI infrastructure (Ollama, vLLM, Monitoring) using the `kanoa` CLI (requires `kanoa-mlops` plugin installed).

## Setup

Ensure you have installed the `kanoa-mlops` plugin:

```bash
pip install -e .
```

## Quick Start

### Start Everything

```bash
# // turbo
kanoa serve all
```

### Start Specific Service

```bash
# // turbo
kanoa serve ollama
```

```bash
# // turbo
kanoa serve monitoring
```

## Stopping Services

To stop all running services:

```bash
# // turbo
kanoa stop
```
