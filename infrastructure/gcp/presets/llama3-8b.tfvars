# Llama 3.1 8B Instruct (Text-only)
# Good for: Text generation, code, reasoning
# VRAM: ~16GB, comfortable on L4 (24GB)
# Note: Requires HF token for gated model access

model_name       = "meta-llama/Llama-3.1-8B-Instruct"
max_model_len    = 8192
machine_type     = "g2-standard-8"
gpu_type         = "nvidia-l4"
boot_disk_size_gb = 150

labels = {
  project     = "kanoa-mlops"
  environment = "dev"
  model       = "llama3-8b"
  managed-by  = "terraform"
}
