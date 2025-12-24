from playwright.sync_api import sync_playwright, Page, Browser
from config.settings import settings
from utils.logger import logger
import time


class BrowserManager:
    """Manages Playwright browser instance with automatic restart capability"""
    
    # Maximum number of restart attempts
    MAX_RESTART_ATTEMPTS = 3
    RESTART_DELAY = 5  # seconds between restart attempts
    
    def __init__(self):
        self.playwright = None
        self.browser: Browser = None
        self.context = None
        self.page: Page = None
        self._restart_count = 0
        self._is_healthy = False
    
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
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',  # Prevents memory issues
                    '--disable-gpu',  # Reduces resource usage
                    '--single-process',  # More stable for long runs
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
            
            self._is_healthy = True
            self._restart_count = 0
            logger.success("Browser started successfully")
            return self.page
            
        except Exception as e:
            logger.failure(f"Failed to start browser: {e}")
            self._is_healthy = False
            raise
    
    def close(self):
        """Close browser and cleanup"""
        self._is_healthy = False
        try:
            if self.page:
                try:
                    self.page.close()
                except:
                    pass
            if self.context:
                try:
                    self.context.close()
                except:
                    pass
            if self.browser:
                try:
                    self.browser.close()
                except:
                    pass
            if self.playwright:
                try:
                    self.playwright.stop()
                except:
                    pass
            
            logger.info("Browser closed")
            
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    def restart(self) -> Page:
        """Restart the browser - useful for recovering from crashes"""
        self._restart_count += 1
        
        if self._restart_count > self.MAX_RESTART_ATTEMPTS:
            logger.error(f"Max restart attempts ({self.MAX_RESTART_ATTEMPTS}) exceeded")
            raise RuntimeError("Browser restart limit exceeded")
        
        logger.warning(f"🔄 Restarting browser (attempt {self._restart_count}/{self.MAX_RESTART_ATTEMPTS})...")
        
        # Close existing browser
        self.close()
        
        # Wait before restarting
        logger.info(f"⏳ Waiting {self.RESTART_DELAY}s before restart...")
        time.sleep(self.RESTART_DELAY)
        
        # Start fresh
        return self.start()
    
    def is_healthy(self) -> bool:
        """Check if the browser is still responsive"""
        if not self._is_healthy or not self.page:
            return False
        
        try:
            # Try a simple operation to check browser health
            self.page.evaluate("() => true")
            return True
        except Exception:
            self._is_healthy = False
            return False
    
    def ensure_healthy(self) -> Page:
        """Ensure browser is healthy, restart if needed"""
        if not self.is_healthy():
            logger.warning("Browser unhealthy, attempting restart...")
            return self.restart()
        return self.page
    
    def reset_restart_count(self):
        """Reset the restart counter (call after successful operations)"""
        self._restart_count = 0
    
    def __enter__(self):
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def with_browser_retry(max_retries: int = 3, delay: float = 2.0):
    """
    Decorator that retries a function on browser-related errors.
    The function must accept 'page' as its first argument.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e).lower()
                    
                    # Check if it's a recoverable browser error
                    recoverable_errors = [
                        'epipe', 'broken pipe', 'target closed',
                        'browser has been closed', 'page closed',
                        'connection closed', 'navigation failed',
                        'timeout', 'frame was detached'
                    ]
                    
                    is_recoverable = any(err in error_str for err in recoverable_errors)
                    
                    if is_recoverable and attempt < max_retries - 1:
                        logger.warning(f"⚠️ Recoverable error (attempt {attempt + 1}/{max_retries}): {e}")
                        logger.info(f"⏳ Retrying in {delay}s...")
                        time.sleep(delay)
                        last_error = e
                    else:
                        raise
            
            # If we exhausted retries, raise the last error
            if last_error:
                raise last_error
        
        return wrapper
    return decorator