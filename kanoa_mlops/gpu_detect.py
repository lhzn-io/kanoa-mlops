"""
GPU detection utilities for automatic quantization selection.

Detects GPU VRAM and provides model-specific deployment recommendations.
"""

import subprocess
from dataclasses import dataclass
from typing import Optional

VRAM_TIER_ULTRA = 80
VRAM_TIER_HIGH = 48
VRAM_TIER_MEDIUM = 24
VRAM_TIER_LOW = 16


@dataclass
class GPUInfo:
    """GPU hardware information."""

    name: str
    vram_mb: int
    vram_gb: float
    compute_capability: Optional[str] = None

    @property
    def vram_tier(self) -> str:
        """Categorize GPU by VRAM for deployment recommendations."""
        if self.vram_gb >= VRAM_TIER_ULTRA:
            return "ultra"  # H100, A100 80GB
        elif self.vram_gb >= VRAM_TIER_HIGH:
            return "high"  # RTX 6000 Ada, A6000
        elif self.vram_gb >= VRAM_TIER_MEDIUM:
            return "medium"  # RTX 4090, RTX 5080
        elif self.vram_gb >= VRAM_TIER_LOW:
            return "low"  # RTX 4080, older cards
        else:
            return "minimal"  # <16GB


@dataclass
class ModelRequirements:
    """Memory requirements for a specific model configuration."""

    model_name: str
    min_vram_gb: float
    recommended_vram_gb: float
    quantization_strategy: dict[str, str]  # vram_tier -> quantization flags


# Model memory requirements database
MODEL_REQUIREMENTS = {
    "nemotron3-nano": ModelRequirements(
        model_name="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16",
        min_vram_gb=18.0,  # FP8 quantized
        recommended_vram_gb=48.0,  # BF16 full precision
        quantization_strategy={
            "ultra": "",  # BF16, no quantization
            "high": "",  # BF16, no quantization
            "medium": "--quantization fp8",  # 24GB GPUs need FP8
            "low": "--quantization fp8",  # 16GB GPUs need FP8 + reduced context
        },
    ),
    "gemma3": ModelRequirements(
        model_name="google/gemma-3-12b-it",
        min_vram_gb=8.0,  # 4-bit quantized
        recommended_vram_gb=24.0,  # BF16
        quantization_strategy={
            "ultra": "",
            "high": "",
            "medium": "",  # 24GB is enough for 12B BF16
            "low": "--quantization bitsandbytes --load-format bitsandbytes",
            "minimal": "--quantization bitsandbytes --load-format bitsandbytes",
        },
    ),
    "olmo3": ModelRequirements(
        model_name="allenai/Olmo-3-7B-Think",
        min_vram_gb=4.0,
        recommended_vram_gb=16.0,
        quantization_strategy={
            "ultra": "",
            "high": "",
            "medium": "",
            "low": "",
            "minimal": "--quantization bitsandbytes --load-format bitsandbytes",
        },
    ),
    "molmo": ModelRequirements(
        model_name="allenai/Molmo-7B-D-0924",
        min_vram_gb=4.0,
        recommended_vram_gb=16.0,
        quantization_strategy={
            "ultra": "",
            "high": "",
            "medium": "",
            "low": "",
            "minimal": "--quantization bitsandbytes --load-format bitsandbytes",
        },
    ),
}


def detect_gpu() -> Optional[GPUInfo]:
    """
    Detect NVIDIA GPU and query VRAM.

    Returns:
        GPUInfo with GPU details, or None if no GPU detected
    """
    try:
        # Query GPU name and memory
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return None

        output = result.stdout.strip()
        if not output or "[N/A]" in output:
            # Jetson devices report [N/A] for memory.total
            # Fall back to reading from device tree or use platform defaults
            return _detect_jetson_gpu()

        # Parse: "NVIDIA GeForce RTX 5080, 16384"
        parts = output.split(",")
        if len(parts) < 2:  # noqa: PLR2004
            return None

        name = parts[0].strip()
        try:
            vram_mb = int(parts[1].strip())
        except ValueError:
            return None

        return GPUInfo(
            name=name,
            vram_mb=vram_mb,
            vram_gb=round(vram_mb / 1024, 1),
        )

    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _detect_jetson_gpu() -> Optional[GPUInfo]:
    """
    Special handling for Jetson devices (Thor, Orin, etc.).

    Jetson uses unified memory, so we read total system memory.
    """
    try:
        # Check if this is Jetson Thor
        with open("/proc/device-tree/model", "r") as f:
            model = f.read().strip("\x00").lower()

        if "thor" in model:
            # Jetson Thor has 128GB unified memory
            return GPUInfo(
                name="NVIDIA Jetson Thor",
                vram_mb=128 * 1024,  # 128GB unified memory
                vram_gb=128.0,
            )
        elif "orin" in model:
            # Jetson Orin AGX has 64GB unified memory
            return GPUInfo(
                name="NVIDIA Jetson Orin",
                vram_mb=64 * 1024,
                vram_gb=64.0,
            )

    except FileNotFoundError:
        pass

    return None


def get_recommended_config(
    model_family: str, gpu_info: Optional[GPUInfo] = None
) -> dict[str, str]:
    """
    Get recommended deployment configuration for a model based on available VRAM.

    Args:
        model_family: Model identifier (e.g., 'nemotron3-nano', 'gemma3')
        gpu_info: GPU information (auto-detected if None)

    Returns:
        Dict of environment variables for docker-compose
    """
    if gpu_info is None:
        gpu_info = detect_gpu()

    if gpu_info is None:
        # No GPU detected - return minimal config
        return {
            "QUANTIZATION_FLAGS": "--quantization bitsandbytes --load-format bitsandbytes"
        }

    # Get model requirements
    requirements = MODEL_REQUIREMENTS.get(model_family)
    if requirements is None:
        # Unknown model - use conservative defaults
        return {}

    # Check if GPU has enough VRAM
    if gpu_info.vram_gb < requirements.min_vram_gb:
        raise ValueError(
            f"Insufficient VRAM: {model_family} requires at least "
            f"{requirements.min_vram_gb}GB, but GPU only has {gpu_info.vram_gb}GB"
        )

    # Get quantization strategy for this VRAM tier
    tier = gpu_info.vram_tier
    quant_flags = requirements.quantization_strategy.get(tier)

    if quant_flags is None:
        raise ValueError(f"Model {model_family} cannot run on VRAM tier '{tier}'")

    config = {}
    if quant_flags:
        config["QUANTIZATION_FLAGS"] = quant_flags

    # Adjust context length for lower-VRAM GPUs
    if model_family == "nemotron3-nano":
        if tier in ("low", "minimal"):
            config["MAX_MODEL_LEN"] = "65536"  # 64K context to save memory
        elif tier == "medium":
            config["MAX_MODEL_LEN"] = "131072"  # 128K context (default)
        else:
            config["MAX_MODEL_LEN"] = "262144"  # 256K context for high-VRAM GPUs

    return config


def print_gpu_info(gpu_info: Optional[GPUInfo] = None) -> None:
    """Print detected GPU information for debugging."""
    if gpu_info is None:
        gpu_info = detect_gpu()

    if gpu_info is None:
        print("No NVIDIA GPU detected")
        return

    print(f"GPU: {gpu_info.name}")
    print(f"VRAM: {gpu_info.vram_gb:.1f} GB")
    print(f"VRAM Tier: {gpu_info.vram_tier}")
