import os
import time
import base64
import random
import requests
from pathlib import Path
from io import BytesIO
from PIL import Image
from openai import OpenAI

# === Configuration ===
OPENAI_API_KEY ="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"
OUTPUT_DIR = Path("test_ai_images_single")
OUTPUT_DIR.mkdir(exist_ok=True)

TEST_PRODUCT = {
    "name": "Commercial Grade Rubber Sheet – Linear Meter",
    "image_url": "https://rubberco.co.uk/cdn/shop/products/commercial-grade-rubber-sheet-linear-meter-888058_720x.jpg?v=1662146059",
    "description": "Black rubber sheet sold by the metre, heavy-duty industrial floor/lining material"
}

def download_and_encode_image(image_url: str) -> str:
    print("Download & encode image from:", image_url)
    resp = requests.get(image_url, timeout=15)
    resp.raise_for_status()
    img = Image.open(BytesIO(resp.content))
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b = buf.getvalue()
    s = base64.b64encode(b).decode("utf-8")
    print("Encoded base64 length:", len(s))
    return s

def analyze_with_vision(client, image_url: str, product_name: str) -> str:
    print("Running vision analysis for:", product_name)
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Analyze this product image for: {product_name}"},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        max_tokens=150
    )
    desc = resp.choices[0].message.content.strip()
    print("Vision result:", desc)
    return desc

def create_dynamic_prompt(client, product_name: str, vision_desc: str) -> str:
    print("Creating dynamic prompt …")
    analysis_prompt = (
        f"You are analyzing a product to help generate a realistic customer review photo.\n\n"
        f"Product Name: {product_name}\n"
        f"Product Description: {vision_desc}\n\n"
        f"Analyze this product and provide:\n"
        f"1. Environment: Where is this product typically installed/used?\n"
        f"2. Installation Surface: What is it installed on?\n"
        f"3. Viewing Angle: Best angle for a customer photo?\n"
        f"4. Key Visual: What should be clearly visible?\n\n"
        f"Respond in this EXACT format (be brief):\n"
        f"ENVIRONMENT: [indoor home/outdoor/commercial/industrial/etc]\n"
        f"SURFACE: [stairs/floor/wall/door/ground/etc]\n"
        f"ANGLE: [from above/side angle/close-up/etc]\n"
        f"FOCUS: [what to show clearly]"
    )
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role":"user","content":analysis_prompt}],
        max_tokens=150,
        temperature=0.3
    )
    analysis = resp.choices[0].message.content.strip()
    print("Context analysis:", analysis)
    # parse basic
    lines = analysis.split("\n")
    ctx = {}
    for line in lines:
        if line.startswith("ENVIRONMENT:"):
            ctx['environment'] = line.split("ENVIRONMENT:")[1].strip()
        elif line.startswith("SURFACE:"):
            ctx['surface'] = line.split("SURFACE:")[1].strip()
        elif line.startswith("ANGLE:"):
            ctx['angle'] = line.split("ANGLE:")[1].strip()
        elif line.startswith("FOCUS:"):
            ctx['focus'] = line.split("FOCUS:")[1].strip()
    lighting = "natural window lighting"
    if "outdoor" in ctx.get('environment', '').lower():
        lighting = "natural daylight, clear weather"
    elif "commercial" in ctx.get('environment', '').lower() or "industrial" in ctx.get('environment', '').lower():
        lighting = "standard facility lighting"
    prompt = (
        f"A realistic customer photo showing {product_name} installed in {ctx.get('environment','')}."
        f"{vision_desc} The product is shown on/at {ctx.get('surface','')}, photographed {ctx.get('angle','')}. "
        f"The photo clearly shows {ctx.get('focus','')}. Taken with a smartphone camera. {lighting}. "
        f"Natural composition with minor imperfections typical of customer photos. "
        f"This must look like a real customer took this photo with their phone - NOT a professional product shot, NOT a marketing photo. "
        f"The setting must match where this product is actually used in real life. Photorealistic customer review photo style."
    )
    print("Generated prompt:", prompt)
    return prompt

def generate_image(client, prompt: str, product_name: str) -> Path:
    print("Generating image …")
    resp = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
        quality="high",
        n=1
    )
    data = resp.data[0]
    image_bytes = None
    if hasattr(data, "b64_json") and data.b64_json:
        image_bytes = base64.b64decode(data.b64_json)
    elif hasattr(data, "url") and data.url:
        image_bytes = requests.get(data.url, timeout=30).content
    else:
        raise RuntimeError("No image output in response")
    img = Image.open(BytesIO(image_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")
    safe_name = product_name.replace(" ", "_").lower()[:30]
    filename = f"{safe_name}_{random.randint(1000,9999)}.jpg"
    filepath = OUTPUT_DIR / filename
    img.save(filepath, "JPEG", quality=90)
    print("Saved generated image to:", filepath)
    return filepath

def main():
    print("=== START SINGLE TEST ===")
    client = OpenAI(api_key=OPENAI_API_KEY)
    p = TEST_PRODUCT
    try:
        # use URL directly for vision step (skip base64 for now)
        vision_desc = analyze_with_vision(client, p["image_url"], p["name"])
    except Exception as e:
        print("Vision step failed, falling back to description:", e)
        vision_desc = p["description"]
    prompt = create_dynamic_prompt(client, p["name"], vision_desc)
    try:
        generated_path = generate_image(client, prompt, p["name"])
        print("SUCCESS: Generated image at:", generated_path.absolute())
    except Exception as e:
        print("Image generation failed:", e)
    print("=== END SINGLE TEST ===")

if __name__ == "__main__":
    main()
