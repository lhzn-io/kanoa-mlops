# Model Troubleshooting & Known Issues

This guide documents known issues, workarounds, and specific configurations for models supported by `kanoa-mlops`.

## AllenAI Olmo 3 (32B-Think)

### Issue: Incoherent or Garbage Output
**Symptoms**: The model generates nonsensical text (e.g., "the fabric is knotty", random word associations) or gets stuck in repetitive loops, particularly when running via vLLM API.

**Cause**: This is a known incompatibility between the Olmo 3 architecture and vLLM's **Chunked Prefill** feature. Additionally, the model is sensitive to **FP8 KV Cache** quantization.

**Solution**:
When deploying Olmo 3 with vLLM (especially on Jetson Thor or other NVIDIA GPUs), use the following configuration:

1.  **Disable Chunked Prefill**: Remove `--enable-chunked-prefill` or explicitly set `--no-enable-chunked-prefill`.
2.  **Enforce Eager Execution**: Add `--enforce-eager`.
3.  **KV Cache Precision**: Set `--kv-cache-dtype auto` or `bfloat16`. Do **not** use `fp8`.

**Correct `docker-compose` Configuration**:

```yaml
command: >
  vllm serve
  --model allenai/Olmo-3-32B-Think
  --kv-cache-dtype auto       # Changed from fp8
  --enforce-eager             # Added
  # --enable-chunked-prefill  # REMOVED
  ...
```

### Prompt Format
Olmo 3 uses the **ChatML** format and supports a `<think>` tag for Chain-of-Thought reasoning.

```text
<|im_start|>system
You are a helpful AI assistant.<|im_end|>
<|im_start|>user
{user_prompt}<|im_end|>
<|im_start|>assistant
<think>
{reasoning_process}
</think>
{response}<|im_end|>
```

vLLM should automatically detect this template from the tokenizer.

---

## Molmo 7B / 72B

### Issue: Vision Encoder OOM
**Symptoms**: Out of Memory (OOM) errors during initialization, specifically related to the vision tower.

**Solution**: Ensure you are using the correct quantization (4-bit or 8-bit) if running on limited VRAM. For Jetson Thor, 4-bit is recommended for the 72B model.

---

## General vLLM Issues

### "Connection Refused" on Startup
**Cause**: The model is still loading weights into GPU memory.
**Solution**: Wait for the "Application startup complete" log message. Use the `/health` endpoint to check status.
