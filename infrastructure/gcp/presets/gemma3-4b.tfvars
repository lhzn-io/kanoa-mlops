# Gemma 3 4B Vision-Language Model
# Good for: Fast inference, lower cost, multimodal
# VRAM: ~8GB, very comfortable on L4 (24GB)
# Note: Requires HF token for gated model access

model_name       = "google/gemma-3-4b-it"
max_model_len    = 8192
machine_type     = "g2-standard-8"
gpu_type         = "nvidia-l4"
boot_disk_size_gb = 150

labels = {
  project     = "kanoa-mlops"
  environment = "dev"
  model       = "gemma3-4b"
  managed-by  = "terraform"
}
