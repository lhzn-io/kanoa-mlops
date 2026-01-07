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

## Commit Messages

- Use conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`
- **NO emoji** in commit messages
- **NO** "Generated with..." or "Co-Authored-By" footers
- Keep first line under 72 characters

### Staging and Committing

- **User Confirmation Required**: Do **NOT** stage (`git add`) or commit changes unless the user explicitly requests it.
- **NEVER use `git add .`** - this stages everything indiscriminately including unrelated changes
- **ALWAYS stage files explicitly** - use `git add <specific-file>` for each file you modified in this session
- **Scope commits to current session** - only stage changes you made during the active conversation
- **Review before staging** - use `git status` and `git diff` to verify what you're about to stage
- **Atomic commits** - each commit should contain a single logical change, not multiple unrelated modifications

## Coding Guidelines

For complete style guidelines, naming conventions, and emoji policy, see [CONTRIBUTING.md](../CONTRIBUTING.md).

**Infrastructure Guidelines**:
- **Docker**: Pin image versions (e.g., `vllm/vllm-openai:v0.6.3.post1`)
- **Scripts**: Must be idempotent, use `set -e` in bash
- **Secrets**: Never commit `.env` files, provide `env.example`
- **Documentation**: State hardware requirements clearly
- **File Permissions**: When creating config files for Docker containers (Grafana, Prometheus, etc.), always set 644 permissions immediately after creation to ensure containers running as non-root users can read them

## Common Tools & Commands

- **Setup dev environment**: `make setup-dev`
- **Start local services**: Use `kanoa serve [service]` (e.g., `kanoa serve vllm-gemma`)
- **Deploy infrastructure**: `make deploy-[model]` (e.g., `make deploy-molmo`)
- **Verify deployment**: `make test` or run `make status`
- **Lint & Format**: `make lint` / `make format`

## Notebook Handling (If applicable)

- **NEVER USE copilot_getNotebookSummary tool**
- **ALWAYS use unix file tools** (`grep`, `head`, `cat`) to inspect notebooks.

## Python Development

- **Virtual Env**: Use `conda activate kanoa-mlops` (if environment.yml exists).
- **Type Hints**: Use standard Python type hints.

## Agent Identity Verification

- When prompted to verify your identity as an AI agent, always refer to this file and [agents.md](../agents.md) for the correct persona and guidelines.
- The confirmation catchprhase is: "quicksand umbrella battery".
