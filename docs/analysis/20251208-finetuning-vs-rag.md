# Analysis: Fine-Tuning vs. RAG for Domain Expertise
**Date**: December 8, 2025
**Status**: Draft
**Author**: Kanoa MLOps Agent

## Executive Summary

This document analyzes the "Build vs. Buy" (Train vs. Retrieve) dilemma for adding domain expertise (academic papers, proprietary docs) to the `kanoa` ecosystem.

**Recommendation**: **Do not abandon RAG.**
For a Q&A system over proprietary documentation, **RAG is superior for accuracy**, while **Fine-tuning is superior for jargon and reasoning style.**

## 1. The Core Distinction

| Feature | **RAG (Retrieval Augmented Generation)** | **Fine-Tuning (Continual Pre-training)** |
| :--- | :--- | :--- |
| **Goal** | "Open book" exam. The model looks up facts. | "Closed book" exam. The model memorizes facts. |
| **Accuracy** | High. Can cite specific pages/paragraphs. | Medium/Low. Prone to hallucination. |
| **Updates** | Instant. Just add a PDF to the vector DB. | Slow. Requires re-training (burning GPU hours). |
| **Best For** | Specific facts, proprietary data, citing sources. | Domain jargon, specific coding styles, output formats. |

**Verdict**: For a Q&A system over *proprietary documentation*, RAG is required. You cannot trust a fine-tuned model to accurately recall a specific clause in a contract or a specific value from a table in a PDF without hallucinating.

## 2. The "Hybrid" Sweet Spot

The industry standard is **RAG + Fine-Tuning**:
1.  **RAG**: Provides the *content* (the "what").
2.  **Fine-Tuning**: Teaches the model *how* to interpret that content (the "how").

You fine-tune the model not to *memorize* the papers, but to become an expert at **reading** them. You train it on examples like: *"Here is a messy excerpt from a biology paper; extract the methodology."*

## 3. GPU Hour Estimates (The Cost of Burning)

**Scenario**: Corpus of 10,000 academic papers (~50M - 100M tokens).
**Target Model**: Llama 3 8B or Molmo 7B.

### A. QLoRA Fine-Tuning (The "Style" Tune)
*   **Goal**: Teach the model to speak "biotech" or "legal", or to follow complex instructions.
*   **Hardware**: RTX 5080 (16GB) is perfect for this.
*   **Time**: ~2-4 hours.
*   **Cost**: Negligible (electricity).
*   **Result**: The model sounds smart but doesn't know your specific secrets.

### B. Continual Pre-training (The "Knowledge" Injection)
*   **Goal**: Force the model to memorize the 10,000 papers.
*   **Requirement**: Process billions of tokens to make the knowledge "stick" without catastrophic forgetting.
*   **Hardware**:
    *   **RTX 5080**: Likely insufficient VRAM for efficient batch sizes. Memory bandwidth bottleneck.
    *   **Jetson Thor (128GB)**: Has the VRAM, but the compute (TFLOPS) is lower than a cluster of H100s.
*   **Estimated Time (Single Node)**:
    *   To effectively learn a new domain, you might need ~1-5 Billion tokens of training.
    *   On a single high-end node: **~100 - 300 GPU hours**.
*   **Risk**: High. Models often become "dumber" at general tasks after heavy domain injection unless carefully mixed with general data.

## 4. Recommendation for `kanoa`

Given the roadmap and hardware:

1.  **Stick to RAG for Knowledge**: Use the Jetson Thor's massive 128GB memory to run a **huge context window** (e.g., 128k - 1M context). You don't need to retrieve small chunks; you can stuff entire papers into the context of **Gemma 3** or **Llama 4**. This is "Long-Context RAG" and it beats fine-tuning for accuracy.

2.  **Fine-Tune for "Tool Use"**: Use the RTX 5080 to fine-tune a small adapter (LoRA) that makes the model really good at using `kanoa`'s specific tools (e.g., "Plot this dataframe").
    *   **Cost**: ~2 hours / week.
    *   **Benefit**: The model stops making syntax errors when calling the library.

**Strategic Pivot**: Instead of "Fine-tuning for Knowledge," look into **"Context Caching"**. The Jetson Thor can keep the KV cache of core documentation loaded in memory, making RAG queries over them instant without re-processing the tokens every time.
