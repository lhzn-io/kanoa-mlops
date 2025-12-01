# User Setup Guide

How to deploy kanoa-mlops infrastructure in your own GCP project.

---

## Overview

This guide covers everything a new user needs to spin up vLLM on GCP using this repository.

**Time Required:** ~15-30 minutes
**Cost:** ~$0.70/hr when running (L4 GPU)

---

## Prerequisites

### 1. GCP Account & Project

You need:

- [ ] Google Cloud account with billing enabled
- [ ] A GCP project (create one or use existing)
- [ ] Project ID (found in GCP Console → Project Settings)

```bash
# Create a new project (optional)
gcloud projects create my-kanoa-project --name="kanoa MLOps"

# Set as active project
gcloud config set project my-kanoa-project

# Enable billing (must be done in Console)
# https://console.cloud.google.com/billing
```

### 2. Enable Required APIs

```bash
# Enable Compute Engine API
gcloud services enable compute.googleapis.com

# Enable Cloud Resource Manager (for Terraform)
gcloud services enable cloudresourcemanager.googleapis.com
```

### 3. GPU Quota

L4 GPUs may require quota approval for new projects:

```bash
# Check current quota
gcloud compute regions describe us-central1 \
    --format="table(quotas.filter(metric:NVIDIA_L4_GPUS))"
```

If quota is 0, request an increase:

