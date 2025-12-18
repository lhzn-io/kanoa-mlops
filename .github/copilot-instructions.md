---
description: Consult the GitHub Copilot instructions for project-specific guidelines
---
# Copilot Instructions

For detailed persona, commands, and boundaries, consult [agents.md](../agents.md).

## Core Directives

0.  **Conda Environment**:
    *   **ALWAYS** use the correct conda environment for the repository you are working in.
    *   For `kanoa-mlops`: Use `conda run -n kanoa-mlops` for all Python commands, or activate with `conda activate kanoa-mlops` first.
    *   **NEVER** run Python/pip/pytest commands in the base environment or without the correct environment.
    *   Examples:
        *   `conda run -n kanoa-mlops python script.py`
        *   `conda run -n kanoa-mlops pytest tests/`
        *   `conda run -n kanoa-mlops pip install package`

## Project Context

`kanoa-mlops` is the infrastructure companion to the `kanoa` library.
It provides the "brawn" (compute, storage, serving) for local AI interpretation.

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
