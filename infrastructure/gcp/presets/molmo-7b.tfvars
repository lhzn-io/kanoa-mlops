# Molmo 7B-D Vision-Language Model
# Good for: Chart interpretation, image analysis
# VRAM: ~14GB, fits comfortably on L4 (24GB)

model_name       = "allenai/Molmo-7B-D-0924"
max_model_len    = 4096
machine_type     = "g2-standard-8"
gpu_type         = "nvidia-l4"
boot_disk_size_gb = 200

labels = {
  project     = "kanoa-mlops"
  environment = "dev"
  model       = "molmo-7b"
  managed-by  = "terraform"
}
