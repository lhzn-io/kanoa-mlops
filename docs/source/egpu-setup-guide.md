# eGPU Setup Guide

This guide covers setting up `kanoa-mlops` with an external GPU (eGPU), specifically targeting NVIDIA RTX 50-series cards (e.g., RTX 5080) connected via Thunderbolt or OCulink.

## Hardware Requirements

*   **Host Machine**: Laptop or Mini-PC with Thunderbolt 3/4 or OCulink support.
*   **eGPU Enclosure**: Compatible enclosure (e.g., Razer Core X, Sonnet Breakaway Box).
*   **GPU**: NVIDIA RTX 3090, 4090, or 5080 (Recommended: 16GB+ VRAM).
*   **OS**: Linux (Ubuntu 22.04+) or Windows 11 (via WSL2).

## Driver Installation

Ensure you have the latest NVIDIA drivers installed on the host system.

### Linux (Native)

```bash
sudo apt install nvidia-driver-550
nvidia-smi
```

### Windows (WSL2)

Install the **Game Ready Driver** or **Studio Driver** on Windows. **Do not** install drivers inside WSL2.

## Docker Configuration

To expose the eGPU to Docker, you need the NVIDIA Container Toolkit.

1.  **Install Toolkit**:
    ```bash
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
    && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    ```

2.  **Configure Docker**:
    ```bash
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
    ```

3.  **Verify**:
    ```bash
    docker run --rm --runtime=nvidia --gpus all ubuntu nvidia-smi
    ```

## Running vLLM on eGPU

The `docker-compose` files in this repository are pre-configured for NVIDIA GPUs.

### 1. Check Bandwidth (Optional)

eGPUs are limited by Thunderbolt bandwidth (PCIe x4). This mainly affects **model loading time**, not inference speed (token generation), as the model resides in VRAM.

### 2. Launch Service

```bash
# For Molmo 7B
docker compose -f docker/vllm/docker-compose.molmo.yml up -d

# For Gemma 3 12B
docker compose -f docker/vllm/docker-compose.gemma.yml up -d
```

### 3. Troubleshooting

*   **"No devices were found"**: Ensure the eGPU is authorized in your OS settings (boltctl on Linux).
*   **Slow Inference**: Check if you are offloading to CPU. Ensure `gpu-memory-utilization` is set correctly (default 0.9).

