# -----------------------------------------------------------------------------
# kanoa-mlops GCP Infrastructure
# GPU-enabled VM for vLLM inference with auto-shutdown
# -----------------------------------------------------------------------------

locals {
  instance_name = "kanoa-vllm-server"
  tags          = ["vllm-server", "allow-health-check"]
}

# -----------------------------------------------------------------------------
# Compute Instance - GPU VM for vLLM
# -----------------------------------------------------------------------------
resource "google_compute_instance" "vllm_server" {
  name         = local.instance_name
  machine_type = var.machine_type
  zone         = var.zone

  tags   = local.tags
  labels = var.labels

  boot_disk {
    initialize_params {
      image = "deeplearning-platform-release/common-cu121-v20231105-debian-11"
      size  = var.boot_disk_size_gb
      type  = var.boot_disk_type
    }
  }

  # GPU Configuration
  guest_accelerator {
    type  = var.gpu_type
    count = var.gpu_count
  }

  scheduling {
    on_host_maintenance = "TERMINATE" # Required for GPU instances
    automatic_restart   = false       # Don't auto-restart on maintenance
    preemptible         = false       # Use spot instances for cost savings if desired
  }

  network_interface {
    network = var.network
    access_config {
      # Ephemeral public IP
    }
  }

  metadata = {
    # Pass configuration to startup script
    model-name             = var.model_name
    vllm-image             = var.vllm_image
    max-model-len          = var.max_model_len
    gpu-memory-utilization = var.gpu_memory_utilization
    idle-timeout-minutes   = var.idle_timeout_minutes
    hf-token               = var.hf_token

    # Enable OS Login for better SSH security
    enable-oslogin = "TRUE"
  }

  metadata_startup_script = file("${path.module}/scripts/startup.sh")

  service_account {
    scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]
  }

  lifecycle {
    ignore_changes = [
      # Ignore changes to metadata that may be modified at runtime
      metadata["ssh-keys"],
    ]
  }
}

# -----------------------------------------------------------------------------
# Firewall Rules
# -----------------------------------------------------------------------------

# Allow vLLM API access from specified source ranges
resource "google_compute_firewall" "vllm_api" {
  name    = "kanoa-allow-vllm-api"
  network = var.network

  allow {
    protocol = "tcp"
    ports    = ["8000"]
  }

  source_ranges = var.allowed_source_ranges
  target_tags   = local.tags

  description = "Allow vLLM API access from authorized IPs"
}

# Allow SSH from specified source ranges
resource "google_compute_firewall" "ssh" {
  name    = "kanoa-allow-ssh"
  network = var.network

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = var.allowed_source_ranges
  target_tags   = local.tags

  description = "Allow SSH access from authorized IPs"
}

# Allow health checks from GCP load balancers (if using)
resource "google_compute_firewall" "health_check" {
  name    = "kanoa-allow-health-check"
  network = var.network

  allow {
    protocol = "tcp"
    ports    = ["8000"]
  }

  # GCP health check IP ranges
  source_ranges = ["35.191.0.0/16", "130.211.0.0/22"]
  target_tags   = ["allow-health-check"]

  description = "Allow GCP health checks"
}

# -----------------------------------------------------------------------------
# Instance Schedule (Optional)
# Auto start/stop at specific times
# -----------------------------------------------------------------------------
resource "google_compute_resource_policy" "schedule" {
  count = var.enable_schedule ? 1 : 0

  name   = "kanoa-vllm-schedule"
  region = var.region

  instance_schedule_policy {
    vm_start_schedule {
      schedule = var.schedule_start_time
    }
    vm_stop_schedule {
      schedule = var.schedule_stop_time
    }
    time_zone = var.schedule_timezone
  }
}

resource "google_compute_instance_resource_policy_attachment" "schedule" {
  count = var.enable_schedule ? 1 : 0

  name     = google_compute_resource_policy.schedule[0].name
  instance = google_compute_instance.vllm_server.name
  zone     = var.zone
}
