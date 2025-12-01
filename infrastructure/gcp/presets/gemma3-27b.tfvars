# Gemma 3 27B Vision-Language Model
# Good for: Highest quality, complex reasoning
# VRAM: ~54GB, requires A100 40GB or 2x L4
# Note: Requires HF token for gated model access
# WARNING: Higher cost (~$3/hr for A100)

model_name       = "google/gemma-3-27b-it"
max_model_len    = 4096
machine_type     = "a2-highgpu-1g"  # A100 40GB
gpu_type         = "nvidia-tesla-a100"
boot_disk_size_gb = 300

labels = {
  project     = "kanoa-mlops"
  environment = "dev"
  model       = "gemma3-27b"
  managed-by  = "terraform"
}
