# Model Presets for kanoa-mlops

Pre-configured model settings for quick deployment.

## Available Presets

| Preset | Model | VRAM | GPU | Cost/hr | Use Case |
|--------|-------|------|-----|---------|----------|
| `molmo-7b` | Molmo-7B-D | ~14GB | L4 | ~$0.70 | Chart/image analysis |
| `gemma3-4b` | Gemma 3 4B | ~8GB | L4 | ~$0.70 | Fast multimodal |
| `gemma3-12b` | Gemma 3 12B | ~24GB | L4 | ~$0.70 | Quality multimodal |
| `gemma3-27b` | Gemma 3 27B | ~54GB | A100 | ~$3.00 | Best quality |
| `llama3-8b` | Llama 3.1 8B | ~16GB | L4 | ~$0.70 | Text-only tasks |

## Usage

```bash
# Deploy a specific model
make deploy-molmo
make deploy-gemma3-4b
make deploy-gemma3-12b

# Check status
make status

# Destroy when done
make destroy
```

## Gated Models

Gemma 3 and Llama 3 require HuggingFace authentication:

1. Accept model license on HuggingFace
2. Get API token from [HuggingFace Settings](https://huggingface.co/settings/tokens)
3. Add to `terraform.tfvars`:

```hcl
hf_token = "hf_xxxxxxxxxxxxxxxxxxxxx"
```

## Custom Presets

Create your own preset by copying an existing one:

```bash
cp presets/molmo-7b.tfvars presets/my-model.tfvars
# Edit with your model settings
```

Then add a Makefile target:

```makefile
deploy-mymodel:
    @$(MAKE) _deploy WORKSPACE=mymodel PRESET=my-model
```

## Memory Guidelines

| Model Size | Min VRAM | Recommended GPU |
|------------|----------|-----------------|
| 1-4B | 8GB | T4, L4 |
| 7-8B | 16GB | T4, L4 |
| 12-13B | 24GB | L4, A10G |
| 27-34B | 48GB | A100 40GB |
| 70B+ | 80GB+ | A100 80GB, 2x A100 |
