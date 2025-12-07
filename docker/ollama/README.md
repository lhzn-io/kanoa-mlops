# Kanoa MLOps: Ollama Setup

This directory contains the Docker Compose configuration for running [Ollama](https://ollama.com/) with GPU support.

## Usage

Use the Makefile in the root directory:

```bash
make serve-ollama
```

This will start the Ollama service on port `11434`.

## Managing Models

### Pulling Models

You can pull models directly using the `ollama` CLI inside the container:

```bash
docker compose -f docker/ollama/docker-compose.ollama.yml exec ollama ollama pull llama3
docker compose -f docker/ollama/docker-compose.ollama.yml exec ollama ollama pull gemma3:4b
```

### Using Hugging Face Cache

The host's `~/.cache/huggingface` directory is mounted to `/root/.cache/huggingface` (read-only) inside the container. This allows you to access models you've already downloaded, but note that **Ollama requires models in GGUF format**.

If you have raw weights (SafeTensors/bin) in your HF cache, you cannot use them directly with `ollama run`. You must first convert them to GGUF using `llama.cpp` or simply pull the GGUF version directly via `ollama pull` (recommended).

## Compatibility

- **Supported**: Gemma 3 (1B, 4B, 12B, 27B), Llama 3, Mistral, etc.
- **Not Supported Directly**: AllenAI Molmo (requires vLLM, use `make deploy-molmo` or `make serve-molmo`).
