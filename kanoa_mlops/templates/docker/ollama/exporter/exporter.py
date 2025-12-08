import os
import time

import requests
from prometheus_client import Gauge, Info, start_http_server

# Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", "15"))
PORT = int(os.getenv("PORT", "8000"))

# Metrics
OLLAMA_UP = Gauge("ollama_up", "Ollama service status (1=up, 0=down)")
OLLAMA_MODEL_COUNT = Gauge("ollama_models_total", "Total number of available models")
OLLAMA_RUNNING_MODELS = Gauge(
    "ollama_running_models", "Number of models currently loaded in memory"
)
OLLAMA_INFO = Info("ollama_info", "Ollama version information")


def scrape_metrics():
    """Fetch metrics from Ollama API."""
    try:
        # Check Health / Version
        resp = requests.get(f"{OLLAMA_HOST}/api/version", timeout=5)
        if resp.status_code == 200:
            OLLAMA_UP.set(1)
            data = resp.json()
            OLLAMA_INFO.info({"version": data.get("version", "unknown")})
        else:
            OLLAMA_UP.set(0)
    except Exception:
        OLLAMA_UP.set(0)
        return  # Cannot fetch other metrics if down

    try:
        # Check Available Models
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            OLLAMA_MODEL_COUNT.set(len(models))
    except Exception:
        pass

    try:
        # Check Running Models (Process Status)
        resp = requests.get(f"{OLLAMA_HOST}/api/ps", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            OLLAMA_RUNNING_MODELS.set(len(models))
        elif resp.status_code == 404:
            # Fallback for older Ollama versions
            OLLAMA_RUNNING_MODELS.set(0)
    except Exception:
        pass


if __name__ == "__main__":
    print(f"Starting Ollama Exporter on port {PORT}...")
    print(f"Target Ollama Host: {OLLAMA_HOST}")

    start_http_server(PORT)

    while True:
        scrape_metrics()
        time.sleep(SCRAPE_INTERVAL)
