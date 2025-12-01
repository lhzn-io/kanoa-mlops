# GCP GPU Integration for kanoa-mlops

## Overview

This document outlines the plan for running vLLM on GCP with GPU support,
including auto-shutdown to prevent runaway costs.

## Architecture Options

### Option 1: Single GCE VM with GPU (Recommended for Dev/Test)

- **Pros**: Simple, full control, predictable costs
- **Cons**: Manual scaling, single point of failure

### Option 2: GKE with GPU Node Pool

- **Pros**: Kubernetes-native, auto-scaling, better for production
- **Cons**: More complex, minimum node costs, overkill for dev/test

### Option 3: Cloud Run with GPU (Preview)

- **Pros**: Serverless, pay-per-request, auto-scaling to zero
- **Cons**: Cold starts (30-60s), limited GPU options, still in preview

**Recommendation**: Start with Option 1 for development, migrate to Option 3 when GA.

---

## Option 1: GCE VM Implementation

### GPU Selection & Costs (us-central1, Nov 2025)

| GPU | VRAM | Hourly Cost | Good For |
|-----|------|-------------|----------|
| T4 | 16GB | ~$0.35/hr | 7B models, budget |
| L4 | 24GB | ~$0.70/hr | 7B-13B models, good perf |
| A100 40GB | 40GB | ~$3.00/hr | 70B models, production |

**Recommended**: L4 for Molmo-7B (~$0.70/hr = ~$17/day if always on)

### Auto-Shutdown Strategy

#### Method 1: Idle Detection Script (Recommended)

```bash
#!/bin/bash
# /opt/kanoa/idle-shutdown.sh
# Shuts down VM if no API requests for IDLE_TIMEOUT minutes

IDLE_TIMEOUT=${IDLE_TIMEOUT:-30}  # minutes
LAST_REQUEST_FILE="/tmp/last_vllm_request"
HEALTH_ENDPOINT="http://localhost:8000/health"

while true; do
    # Check if vLLM is responding
    if curl -sf "$HEALTH_ENDPOINT" > /dev/null; then
        # Check last request time from vLLM metrics or access log
        LAST_REQUEST=$(stat -c %Y "$LAST_REQUEST_FILE" 2>/dev/null || echo 0)
        NOW=$(date +%s)
        IDLE_SECONDS=$((NOW - LAST_REQUEST))
        IDLE_MINUTES=$((IDLE_SECONDS / 60))

        if [ "$IDLE_MINUTES" -ge "$IDLE_TIMEOUT" ]; then
            echo "Idle for $IDLE_MINUTES minutes, shutting down..."
            sudo shutdown -h now
        fi
    fi
    sleep 60
done
```

#### Method 2: GCP Instance Schedule (Simpler)

Set specific hours when the VM should run:

- Auto-start at 9 AM
- Auto-stop at 6 PM
- Weekend shutdown

#### Method 3: Budget Alerts + Cloud Function

- Set budget alert at $X/day
- Cloud Function stops VM when budget exceeded

### Implementation Checklist

- [ ] Create GCP project or use existing
- [ ] Enable Compute Engine API
- [ ] Create service account with minimal permissions
- [ ] Set up Terraform or gcloud scripts
- [ ] Configure firewall rules (restrict to your IP)
- [ ] Set up idle shutdown mechanism
- [ ] Create startup script to launch vLLM
- [ ] Document costs and usage

---

## Terraform Configuration (Draft)

```hcl
# infrastructure/gcp/main.tf

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  default = "us-central1"
}

variable "zone" {
  default = "us-central1-a"
}

variable "idle_timeout_minutes" {
  default = 30
}

variable "allowed_ip" {
  description = "Your IP for SSH/API access (CIDR notation)"
  type        = string
}

# GPU VM for vLLM
resource "google_compute_instance" "vllm_server" {
  name         = "kanoa-vllm-server"
  machine_type = "g2-standard-8"  # 8 vCPU, 32GB RAM, includes L4 GPU
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "deeplearning-platform-release/common-cu121-v20231105-debian-11"
      size  = 200  # GB, for model storage
      type  = "pd-ssd"
    }
  }

  guest_accelerator {
    type  = "nvidia-l4"
    count = 1
  }

  scheduling {
    on_host_maintenance = "TERMINATE"  # Required for GPU
    automatic_restart   = false
  }

  network_interface {
    network = "default"
    access_config {
      // Ephemeral public IP
    }
  }

  metadata_startup_script = file("${path.module}/startup.sh")

  metadata = {
    idle-timeout-minutes = var.idle_timeout_minutes
  }

  tags = ["vllm-server", "allow-health-check"]

  labels = {
    purpose = "kanoa-mlops"
    auto-shutdown = "enabled"
  }
}

# Firewall: Allow vLLM API from your IP only
resource "google_compute_firewall" "vllm_api" {
  name    = "allow-vllm-api"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["8000"]
  }

  source_ranges = [var.allowed_ip]
  target_tags   = ["vllm-server"]
}

# Firewall: Allow SSH from your IP only
resource "google_compute_firewall" "ssh" {
  name    = "allow-ssh-restricted"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = [var.allowed_ip]
  target_tags   = ["vllm-server"]
}

# Instance schedule for auto start/stop
resource "google_compute_resource_policy" "vllm_schedule" {
  name   = "kanoa-vllm-schedule"
  region = var.region

  instance_schedule_policy {
    vm_start_schedule {
      schedule = "0 9 * * 1-5"  # 9 AM Mon-Fri
    }
    vm_stop_schedule {
      schedule = "0 18 * * 1-5"  # 6 PM Mon-Fri
    }
    time_zone = "America/Los_Angeles"
  }
}

output "instance_ip" {
  value = google_compute_instance.vllm_server.network_interface[0].access_config[0].nat_ip
}

output "ssh_command" {
  value = "gcloud compute ssh kanoa-vllm-server --zone=${var.zone}"
}

output "api_endpoint" {
  value = "http://${google_compute_instance.vllm_server.network_interface[0].access_config[0].nat_ip}:8000"
}
```

