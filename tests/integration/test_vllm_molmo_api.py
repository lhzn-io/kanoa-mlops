import base64
import io

import matplotlib.pyplot as plt
import numpy as np
import requests
from PIL import Image

MODEL_NAME = "allenai/Molmo-7B-D-0924"
API_URL = "http://localhost:8000/v1/chat/completions"

def query_molmo(prompt, image_url):
    headers = {"Content-Type": "application/json"}
    data = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        "max_tokens": 200,
        "temperature": 0.1
    }

    response = requests.post(API_URL, headers=headers, json=data)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

def test_boardwalk_photo():
    print("\n[TEST] Testing Boardwalk Photo (URL -> Base64)...")
    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/960px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"

    try:
        # Download image locally first to avoid container networking issues
        print(f"   Downloading {image_url}...")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        img_resp = requests.get(image_url, headers=headers)
        img_resp.raise_for_status()

        # Convert to Base64
        img = Image.open(io.BytesIO(img_resp.content))
        # Resize if too large (Molmo handles large images well, but let's be safe and fast)
        if max(img.size) > 1024:
            img.thumbnail((1024, 1024))

        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        base64_url = f"data:image/jpeg;base64,{img_str}"

        description = query_molmo("Describe this image in detail.", base64_url)
        print(f"[OK] Response:\n{description}")
    except Exception as e:
        print(f"[ERROR] Failed: {e}")

def test_complex_plot():
    print("\n[TEST] Testing Complex Matplotlib Plot (Base64)...")

    # Generate Plot
    fig, axs = plt.subplots(2, 2, figsize=(10, 8))

    # 1. Sine Wave
    x = np.linspace(0, 10, 100)
    axs[0, 0].plot(x, np.sin(x), 'r-', linewidth=2)
    axs[0, 0].set_title('Sine Wave')
    axs[0, 0].grid(True)

    # 2. Scatter Plot
    np.random.seed(42)
    axs[0, 1].scatter(np.random.rand(50), np.random.rand(50), c=np.random.rand(50), cmap='viridis')
    axs[0, 1].set_title('Random Scatter')

    # 3. Histogram
    axs[1, 0].hist(np.random.randn(1000), bins=30, color='green', alpha=0.7)
    axs[1, 0].set_title('Normal Distribution')

    # 4. Bar Chart
    categories = ['A', 'B', 'C', 'D']
    values = [15, 30, 45, 10]
    axs[1, 1].bar(categories, values, color='purple')
    axs[1, 1].set_title('Category Values')

    plt.tight_layout()

    # Convert to Base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)

    image_url = f"data:image/png;base64,{img_str}"

    try:
        description = query_molmo("Analyze this multi-panel plot. What does each subplot show?", image_url)
        print(f"[OK] Response:\n{description}")
    except Exception as e:
        print(f"[ERROR] Failed: {e}")

if __name__ == "__main__":
    print("[INFO] Starting Integration Tests for Molmo Vision...")
    test_boardwalk_photo()
    test_complex_plot()
