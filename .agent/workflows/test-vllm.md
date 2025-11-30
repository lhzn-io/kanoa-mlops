---
description: How to verify the vLLM server is running correctly
---

1. **Check Container Status**

   ```bash
   docker compose -f docker/vllm/docker-compose.yml ps
   ```

   Ensure the `vllm` service is `Up (healthy)`.

2. **Check Logs**

   ```bash
   docker compose -f docker/vllm/docker-compose.yml logs -f vllm
   ```

   Look for "Uvicorn running on <http://0.0.0.0:8000>".

3. **Run Smoke Test**

   ```bash
   python examples/quickstart-molmo.py
   ```

   (Or `quickstart-gemma3.py` if running Gemma).
