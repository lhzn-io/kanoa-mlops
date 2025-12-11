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

3. **Install pre-commit hooks** (Required):
    This ensures your code is linted, formatted, and tested before every commit.

    ```bash
    pre-commit install
    ```

    **What this does:**
    - **Ruff**: Lints and formats Python code
    - **ShellCheck**: Checks shell scripts
    - **Detect Secrets**: Prevents committing API keys
    - **Pytest**: Runs unit tests automatically

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

## Co-Development with `kanoa`

Since `kanoa-mlops` is the infrastructure layer for [kanoa](https://github.com/lhzn-io/kanoa), you may need to develop both simultaneously.

### Local Editable Setup

To verify your infrastructure against local changes in `kanoa` (instead of the PyPI version):

1. **Ensure sibling directory structure**:

    ```text
    ~/Projects/lhzn-io/
    ├── kanoa/
    └── kanoa-mlops/
    ```

2. **Create local requirements override**:

    ```bash
    cd kanoa-mlops
    cp requirements-local.txt.template requirements-local.txt
    ```

    *(This file is gitignored so it won't affect other users)*

3. **Install editable link**:

    ```bash
    # Activate your environment first
    conda activate kanoa-mlops

    # Install kanoa in editable mode
    pip install -r requirements-local.txt
    ```

Now, changes you make in `../kanoa` will be immediately reflected in your `kanoa-mlops` environment.

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

We use emojis sparingly to highlight important information without creating visual clutter. We prefer a "classy", structured aesthetic over a "cartoony" one.

#### Allowed Contexts

- **Warnings/Alerts**: ⚠️ for warnings, cautions, or important notes (replaces "WARNING:", "CRITICAL:", etc.)
- **Errors**: ❌ for error messages or failed states
- **Checklists**: Use `[✓]` for completed items and `[ ]` for planned/incomplete items in planning documents
- **Marketing docs (README only)**: To distinguish key features in bullet points (e.g., "- 🔒 **Privacy First**")
- **Agent Layer / CLI Output**:
  - **Allowed**: Structural symbols and minimal emojis that enhance readability (e.g., `•`, `→`, `📦` for blobs, `📄` for files).
  - **Style**: Prefer bracketed tags (e.g., `[Blob]`, `[Text]`) over heavy emoji usage.
  - **Goal**: "Classy" and "Technical", not "Playful".

#### Prohibited Contexts

- **Headers**: Do not use emojis in section headers (H1-H6). Let the words speak for themselves.
- **Success indicators**: Avoid ✅ checkmarks in prose, lists, or status messages (use `[✓]` in checklists only)
- **Code comments**: Keep comments strictly technical
- **Commit messages**: Use conventional commits (e.g., `feat:`, `fix:`) without emojis
- **Mid-sentence**: Do not put emojis in the middle of a sentence
- **Excessive decoration**: Do not use emojis as visual flair or decoration
- **"Cartoony" Emojis**: Avoid emojis that look too informal or "cute" (e.g., 🧠, 🚀, 🤖) in technical logs.

#### Checklist Convention

For planning documents and task lists:

```markdown
[✓] Completed task
[ ] Planned/incomplete task
```

**Do not use**:

- `[x]` - too harsh, prefer the elegant checkmark
- `✅` - standalone emoji, use bracketed version in checklists
- Mixed styles - be consistent within a document

#### Guidelines

- **Replace ALL CAPS with symbols**: Use ⚠️ instead of "WARNING:", "CRITICAL:", "IMPORTANT:", etc.
- **One emoji per context**: If you use ⚠️ for a warning, don't add additional emojis
- **When in doubt, omit**: Professional technical writing should default to no emojis

### 3. Infrastructure as Code Standards

#### Docker

- **Explicit Versions**: Always pin Docker image tags (e.g., `vllm/vllm-openai:v0.6.3.post1`).
- **Volume Mapping**: Use relative paths for volumes (`./data:/data`).
- **Health Checks**: All services must have health checks defined.

#### Scripts

- **Idempotency**: Scripts should be safe to run multiple times.
- **Error Handling**: Use `set -e` in bash scripts.
- **Help**: All scripts must implement a `-h` or `--help` flag.

### 4. AI Contribution Policy

`kanoa-mlops` was built with the assistance of GitHub coding agents, and we embrace the use of AI tools in development. We particularly recommend **Claude Code** for DevOps and infrastructure tasks.

However, to maintain the stability and reliability of our infrastructure, we enforce a strict **Human-in-the-Loop** policy:

1. **You Own the Code**: If you submit a PR generated by AI, you are responsible for understanding, explaining, and maintaining it. "The AI wrote it" is not a valid defense for bugs or security issues.
2. **Testing is Mandatory**: AI-generated scripts and configs must be verified. Do not rely on the AI to verify its own work.
3. **No "Vibe Coding"**: Do not submit raw, unreviewed AI output. You must review the code for style, efficiency, and correctness before submitting.
4. **Transparency**: We appreciate transparency. If a significant portion of your PR was AI-generated, feel free to mention the tools used in the PR description.

### 5. AI Agent Instructions

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