1. Go to [IAM & Admin → Quotas](https://console.cloud.google.com/iam-admin/quotas)
2. Filter: `Metric: NVIDIA L4 GPUs`
3. Select region (us-central1)
4. Click "Edit Quotas" → Request 1
5. Wait for approval (usually <24 hours)

### 4. Local Tools

Install on your workstation:

| Tool | Version | Installation |
|------|---------|--------------|
| **gcloud CLI** | Latest | [Install Guide](https://cloud.google.com/sdk/docs/install) |
| **Terraform** | >= 1.5.0 | `brew install terraform` or [Download](https://terraform.io/downloads) |

```bash
# Authenticate gcloud
gcloud auth login
gcloud auth application-default login

# Verify
gcloud config list
terraform --version
```

---

## Configuration

### Required Variables

You **must** configure these values:

| Variable | Description | How to Get |
|----------|-------------|------------|
| `project_id` | Your GCP project ID | `gcloud config get-value project` |
| `allowed_source_ranges` | Your IP address (CIDR) | `curl -s ifconfig.me` then add `/32` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `region` | `us-central1` | GCP region |
| `zone` | `us-central1-a` | GCP zone |
| `model_name` | `allenai/Molmo-7B-D-0924` | HuggingFace model ID |
| `idle_timeout_minutes` | `30` | Auto-shutdown after idle |
| `hf_token` | `""` | HuggingFace token (for gated models) |

### Setup Steps

```bash
# 1. Clone the repo
git clone https://github.com/lhzn-io/kanoa-mlops.git
cd kanoa-mlops/infrastructure/gcp

# 2. Create your config file
cp terraform.tfvars.example terraform.tfvars

# 3. Edit with your values
# Replace YOUR_PROJECT_ID and YOUR_IP
cat > terraform.tfvars << EOF
project_id            = "YOUR_PROJECT_ID"
allowed_source_ranges = ["YOUR_IP/32"]
EOF

# Or edit manually
nano terraform.tfvars
```

---

## Deployment

### Option A: Terraform (Recommended)

```bash
cd infrastructure/gcp

# Initialize Terraform
terraform init

# Preview what will be created
terraform plan

# Deploy (type 'yes' to confirm)
terraform apply
```

**Outputs:**

```text
vllm_api_endpoint = "http://34.XX.XX.XX:8000"
ssh_command = "gcloud compute ssh kanoa-vllm-server --zone=us-central1-a"
stop_command = "gcloud compute instances stop kanoa-vllm-server ..."
```

### Option B: gcloud CLI Only

If you prefer not to use Terraform:

```bash
# Set variables
export PROJECT_ID="your-project-id"
export ZONE="us-central1-a"
export MY_IP="$(curl -s ifconfig.me)/32"

# Download startup script
curl -O https://raw.githubusercontent.com/lhzn-io/kanoa-mlops/main/infrastructure/gcp/scripts/startup.sh

# Create VM
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
    --tags=vllm-server \
    --metadata-from-file=startup-script=startup.sh

# Create firewall rules
gcloud compute firewall-rules create kanoa-allow-vllm-api \
    --project=$PROJECT_ID \
    --allow=tcp:8000 \
    --source-ranges=$MY_IP \
    --target-tags=vllm-server

gcloud compute firewall-rules create kanoa-allow-ssh \
    --project=$PROJECT_ID \
    --allow=tcp:22 \
    --source-ranges=$MY_IP \
    --target-tags=vllm-server

# Get external IP
gcloud compute instances describe kanoa-vllm-server \
    --zone=$ZONE \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

---

## Usage

### Test the API

```bash
# Health check
curl http://EXTERNAL_IP:8000/health

# List models
curl http://EXTERNAL_IP:8000/v1/models

# Chat completion
curl http://EXTERNAL_IP:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "allenai/Molmo-7B-D-0924",
        "messages": [{"role": "user", "content": "Hello!"}]
    }'
```

### Use with kanoa

```python
from kanoa.backends import VLLMBackend

backend = VLLMBackend(
    api_base="http://EXTERNAL_IP:8000/v1",
    model="allenai/Molmo-7B-D-0924"
)
```

### Manage Instance

```bash
# SSH into instance
gcloud compute ssh kanoa-vllm-server --zone=us-central1-a

# View vLLM logs
gcloud compute ssh kanoa-vllm-server --zone=us-central1-a \
    --command="docker logs -f kanoa-vllm"

# Stop instance (save costs)
gcloud compute instances stop kanoa-vllm-server --zone=us-central1-a

# Start instance
gcloud compute instances start kanoa-vllm-server --zone=us-central1-a
```

---

## Cost Management

### Monitor Spending

```bash
# View current month costs (requires billing export)
gcloud billing accounts list
```

Or use [GCP Billing Console](https://console.cloud.google.com/billing).

### Set Budget Alerts

1. Go to [Billing → Budgets & Alerts](https://console.cloud.google.com/billing/budgets)
2. Create budget: $100/month
3. Set alerts at 50%, 80%, 100%

### Auto-Shutdown

The VM automatically shuts down after 30 minutes of no API activity.

To change the timeout:

```hcl
# In terraform.tfvars
idle_timeout_minutes = 60  # 1 hour
```

### Manual Cleanup

```bash
# Stop (preserves disk, no compute charges)
gcloud compute instances stop kanoa-vllm-server --zone=us-central1-a

# Delete (removes everything)
terraform destroy
# OR
gcloud compute instances delete kanoa-vllm-server --zone=us-central1-a
gcloud compute firewall-rules delete kanoa-allow-vllm-api kanoa-allow-ssh
```

---

## Troubleshooting

### "Quota exceeded" Error

Request GPU quota increase (see Prerequisites section).

### "Permission denied" Error

```bash
# Ensure correct project
gcloud config set project YOUR_PROJECT_ID

# Re-authenticate
gcloud auth application-default login
```

### VM Created but vLLM Not Running

```bash
# SSH and check startup logs
gcloud compute ssh kanoa-vllm-server --zone=us-central1-a
sudo cat /var/log/kanoa-startup.log

# Check Docker
docker ps
docker logs kanoa-vllm
```

### Can't Connect to API

1. Check your IP hasn't changed: `curl -s ifconfig.me`
2. Update firewall rule with new IP
3. Verify VM is running: `gcloud compute instances list`

---

## Security Notes

- **Firewall rules** restrict access to your IP only
- **No secrets in repo** - `terraform.tfvars` is gitignored
- **HF tokens** passed via instance metadata (not in startup script)
- **OS Login enabled** for SSH key management

For production, consider:

- VPC with private IP + Cloud NAT
- Identity-Aware Proxy (IAP) for SSH
- Secret Manager for HF tokens
