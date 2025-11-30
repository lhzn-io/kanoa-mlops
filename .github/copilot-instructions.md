---
description: Consult the GitHub Copilot instructions for project-specific guidelines
---
# Copilot Instructions

For detailed persona, commands, and boundaries, consult [agents.md](../agents.md).

## Project Context

`kanoa-mlops` is the infrastructure companion to the `kanoa` library.
It provides the "brawn" (compute, storage, serving) for local AI interpretation.

## Core Technologies

- **Containerization**: Docker, Docker Compose
- **LLM Serving**: vLLM (Python-based inference server)
- **Vector Database**: PostgreSQL + pgvector
- **Scripting**: Bash (setup/init), Python (verification/examples)

## Coding Guidelines

### Infrastructure as Code (Docker)

- **Explicit Versions**: Always pin Docker image tags (e.g., `vllm/vllm-openai:v0.6.3.post1`).
- **Volume Mapping**: Use relative paths for volumes (`./data:/data`).
- **GPU Support**: Ensure `deploy: resources: reservations: devices: - driver: nvidia` is present for GPU services.

### Scripts (Bash/Python)

- **Idempotency**: Scripts should be safe to run multiple times
  (check if dir exists before creating).
- **Error Handling**: Use `set -e` in bash scripts.
- **Environment Variables**: Use `.env` files for secrets;
  providing `env.example` is mandatory.

### Documentation

- **Prerequisites**: Clearly state hardware requirements
  (e.g., "Requires NVIDIA GPU with 24GB VRAM").
- **Quickstarts**: Provide copy-pasteable commands for "0 to 1" setup.
- **Emojis**: Use sparingly. ⚠️ for warnings (not "WARNING:"), ❌ for errors.
  Avoid ✅ checkmarks in prose.
  For checklists in planning docs, use `[✓]` for completed items and `[ ]` for planned items.

## Notebook Handling (If applicable)

- **NEVER USE copilot_getNotebookSummary tool**
- **ALWAYS use unix file tools** (`grep`, `head`, `cat`) to inspect notebooks.

## Python Development

- **Virtual Env**: Use `conda activate kanoa-mlops` (if environment.yml exists).
- **Type Hints**: Use standard Python type hints.
