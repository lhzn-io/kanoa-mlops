# Agent Platform Setup Guide

This guide covers setting up autonomous agents using **OpenHands** with `kanoa-mlops` infrastructure.

## What is OpenHands?

[OpenHands](https://github.com/All-Hands-AI/OpenHands)  is an open-source platform for autonomous AI software engineers. It executes code, runs shell commands, and modifies files to complete complex coding tasks.

In `kanoa-mlops`, OpenHands runs as a containerized service that connects to your local LLM inference backend (Ollama or vLLM).

---

## macOS Setup (Apple Silicon)

For macOS users, we **strongly recommend** using **OrbStack** instead of Docker Desktop.

### Why OrbStack?

- **Performance**: Faster file system performance (critical for agents that read/write code heavily).
- **Efficiency**: Significantly lower CPU and battery usage.
- **Network**: Seamless networking between containers and host services.

### 1. Install OrbStack

```bash
brew install orbstack
```

Then open the OrbStack app to complete the setup.

### 2. Architecture Overview

We use a hybrid architecture for optimal performance on macOS M-series chips:

1. **Inference (Native)**: Ollama runs natively on macOS to leverage Metal (GPU) acceleration.
2. **Agent (Docker)**: OpenHands runs in a Docker container (via OrbStack) to provide a sandboxed environment for code execution.

To connect them, OpenHands needs to reach the host's Ollama service. Docker/OrbStack provides a special DNS name for this: `host.docker.internal`.

### 3. Start OpenHands

Using the CLI:

```bash
kanoa mlops serve openhands
```

This will:

1. Start the OpenHands container.
2. Mount your `~/.openhands` directory for state persistence.
3. Mount a workspace directory (default: `$PWD/workspace` or defined by config).

### 4. Configure OpenHands

Once running, open [http://localhost:3000](http://localhost:3000).

1. **Settings** (Gear Icon):
    - **LLM Provider**: `Ollama`
    - **Base URL**: `http://host.docker.internal:11434` (Crucial: use `host.docker.internal`, NOT `localhost`)
    - **Model**: `gemma3:4b` (or whatever model you have pulled in Ollama)

---

## Linux / Windows Setup

For Linux and Windows (WSL2), the setup is similar, but you typically run Docker directly.

### Network Configuration

If running Ollama natively on the host:

- **Base URL**: `http://host.docker.internal:11434` (Windows/Mac)
- **Linux**: You may need to add `--add-host=host.docker.internal:host-gateway` to the specific Docker command if not using the provided `docker-compose` template (our template includes this automatically).

---

## Performance Considerations

### Agent Overhead

OpenHands itself is an orchestration layer. It runs Python/Node.js logic to parse LLM outputs and execute commands. The computational overhead is minimal compared to LLM inference.

### File System Speed

Agents perform many file operations (linting, searching, reading files).
- **macOS (Docker Desktop)**: File mounts can be slow (virtiofs helps, but overhead exists).
- **macOS (OrbStack)**: Highly optimized file sharing, near-native speed. **Recommended.**
- **Linux**: Native speed.

---

## Troubleshooting

### "Connection Refused" to LLM

* Ensure Ollama is running (`ollama serve` or `kanoa mlops serve ollama`).
- Ensure you are using `http://host.docker.internal:11434` in OpenHands settings, not `localhost`. Inside the container, `localhost` refers to the container itself, not your Mac.

### "Workspace Not Wraitable"

* Check permissions of the `workspace` directory. OpenHands runs as a non-root user (usually UID 1000) inside the container.
- Ensure your local user has read/write access to the mounted volume.

### Models

* Agents require capability-strong models. Small models (like 4B) might struggle with complex multi-step tasks.
- **Recommended**: `llama3.1:70b` (if hardware allows) or `qwen2.5-coder:14b` / `gemma-2-27b` for a balance of speed and smarts.
