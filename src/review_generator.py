from typing import Dict, Optional, Tuple
import random
import base64
import requests
from pathlib import Path
from io import BytesIO
from PIL import Image
import cv2
import numpy as np
from openai import OpenAI
from config.settings import settings
from utils.logger import logger

class ReviewGenerator:
    """Generates AI-powered product reviews with GPT-Image-1 photos"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o"
        self.temp_dir = settings.TEMP_DIR
    
    def generate(self, product_name: str, product_description: str = "", 
                 product_image_url: str = None, with_image: bool = True) -> Dict:
        """Generate a realistic review with context and optional AI image"""
        rating = random.choices([5, 6], weights=[1, 99])[0]
        
        try:
            review_data = self._generate_with_ai(product_name, product_description, rating)
            logger.success(f"Generated {rating}-star review")
        except Exception as e:
            logger.warning(f"AI generation failed, using fallback: {e}")
            review_data = self._generate_fallback(product_name, rating)
        
        # Generate AI image if requested and product image URL provided
        if with_image and product_image_url:
            try:
                image_path = self.generate_review_image_with_vision(
                    product_name, 
                    product_image_url,
                    product_description
                )
                review_data['image_path'] = image_path
            except Exception as e:
                logger.warning(f"Image generation failed: {e}")
                review_data['image_path'] = None
        else:
            review_data['image_path'] = None
        
        return review_data
    
    def generate_review_image_with_vision(self, product_name: str, 
                                         product_image_url: str,
                                         product_description: str = "") -> Optional[Path]:
        """
        Complete workflow: Download → Dominant Color Detection → Vision Analysis → Image Generation
        """
        try:
            logger.info("🎨 Starting AI review image generation workflow...")
            
            # Step 1: Download product image
            img_pil = self._download_image(product_image_url)
            if not img_pil:
                logger.error("Failed to download product image")
                return None
            
            # Step 2: Extract dominant color (MOST ACCURATE METHOD)
            color_name, color_info = self._extract_dominant_color(img_pil)
            logger.success(f"✅ Detected color: {color_name.upper()} {color_info['hex']}")
            
            # Step 3: Convert image to base64 for GPT-4 Vision
            img_base64 = self._pil_to_base64(img_pil)
            
            # Step 4: Analyze product with GPT-4 Vision (with color hint)
            vision_description = self._analyze_product_with_vision(
                img_base64, 
                product_name, 
                color_name,
                color_info
            )
            if not vision_description:
                logger.warning("Vision analysis failed, using description fallback")
                vision_description = f"This is a {color_name} {product_description[:150] if product_description else product_name}"
            
            # Step 5: Create customer photo prompt with exact color
            customer_photo_prompt = self._create_customer_photo_prompt(
                product_name, 
                vision_description, 
                color_name,
                color_info
            )
            
            # Step 6: Generate customer photo with GPT-Image-1
            image_path = self._generate_with_gpt_image_1(customer_photo_prompt, product_name)
            
            if image_path:
                logger.success(f"✅ Review image generated: {image_path.name}")
            
            return image_path
            
        except Exception as e:
            logger.error(f"Error in image generation workflow: {e}")
            return None
    
    def _download_image(self, image_url: str) -> Optional[Image.Image]:
        """Download product image and return PIL Image"""
        try:
            logger.info("📥 Downloading product image...")
            
            response = requests.get(image_url, timeout=15)
            if response.status_code != 200:
                logger.error(f"Failed to download: HTTP {response.status_code}")
                return None
            
            # Load and convert image
            img = Image.open(BytesIO(response.content))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            logger.success("✅ Product image downloaded")
            return img
            
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return None
    
    def _extract_dominant_color(self, img: Image.Image) -> Tuple[str, Dict]:
        """
        Extract dominant color using OpenCV + KMeans (MOST ACCURATE METHOD)
        Automatically removes glare and reflections
        """
        try:
            logger.info("🎨 Extracting dominant color with KMeans...")
            
            # Convert PIL to OpenCV format
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
            # Convert to HSV for glare detection
            hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
            v = hsv[:, :, 2]  # Value (brightness)
            s = hsv[:, :, 1]  # Saturation
            
            # Create mask to remove glossy reflections
            # Glare = very bright (v > 220) + low saturation (s < 40)
            gloss_mask = (v > 220) & (s < 40)
            gloss_mask = gloss_mask.astype(np.uint8) * 255
            glare_percentage = (np.sum(gloss_mask > 0) / gloss_mask.size) * 100
            
            logger.info(f"📊 Glare pixels removed: {glare_percentage:.1f}%")
            
            # Invert mask to keep non-glossy areas
            non_gloss_mask = cv2.bitwise_not(gloss_mask)
            
            # Apply mask
            masked = cv2.bitwise_and(img_cv, img_cv, mask=non_gloss_mask)
            
            # Reshape for clustering
            pixels = masked.reshape(-1, 3)
            pixels = pixels[np.any(pixels != [0, 0, 0], axis=1)]  # Remove black background
            
            if len(pixels) == 0:
                logger.warning("⚠️ No valid pixels after masking, using fallback")
                return "black", {"r": 0, "g": 0, "b": 0, "hex": "#000000"}
            
            # KMeans clustering to find dominant colors
            from sklearn.cluster import KMeans
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10).fit(pixels)
            
            # Get the most dominant color (largest cluster)
            labels = kmeans.labels_
            centers = kmeans.cluster_centers_
            unique, counts = np.unique(labels, return_counts=True)
            dominant_idx = np.argmax(counts)
            dominant_bgr = centers[dominant_idx]
            
            # Convert BGR to RGB
            b, g, r = [int(c) for c in dominant_bgr]
            hex_color = '#%02x%02x%02x' % (r, g, b)
            
            # Interpret color name from RGB
            color_name = self._rgb_to_color_name(r, g, b)
            percentage = (counts[dominant_idx] / len(pixels)) * 100
            
            logger.info(f"🎨 RGB: ({r}, {g}, {b}) | HEX: {hex_color} | {percentage:.1f}% of pixels")
            logger.success(f"✅ Color identified: {color_name.upper()}")
            
            color_info = {
                "r": r,
                "g": g,
                "b": b,
                "hex": hex_color,
                "percentage": percentage
            }
            
            return color_name, color_info
            
        except Exception as e:
            logger.error(f"Dominant color extraction failed: {e}")
            return "black", {"r": 0, "g": 0, "b": 0, "hex": "#000000"}
    
    def _rgb_to_color_name(self, r: int, g: int, b: int) -> str:
        """Convert RGB to approximate color name"""
        brightness = (r + g + b) / 3
        color_diff = max(r, g, b) - min(r, g, b)
        
        # Grayscale detection (low color variation)
        if color_diff < 30:
            if brightness < 50:
                return "black"
            elif brightness < 100:
                return "dark grey"
            elif brightness < 180:
                return "grey"
            else:
                return "white"
        
        # Color detection
        if r > g and r > b:
            if r - max(g, b) > 50:
                return "red"
            else:
                return "brown"
        elif g > r and g > b:
            return "green"
        elif b > r and b > g:
            return "blue"
        elif r > 200 and g > 200 and b < 100:
            return "yellow"
        elif r > 150 and g < 100 and b > 150:
            return "purple"
        elif r > 200 and g > 100 and b < 100:
            return "orange"
        else:
            return "mixed color"
    
    def _pil_to_base64(self, img: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        try:
            # Save to temporary buffer
            temp_path = self.temp_dir / "temp_product.jpg"
            img.save(temp_path, "JPEG", quality=85)
            
            # Convert to base64
            with open(temp_path, "rb") as f:
                img_bytes = f.read()
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            # Cleanup
            temp_path.unlink()
            
            return img_base64
            
        except Exception as e:
            logger.error(f"Base64 conversion failed: {e}")
            return ""
    
    def _analyze_product_with_vision(self, img_base64: str, product_name: str, 
                                    color_name: str, color_info: Dict) -> Optional[str]:
        """Analyze product with GPT-4 Vision, providing the detected color as context"""
        try:
            logger.info("👁️ Analyzing product with GPT-4 Vision...")
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""Analyze this product image for: {product_name}

DETECTED COLOR: {color_name.upper()} (RGB: {color_info['r']}, {color_info['g']}, {color_info['b']})

This color was extracted from the actual product pixels, ignoring reflections and glare.

Describe in 2-3 sentences:
1. Confirm this is a {color_name} product (the color detection is accurate)
2. The material type, texture, and thickness/size
3. How it's designed to be installed or used

Focus on material properties and use case, not lighting effects."""
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
                max_tokens=200,
                temperature=0.1
            )
            
            description = response.choices[0].message.content.strip()
            logger.info(f"📋 Vision Analysis: {description[:100]}...")
            return description
            
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return None
    
    def _create_customer_photo_prompt(self, product_name: str, vision_description: str, 
                                     color_name: str, color_info: Dict) -> str:
        """Create prompt for GPT-Image-1 with precise color specification"""
        
        prompt = f"""A realistic customer photo showing {product_name} installed in its typical use environment.

CRITICAL COLOR SPECIFICATION:
- The product MUST be {color_name.upper()} color
- Exact RGB color: ({color_info['r']}, {color_info['g']}, {color_info['b']})
- HEX color: {color_info['hex']}
- DO NOT use white, light grey, or any other color
- The {color_name} color must be clearly visible in the photo

Product details: {vision_description}

Photo requirements:
- Show the {color_name} {product_name} in its proper installation location
- Natural lighting (not too bright, not too dark)
- Smartphone camera quality (not professional photography)
- Real customer perspective showing the installed product
- The {color_name} color must match RGB({color_info['r']}, {color_info['g']}, {color_info['b']})

This must look like a genuine customer took this photo with their phone to show the installed {color_name} {product_name}."""
        
        logger.debug(f"🎨 Generated prompt with color: {color_name} {color_info['hex']}")
        return prompt
    
    def _generate_with_gpt_image_1(self, prompt: str, product_name: str) -> Optional[Path]:
        """Generate customer review photo using GPT-Image-1"""
        try:
            logger.info("🎨 Generating customer photo with GPT-Image-1...")
            
            response = self.client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size="1024x1024",
                quality="high",
                n=1
            )
            
            # Handle URL response
            if hasattr(response.data[0], "url") and response.data[0].url:
                url = response.data[0].url
                logger.debug(f"Image URL received: {url[:60]}...")
                
                # Download the generated image
                img_response = requests.get(url, timeout=30)
                if img_response.status_code != 200:
                    logger.error("Failed to download generated image")
                    return None
                
                img = Image.open(BytesIO(img_response.content))
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save with unique filename
                filename = f"ai_review_{random.randint(10000, 99999)}.jpg"
                filepath = self.temp_dir / filename
                img.save(filepath, "JPEG", quality=90)
                
                return filepath
            
            # Handle base64 response
            elif hasattr(response.data[0], "b64_json") and response.data[0].b64_json:
                logger.debug("Image received as base64")
                img_data = base64.b64decode(response.data[0].b64_json)
                
                filename = f"ai_review_{random.randint(10000, 99999)}.jpg"
                filepath = self.temp_dir / filename
                
                with open(filepath, "wb") as f:
                    f.write(img_data)
                
                return filepath
            
            else:
                logger.error("No valid image data in response")
                return None
                
        except Exception as e:
            logger.error(f"GPT-Image-1 generation failed: {e}")
            return None
    
    def _generate_with_ai(self, product_name: str, description: str, rating: int) -> Dict:
        """Generate review, name, and email using OpenAI"""
        prompt = f"""Generate a realistic customer review with reviewer details for this product:

Product Name: {product_name}
Description: {description[:300]}
Rating: {rating}/5 stars

Requirements for the review:
- Write 2-4 sentences in first person
- Sound like a real customer who bought and used the product
- Be specific about product features from the description
- Dont use common phrases like I recently installed or I bought this use different wording every time
- Match the {rating}-star rating sentiment
- Always give a positive review  
- Use casual, natural language
- NO emojis, NO marketing speak
- Mention installation, quality, appearance, or functionality
- Each review must be unique
- Don't use similar phrases across reviews
- Avoid overly generic statements
- Be authentic and conversational

Requirements for reviewer details:
- Generate a realistic first name and last name separately
- Just use one name one time 
- Generate a realistic email address that matches the name
- Use REAL email domains like gmail.com, yahoo.com, outlook.com, hotmail.com, icloud.com
- NEVER use fake domains like example.com, test.com, fake.com, sample.com
- Make the email look natural (e.g., firstname.lastname@gmail.com or variations)

Return your response in this EXACT format:
FIRST_NAME: [first name]
LAST_NAME: [last name]
EMAIL: [email address]
REVIEW: [review text only]"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse response
        first_name = ""
        last_name = ""
        email = ""
        review = ""
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if 'FIRST_NAME' in line.upper():
                first_name = line.split(':', 1)[-1].strip()
            elif 'LAST_NAME' in line.upper():
                last_name = line.split(':', 1)[-1].strip()
            elif 'EMAIL' in line.upper() and '@' in line:
                email = line.split(':', 1)[-1].strip()
            elif 'REVIEW' in line.upper():
                review = line.split(':', 1)[-1].strip()
            elif review and not first_name in line and not last_name in line:
                review += " " + line
        
        review = review.replace('"', '').replace("'", "").strip()
        
        logger.info(f"🤖 AI Generated - Name: {first_name} {last_name}, Email: {email}")
        
        # Validate
        if not first_name or not last_name or not email or not review:
            raise ValueError("Incomplete AI response")
        
        fake_domains = ['example.com', 'test.com', 'fake.com', 'sample.com']
        if any(domain in email.lower() for domain in fake_domains):
            raise ValueError("Fake email domain detected")
        
        return {
            'rating': rating,
            'text': review,
            'title': self._generate_title(product_name, rating),
            'first_name': first_name,
            'last_name': last_name,
            'email': email
        }
    
    def _generate_fallback(self, product_name: str, rating: int) -> Dict:
        """Fallback template-based reviews"""
        from faker import Faker
        fake = Faker()
        
        templates = {
            5: [
                f"Absolutely love this {product_name}! The quality exceeded my expectations. Installation was straightforward and it looks fantastic. Would definitely buy again.",
                f"Best {product_name} I've purchased! The finish is professional-grade and very durable. Highly recommend to anyone looking for quality.",
            ],
            4: [
                f"Really happy with this {product_name}. Good quality and works as described.",
                f"Solid {product_name} for the price. Meets my expectations and looks good.",
            ]
        }
        
        return {
            'rating': rating,
            'text': random.choice(templates.get(rating, templates[4])),
            'title': self._generate_title(product_name, rating),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'email': fake.email()
        }
    
    def _generate_title(self, product_name: str, rating: int) -> str:
        """Generate review title"""
        titles = {
            5: ["Excellent!", "Love it!", "Perfect!", "Highly recommend", "Amazing quality"],
            4: ["Good product", "Happy with purchase", "Solid choice", "Works well"],
        }
        return random.choice(titles.get(rating, titles[4]))