---

## Startup Script (Draft)

```bash
#!/bin/bash
# infrastructure/gcp/startup.sh

set -e

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
fi

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Pull vLLM image
docker pull vllm/vllm-openai:v0.6.3.post1

# Start vLLM with Molmo
docker run -d \
    --name kanoa-vllm \
    --gpus all \
    --restart unless-stopped \
    -p 8000:8000 \
    -e HF_TOKEN=${HF_TOKEN:-} \
    vllm/vllm-openai:v0.6.3.post1 \
    --model allenai/Molmo-7B-D-0924 \
    --host 0.0.0.0 \
    --port 8000 \
    --served-model-name allenai/Molmo-7B-D-0924 \
    --trust-remote-code \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9

# Setup idle shutdown
cat > /opt/idle-shutdown.sh << 'EOF'
#!/bin/bash
IDLE_TIMEOUT=${1:-30}
LAST_ACTIVITY=$(date +%s)

while true; do
    # Check for recent requests via Docker logs
    RECENT=$(docker logs --since=1m kanoa-vllm 2>&1 | grep -c "POST\|GET" || echo 0)
    
    if [ "$RECENT" -gt 0 ]; then
        LAST_ACTIVITY=$(date +%s)
    fi
    
    NOW=$(date +%s)
    IDLE=$((NOW - LAST_ACTIVITY))
    IDLE_MIN=$((IDLE / 60))
    
    if [ "$IDLE_MIN" -ge "$IDLE_TIMEOUT" ]; then
        echo "$(date): Idle for $IDLE_MIN min, shutting down"
        sudo shutdown -h now
    fi
    
    sleep 60
done
EOF

chmod +x /opt/idle-shutdown.sh
nohup /opt/idle-shutdown.sh 30 > /var/log/idle-shutdown.log 2>&1 &
```

---

## Quick Start Commands (gcloud CLI)

For those who prefer CLI over Terraform:

```bash
# Set variables
PROJECT_ID="your-project-id"
ZONE="us-central1-a"
MY_IP="$(curl -s ifconfig.me)/32"

# Create GPU VM
gcloud compute instances create kanoa-vllm-server \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=g2-standard-8 \
    --accelerator=type=nvidia-l4,count=1 \
    --image-family=common-cu121 \
    --image-project=deeplearning-platform-release \
    --boot-disk-size=200GB \
    --boot-disk-type=pd-ssd \
    --maintenance-policy=TERMINATE \
    --metadata-from-file=startup-script=startup.sh

# Firewall rules
gcloud compute firewall-rules create allow-vllm-api \
    --project=$PROJECT_ID \
    --allow=tcp:8000 \
    --source-ranges=$MY_IP \
    --target-tags=vllm-server

# Get IP
gcloud compute instances describe kanoa-vllm-server \
    --zone=$ZONE \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

# SSH
gcloud compute ssh kanoa-vllm-server --zone=$ZONE

# Stop when done
gcloud compute instances stop kanoa-vllm-server --zone=$ZONE

# Delete when no longer needed
gcloud compute instances delete kanoa-vllm-server --zone=$ZONE
```

---

## Cost Estimates

### Development Usage (4 hrs/day, weekdays)

| Component | Cost/Month |
|-----------|------------|
| L4 GPU VM (g2-standard-8) | ~$56 (80 hrs × $0.70) |
| Boot disk (200GB SSD) | ~$34 |
| Network egress | ~$5 |
| **Total** | **~$95/month** |

### With Auto-Shutdown

If idle-shutdown triggers after 30 min of no use:

- Realistic usage: ~2 hrs/day actual
- **Estimated: ~$50/month**

### Cost Safety Measures

1. **Budget alerts**: Set at $100/month, alert at 50%, 80%, 100%
2. **Billing export**: Monitor in BigQuery
3. **Idle shutdown**: 30-minute timeout
4. **Instance schedule**: Auto-stop at 6 PM

---

## Next Steps

1. [ ] Decide on Terraform vs gcloud CLI approach
2. [ ] Set up GCP project and enable APIs
3. [ ] Configure authentication (service account or user credentials)
4. [ ] Test deployment
5. [ ] Integrate with kanoa client (remote API endpoint)
6. [ ] Add monitoring/alerting
