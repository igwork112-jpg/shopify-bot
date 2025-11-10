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
        self.model = "gpt-4o"
        self.temp_dir = settings.TEMP_DIR
    
    def generate(self, product_name: str, product_description: str = "", 
                 product_image_url: str = None, with_image: bool = True, 
                 page_html: str = "") -> Dict:
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
                    product_description,
                    page_html
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
                                         product_description: str = "",
                                         page_html: str = "") -> Optional[Path]:
        """
        Complete workflow: Color Detection → Vision Analysis → Image Generation
        """
        try:
            logger.info("🎨 Starting AI review image generation workflow...")
            
            # Step 1: Extract color from product page (most reliable)
            page_color = self._extract_color_from_text(product_name, product_description, page_html)
            logger.info(f"🎨 Color from page text: {page_color}")
            
            # Step 2: Download and encode product image
            img_base64, img_pil = self._download_and_encode_image(product_image_url)
            if not img_base64:
                logger.error("Failed to download product image")
                return None
            
            # Step 3: Detect color using histogram (backup method)
            histogram_color = self._detect_color_from_histogram(img_pil)
            logger.info(f"📊 Color from histogram: {histogram_color}")
            
            # Step 4: Determine the most reliable color
            final_color = self._resolve_color(page_color, histogram_color)
            logger.success(f"✅ Final color determined: {final_color}")
            
            # Step 5: Analyze product with GPT-4 Vision
            vision_description = self._analyze_product_with_vision(img_base64, product_name, final_color)
            if not vision_description:
                logger.warning("Vision analysis failed, using description fallback")
                vision_description = product_description[:200] if product_description else f"This is a {final_color} {product_name}"
            
            # Step 6: Ensure color is in the description
            if final_color not in vision_description.lower():
                logger.warning(f"⚠️ Injecting correct color ({final_color}) into description")
                vision_description = f"This is a {final_color} {vision_description}"
            
            # Step 7: Create customer photo prompt
            customer_photo_prompt = self._create_customer_photo_prompt(product_name, vision_description, final_color)
            
            # Step 8: Generate customer photo with GPT-Image-1
            image_path = self._generate_with_gpt_image_1(customer_photo_prompt, product_name)
            
            if image_path:
                logger.success(f"✅ Review image generated: {image_path.name}")
            
            return image_path
            
        except Exception as e:
            logger.error(f"Error in image generation workflow: {e}")
            return None
    
    def _extract_color_from_text(self, product_name: str, description: str, page_html: str) -> str:
        """Extract color from product name, description, or HTML (most reliable method)"""
        try:
            logger.info("🔍 Extracting color from text sources...")
            
            # Combine all text sources
            combined_text = f"{product_name} {description} {page_html}".lower()
            
            # Define color keywords with priority
            color_keywords = {
                'black': ['black', 'noir', 'schwarz'],
                'white': ['white', 'blanc', 'weiß'],
                'grey': ['grey', 'gray', 'gris'],
                'red': ['red', 'rouge', 'rot'],
                'blue': ['blue', 'bleu', 'blau'],
                'green': ['green', 'vert', 'grün'],
                'yellow': ['yellow', 'jaune', 'gelb'],
                'brown': ['brown', 'brun', 'braun'],
            }
            
            # Check for color mentions
            for color, keywords in color_keywords.items():
                for keyword in keywords:
                    if keyword in combined_text:
                        logger.info(f"✅ Found color keyword: '{keyword}' → {color}")
                        return color
            
            logger.warning("⚠️ No color found in text sources")
            return 'unknown'
            
        except Exception as e:
            logger.error(f"Color extraction from text failed: {e}")
            return 'unknown'
    
    def _detect_color_from_histogram(self, img: Image.Image) -> str:
        """Detect if product is predominantly black, white, or other color using histogram"""
        try:
            logger.info("📊 Analyzing image histogram...")
            
            # Convert to grayscale for brightness analysis
            gray = img.convert('L')
            pixels = list(gray.getdata())
            
            # Calculate average brightness (0=black, 255=white)
            avg_brightness = sum(pixels) / len(pixels)
            
            # Get histogram
            histogram = gray.histogram()
            
            # Count dark pixels (0-85) vs light pixels (170-255)
            dark_pixels = sum(histogram[0:86])
            light_pixels = sum(histogram[170:256])
            mid_pixels = sum(histogram[86:170])
            
            total_pixels = len(pixels)
            dark_ratio = dark_pixels / total_pixels
            light_ratio = light_pixels / total_pixels
            
            logger.info(f"📊 Brightness: {avg_brightness:.1f}, Dark: {dark_ratio:.2%}, Light: {light_ratio:.2%}")
            
            # Decision logic
            if dark_ratio > 0.4 or avg_brightness < 85:
                return "black"
            elif light_ratio > 0.4 or avg_brightness > 170:
                return "white"
            elif avg_brightness < 130:
                return "dark grey"
            else:
                return "grey"
                
        except Exception as e:
            logger.error(f"Histogram analysis failed: {e}")
            return "unknown"
    
    def _resolve_color(self, page_color: str, histogram_color: str) -> str:
        """Resolve the final color using priority: page_color > histogram_color"""
        
        # Priority 1: Page text (most reliable)
        if page_color != 'unknown':
            logger.info(f"✅ Using page color: {page_color}")
            return page_color
        
        # Priority 2: Histogram analysis
        if histogram_color != 'unknown':
            logger.info(f"✅ Using histogram color: {histogram_color}")
            return histogram_color
        
        # Fallback: assume black for rubber/flooring products
        logger.warning("⚠️ No color detected, defaulting to 'black'")
        return "black"
    
    def _download_and_encode_image(self, image_url: str) -> tuple[Optional[str], Optional[Image.Image]]:
        """Download product image and return both base64 AND PIL Image"""
        try:
            logger.info("📥 Downloading product image...")
            
            response = requests.get(image_url, timeout=15)
            if response.status_code != 200:
                logger.error(f"Failed to download: HTTP {response.status_code}")
                return None, None
            
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
            return img_base64, img
            
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return None, None
    
    def _analyze_product_with_vision(self, img_base64: str, product_name: str, known_color: str) -> Optional[str]:
        """Analyze product image using GPT-4o Vision with color hint"""
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

IMPORTANT: This product is {known_color.upper()} in color. Ignore any white highlights or reflections - those are just light glare on the surface.

Describe in 2-3 sentences:
1. Confirm the color is {known_color} (ignore reflections)
2. The material type and thickness
3. How it's designed to be installed or used

Focus on the actual material properties, not lighting effects."""
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
    
    def _create_customer_photo_prompt(self, product_name: str, vision_description: str, final_color: str) -> str:
        """Create prompt for GPT-Image-1 with explicit color enforcement"""
        
        prompt = f"""A realistic customer photo showing {product_name} installed in its typical use environment.

CRITICAL COLOR REQUIREMENT: The product MUST be {final_color.upper()} in color. NOT white, NOT light colored, specifically {final_color.upper()}.

Product details: {vision_description}

The photo should show:
- The {final_color} product clearly visible in proper lighting
- Appropriate installation location (home/commercial/industrial based on product type)
- Natural smartphone photography style
- Real customer perspective, NOT professional marketing photo
- The {final_color} color must be clearly visible

This must look like a genuine customer took this photo with their phone to show how the {final_color} {product_name} looks after installation."""
        
        logger.debug(f"🎨 Generated prompt with color: {final_color}")
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


