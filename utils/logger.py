import logging
import sys
import os
import re
from datetime import datetime
from config.settings import settings

def remove_emojis(text: str) -> str:
    """Remove unsupported characters if encoding fails"""
    return re.sub(r'[^\x00-\x7F]+', '', text)

class BotLogger:
    """Custom logger for the review bot with emoji-safe output"""
    
    def __init__(self, name="ReviewBot"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers = []
        
        # --- Console Handler with UTF-8 support ---
        console_handler = logging.StreamHandler(sys.stdout)
        try:
            # Reopen stdout with UTF-8 encoding (Windows safe)
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            # Fallback if reconfigure isn't available
            console_handler.setStream(open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1))
        
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # --- File Handler (UTF-8 safe) ---
        log_file = settings.LOGS_DIR / f"bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
    
    # --- Safe log writer ---
    def _safe_log(self, level_func, message):
        try:
            level_func(message)
        except UnicodeEncodeError:
            # Strip emojis if terminal doesn't support them
            level_func(remove_emojis(message))
    
    # --- Log methods ---
    def info(self, message): self._safe_log(self.logger.info, message)
    def error(self, message): self._safe_log(self.logger.error, message)
    def warning(self, message): self._safe_log(self.logger.warning, message)
    def debug(self, message): self._safe_log(self.logger.debug, message)
    
    def success(self, message): self._safe_log(self.logger.info, f"✅ {message}")
    def failure(self, message): self._safe_log(self.logger.error, f"❌ {message}")

logger = BotLogger()
