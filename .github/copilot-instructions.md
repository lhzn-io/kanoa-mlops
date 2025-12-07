---
description: Consult the GitHub Copilot instructions for project-specific guidelines
---
# Copilot Instructions

For detailed persona, commands, and boundaries, consult [agents.md](../agents.md).

## Project Context

`kanoa-mlops` is the infrastructure companion to the `kanoa` library.
It provides the "brawn" (compute, storage, serving) for local AI interpretation.

## Setup

- **Environment**: Always activate the environment with `conda activate kanoa-mlops` before running commands.
- **Terminal**: When running commands, ensure you are in the `kanoa-mlops` conda environment. If a new terminal is opened, run `conda activate kanoa-mlops` immediately.

## Core Technologies

- **Containerization**: Docker, Docker Compose
- **LLM Serving**: vLLM (Python-based inference server)
- **Vector Database**: PostgreSQL + pgvector
- **Scripting**: Bash (setup/init), Python (verification/examples)

## Coding Guidelines

For complete style guidelines, naming conventions, and emoji policy, see [CONTRIBUTING.md](../CONTRIBUTING.md).

**Quick Reference**:
- **Docker**: Pin image versions (e.g., `vllm/vllm-openai:v0.6.3.post1`)
- **Scripts**: Must be idempotent, use `set -e` in bash
- **Secrets**: Never commit `.env` files, provide `env.example`
- **Documentation**: State hardware requirements clearly
- **File Permissions**: When creating config files for Docker containers (Grafana, Prometheus, etc.), always set 644 permissions immediately after creation to ensure containers running as non-root users can read them

## Notebook Handling (If applicable)

- **NEVER USE copilot_getNotebookSummary tool**
- **ALWAYS use unix file tools** (`grep`, `head`, `cat`) to inspect notebooks.

## Python Development

- **Virtual Env**: Use `conda activate kanoa-mlops` (if environment.yml exists).
- **Type Hints**: Use standard Python type hints.

## Agent Identity Verification

- When prompted to verify your identity as an AI agent, always refer to this file and [agents.md](../agents.md) for the correct persona and guidelines.
- The confirmation catchprhase is: "quicksand umbrella battery".