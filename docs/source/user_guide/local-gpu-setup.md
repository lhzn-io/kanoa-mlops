# Local GPU Setup Guide

This guide covers setting up `kanoa-mlops` on local NVIDIA GPU hardware, including native Linux, WSL2, eGPU enclosures, and NVIDIA Jetson platforms.

## Table of Contents

- [Prerequisites](#prerequisites)
- [macOS Setup (Apple Silicon)](#macos-setup-apple-silicon)
- [Native Linux Setup](#native-linux-setup)
- [WSL2 Setup (Windows)](#wsl2-setup-windows)
- [eGPU Setup (Thunderbolt/OCuLink)](#egpu-setup-thunderboltoculink)
- [NVIDIA Jetson Setup](#nvidia-jetson-setup)
- [Docker GPU Configuration](#docker-gpu-configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Hardware

- **GPU**: NVIDIA GPU with CUDA support
  - Consumer: RTX 30/40/50 series (16GB+ VRAM recommended)
  - Data Center: A100, H100, L40S
  - Jetson: Orin, Thor
  - eGPU: Any NVIDIA GPU in Thunderbolt/OCuLink enclosure

- **System RAM**: 16GB minimum, 32GB+ recommended
- **Storage**: 50GB+ free space (for models)

### Software

- **OS**: Ubuntu 22.04+ (or WSL2 on Windows 11)
- **Docker**: 24.0+ with NVIDIA Container Toolkit
- **NVIDIA Driver**: 535+ (550+ for RTX 50 series)

## macOS Setup (Apple Silicon)

For M1/M2/M3 Macs, we recommend running Ollama natively to leverage Metal acceleration for optimal performance.

### 1. Install Ollama

```bash
brew install ollama
```

### 2. Start Service

```bash
# Start as background service
brew services start ollama

# Or run interactively
ollama serve
```

### 3. Verify Metal Acceleration

When running a model, check the server logs. You should see "Metal" being used for computation.

```bash
ollama run gemma3:4b "Hello!"
```

### 4. Comparison with Docker

While you *can* run `kanoa-mlops` via Docker on Mac, you will incur meaningful performance overhead compared to native execution. We recommend:

- **Use Native Ollama**: For running models and inference.
- **Use Docker**: For `kanoa-mlops` monitoring and orchestration tools (Grafana, Prometheus), which can connect to your native Ollama instance via `host.docker.internal`.

## Native Linux Setup

### 1. Install NVIDIA Drivers

```bash
# Check for available drivers
ubuntu-drivers devices

# Install recommended driver
sudo ubuntu-drivers autoinstall

# Or install specific version
sudo apt install nvidia-driver-550

# Reboot
sudo reboot
```

### 2. Verify Installation

```bash
nvidia-smi
```

Expected output showing your GPU(s), driver version, and CUDA version.

### 3. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 4. Install NVIDIA Container Toolkit

```bash
# Add NVIDIA repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### 5. Verify Docker GPU Access

```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

✅ **Success**: You should see your GPU information.

## WSL2 Setup (Windows)

### 1. Install NVIDIA Drivers on Windows

⚠️ **Critical**: Install drivers on **Windows**, not inside WSL2.

1. Download latest drivers from [nvidia.com/drivers](https://www.nvidia.com/download/index.aspx)
2. Install on Windows (minimum version: R470+)
3. Restart Windows

### 2. Enable WSL2

```powershell
# In PowerShell (Administrator)
wsl --install
wsl --set-default-version 2

# Install Ubuntu
wsl --install -d Ubuntu-22.04
```

### 3. Verify GPU in WSL2

```bash
# In WSL2 terminal
nvidia-smi
```

If this works, skip to [Docker GPU Configuration](#docker-gpu-configuration).

### 4. Troubleshooting WSL2 GPU Access

#### Check NVIDIA Libraries

```bash
ls /usr/lib/wsl/lib
```

Should show `libcuda.so.1`, `libnvidia-ml.so.1`, etc.

If missing:

```bash
# Update WSL2 (in Windows PowerShell)
wsl --update
wsl --shutdown

# Set library path in WSL2
echo 'export LD_LIBRARY_PATH=/usr/lib/wsl/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

#### eGPU-Specific Issues

If using eGPU over Thunderbolt:

1. **Connect eGPU before booting Windows**
2. **Verify in Windows Device Manager** - if not visible there, won't work in WSL2
3. **Authorize Thunderbolt** in Windows settings
4. **Update Thunderbolt drivers**
5. **Check BIOS settings**:
   - Enable Thunderbolt
   - Enable "Thunderbolt Boot Support"

### 5. Install CUDA Toolkit (Optional)

For CUDA development:

```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install cuda-toolkit-12-3

# Add to ~/.bashrc
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

## eGPU Setup (Thunderbolt/OCuLink)

### Hardware Requirements

- **Host**: Laptop/Mini-PC with Thunderbolt 3/4 or OCuLink
- **Enclosure**: Razer Core X, Sonnet Breakaway Box, etc.
- **GPU**: Any NVIDIA GPU (RTX 3090/4090/5080 recommended)
- **Power**: Ensure enclosure provides adequate power (450W+ for high-end GPUs)

### Linux Setup

Follow [Native Linux Setup](#native-linux-setup), then:

#### 1. Authorize Thunderbolt Device

```bash
# List Thunderbolt devices
boltctl list

# Authorize eGPU
boltctl authorize <device-uuid>

# Make permanent
boltctl enroll <device-uuid>
```

#### 2. Verify PCIe Connection

```bash
nvidia-smi -q | grep -A 5 "PCIe"
```

Expected for Thunderbolt: `Gen3 x4` or `Gen4 x4`

#### 3. Check Bandwidth (Optional)

```bash
# Install nvbandwidth
sudo apt install nvidia-cuda-toolkit

# Test bandwidth
nvidia-cuda-mps-control
```

### Windows/WSL2 eGPU Setup

Follow [WSL2 Setup](#wsl2-setup-windows) with additional eGPU considerations noted above.

### Performance Notes

- **Bandwidth**: Thunderbolt provides PCIe Gen3/4 x4 (~32-64 Gbps)
  - ✅ Sufficient for ML inference
  - ⚠️ May bottleneck large model training
- **Latency**: Slightly higher than native PCIe
  - Negligible for batch inference
  - May impact real-time applications
- **Model Loading**: Slower due to bandwidth limits
  - Inference speed unaffected (model in VRAM)

## NVIDIA Jetson Setup

### Supported Platforms

- Jetson Orin Nano/NX/AGX
- Jetson Thor (upcoming)

### 1. Flash JetPack

Use NVIDIA SDK Manager to flash latest JetPack (6.0+):

```bash
# Check JetPack version
cat /etc/nv_tegra_release
```

### 2. Install Docker

```bash
# Docker is pre-installed on JetPack 6.0+
# Verify
docker --version

# If not installed
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### 3. Configure NVIDIA Runtime

```bash
# Already configured on JetPack
# Verify
docker run --rm --runtime nvidia --gpus all nvcr.io/nvidia/l4t-base:r35.4.1 nvidia-smi
```

### 4. Jetson-Specific Considerations

- **Power Mode**: Set to MAX for benchmarking

  ```bash
  sudo nvpmodel -m 0
  sudo jetson_clocks
  ```

- **Thermal Monitoring**:

  ```bash
  tegrastats
  ```

- **Model Selection**: Use smaller models (4B-12B) due to memory constraints
- **Quantization**: INT8/INT4 recommended for larger models

## Docker GPU Configuration

After completing platform-specific setup above:

### 1. Verify Docker GPU Access

```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### 2. Test with kanoa-mlops

```bash
cd /path/to/kanoa-mlops

# Start Ollama (easiest)
make serve-ollama

# Verify
docker ps
```

### 3. Pull a Model

```bash
# For Ollama
docker compose -f docker/ollama/docker-compose.ollama.yml exec ollama ollama pull gemma3:4b

# For vLLM (download from Hugging Face)
huggingface-cli download google/gemma-3-12b-it
```

## Verification

### Quick Test

```bash
# Run integration test
make test-ollama

# Or manual test
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:4b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Benchmark

```bash
cd tests/integration
python3 run_benchmark_suite_ollama.py
```

Expected throughput (varies by hardware):

- RTX 5080: ~55-65 tok/s (Gemma 4B)
- RTX 4090: ~50-60 tok/s (Gemma 4B)
- Jetson Orin: ~20-30 tok/s (Gemma 4B)

## Troubleshooting

### "CUDA out of memory"

```bash
# Reduce GPU memory utilization
vllm serve <model> --gpu-memory-utilization 0.7

# Or use smaller model
docker compose -f docker/ollama/docker-compose.ollama.yml exec ollama ollama pull gemma3:4b
```

### "No devices were found"

**Linux**:

```bash
# Check driver
nvidia-smi

# Reinstall NVIDIA Container Toolkit
sudo apt-get install --reinstall nvidia-container-toolkit
sudo systemctl restart docker
```

**WSL2**:

```bash
# Restart WSL2 (in Windows PowerShell)
wsl --shutdown

# Check library path
echo $LD_LIBRARY_PATH
```

**eGPU**:

```bash
# Linux: Check Thunderbolt authorization
boltctl list

# Windows: Verify in Device Manager
```

### GPU Disappears After Sleep/Hibernate

**WSL2**:

```powershell
# Restart WSL2
wsl --shutdown
```

**eGPU**:

- Disable sleep/hibernate
- Or reconnect eGPU and restart services

### Low Performance

```bash
# Check GPU utilization
nvidia-smi dmon

# Check thermal throttling
nvidia-smi -q -d TEMPERATURE

# Jetson: Ensure max power mode
sudo nvpmodel -m 0
sudo jetson_clocks
```

### Docker Permission Denied

```bash
sudo usermod -aG docker $USER
newgrp docker
```

## Next Steps

- [Quickstart Guide](quickstart.md) - Get started with your first model
- [GPU Monitoring](gpu-monitoring.md) - Set up Prometheus/Grafana
- [Performance Analysis](performance-analysis.md) - Optimize your setup
- [Model Support Guide](model-support.md) - Add new models

## Platform-Specific Resources

- **Native Linux**: [NVIDIA CUDA Installation Guide](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/)
- **WSL2**: [NVIDIA CUDA on WSL2](https://docs.nvidia.com/cuda/wsl-user-guide/)
- **Jetson**: [NVIDIA Jetson Documentation](https://docs.nvidia.com/jetson/)
- **eGPU**: [Thunderbolt on Linux](https://www.kernel.org/doc/html/latest/admin-guide/thunderbolt.html)
