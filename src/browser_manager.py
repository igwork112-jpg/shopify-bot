from playwright.sync_api import sync_playwright, Page, Browser
from config.settings import settings
from utils.logger import logger

class BrowserManager:
    """Manages Playwright browser instance"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Browser = None
        self.context = None
        self.page: Page = None
    
    def start(self):
        """Initialize and start browser"""
        try:
            logger.info("Starting browser...")
            
            self.playwright = sync_playwright().start()
            
            self.browser = self.playwright.chromium.launch(
                headless=settings.HEADLESS,
                slow_mo=300,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
                ]
            )
            
            self.context = self.browser.new_context(
                viewport={
                    'width': settings.VIEWPORT_WIDTH,
                    'height': settings.VIEWPORT_HEIGHT
                },
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Add stealth scripts
            self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            self.page = self.context.new_page()
            self.page.set_default_timeout(settings.BROWSER_TIMEOUT)
            
            logger.success("Browser started successfully")
            return self.page
            
        except Exception as e:
            logger.failure(f"Failed to start browser: {e}")
            raise
    
    def close(self):
        """Close browser and cleanup"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            
            logger.info("Browser closed")
            
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    def __enter__(self):
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()