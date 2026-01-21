"""
Architecture detection utilities for kanoa-mlops.

Detects hardware platform and selects appropriate container images.
"""

import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from kanoa_mlops.gpu_detect import GPUInfo, detect_gpu


@dataclass
class ArchConfig:
    """Hardware architecture configuration."""

    arch: str  # aarch64, x86_64
    platform_name: str  # jetson-thor, x86-cuda
    cuda_arch: str  # sm_110, sm_120
    vllm_image: str  # Docker image for vLLM
    description: str
    gpu_info: Optional[GPUInfo] = None  # Detected GPU information


def detect_architecture() -> ArchConfig:
    """
    Detect hardware architecture and return appropriate configuration.

    Returns:
        ArchConfig with platform-specific settings
    """
    system = platform.system().lower()
    machine = platform.machine().lower()
    gpu_info = detect_gpu()  # Detect GPU for all platforms

    if system == "darwin":
        return ArchConfig(
            arch=machine,
            platform_name="macos-arm64" if machine == "arm64" else "macos-x86_64",
            cuda_arch="none",
            vllm_image="vllm/vllm-openai:latest",
            description="Apple Silicon (M-series)"
            if machine == "arm64"
            else "Intel Mac",
            gpu_info=gpu_info,
        )

    if machine in ("aarch64", "arm64"):
        # ARM64 - check if Jetson Thor
        if _is_jetson_thor():
            return ArchConfig(
                arch="aarch64",
                platform_name="jetson-thor",
                cuda_arch="sm_110",
                vllm_image="ghcr.io/nvidia-ai-iot/vllm:latest-jetson-thor",
                description="NVIDIA Jetson Thor (Blackwell sm_110)",
                gpu_info=gpu_info,
            )
        else:
            return ArchConfig(
                arch="aarch64",
                platform_name="jetson-orin",
                cuda_arch="sm_87",
                vllm_image="dustynv/vllm:r36.4-cu129-24.04",
                description="NVIDIA Jetson Orin/Xavier (sm_87)",
                gpu_info=gpu_info,
            )

    elif machine in ("x86_64", "amd64"):
        # x86_64 - detect GPU and build description
        desc = "x86_64 with NVIDIA GPU"
        if gpu_info:
            desc += f" ({gpu_info.name}, {gpu_info.vram_gb}GB VRAM)"
        return ArchConfig(
            arch="x86_64",
            platform_name="x86-cuda",
            cuda_arch="sm_120",
            vllm_image="vllm/vllm-openai:latest",
            description=desc,
            gpu_info=gpu_info,
        )

    else:
        # Fallback to CPU-only
        return ArchConfig(
            arch=machine,
            platform_name="cpu",
            cuda_arch="none",
            vllm_image="vllm/vllm-openai:latest",
            description=f"Unknown architecture: {machine}",
            gpu_info=gpu_info,
        )


def _is_jetson_thor() -> bool:
    """
    Check if running on Jetson Thor by examining model name.

    Returns:
        True if Jetson Thor detected
    """
    model_file = Path("/proc/device-tree/model")
    if model_file.exists():
        try:
            model = model_file.read_text().strip("\x00").lower()
            return "thor" in model
        except Exception:
            pass

    # Fallback: check nvidia-smi for Thor GPU
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            gpu_name = result.stdout.strip().lower()
            return "thor" in gpu_name or "blackwell" in gpu_name
    except Exception:
        pass

    return False


def get_vllm_image_for_model(model_name: str) -> str:
    """
    Get the appropriate vLLM Docker image for a model on this architecture.

    Args:
        model_name: Model identifier (e.g., 'molmo', 'gemma3', 'olmo3')

    Returns:
        Docker image name
    """
    config = detect_architecture()
    return config.vllm_image
