"""
Standalone test for GPT-4 Vision + DALL-E 3 image generation
Simulates a 'real customer photo' of a given product.
"""
import base64
import random
import requests
from io import BytesIO
from pathlib import Path
from PIL import Image
from openai import OpenAI

# === Configuration ===
OPENAI_API_KEY="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"  # 🔹 Replace with your actual API key
OUTPUT_DIR = Path("generated_review_images")
OUTPUT_DIR.mkdir(exist_ok=True)

# === Test product sample ===
TEST_PRODUCT = {
    "name":"Commercial Rubber Sheet Linear Metre Durable Heavy Duty Rubber for Sealing, Insulation & Protection Temperature & Chemical Resistan",
    "image_url": "https://rubberco.co.uk/cdn/shop/files/AF5E642A-F1A5-4AA9-A1AA-10BA2163B07A_720x.png?v=1760307434",
}

# === Initialize client ===
client = OpenAI(api_key=OPENAI_API_KEY)


def analyze_with_vision(image_url: str, product_name: str) -> str:
    """Use GPT-4o-mini Vision to analyze a product image."""
    print("\n👁️ Analyzing product image with GPT-4o-mini Vision...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Describe this product: {product_name}. "
                                    "Focus on its material, color, and intended installation. "
                                    "Keep it under 3 sentences.",
                        },
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            max_tokens=100,
        )
        desc = response.choices[0].message.content.strip()
        print(f"✅ Vision analysis complete:\n{desc}\n")
        return desc
    except Exception as e:
        print(f"❌ Vision analysis failed: {e}")
        return ""


def create_gpt_image_prompt(product_name: str, vision_description: str) -> str:
    """Compose a realistic prompt for GPT-Image-1."""
    templates = [
        f"Realistic customer photo showing newly installed {product_name}. {vision_description} "
        "Taken indoors with a smartphone in natural light. Slightly imperfect framing. "
        "Photorealistic, real-world review photo style.",

        f"Authentic smartphone photo of {product_name} in a home setting. {vision_description} "
        "Natural lighting, realistic environment, and small imperfections in composition.",

        f"Homeowner photo of {product_name} installed on stairs. {vision_description} "
        "Taken casually with a phone camera, not professional lighting. Real customer review look."
    ]
    
    
    prompt = f"A realistic customer photo showing {product_name} generate a image that should match the product use case if there is a floor mat that should be shown in home not on some other place if product is for commercial use case that should be at commercial place by getting vision description you will know what is the use case of the product make no mistakes be tight. {vision_description} .This must look like a real person took this photo with their phone to share in a product review - not a professional or marketing photo."
        
    print(f"🧾 Generated GPT-Image-1 Prompt:\n{prompt}\n")
    return prompt


def generate_with_gpt_image(prompt: str) -> str:
    """Generate customer photo with GPT-Image-1 and handle both URL and base64 outputs."""
    print("🎨 Generating image with GPT-Image-1...")
    try:
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            n=1,
            quality="high"
        )

        # Case 1: Image URL
        if hasattr(response.data[0], "url") and response.data[0].url:
            url = response.data[0].url
            print(f"✅ Image generated successfully!\nURL: {url}\n")
            return url

        # Case 2: Base64 image data
        elif hasattr(response.data[0], "b64_json") and response.data[0].b64_json:
            print("✅ Image generated successfully (base64 data received).")
            img_data = base64.b64decode(response.data[0].b64_json)

            filename = f"generated_{random.randint(1000,9999)}.jpg"
            path = OUTPUT_DIR / filename
            with open(path, "wb") as f:
                f.write(img_data)

            print(f"💾 Image saved locally: {path.resolve()}\n")
            return str(path.resolve())

        else:
            print("⚠️ No valid image data found in response.")
            return ""

    except Exception as e:
        print(f"❌ GPT-Image-1 generation failed: {e}")
        return ""


def describe_generated_image(image_path: str):
    """Use GPT-4o-mini Vision to describe what GPT-Image-1 generated."""
    try:
        print("🔍 Verifying generated image content with GPT-4o-mini Vision...")
        with open(image_path, "rb") as f:
            img_bytes = f.read()

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe what you see in this image."},
                        {"type": "image", "image": img_bytes},
                    ],
                }
            ],
            max_tokens=100,
        )

        desc = response.choices[0].message.content.strip()
        print(f"🧠 GPT-4o-mini says:\n{desc}\n")
    except Exception as e:
        print(f"❌ Post-verification failed: {e}")


def download_image(url: str, filename: str) -> Path | None:
    """Download generated image from URL to local folder."""
    try:
        print("💾 Downloading generated image...")
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            print(f"❌ Failed to download image: HTTP {r.status_code}")
            return None

        img = Image.open(BytesIO(r.content))
        if img.mode != "RGB":
            img = img.convert("RGB")

        path = OUTPUT_DIR / filename
        img.save(path, "JPEG", quality=90)
        print(f"✅ Image saved: {path.resolve()}\n")
        return path
    except Exception as e:
        print(f"❌ Error saving image: {e}")
        return None


def main():
    print("=" * 90)
    print("🧪 TESTING GPT-4 VISION + GPT-IMAGE-1 IMAGE GENERATION")
    print("=" * 90)

    product = TEST_PRODUCT["name"]
    image_url = TEST_PRODUCT["image_url"]

    # Step 1: Analyze product
    vision_desc = analyze_with_vision(image_url, product)
    if not vision_desc:
        vision_desc = "A metallic stair edging designed for home staircases."

    # Step 2: Build prompt
    image_prompt = create_gpt_image_prompt(product, vision_desc)

    # Step 3: Generate image
    generated_output = generate_with_gpt_image(image_prompt)
    if not generated_output:
        print("❌ Test failed: No image returned.")
        return

    # Step 4: Handle URL or file
    if generated_output.startswith("http"):
        filename = f"{product.replace(' ', '_').lower()}_{random.randint(1000,9999)}.jpg"
        local_path = download_image(generated_output, filename)
    else:
        local_path = Path(generated_output)

    if not local_path:
        print("⚠️ Could not save the image locally.")
    else:
        # Step 5: Auto verify what GPT generated
        describe_generated_image(str(local_path))
        print("✅ TEST SUCCESSFULLY COMPLETED!")
        print(f"📍 Local file: {local_path.absolute()}")

    print("=" * 90)
    print("💰 Approximate Cost per Run:")
    print("- GPT-4o-mini Vision: ~$0.002")
    print("- GPT-Image-1 (1024×1024): ~$0.04")
    print("- Total: ~$0.042")
    print("=" * 90)


if __name__ == "__main__":
    main()