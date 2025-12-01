# Gemma 3 12B Vision-Language Model
# Good for: Better quality, still fast, multimodal
# VRAM: ~24GB, tight fit on L4 (24GB)
# Note: Requires HF token for gated model access

model_name       = "google/gemma-3-12b-it"
max_model_len    = 4096  # Reduced for memory
machine_type     = "g2-standard-8"
gpu_type         = "nvidia-l4"
boot_disk_size_gb = 200

# Lower GPU memory utilization to leave headroom
gpu_memory_utilization = 0.85

labels = {
  project     = "kanoa-mlops"
  environment = "dev"
  model       = "gemma3-12b"
  managed-by  = "terraform"
}
