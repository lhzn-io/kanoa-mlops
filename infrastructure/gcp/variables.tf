# -----------------------------------------------------------------------------
# Project Configuration
# -----------------------------------------------------------------------------
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone for compute instances"
  type        = string
  default     = "us-central1-a"
}

# -----------------------------------------------------------------------------
# Network & Security
# -----------------------------------------------------------------------------
variable "allowed_source_ranges" {
  description = "CIDR ranges allowed to access vLLM API and SSH (e.g., your IP)"
  type        = list(string)
}

variable "network" {
  description = "VPC network name"
  type        = string
  default     = "default"
}

# -----------------------------------------------------------------------------
# Compute Instance
# -----------------------------------------------------------------------------
variable "machine_type" {
  description = "GCE machine type (g2-standard-8 includes L4 GPU)"
  type        = string
  default     = "g2-standard-8"
}

variable "gpu_type" {
  description = "GPU accelerator type"
  type        = string
  default     = "nvidia-l4"
}

variable "gpu_count" {
  description = "Number of GPUs to attach"
  type        = number
  default     = 1
}

variable "boot_disk_size_gb" {
  description = "Boot disk size in GB (needs space for models)"
  type        = number
  default     = 200
}

variable "boot_disk_type" {
  description = "Boot disk type"
  type        = string
  default     = "pd-ssd"
}

# -----------------------------------------------------------------------------
# vLLM Configuration
# -----------------------------------------------------------------------------
variable "model_name" {
  description = "HuggingFace model ID to serve"
  type        = string
  default     = "allenai/Molmo-7B-D-0924"
}

variable "hf_token" {
  description = "HuggingFace API token (for gated models)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "vllm_image" {
  description = "vLLM Docker image"
  type        = string
  default     = "vllm/vllm-openai:v0.6.3.post1"
}

variable "max_model_len" {
  description = "Maximum sequence length for vLLM"
  type        = number
  default     = 4096
}

variable "gpu_memory_utilization" {
  description = "Fraction of GPU memory to use (0.0-1.0)"
  type        = number
  default     = 0.9
}

# -----------------------------------------------------------------------------
# Auto-Shutdown Configuration
# -----------------------------------------------------------------------------
variable "idle_timeout_minutes" {
  description = "Shutdown VM after this many minutes of inactivity (0 to disable)"
  type        = number
  default     = 30
}

variable "enable_schedule" {
  description = "Enable instance schedule (auto start/stop at specific times)"
  type        = bool
  default     = false
}

variable "schedule_start_time" {
  description = "Cron expression for auto-start (e.g., '0 9 * * 1-5' for 9 AM Mon-Fri)"
  type        = string
  default     = "0 9 * * 1-5"
}

variable "schedule_stop_time" {
  description = "Cron expression for auto-stop (e.g., '0 18 * * 1-5' for 6 PM Mon-Fri)"
  type        = string
  default     = "0 18 * * 1-5"
}

variable "schedule_timezone" {
  description = "Timezone for instance schedule"
  type        = string
  default     = "America/Los_Angeles"
}

# -----------------------------------------------------------------------------
# Labels & Tags
# -----------------------------------------------------------------------------
variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
  default = {
    project     = "kanoa-mlops"
    environment = "dev"
    managed-by  = "terraform"
  }
}
