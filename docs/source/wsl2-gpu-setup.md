# WSL2 GPU Setup Guide

Guide for setting up NVIDIA GPU access in WSL2, including support for eGPU enclosures over USB-4/Thunderbolt.

## Prerequisites

- Windows 11 (recommended) or Windows 10 version 21H2 or higher
- WSL2 installed and configured
- NVIDIA GPU (discrete or eGPU via USB-4/Thunderbolt)

## Step 1: Install NVIDIA Drivers on Windows

⚠️ **Critical**: Install drivers on **Windows**, not inside WSL2.

1. Download the latest NVIDIA GeForce or Studio drivers from [nvidia.com/drivers](https://www.nvidia.com/download/index.aspx)
2. Install the drivers on Windows
3. Minimum required version: **R470 or newer** (for WSL2 GPU support)
4. Restart Windows after installation

## Step 2: Verify WSL2 GPU Access

Open WSL2 terminal and check if the GPU is visible:

```bash
nvidia-smi
```

Expected output:

```text
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.xx.xx    Driver Version: 535.xx.xx    CUDA Version: 12.x   |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA GeForce ...  Off  | 00000000:01:00.0 Off |                  N/A |
...
```

If you see this, GPU is working! Proceed to Step 4.

## Step 3: Troubleshooting WSL2 GPU Access

If `nvidia-smi` doesn't work:

### Check NVIDIA Libraries in WSL2

```bash
ls /usr/lib/wsl/lib
```

You should see files like `libcuda.so.1`, `libnvidia-ml.so.1`, etc.

If missing:

1. Ensure Windows NVIDIA drivers are **R470 or newer**
2. Update WSL2: `wsl --update` (in Windows PowerShell)
3. Restart WSL2: `wsl --shutdown` then reopen

### Set Library Path

Add to your `~/.bashrc`:

```bash
export LD_LIBRARY_PATH=/usr/lib/wsl/lib:$LD_LIBRARY_PATH
```

Then reload:

```bash
source ~/.bashrc
```

### eGPU Specific Issues

If using an eGPU over USB-4/Thunderbolt:

1. **Connect eGPU before booting Windows**
2. **Ensure Thunderbolt is authorized** in Windows Device Manager
3. **Check if GPU shows in Windows Device Manager**
   - If not visible in Windows, it won't work in WSL2
   - Try updating Thunderbolt drivers
4. **Some eGPUs require BIOS settings**
   - Enable Thunderbolt in BIOS
   - Enable "Thunderbolt Boot Support"

## Step 4: Install CUDA Toolkit in WSL2 (Optional)

For development with CUDA:

```bash
# Add NVIDIA package repositories
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update

# Install CUDA toolkit
sudo apt install cuda-toolkit-12-3
```

Add to `~/.bashrc`:

```bash
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
```

## Step 5: Verify GPU with kanoa-mlops

### Install Dependencies

```bash
cd /path/to/kanoa-mlops
pip install -r requirements.txt
```

### Run GPU Probe Script

```bash
python scripts/probe-gpu.py
```

Expected output:

```text
Probing for NVIDIA GPUs...
Platform: linux
✓ nvidia-smi found

PyTorch CUDA Status:
  CUDA Available:      True
  CUDA Version:        12.3
  Device Count:        1
  cuDNN Version:       8902

================================================================================
NVIDIA GPU DETECTION REPORT
================================================================================

GPU 0: NVIDIA GeForce RTX 4090
--------------------------------------------------------------------------------
  UUID:                GPU-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  Compute Capability:  8.9
  Driver Version:      535.xx.xx
  CUDA Version:        12.3

  Memory:
    Total:   24.00 GB
    Used:    0.50 GB
    Free:    23.50 GB

  Temperature:         45°C

  Power:
    Current: 35.20 W
    Limit:   450.00 W

  Clock Speeds:
    Graphics: 210 MHz
    Memory:   405 MHz

  PCIe:
    Max:     Gen4 x16
    Current: Gen4 x16

✓ Found 1 NVIDIA GPU(s)
```

⚠️ **eGPU Note**: If you see `Current: Gen3 x4` or lower in PCIe info, your eGPU may not be getting full bandwidth. This is common with USB-4 enclosures and is usually acceptable for ML inference.

## Step 6: Test with PyTorch

```python
import torch

print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
print(f"Device count: {torch.cuda.device_count()}")
print(f"Current device: {torch.cuda.current_device()}")
print(f"Device name: {torch.cuda.get_device_name(0)}")

# Test tensor operation
x = torch.randn(1000, 1000).cuda()
y = torch.randn(1000, 1000).cuda()
z = x @ y
print(f"GPU computation successful: {z.shape}")
```

## Performance Considerations for eGPU

1. **Bandwidth**: USB-4 provides ~40 Gbps, PCIe Gen3 x4 equivalent
   - Sufficient for ML inference
   - May bottleneck for training large models

2. **Latency**: Slightly higher than native PCIe
   - Usually negligible for batch inference
   - May impact real-time applications

3. **Power**: Ensure your eGPU enclosure provides adequate power
   - High-end GPUs (RTX 4090) need 450W+
   - Check enclosure power supply rating

## Common Issues

### Issue: `nvidia-smi` shows GPU but PyTorch can't find it

**Solution**: Reinstall PyTorch with CUDA support:

```bash
pip uninstall torch
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### Issue: GPU disappears after Windows sleep/hibernate

**Solution**:

1. Disable sleep/hibernate for eGPU
2. Or reconnect/restart WSL2:

   ```powershell
   wsl --shutdown
   ```

### Issue: Low PCIe bandwidth (Gen1 or Gen2)

**Solution**:

1. Check Thunderbolt cable quality (use certified cables)
2. Update Thunderbolt firmware
3. Try different Thunderbolt port
4. Disable power saving for Thunderbolt in Windows

## References

- [NVIDIA CUDA on WSL2](https://docs.nvidia.com/cuda/wsl-user-guide/index.html)
- [Microsoft WSL2 GPU Guide](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gpu-compute)
- [docker/vllm/README.md](../../docker/vllm/README.md) - vLLM Docker setup with GPU
