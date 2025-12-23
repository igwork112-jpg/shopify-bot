"""
Progress Manager for Resume/Checkpoint Functionality
Tracks processed products and allows bot to resume from where it left off.
Includes review-level tracking for granular resume capability.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, Optional
from utils.logger import logger


class ProgressManager:
    """Manages bot progress for resume capability with review-level granularity"""
    
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
        
        # NEW: Track current in-progress product for review-level resume
        self.current_product: Optional[Dict] = None
        
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
            
            # NEW: Load current product state (for review-level resume)
            self.current_product = data.get('current_product', None)
            
            if self.processed_products:
                logger.success(f"✅ Loaded progress: {len(self.processed_products)} products already processed")
                logger.info(f"   📊 Stats: {self.stats['reviews_posted']} reviews posted")
            
            # Show resume position if we have an in-progress product
            if self.current_product:
                logger.info(f"🔄 Found in-progress product: {self.current_product.get('reviews_completed', 0)}/{self.current_product.get('total_reviews', 0)} reviews done")
            
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
            'stats': self.stats,
            'current_product': self.current_product  # NEW: Save current product state
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
    
    # ============================================================
    # NEW: Review-level tracking methods
    # ============================================================
    
    def start_product(self, product_url: str, total_reviews: int, 
                      collection_index: int, product_index: int) -> int:
        """
        Start tracking a new product. Returns the review number to start from.
        If this is the same product we were working on before, resume from where we left off.
        """
        # Check if we're resuming the same product
        if self.current_product and self.current_product.get('product_url') == product_url:
            resume_from = self.current_product.get('reviews_completed', 0) + 1
            logger.info(f"🔄 Resuming product from review {resume_from}/{total_reviews}")
            return resume_from
        
        # New product - start fresh
        self.current_product = {
            'product_url': product_url,
            'total_reviews': total_reviews,
            'reviews_completed': 0,
            'collection_index': collection_index,
            'product_index': product_index
        }
        self.save_progress()
        return 1  # Start from review 1
    
    def mark_review_done(self, success: bool = True) -> None:
        """Mark a single review as done and save immediately"""
        if self.current_product:
            self.current_product['reviews_completed'] += 1
            if success:
                self.stats['reviews_posted'] += 1
            else:
                self.stats['reviews_failed'] += 1
            self.save_progress()
            logger.debug(f"💾 Review {self.current_product['reviews_completed']}/{self.current_product['total_reviews']} saved")
    
    def complete_current_product(self, images_generated: int = 0) -> None:
        """Mark current product as fully completed and clear in-progress state"""
        if self.current_product:
            product_url = self.current_product['product_url']
            self.processed_products.add(product_url)
            self.stats['products_processed'] = len(self.processed_products)
            self.stats['images_generated'] += images_generated
            
            # Clear current product state
            self.current_product = None
            self.save_progress()
    
    def get_resume_position(self) -> Optional[Dict]:
        """
        Get the position to resume from (collection/product/review indices).
        Returns None if starting fresh, or a dict with resume position.
        """
        if self.current_product:
            return {
                'collection_index': self.current_product.get('collection_index', 0),
                'product_index': self.current_product.get('product_index', 0),
                'review_index': self.current_product.get('reviews_completed', 0) + 1,
                'total_reviews': self.current_product.get('total_reviews', 0),
                'product_url': self.current_product.get('product_url', '')
            }
        return None
    
    # ============================================================
    # Original methods (preserved for compatibility)
    # ============================================================
    
    def mark_product_done(self, product_url: str, reviews_posted: int = 0, 
                          reviews_failed: int = 0, images_generated: int = 0) -> None:
        """Mark a product as processed and update stats (legacy method)"""
        self.processed_products.add(product_url)
        self.stats['products_processed'] = len(self.processed_products)
        # Note: reviews_posted/failed now tracked per-review in mark_review_done()
        self.stats['images_generated'] += images_generated
        
        # Clear current product state since it's done
        self.current_product = None
        
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
        self.current_product = None  # NEW: Clear current product
        self.started_at = datetime.now().isoformat()
        self.last_updated = None
    
    def get_resume_info(self) -> Dict:
        """Get information about resume state"""
        info = {
            'has_progress': len(self.processed_products) > 0 or self.current_product is not None,
            'products_done': len(self.processed_products),
            'reviews_posted': self.stats['reviews_posted'],
            'started_at': self.started_at,
            'last_updated': self.last_updated
        }
        
        # NEW: Add current product info if available
        if self.current_product:
            info['in_progress_product'] = {
                'reviews_completed': self.current_product.get('reviews_completed', 0),
                'total_reviews': self.current_product.get('total_reviews', 0)
            }
        
        return info
