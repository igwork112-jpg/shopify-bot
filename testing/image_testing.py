"""
Complete test script for AI image generation workflow
Tests: Product URL → Download → GPT-4 Vision → Dynamic Prompt → GPT-Image-1
"""
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
OPENAI_API_KEY="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"  # 🔹 Replace with your actual API key
  # 🔹 Replace with your actual API key
OUTPUT_DIR = Path("test_ai_images")
OUTPUT_DIR.mkdir(exist_ok=True)

# === Real products from your stores ===
TEST_PRODUCTS = [
   
    {
        "name": "Commercial Grade Shock Absorbing Rubber Interlocking Gym Mats",
        "image_url": "https://rubberco.co.uk/cdn/shop/products/classico-rubber-interlocking-gym-mats40342_540x.jpg?v=1628247545",
        "description": "rubber floor mat for workshops and industrial use"
    },
   
]


def download_and_encode_image(image_url: str) -> str:
    """Step 1: Download product image and encode to base64"""
    print(f"\n📥 Step 1: Downloading product image...")
    print(f"   URL: {image_url}...")
    
    try:
        response = requests.get(image_url, timeout=15)
        if response.status_code != 200:
            print(f"   ❌ Failed: HTTP {response.status_code}")
            return None
        
        img = Image.open(BytesIO(response.content))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        img_bytes = buffered.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        print(f"   ✅ Downloaded and encoded ({len(img_base64)} chars)")
        return img_base64
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def analyze_with_vision(client, img_base64: str, product_name: str) -> str:
    """Step 2: Analyze product with GPT-4 Vision"""
    print(f"\n👁️ Step 2: Analyzing with GPT-4 Vision...")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Analyze this product image for: {product_name}

Describe in 2-3 sentences:
- The product's appearance, material, and color
- How it's designed to be installed or used
- Key visual features

