"""
Progress Manager for Resume/Checkpoint Functionality
Tracks processed products and allows bot to resume from where it left off.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, Optional
from utils.logger import logger


class ProgressManager:
    """Manages bot progress for resume capability"""
    
    def __init__(self, store_url: str, progress_file: str = "progress.json"):
        self.store_url = store_url
        self.progress_file = Path(progress_file)
        self.processed_products: Set[str] = set()
        self.stats = {
            'collections_processed': 0,
            'products_processed': 0,
            'reviews_posted': 0,
            'reviews_failed': 0,
            'images_generated': 0
        }
        self.started_at: Optional[str] = None
        self.last_updated: Optional[str] = None
        
        # Load existing progress if available
        self._load_progress()
    
    def _load_progress(self) -> None:
        """Load existing progress from file"""
        if not self.progress_file.exists():
            logger.info("📝 No existing progress found - starting fresh")
            self.started_at = datetime.now().isoformat()
            return
        
        try:
            with open(self.progress_file, 'r') as f:
                data = json.load(f)
            
            # Check if progress is for the same store
            if data.get('store_url') != self.store_url:
                logger.warning(f"⚠️ Progress file is for different store, starting fresh")
                logger.warning(f"   Saved: {data.get('store_url')}")
                logger.warning(f"   Current: {self.store_url}")
                self.started_at = datetime.now().isoformat()
                return
            
            # Load progress data
            self.processed_products = set(data.get('processed_products', []))
            self.stats = data.get('stats', self.stats)
            self.started_at = data.get('started_at', datetime.now().isoformat())
            self.last_updated = data.get('last_updated')
            
            if self.processed_products:
                logger.success(f"✅ Loaded progress: {len(self.processed_products)} products already processed")
                logger.info(f"   📊 Stats: {self.stats['reviews_posted']} reviews posted")
            
        except Exception as e:
            logger.error(f"Failed to load progress: {e}")
            self.started_at = datetime.now().isoformat()
    
    def save_progress(self) -> None:
        """Save current progress to file"""
        self.last_updated = datetime.now().isoformat()
        
        data = {
            'store_url': self.store_url,
            'started_at': self.started_at,
            'last_updated': self.last_updated,
            'processed_products': list(self.processed_products),
            'stats': self.stats
        }
        
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"💾 Progress saved: {len(self.processed_products)} products")
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
    
    def is_product_processed(self, product_url: str) -> bool:
        """Check if a product has already been processed"""
        return product_url in self.processed_products
    
    def mark_product_done(self, product_url: str, reviews_posted: int = 0, 
                          reviews_failed: int = 0, images_generated: int = 0) -> None:
        """Mark a product as processed and update stats"""
        self.processed_products.add(product_url)
        self.stats['products_processed'] = len(self.processed_products)
        self.stats['reviews_posted'] += reviews_posted
        self.stats['reviews_failed'] += reviews_failed
        self.stats['images_generated'] += images_generated
        
        # Auto-save after each product
        self.save_progress()
    
    def mark_collection_done(self) -> None:
        """Increment collections processed count"""
        self.stats['collections_processed'] += 1
        self.save_progress()
    
    def clear_progress(self) -> None:
        """Clear all progress (called on successful completion)"""
        if self.progress_file.exists():
            try:
                self.progress_file.unlink()
                logger.success("🧹 Progress cleared - ready for fresh start")
            except Exception as e:
                logger.error(f"Failed to clear progress: {e}")
        
        # Reset in-memory state
        self.processed_products = set()
        self.stats = {
            'collections_processed': 0,
            'products_processed': 0,
            'reviews_posted': 0,
            'reviews_failed': 0,
            'images_generated': 0
        }
        self.started_at = datetime.now().isoformat()
        self.last_updated = None
    
    def get_resume_info(self) -> Dict:
        """Get information about resume state"""
        return {
            'has_progress': len(self.processed_products) > 0,
            'products_done': len(self.processed_products),
            'reviews_posted': self.stats['reviews_posted'],
            'started_at': self.started_at,
            'last_updated': self.last_updated
        }
