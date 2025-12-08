# Examples

Interactive Jupyter notebooks demonstrating how to deploy and use vLLM servers on GCP.

## Quickstart Notebooks

| Notebook | Model | Description |
|----------|-------|-------------|
| [quickstart-molmo.ipynb](./quickstart-molmo.ipynb) | Molmo 7B | Multimodal model for text + image understanding |
| [quickstart-gemma3.ipynb](./quickstart-gemma3.ipynb) | Gemma 3 (4B/12B/27B) | Google's instruction-tuned language model |

## Prerequisites

Before running these notebooks:

1. **GCP Setup**

   ```bash
   gcloud auth application-default login
   ```

2. **Terraform** (>= 1.5.0)

   ```bash
   # macOS
   brew install terraform

   # Linux
   # See https://developer.hashicorp.com/terraform/install
   ```

3. **Python Dependencies**

   ```bash
   pip install kanoa requests jupyter
   ```

4. **Hugging Face Token** (for gated models like Gemma)
   - Create token at <https://huggingface.co/settings/tokens>
   - Accept model terms (e.g., <https://huggingface.co/google/gemma-3-4b-it>)

## Running Notebooks

```bash
# From repo root
cd examples
jupyter notebook
```

Or open directly in VS Code with the Jupyter extension.

## Cost Estimates

| Model | GPU | Hourly Cost |
|-------|-----|-------------|
| Molmo 7B | L4 (24GB) | ~$0.70 |
| Gemma 3 4B | L4 (24GB) | ~$0.70 |
| Gemma 3 12B | L4 (24GB) | ~$0.70 |
| Gemma 3 27B | A100 (80GB) | ~$3.00 |

⚠️ **Remember**: The notebooks include automatic 30-minute idle shutdown, but always run the **Cleanup** cell when done!
