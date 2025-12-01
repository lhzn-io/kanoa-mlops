# Contributing to kanoa-mlops

We welcome contributions! Please follow these guidelines to ensure a smooth process.

## Getting Started

1. **Fork the repository** and clone it locally.
2. **Install dependencies**:
    - **Docker & Docker Compose**: Required for running infrastructure.
    - **NVIDIA Container Toolkit**: Required for GPU support.
    - **Python Environment**:

        ```bash
        conda env create -f environment.yml
        conda activate kanoa-mlops
        ```

3. **Install pre-commit hooks** (if applicable):

    ```bash
    pre-commit install
    ```

4. **Create a branch** for your feature or fix:

    ```bash
    git checkout -b feature/my-awesome-infra
    ```

5. **Renaming files**: Use `git mv` to preserve file history:

    ```bash
    # ✅ Correct - preserves git history
    git mv old_name.sh new_name.sh

    # ❌ Incorrect - breaks git history
    rm old_name.sh
    touch new_name.sh
    ```

## Style Guide

This section outlines the coding, documentation, and aesthetic standards for the `kanoa-mlops` repository.

### 0. Tooling

We use [Ruff](https://docs.astral.sh/ruff/) for Python linting and formatting (replaces black, isort, flake8).

```bash
# Format code
ruff format .

# Check for issues (auto-fix where possible)
ruff check --fix .

# Run all pre-commit hooks
pre-commit run --all-files
```

### 1. Naming Conventions

#### Project Name

- **Always** refer to the project as `kanoa-mlops` (lowercase).
- **Do not** use "Kanoa-MLOps" or "Kanoa MLOps".

#### Infrastructure

- **Docker Services**: `kebab-case` (e.g., `vllm-server`, `pgvector-db`)
- **Scripts**: `kebab-case` (e.g., `setup-vllm.sh`)
- **Env Vars**: `UPPER_CASE` (e.g., `MODEL_NAME`)

### 2. Emoji Policy

We use emojis sparingly to highlight important information.

- **Warnings/Alerts**: ⚠️ for warnings (replaces "WARNING:")
- **Errors**: ❌ for error messages
- **Checklists**: Use `[✓]` for completed items and `[ ]` for planned items

### 3. Infrastructure as Code Standards

#### Docker

- **Explicit Versions**: Always pin Docker image tags (e.g., `vllm/vllm-openai:v0.6.3.post1`).
- **Volume Mapping**: Use relative paths for volumes (`./data:/data`).
- **Health Checks**: All services must have health checks defined.

#### Scripts

- **Idempotency**: Scripts should be safe to run multiple times.
- **Error Handling**: Use `set -e` in bash scripts.
- **Help**: All scripts must implement a `-h` or `--help` flag.

### 4. AI Agent Instructions

If you are an AI assistant (GitHub Copilot, Antigravity, etc.):

1. **Read this file first.**
2. **Respect the `kanoa-mlops` lowercase branding.**
3. **Prioritize stability and reproducibility.**
4. **Keep responses concise.**

## Testing

We use a combination of smoke tests and integration scripts.

### 1. Smoke Tests (Quick)

Run the quickstart scripts to verify basic functionality:

```bash
python examples/quickstart-molmo.py
```

### 2. Infrastructure Tests

Verify Docker containers are healthy:

```bash
docker compose -f docker/vllm/docker-compose.yml ps
```

## Pull Requests

1. Ensure all scripts run without errors.
2. Update documentation if you change infrastructure (ports, volumes, env vars).
3. Describe your changes clearly in the PR description.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
