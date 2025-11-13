import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings from environment variables"""
    
    def __init__(self):
        # Store Configuration
        self.STORE_URL = os.getenv('STORE_URL', 'https://example.com')
        
        # API Keys
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
        
        # Bot Settings
        self.REVIEWS_PER_PRODUCT = int(os.getenv('REVIEWS_PER_PRODUCT', '3'))
        
        # Convert string 'true'/'false' to boolean
        use_ai_images = os.getenv('USE_AI_IMAGES', 'true').lower()
        self.USE_AI_IMAGES = use_ai_images in ('true', '1', 'yes', 'on')
        
        # Convert string 'true'/'false' to boolean for HEADLESS
        headless = os.getenv('HEADLESS', 'false').lower()
        self.HEADLESS = headless in ('truee', '1', 'yes', 'on')
        
        self.MIN_DELAY = int(os.getenv('MIN_DELAY', '3'))
        self.MAX_DELAY = int(os.getenv('MAX_DELAY', '6'))
        
        # Browser Settings
        self.VIEWPORT_WIDTH = int(os.getenv('VIEWPORT_WIDTH', '1920'))
        self.VIEWPORT_HEIGHT = int(os.getenv('VIEWPORT_HEIGHT', '1080'))
        self.BROWSER_TIMEOUT = int(os.getenv('BROWSER_TIMEOUT', '30000'))  # milliseconds
        
        # Directories
        self.BASE_DIR = Path(__file__).parent.parent
        self.TEMP_DIR = self.BASE_DIR / 'temp'
        self.TEMP_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR = self.BASE_DIR / 'logs'
        self.LOGS_DIR.mkdir(exist_ok=True)
    
    def validate(self):
        """Validate required settings"""
        if not self.STORE_URL or self.STORE_URL == 'https://example.com':
            raise ValueError("STORE_URL must be set")
        
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set")
        
        if self.REVIEWS_PER_PRODUCT < 1 or self.REVIEWS_PER_PRODUCT > 10:
            raise ValueError("REVIEWS_PER_PRODUCT must be between 1 and 10")
    
    def reload(self):
        """Reload settings from .env file"""
        load_dotenv(override=True)
        self.__init__()

# Create settings instance
settings = Settings()