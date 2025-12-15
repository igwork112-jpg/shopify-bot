from typing import Dict, Optional
import random
import requests
import base64
from pathlib import Path
from io import BytesIO
from PIL import Image
from openai import OpenAI
from google import genai
from google.genai import types
from config.settings import settings
from utils.logger import logger

class ReviewGenerator:
    """Generates AI-powered product reviews with Gemini/Nano Banana photos"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o"
        self.temp_dir = settings.TEMP_DIR
        
        # Initialize Gemini client only if API key is provided
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != 'YOUR_GEMINI_API_KEY_HERE':
            self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        else:
            self.gemini_client = None
    
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
            
            # Step 3: Generate customer photo based on provider selection
            provider = settings.IMAGE_PROVIDER.lower()
            logger.info(f"🎨 Using image provider: {provider}")
            
            if provider == 'gemini':
                image_path = self._generate_with_gemini(customer_photo_prompt, product_name)
            elif provider == 'openai':
                image_path = self._generate_with_gpt_image_1(customer_photo_prompt, product_name)
            elif provider == 'none':
                logger.info("⏭️ Image generation disabled by provider setting")
                return None
            else:
                # Default fallback to Gemini
                logger.warning(f"Unknown provider '{provider}', falling back to Gemini")
                image_path = self._generate_with_gemini(customer_photo_prompt, product_name)
            
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
        
        # EXTENSIVE variety elements for maximum uniqueness
        floor_textures = [
            # Tile varieties
            "ceramic tile floor", "porcelain tile floor", "terracotta tiles", "mosaic tile floor",
            "slate tile floor", "marble tile floor", "travertine floor", "quarry tiles",
            # Wood varieties  
            "oak hardwood floor", "maple hardwood floor", "walnut wood floor", "pine wood floor",
            "bamboo flooring", "reclaimed wood floor", "parquet flooring", "engineered wood floor",
            "dark stained wood floor", "light natural wood floor", "distressed wood floor",
            # Concrete varieties
            "polished concrete", "raw concrete floor", "stained concrete", "stamped concrete",
            "industrial epoxy floor", "sealed concrete", "exposed aggregate concrete",
            # Other
            "vinyl flooring", "laminate flooring", "linoleum floor", "rubber flooring",
            "terrazzo floor", "cork flooring", "carpet", "stone flagstone floor",
            "brick pavers", "pebble floor", "outdoor decking", "patio stones"
        ]
        
        wall_styles = [
            # Painted walls
            "painted white walls", "painted off-white walls", "painted cream walls",
            "painted grey walls", "painted light grey walls", "painted charcoal walls",
            "painted beige walls", "painted taupe walls", "painted blue walls",
            "painted green walls", "painted sage green walls", "painted navy walls",
            "painted terracotta walls", "painted yellow walls", "painted warm white walls",
            # Textured walls
            "textured plaster walls", "venetian plaster walls", "stucco walls",
            "knockdown texture walls", "orange peel texture walls", "smooth drywall",
            # Material walls
            "exposed brick walls", "painted brick walls", "whitewashed brick walls",
            "concrete walls", "raw concrete walls", "cinder block walls",
            "wood paneling walls", "shiplap walls", "beadboard walls", "wainscoting walls",
            "industrial metal walls", "corrugated metal walls", "stone walls",
            "tile backsplash wall", "wallpapered walls", "accent wall with texture"
        ]
        
        lighting_conditions = [
            # Natural light
            "natural daylight from large windows", "soft morning light from window",
            "bright afternoon sunlight", "golden hour warm light", "overcast daylight",
            "north-facing window light", "south-facing bright light", "dappled sunlight",
            # Artificial light
            "overhead fluorescent lighting", "warm tungsten lighting", "cool LED lighting",
            "soft ambient lighting", "bright workshop lighting", "pendant light overhead",
            "recessed ceiling lights", "track lighting", "under-cabinet lighting",
            "industrial pendant lights", "string lights", "lamp light from corner",
            # Mixed
            "mixed natural and artificial light", "window light with overhead lights on",
            "dimly lit with accent lights", "well-lit commercial space lighting"
        ]
        
        camera_styles = [
            # EXPLICIT VIEWING ANGLES - Very different perspectives
            "shot from directly above looking straight down (bird's eye view)",
            "shot from floor level looking up at the product",
            "shot at eye level with product on table/shelf",
            "shot from 45 degree angle above",
            "shot from low angle making product look larger",
            "shot from behind showing back of product",
            "profile shot from the side",
            "three-quarter front view at standing height",
            "dramatic low angle from ground",
            "overhead flat-lay style shot",
            
            # DISTANCE VARIATIONS
            "extreme close-up showing texture and material",
            "close-up filling 80% of frame",
            "medium shot with product and surroundings visible",
            "wide shot showing product in full room context",
            "pulled back showing product small in frame",
            
            # CANDID POSITIONS
            "product being held in one hand at arm's length",
            "product being held with both hands",
            "product resting on knee while sitting",
            "product placed on floor with feet visible nearby",
            "product on table with hand reaching toward it",
            "product next to everyday objects for scale",
            "product partially in shadow",
            "product caught mid-installation",
            
            # PHONE PHOTO STYLES  
            "quick snapshot taken while walking past",
            "selfie-style with product held up",
            "photo taken through a doorway",
            "reflected in mirror with product",
            "slightly tilted as if taken in a hurry",
            "cropped awkwardly like amateur photo"
        ]
        
        # Product orientation for additional variety
        product_orientations = [
            "product shown right-side up in normal position",
            "product tilted at an angle",
            "product laying on its side",
            "product shown from underneath",
            "product shown installed/in-use",
            "product shown next to packaging",
            "product shown with hands interacting with it",
            "product shown being measured with tape or ruler",
            "product shown compared to common object for size reference",
            "multiple angles of same product visible"
        ]
        
        room_types = [
            "living room", "bedroom", "kitchen", "bathroom", "hallway",
            "garage", "workshop", "home office", "basement", "attic",
            "laundry room", "mudroom", "sunroom", "dining room", "den",
            "commercial warehouse", "industrial facility", "retail store",
            "restaurant kitchen", "gym", "yoga studio", "medical office",
            "dental clinic", "veterinary office", "salon", "spa",
            "hotel lobby", "office building", "school classroom", "library"
        ]
        
        time_of_day = [
            "morning", "midday", "afternoon", "late afternoon", 
            "early evening", "dusk", "well-lit daytime"
        ]
        
        photo_imperfections = [
            "slightly blurry like phone camera", "minor lens flare visible",
            "slightly overexposed", "slightly underexposed", "soft focus",
            "phone camera quality", "slight grain in shadows",
            "quick snapshot quality", "casual phone photo look",
            "not perfectly framed", "amateur photographer style"
        ]
        
        # Randomly select variety elements
        chosen_floor = random.choice(floor_textures)
        chosen_wall = random.choice(wall_styles)
        chosen_lighting = random.choice(lighting_conditions)
        chosen_angle = random.choice(camera_styles)
        chosen_orientation = random.choice(product_orientations)
        chosen_room = random.choice(room_types)
        chosen_time = random.choice(time_of_day)
        chosen_imperfection = random.choice(photo_imperfections)
        
        # Random seed for extra uniqueness
        unique_seed = random.randint(1000, 9999)
        
        prompt = (
            f"A realistic customer photo showing {product_name}. "
            f"CRITICAL CAMERA ANGLE: {chosen_angle}. "
            f"PRODUCT ORIENTATION: {chosen_orientation}. "
            f"Generate an image that matches the product use case: if it's a floor mat or home product, "
            f"show it in a HOME setting (NOT commercial); if it's for commercial/industrial use, "
            f"Also keep {vision_description} in mind while generating the image use the {chosen_floor},{chosen_wall} when needed if product is for outdoor use such as tens or pondliners then it should be shown in outdoor setting accordingly "
            f"show it in a COMMERCIAL or INDUSTRIAL setting also show where its belong if its an office table show it in office setting if its gym mat show in gym as if it is swimming cap show a person wearing that,if  the place should match the product usecase . "
            f"Room type: {chosen_room} during {chosen_time}. "
            f"Setting details: {chosen_floor}, {chosen_wall}, {chosen_lighting}. "
            f"Photo style: {chosen_imperfection}. "
            f"Product description for context: {vision_description}. "
            f"IMPORTANT: Each image background must be UNIQUE and VARIED - different floor textures, "
            f"wall colors, lighting, and angles every time. Unique variation seed: {unique_seed}. "
            f"This must look like a real person took this photo with their phone to share in a product review - "
            f"not a professional or marketing photo. Authentic, casual, unpolished."
            f"Image should be generated according to the product usecase"
        )
        
        logger.debug(f"🎨 Prompt: {prompt[:150]}...")
        return prompt
    def _generate_with_gemini(self, prompt: str, product_name: str) -> Optional[Path]:
        """Generate customer review photo using Gemini (Nano Banana)"""
        try:
            # Check if Gemini client is available
            if self.gemini_client is None:
                logger.error("Gemini client not initialized - no API key provided")
                return None
            
            logger.info("🎨 Generating customer photo with Gemini (Nano Banana)...")
            
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['Text', 'Image']
                )
            )
            
            # Extract image from response
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    # Decode base64 image data
                    img_data = part.inline_data.data
                    img = Image.open(BytesIO(img_data))
                    
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Save with unique filename
                    filename = f"ai_review_{random.randint(10000, 99999)}.jpg"
                    filepath = self.temp_dir / filename
                    img.save(filepath, "JPEG", quality=90)
                    
                    return filepath
            
            logger.error("No image data in Gemini response")
            return None
                
        except Exception as e:
            logger.error(f"Gemini image generation failed: {e}")
            return None
    
    def _generate_with_gpt_image_1(self, prompt: str, product_name: str) -> Optional[Path]:
        """Generate customer review photo using GPT-Image-1 (backup method)"""
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