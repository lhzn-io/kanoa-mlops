# GCP Infrastructure for kanoa-mlops

Terraform configuration for deploying vLLM on Google Cloud Platform with GPU support.

## Features

- **NVIDIA L4 GPU** - 24GB VRAM, ideal for 7B-13B models
- **Auto-shutdown** - VM automatically stops after configurable idle period
- **Instance scheduling** - Optional auto start/stop at specific times
- **Secure by default** - Firewall rules restrict access to your IP only
- **Cost-optimized** - ~$0.70/hr for L4 GPU, with auto-shutdown to prevent waste

## Prerequisites

1. **GCP Account** with billing enabled
2. **gcloud CLI** installed and authenticated:

   ```bash
   gcloud auth application-default login
   ```

3. **Terraform** >= 1.5.0:

   ```bash
   # macOS
   brew install terraform

   # Linux
   sudo apt-get install terraform
   ```

4. **GPU Quota** - Request L4 GPU quota if needed:

   ```bash
   # Check current quota
   gcloud compute regions describe us-central1 \
       --format="table(quotas.filter(metric:NVIDIA_L4_GPUS))"
   ```

## Quick Start

### 1. Configure Variables

```bash
cd infrastructure/gcp

# Copy example and edit with your values
cp terraform.tfvars.example terraform.tfvars

# Get your IP for firewall rules
echo "Your IP: $(curl -s ifconfig.me)/32"

# Edit terraform.tfvars with your project_id and IP
```

### 2. Deploy

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply (creates resources)
terraform apply
```

### 3. Use

After deployment, Terraform outputs useful commands:

```bash
# Get outputs
terraform output

# SSH to instance
$(terraform output -raw ssh_command)

# Test API
curl $(terraform output -raw vllm_health_endpoint)

# Stop instance (save costs)
$(terraform output -raw stop_command)

# Start instance
$(terraform output -raw start_command)
```

### 4. Cleanup

```bash
# Destroy all resources
terraform destroy
```

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `project_id` | GCP Project ID | (required) |
| `allowed_source_ranges` | CIDR ranges for API/SSH access | (required) |
| `model_name` | HuggingFace model ID | `allenai/Molmo-7B-D-0924` |
| `idle_timeout_minutes` | Auto-shutdown after idle (0 to disable) | `30` |
| `enable_schedule` | Enable time-based start/stop | `false` |
| `machine_type` | GCE machine type | `g2-standard-8` |

See `variables.tf` for all options.

## Cost Estimates

| Usage Pattern | Monthly Cost |
|---------------|-------------|
| 4 hrs/day, weekdays | ~$56 |
| With auto-shutdown (2 hrs actual) | ~$28 |
| 24/7 operation | ~$504 |

⚠️ **Set budget alerts** in GCP Console to avoid unexpected charges.

## Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                        GCP Project                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   VPC Network                         │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │            GCE Instance (g2-standard-8)         │  │  │
│  │  │  ┌───────────────────────────────────────────┐  │  │  │
│  │  │  │         Docker Container                  │  │  │  │
│  │  │  │  ┌─────────────────────────────────────┐  │  │  │  │
│  │  │  │  │     vLLM OpenAI Server              │  │  │  │  │
│  │  │  │  │     - Molmo-7B-D                    │  │  │  │  │
│  │  │  │  │     - Port 8000                     │  │  │  │  │
│  │  │  │  └─────────────────────────────────────┘  │  │  │  │
│  │  │  └───────────────────────────────────────────┘  │  │  │
│  │  │                     │                           │  │  │
│  │  │              NVIDIA L4 GPU                      │  │  │
│  │  │                  (24GB)                         │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                        │                              │  │
│  │              Firewall (your IP only)                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                 │
└───────────────────────────┼─────────────────────────────────┘
                            │
                     Your Workstation
                    (kanoa client)
```

## Troubleshooting

### GPU Not Available

```bash
# Check GPU quota
gcloud compute regions describe us-central1 \
    --format="table(quotas.filter(metric:NVIDIA_L4_GPUS))"

# Try a different zone
zone = "us-central1-b"  # or us-central1-c, us-central1-f
```

### vLLM Not Starting

```bash
# SSH to instance
gcloud compute ssh kanoa-vllm-server --zone=us-central1-a

# Check startup logs
sudo cat /var/log/kanoa-startup.log

# Check Docker logs
docker logs kanoa-vllm
```

### Connection Refused

```bash
# Verify your IP in firewall rules
gcloud compute firewall-rules describe kanoa-allow-vllm-api

# Update if your IP changed
terraform apply -var='allowed_source_ranges=["NEW_IP/32"]'
```

## Integration with kanoa

```python
from kanoa.backends import VLLMBackend

# Use the terraform output for api_base
backend = VLLMBackend(
    api_base="http://EXTERNAL_IP:8000/v1",  # From terraform output
    model="allenai/Molmo-7B-D-0924"
)

result = backend.interpret(
    fig=my_figure,
    data=my_data,
    context="Analysis context",
    focus=None,
    kb_context=None,
    custom_prompt=None
)
```
