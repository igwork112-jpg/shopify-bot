from typing import Dict, Optional
import random
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
        Simplified workflow: Direct URL → GPT-4 Vision Analysis → GPT-Image-1 Generation
        """
        try:
            logger.info("🎨 Starting AI review image generation workflow...")
            
            # Step 1: Analyze product with GPT-4 Vision (using direct URL)
            vision_description = self._analyze_product_with_vision(
                product_image_url, 
                product_name,
                product_description
            )
            
            if not vision_description:
                logger.warning("Vision analysis failed, using description fallback")
                vision_description = product_description[:200] if product_description else f"This is a {product_name}"
            
            # Step 2: Create customer photo prompt
            customer_photo_prompt = self._create_customer_photo_prompt(
                product_name, 
                vision_description
                
            )
            
            # Step 3: Generate customer photo with GPT-Image-1
            image_path = self._generate_with_gpt_image_1(customer_photo_prompt, product_name)
            
            if image_path:
                logger.success(f"✅ Review image generated: {image_path.name}")
            
            return image_path
            
        except Exception as e:
            logger.error(f"Error in image generation workflow: {e}")
            return None
    
    # def _analyze_product_with_vision(self, product_image_url: str, 
    #                             product_name: str) -> Optional[str]:
    #     """Analyze product image using GPT-4o-mini Vision - directly with URL"""
    #     try:
    #         logger.info("👁️ Analyzing product with GPT-4o-mini Vision...")
    #         logger.info(f"🔍 Product name being analyzed: '{product_name}'")  # 🔹 ADD THIS
            
    #         response = self.client.chat.completions.create(
    #             model="gpt-4o-mini",
    #             messages=[
    #                 {
    #                     "role": "user",
    #                     "content": [
    #                         {
    #                             "type": "text",
    #                             "text": f"Describe this product: {product_name}. "
    #                                     "Focus on its material, color, and intended installation. "
    #                                     "IF its a commercial grade rubber sheet then its color will be black"
    #                                     "Keep it under 3 sentences."
    #                         },
    #                         {
    #                             "type": "image_url",
    #                             "image_url": {
    #                                 "url": product_image_url
    #                             }
    #                         }
    #                     ]
    #                 }
    #             ],
    #             max_tokens=150
    #         )
            
    #         description = response.choices[0].message.content.strip()
    #         logger.info(f"📋 Vision Analysis FULL: {description}")  # 🔹 LOG FULL RESPONSE
    #         return description
            
    #     except Exception as e:
    #         logger.error(f"Vision analysis failed: {e}")
    #         return None
    def _analyze_product_with_vision(self, product_image_url: str, 
                            product_name: str,
                            product_description: str = "") -> Optional[str]:
        """Analyze product image using GPT-4o-mini Vision with description context"""
        try:
            logger.info("👁️ Analyzing product with GPT-4o-mini Vision...")
            logger.info(f"🔍 Product: '{product_name}'")
            logger.info(f"📝 Description provided: {bool(product_description)}")
            
            # Build prompt with description context if available
            prompt_text = f"Describe this product: {product_name}. "
            if product_description:
                prompt_text += f"Product details: {product_description}. "
            
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image_url", "image_url": {"url": product_image_url}}
                    ]
                }],
                max_tokens=350
            )
            
            description = response.choices[0].message.content.strip()
            logger.info(f"📋 Vision Analysis: {description}")
            return description
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return None
    
    # def _create_customer_photo_prompt(self, product_name: str, 
    #                                  vision_description: str) -> str:
    #     """Create prompt for GPT-Image-1 to generate realistic customer photo"""
        
    #     prompt = f"A realistic customer photo showing {product_name} generate a image that should match the product use case if there is a floor mat that should be shown in home not on some other place and the floor texture and walls should be unique, if product is for commercial use case that should be at commercial place  by getting vision description you will know what is the use case of the product make no mistakes be tight. {vision_description} This must look like a real person took this photo with their phone to share in a product review - not a professional or marketing photo and each image background should varie."
        
    #     logger.debug(f"🎨 Prompt: {prompt[:150]}...")
    #     return prompt
    def _create_customer_photo_prompt(self, product_name: str, 
                                 vision_description: str) -> str:
        """Create prompt for GPT-Image-1 to generate realistic customer photo"""
        
        # Add variety elements
        floor_textures = [
            "ceramic tile floor",
            "concrete floor", 
            "wooden floor",
            "vinyl flooring",
            "polished concrete",
            "industrial epoxy floor",
            "laminate flooring",
            "textured concrete"
        ]
        
        wall_styles = [
            "painted white walls",
            "brick walls",
            "concrete walls",
            "painted grey walls",
            "industrial metal walls",
            "drywall with neutral color",
            "painted beige walls",
            "textured plaster walls"
        ]
        
        lighting_conditions = [
            "natural daylight from windows",
            "overhead fluorescent lighting",
            "warm indoor lighting",
            "bright LED lighting",
            "mixed natural and artificial light",
            "soft ambient lighting"
        ]
        
        camera_styles = [
            "slightly off-center angle",
            "taken from standing height",
            "taken from above at 45 degrees",
            "close-up showing texture",
            "wide angle showing surroundings",
            "casual snapshot angle"
        ]
        
        # Randomly select variety elements
        chosen_floor = random.choice(floor_textures)
        chosen_wall = random.choice(wall_styles)
        chosen_lighting = random.choice(lighting_conditions)
        chosen_angle = random.choice(camera_styles)
        
        prompt = (
            f"A realistic customer photo showing {product_name}. "
            f"Generate an image that matches the product use case: if it's a floor mat or home product, "
            f"show it in a HOME setting (NOT commercial); if it's for commercial/industrial use, "
            f"show it in a COMMERCIAL or INDUSTRIAL setting also show where its belong if its an office table show it in office setting if its gym mat show in gym as if it is swimming cap show a person wearing that the place should match the product usecase . "
            f"Setting details: {chosen_floor}, {chosen_wall}, {chosen_lighting}. "
            f"Photo style: {chosen_angle}, slightly blurry like phone camera. "
            f"Product description for context: {vision_description}. "
            f"IMPORTANT: Each image background must be UNIQUE and VARIED - different floor textures, "
            f"wall colors, lighting, and angles every time. "
            f"This must look like a real person took this photo with their phone to share in a product review - "
            f"not a professional or marketing photo. Authentic, casual, unpolished."
        )
        
        logger.debug(f"🎨 Prompt: {prompt[:150]}...")
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
                logger.debug(f"Image URL received: {url}...")
                
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
                import base64
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
            review_started = False
            
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
                    review_started = True       
                elif review_started:
                    review += " " + line
            
            review = review.replace('"', '').replace("'", "").strip()
            
            logger.info(f"🤖 AI Generated - Name: {first_name} {last_name}, Email: {email}")
            logger.info(f"full review: {review}")

            
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