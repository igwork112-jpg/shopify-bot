import requests
import random
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageEnhance, ImageFilter
from config.settings import settings
from utils.logger import logger

class ImageProcessor:
    """Processes and generates review images"""
    
    def __init__(self):
        self.temp_dir = settings.TEMP_DIR
    
    def download_and_process(self, image_url: str, product_name: str) -> Path:
        """Download product image and create review version"""
        try:
            logger.info("Processing product image for review")
            
            # Download original image
            response = requests.get(image_url, timeout=15)
            if response.status_code != 200:
                logger.error(f"Failed to download image: {response.status_code}")
                return None
            
            img = Image.open(BytesIO(response.content))
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Make it look like a customer photo
            img = self._transform_to_review_photo(img)
            
            # Save to temp file
            filename = f"review_{random.randint(10000, 99999)}.jpg"
            filepath = self.temp_dir / filename
            img.save(filepath, "JPEG", quality=85)
            
            logger.success(f"Review image created: {filename}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return None
    
    def _transform_to_review_photo(self, img: Image.Image) -> Image.Image:
        """Transform product image to look like customer review photo"""
        
        # Resize to realistic phone camera size
        target_size = random.choice([(800, 800), (1000, 1000), (1200, 1200)])
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # Add slight blur (customer photos aren't perfect)
        blur_amount = random.uniform(0.3, 0.8)
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_amount))
        
        # Adjust brightness slightly
        brightness = ImageEnhance.Brightness(img)
        img = brightness.enhance(random.uniform(0.9, 1.1))
        
        # Adjust contrast
        contrast = ImageEnhance.Contrast(img)
        img = contrast.enhance(random.uniform(0.95, 1.05))
        
        # Adjust color saturation
        color = ImageEnhance.Color(img)
        img = color.enhance(random.uniform(0.9, 1.1))
        
        return img
    
    def cleanup(self, filepath: Path):
        """Delete temporary image file"""
        try:
            if filepath and filepath.exists():
                filepath.unlink()
                logger.debug(f"Cleaned up: {filepath.name}")
        except Exception as e:
            logger.error(f"Error cleaning up image: {e}")