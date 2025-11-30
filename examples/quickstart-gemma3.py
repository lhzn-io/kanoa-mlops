"""
Quickstart example for kanoa with vLLM Gemma 3 server.

This example demonstrates how to use kanoa's VLLMBackend to connect
to a local vLLM server hosting the Gemma 3 multimodal model.

Prerequisites:
1. vLLM server running with Gemma 3 (see docker/vllm/README.md)
2. kanoa installed with vllm extra: pip install -e .[vllm]
"""

import matplotlib.pyplot as plt
import numpy as np
from kanoa.backends import VLLMBackend


def create_sample_plot():
    """Create a sample plot for demonstration."""
    # Generate sample data
    x = np.linspace(0, 10, 100)
    y1 = np.sin(x) * np.exp(-x / 5)
    y2 = np.cos(x) * np.exp(-x / 5)

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, y1, label="Damped Sine", linewidth=2, color="#1f77b4")
    ax.plot(x, y2, label="Damped Cosine", linewidth=2, color="#ff7f0e")
    ax.set_xlabel("Time (t)")
    ax.set_ylabel("Amplitude")
    ax.set_title("Damped Oscillation Analysis")
    ax.legend()
    ax.grid(True, alpha=0.3)

    return fig


def main():
    print("=" * 60)
    print("kanoa + vLLM Gemma 3 Quickstart")
    print("=" * 60)
    print()

    # Initialize VLLMBackend
    print("Connecting to vLLM server...")
    backend = VLLMBackend(
        api_base="http://localhost:8000/v1",
        model="google/gemma-3-12b-it",
        temperature=0.7,
    )
    print("✓ Connected to vLLM server")
    print()

    # Create sample plot
    print("Creating sample plot...")
    fig = create_sample_plot()
    print("✓ Plot created")
    print()

    # Interpret the plot
    print("Interpreting plot with Gemma 3...")
    print("-" * 60)

    result = backend.interpret(
        fig=fig,
        data=None,
        context="Physics experiment data showing damped harmonic motion",
        focus="Analyze the decay rate and phase relationship",
        kb_context=None,
        custom_prompt=None,
    )

    print(result.text)
    print("-" * 60)
    print()

    # Show usage information
    if result.usage:
        print(
            f"Tokens used: {result.usage.input_tokens} input, "
            f"{result.usage.output_tokens} output"
        )
        print(f"Estimated cost: ${result.usage.cost:.4f}")
    print()

    # Save the plot
    output_path = "gemma3_analysis.png"
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"✓ Plot saved to {output_path}")

    plt.close(fig)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Ensure vLLM server is running with Gemma 3")
        print("2. Check environment variables: MODEL_NAME=gemma-3-12b")
        print("3. Verify server health: curl http://localhost:8000/health")
