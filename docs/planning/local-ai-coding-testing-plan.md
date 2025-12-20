# Testing Plan: Local AI Coding Setup Documentation

## Test Environment

**Fresh Install Recommended:**

- Clean VSCode (or test profile)
- No existing Continue.dev extension
- Fresh conda environment
- Known GPU (RTX 4090/5080 for optimal testing)

**Create Test Profile:**

```bash
# VSCode test profile (avoids polluting main config)
code --user-data-dir /tmp/vscode-test-local-ai
```

---

## Test Checklist

### Phase 1: Prerequisites (5 min)

- [ ] Verify Python 3.11+ installed: `python --version`
- [ ] Verify Docker running: `docker ps`
- [ ] Verify NVIDIA drivers: `nvidia-smi`
- [ ] No existing vLLM on port 8000: `lsof -i :8000`
- [ ] No existing Ollama on port 11434: `lsof -i :11434`

### Phase 2: Quick Start (10 min)

**Follow:** `user_guide/local-ai-coding-setup.md` Quick Start section

- [ ] Step 1: vLLM starts successfully

  ```bash
  # Start vLLM with AllenAI Olmo 3 (32B)
  kanoa mlops serve vllm olmo3
  ```

  - Verify: `curl http://localhost:8000/v1/models`
  - Expected: JSON response with model list

- [ ] Step 2: Ollama starts successfully

  ```bash
  # Start Ollama service
  kanoa mlops serve ollama

  # Pull embedding model (one-time) - must run inside container
  docker exec -it kanoa-ollama ollama pull nomic-embed-text
  ```

  - Verify: `docker exec -it kanoa-ollama ollama list` shows nomic-embed-text
  - Verify: `curl http://localhost:11434/api/tags`

- [ ] Step 3: Continue.dev installs
  - Open test VSCode
  - Extensions → Search "Continue"
  - Install
  - Verify: `Continue` sidebar appears

- [ ] Step 4: Config created

  ```bash
  cat ~/.continue/config.json
  ```

  - Verify: Contains vLLM apiBase
  - Verify: Contains Ollama embeddings provider

- [ ] Step 5: Autocomplete works
  - Open any Python file
  - Type: `def hello_world():`
  - Wait <1 second
  - Expected: Gray suggestion appears
  - Press Tab to accept

- [ ] Step 6: Chat works
  - Press `Cmd/Ctrl+L`
  - Type: `@codebase Where is the main function?`
  - Wait 5-10 seconds (first index)
  - Expected: Response with code references

### Phase 3: Troubleshooting (5 min)

Test that troubleshooting steps work:

- [ ] **Scenario: Autocomplete not appearing**
  - Stop vLLM: `docker stop $(docker ps -q)`
  - Try autocomplete → should fail
  - Follow troubleshooting step 1
  - Restart vLLM
  - Verify autocomplete works again

- [ ] **Scenario: Slow autocomplete**
  - Check current latency
  - Follow "Autocomplete Too Slow" section
  - Reduce `--max-model-len` to 2048
  - Restart vLLM
  - Verify faster response

- [ ] **Scenario: No search results**
  - Delete index: `rm -rf ~/.continue/index/`
  - Try `@codebase` → no results initially
  - Wait for re-indexing notification
  - Retry → should work

### Phase 4: Verification (2 min)

Run through verification checklist from docs:

- [ ] vLLM responds: `curl http://localhost:8000/v1/models`
- [ ] Ollama running: `ollama list`
- [ ] nomic-embed-text installed: `ollama list | grep nomic`
- [ ] Continue installed: `code --list-extensions | grep Continue`
- [ ] config.json exists: `cat ~/.continue/config.json`
- [ ] Autocomplete appears in <300ms
- [ ] `@codebase` returns results
- [ ] Network tab shows NO external API calls

### Phase 5: Performance Check (Optional, 5 min)

If on reference hardware (RTX 4090):

- [ ] Measure autocomplete latency (should be 250-350ms)

  ```bash
  # See developer guide for benchmark script
  ```

- [ ] Check GPU memory usage: `nvidia-smi`
  - Should be 21-22GB / 24GB for 70B AWQ
- [ ] Test chat throughput
  - Ask long question
  - Count tokens/second (should be 20-25 tok/s)

---

## Known Issues to Watch For

1. **First autocomplete takes 5+ seconds**
   - Expected: Model loading into GPU
   - Not a bug, just warm-up time

2. **Codebase indexing takes 10+ minutes on large repos**
   - Expected for >5k files
   - Should only happen once

3. **GPU memory error on 16GB GPUs with 70B model**
   - Expected: Use 34B model instead
   - See hardware table in docs

4. **Continue sidebar not appearing**
   - Reload window: Cmd/Ctrl+Shift+P → "Reload Window"

---

## Test Environments

### Minimal Test (RTX 4090)

```bash
# Clean environment
docker stop $(docker ps -q)
killall ollama
rm -rf ~/.continue/
code --user-data-dir /tmp/vscode-test
```

### Alternative Hardware Tests

- [ ] RTX 5080 (16GB) with 34B model
- [ ] RTX 3090 (24GB) with 70B AWQ
- [ ] Multi-GPU setup (if available)

---

## Success Criteria

Documentation passes testing if:

1. ✅ Fresh user can complete Quick Start in <15 minutes
2. ✅ Autocomplete appears reliably in <300ms
3. ✅ Troubleshooting steps resolve common issues
4. ✅ All verification checks pass
5. ✅ No external API calls detected

---

## Test Execution Log

**Date:** ___________
**Tester:** ___________
**Hardware:** ___________
**Time to Complete:** ___________

**Issues Found:**
-

-
-

**Documentation Updates Needed:**
-

-
-

**Overall Status:** [ ] Pass [ ] Fail [ ] Pass with minor issues
