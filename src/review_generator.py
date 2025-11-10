from typing import Dict, Optional
import random
import base64
import requests
from pathlib import Path
from io import BytesIO
from PIL import Image
from openai import OpenAI
from config.settings import settings
from utils.logger import logger

class ReviewGenerator:
    """Generates AI-powered product reviews with GPT-Image-1 photos"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"
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
        Complete workflow: Download → GPT-4 Vision Analysis → GPT-Image-1 Generation
        """
        try:
            logger.info("🎨 Starting AI review image generation workflow...")
            
            # Step 1: Download and encode product image
            img_base64 = self._download_and_encode_image(product_image_url)
            if not img_base64:
                logger.error("Failed to download product image")
                return None
            
            # Step 2: Analyze product with GPT-4 Vision
            vision_description = self._analyze_product_with_vision(img_base64, product_name)
            if not vision_description:
                logger.warning("Vision analysis failed, using description fallback")
                vision_description = product_description[:200] if product_description else f"This is a {product_name}"
            
            # Step 3: Create customer photo prompt
            customer_photo_prompt = self._create_customer_photo_prompt(product_name, vision_description)
            
            # Step 4: Generate customer photo with GPT-Image-1
            image_path = self._generate_with_gpt_image_1(customer_photo_prompt, product_name)
            
            if image_path:
                logger.success(f"✅ Review image generated: {image_path.name}")
            
            return image_path
            
        except Exception as e:
            logger.error(f"Error in image generation workflow: {e}")
            return None
    
    def _download_and_encode_image(self, image_url: str) -> Optional[str]:
        """Download product image and convert to base64 for GPT-4 Vision"""
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
            
            # Save temporarily
            temp_path = self.temp_dir / "temp_product.jpg"
            img.save(temp_path, "JPEG", quality=85)
            
            # Convert to base64
            with open(temp_path, "rb") as f:
                img_bytes = f.read()
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            # Cleanup temp file
            temp_path.unlink()
            
            logger.success("✅ Product image downloaded and encoded")
            return img_base64
            
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return None
    
    def _analyze_product_with_vision(self, img_base64: str, product_name: str) -> Optional[str]:
        """Analyze product image using GPT-4o-mini Vision"""
        try:
            logger.info("👁️ Analyzing product with GPT-4 Vision...")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""Analyze this product image for: {product_name}


CRITICAL: Look carefully at the ACTUAL COLOR of the product material itself, not reflections or highlights.

Describe in 2-3 sentences:
1. The EXACT color of the product  - look at the body of the material, not light reflections
2. The material type and thickness
3. How it's designed to be installed or used

Be very precise about color. If you see highlights or reflections or sunlights or anything , ignore those and focus on the base product material color."""
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
            logger.info(f"📋 Vision Analysis: {description[:100]}...")
            return description
            
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return None
    
    def _create_customer_photo_prompt(self, product_name: str, vision_description: str) -> str:
        """Create prompt for GPT-Image-1 using contextual analysis"""
        
        try:
            logger.info("🧠 Creating dynamic context-aware prompt...")
            
            # Step 1: Analyze product context with GPT-4
            analysis_prompt = (
                f"You are analyzing a product to help generate a realistic customer review photo.\n\n"
                f"Product Name: {product_name}\n"
                f"Product Description: {vision_description}\n\n"
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
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=150,
                temperature=0.3
            )
            
            analysis = response.choices[0].message.content.strip()
            logger.debug(f"📊 Context analysis: {analysis}")
            
            # Step 2: Parse the analysis
            lines = analysis.split("\n")
            context = {}
            for line in lines:
                if line.startswith("ENVIRONMENT:"):
                    context['environment'] = line.split("ENVIRONMENT:")[1].strip()
                elif line.startswith("SURFACE:"):
                    context['surface'] = line.split("SURFACE:")[1].strip()
                elif line.startswith("ANGLE:"):
                    context['angle'] = line.split("ANGLE:")[1].strip()
                elif line.startswith("FOCUS:"):
                    context['focus'] = line.split("FOCUS:")[1].strip()
            
            # Step 3: Determine appropriate lighting
            lighting = "natural window lighting"
            if "outdoor" in context.get('environment', '').lower():
                lighting = "natural daylight, clear weather"
            elif "commercial" in context.get('environment', '').lower() or "industrial" in context.get('environment', '').lower():
                lighting = "standard facility lighting"
            
            # Step 4: Build the final prompt
            prompt = (
                f"A realistic customer photo showing {product_name} installed in {context.get('environment', 'its typical setting')}. "
                f"{vision_description} The product is shown on/at {context.get('surface', 'its installation surface')}, "
                f"photographed {context.get('angle', 'from a natural angle')}. "
                f"The photo clearly shows {context.get('focus', 'the installed product')}. "
                f"Taken with a smartphone camera. {lighting}. "
                f"Natural composition with minor imperfections typical of customer photos. "
                f"This must look like a real customer took this photo with their phone - NOT a professional product shot, NOT a marketing photo. "
                f"The setting must match where this product is actually used in real life. Photorealistic customer review photo style."
            )
            
            logger.info(f"✅ Dynamic prompt created: {prompt[:100]}...")
            return prompt
            
        except Exception as e:
            logger.error(f"Context analysis failed, using simple prompt: {e}")
            
            # Fallback to simple prompt if analysis fails
            return (
                f"A realistic customer photo showing {product_name}. {vision_description} "
                f"Taken with a smartphone camera. Natural lighting. "
                f"This must look like a real customer took this photo with their phone - "
                f"NOT a professional product shot. Photorealistic customer review photo style."
            )
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