Keep it concise and factual."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=150
        )
        
        description = response.choices[0].message.content.strip()
        print(f"   ✅ Analysis complete:")
        print(f"   {description}")
        return description
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def create_dynamic_prompt(client, product_name: str, vision_desc: str) -> str:
    """Step 3: Use AI to create context-appropriate prompt"""
    print(f"\n🤖 Step 3: Creating dynamic prompt with AI...")
    
    try:
        # Ask GPT-4 to analyze and determine context
        analysis_prompt = f"""You are analyzing a product to help generate a realistic customer review photo.

Product Name: {product_name}
Product Description: {vision_desc}

Analyze this product and provide:
1. Environment: Where is this product typically installed/used?
2. Installation Surface: What is it installed on?
3. Viewing Angle: Best angle for a customer photo?
4. Key Visual: What should be clearly visible?

Respond in this EXACT format (be brief):
ENVIRONMENT: [indoor home/outdoor/commercial/industrial/etc]
SURFACE: [stairs/floor/wall/door/ground/etc]
ANGLE: [from above/side angle/close-up/etc]
FOCUS: [what to show clearly]"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": analysis_prompt}],
            max_tokens=150,
            temperature=0.3
        )
        
        analysis = response.choices[0].message.content.strip()
        print(f"   ✅ AI Context Analysis:")
        for line in analysis.split('\n'):
            if line.strip():
                print(f"   {line}")
        
        # Parse analysis
        context = {}
        for line in analysis.split('\n'):
            if 'ENVIRONMENT:' in line:
                context['environment'] = line.split('ENVIRONMENT:')[1].strip()
            elif 'SURFACE:' in line:
                context['surface'] = line.split('SURFACE:')[1].strip()
            elif 'ANGLE:' in line:
                context['angle'] = line.split('ANGLE:')[1].strip()
            elif 'FOCUS:' in line:
                context['focus'] = line.split('FOCUS:')[1].strip()
        
        # Determine lighting
        env_lower = context.get('environment', '').lower()
        if 'outdoor' in env_lower:
            lighting = 'natural daylight, clear weather'
        elif 'commercial' in env_lower or 'industrial' in env_lower:
            lighting = 'standard facility lighting'
        else:
            lighting = 'natural window lighting'
        
        # Build final prompt
        final_prompt = (
            f"A realistic customer photo showing {product_name} installed in {context.get('environment', 'appropriate setting')}. "
            f"{vision_desc} "
            f"The product is shown on/at {context.get('surface', 'appropriate surface')}, photographed {context.get('angle', 'casually')}. "
            f"The photo clearly shows {context.get('focus', 'the installation')}. "
            f"Taken with a smartphone camera. {lighting}. "
            f"Natural composition with minor imperfections typical of customer photos. "
            f"This must look like a real customer took this photo with their phone - "
            f"NOT a professional product shot, NOT a marketing photo. "
            f"The setting must match where this product is actually used in real life. "
            f"Photorealistic customer review photo style."
        )
        
        print(f"\n   📝 Generated Prompt:")
        print(f"   {final_prompt[:200]}...")
        
        return final_prompt
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        # Fallback prompt
        return (
            f"A realistic customer photo showing {product_name} installed. "
            f"{vision_desc} "
            f"Taken with a smartphone in natural lighting. "
            f"Casual customer review photo style."
        )


def generate_image(client, prompt: str, product_name: str) -> Path:
    """Step 4: Generate customer photo with GPT-Image-1"""
    print(f"\n🎨 Step 4: Generating image with GPT-Image-1...")
    
    try:
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            quality="high",
            n=1
        )
        
        # Get image URL
        if hasattr(response.data[0], "url") and response.data[0].url:
            url = response.data[0].url
            print(f"   ✅ Image generated!")
            
            # Download
            img_response = requests.get(url, timeout=30)
            if img_response.status_code != 200:
                print(f"   ❌ Failed to download")
                return None
            
            img = Image.open(BytesIO(img_response.content))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save
            safe_name = product_name.replace(' ', '_').lower()[:30]
            filename = f"{safe_name}_{random.randint(1000,9999)}.jpg"
            filepath = OUTPUT_DIR / filename
            img.save(filepath, "JPEG", quality=90)
            
            print(f"   💾 Saved: {filepath.name}")
            return filepath
        
        else:
            print(f"   ❌ No image URL in response")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def main():
    print("=" * 100)
    print("🧪 TESTING COMPLETE AI IMAGE GENERATION WORKFLOW")
    print("=" * 100)
    print(f"Output directory: {OUTPUT_DIR.absolute()}")
    print(f"Testing {len(TEST_PRODUCTS)} products\n")
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    for idx, product in enumerate(TEST_PRODUCTS, 1):
        print(f"\n{'='*100}")
        print(f"TEST {idx}/{len(TEST_PRODUCTS)}: {product['name']}")
        print('='*100)
        
        # Step 1: Download product image
        img_base64 = download_and_encode_image(product['image_url'])
        if not img_base64:
            print("   ⏭️ Skipping to next product")
            continue
        
        # Step 2: Analyze with Vision
        vision_desc = analyze_with_vision(client, img_base64, product['name'])
        if not vision_desc:
            vision_desc = product['description']
            print(f"   ⚠️ Using fallback description")
        
        # Step 3: Create dynamic prompt
        customer_prompt = create_dynamic_prompt(client, product['name'], vision_desc)
        
        # Step 4: Generate image
        generated_path = generate_image(client, customer_prompt, product['name'])
        
        if generated_path:
            print(f"\n   ✅ SUCCESS! Image saved to:")
            print(f"   {generated_path.absolute()}")
        else:
            print(f"\n   ❌ FAILED to generate image")
        
        # Small delay between products
        if idx < len(TEST_PRODUCTS):
            print(f"\n   ⏳ Waiting 3 seconds before next test...")
            time.sleep(3)
    
    # Summary
    print(f"\n{'='*100}")
    print("📊 TEST SUMMARY")
    print('='*100)
    
    generated_images = list(OUTPUT_DIR.glob("*.jpg"))
    print(f"✅ Images generated: {len(generated_images)}/{len(TEST_PRODUCTS)}")
    
    if generated_images:
        print(f"\n📁 All images saved in: {OUTPUT_DIR.absolute()}")
        print(f"\n📸 Generated images:")
        for img in generated_images:
            print(f"   - {img.name}")
    
    print(f"\n💰 ESTIMATED COST:")
    print(f"   - GPT-4 Vision (analyze): $0.002 x {len(TEST_PRODUCTS)} = ${0.002 * len(TEST_PRODUCTS):.4f}")
    print(f"   - GPT-4 (dynamic prompt): $0.002 x {len(TEST_PRODUCTS)} = ${0.002 * len(TEST_PRODUCTS):.4f}")
    print(f"   - GPT-Image-1 (generate): $0.040 x {len(generated_images)} = ${0.040 * len(generated_images):.4f}")
    total_cost = (0.002 * len(TEST_PRODUCTS) * 2) + (0.040 * len(generated_images))
    print(f"   - TOTAL: ${total_cost:.4f}")
    
    print('='*100)


if __name__ == "__main__":
    main()