# kanoa-mlops Docker Templates

These are reference Docker Compose configurations for running local AI services.

## Included Services

### Ollama (`ollama/`)

- **docker-compose.ollama.yml** - Ollama server with GPU support
- **exporter/** - Prometheus metrics exporter for Ollama

### vLLM (`vllm/`)

- **docker-compose.molmo.yml** - Molmo-7B vision model with 4-bit quantization
- **docker-compose.gemma3.yml** - Gemma 3 text model
- **docker-compose.olmo3.yml** - OLMo 3 text model
- **docker-compose.nemotron3-nano.yml** - NVIDIA Nemotron 3 Nano 30B (Mamba-2 MoE)
- **docker-compose.llama-scout.yml** - Llama 4 Scout 17B MoE
- **docker-compose.mixtral.yml** - Mixtral 8x7B MoE

### Monitoring (`monitoring/`)

- **docker-compose.yml** - Prometheus + Grafana stack

## Usage

After running `kanoa mlops init mlops`, use the kanoa CLI:

```bash
# Start Ollama
kanoa mlops serve ollama

# Start monitoring
kanoa mlops serve monitoring

# Stop all services
kanoa mlops stop
```

## Full Configuration

For the complete monitoring dashboards, Prometheus configs, and Grafana provisioning,
clone the full kanoa-mlops repository:

```bash
git clone https://github.com/lhzn-io/kanoa-mlops.git
```
