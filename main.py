import time
import random
from config.settings import settings
from utils.logger import logger
from src.browser_manager import BrowserManager
from src.product_scraper import ProductScraper
from src.review_generator import ReviewGenerator
from src.loox_review_poster import LooxReviewPoster
from src.progress_manager import ProgressManager

# Global web logs for Flask interface
web_logs = []

# Global stop check function - set by app.py
stop_check_fn = None

def set_stop_check(fn):
    """Set the stop check function from app.py"""
    global stop_check_fn
    stop_check_fn = fn

def check_stop_signal():
    """Check if stop was requested and raise if so"""
    global stop_check_fn
    if stop_check_fn and stop_check_fn():
        raise KeyboardInterrupt("Stop requested by user")

def add_web_log(log_type, message):
    """Add log for web interface"""
    global web_logs
    web_logs.append({
        'type': log_type,
        'message': message,
        'timestamp': time.time()
    })

class ReviewBot:
    """Main bot orchestrator"""
    
    def __init__(self, store_url=None):
        self.stats = {
            'collections_processed': 0,
            'products_processed': 0,
            'products_found': 0,
            'reviews_posted': 0,
            'reviews_failed': 0,
            'images_generated': 0
        }

        # Use provided store_url or fall back to settings
        self.store_url = store_url or settings.STORE_URL
        
        # Initialize progress manager for resume capability
        self.progress = ProgressManager(self.store_url)
    
    def run(self):
        """Main execution flow"""
        try:
            # Validate settings
            settings.validate()
            
            logger.info("=" * 70)
            add_web_log('info', '🚀 Starting Shopify Loox Review Bot')
            logger.info("🚀 SHOPIFY LOOX REVIEW BOT STARTED")
            logger.info("=" * 70)
            logger.info(f"📍 Store: {self.store_url}")
            add_web_log('info', f'Store: {self.store_url}')
            logger.info(f"📝 Reviews per product: {settings.MIN_REVIEWS_PER_PRODUCT}-{settings.MAX_REVIEWS_PER_PRODUCT} (random)")
            add_web_log('info', f'Reviews per product: {settings.MIN_REVIEWS_PER_PRODUCT}-{settings.MAX_REVIEWS_PER_PRODUCT} (random)')
            logger.info(f"📸 AI Images: {'Enabled' if settings.USE_AI_IMAGES else 'Disabled'}")
            add_web_log('info', f"AI Images: {'Enabled' if settings.USE_AI_IMAGES else 'Disabled'}")
            
            # Show resume status
            resume_info = self.progress.get_resume_info()
            if resume_info['has_progress']:
                logger.info(f"🔄 RESUMING: {resume_info['products_done']} products already processed")
                add_web_log('info', f"🔄 Resuming from previous run: {resume_info['products_done']} products done")
                
                # Show in-progress product info if available
                if 'in_progress_product' in resume_info:
                    in_prog = resume_info['in_progress_product']
                    logger.info(f"   📦 In-progress: {in_prog['reviews_completed']}/{in_prog['total_reviews']} reviews done")
                    add_web_log('info', f"📦 Resuming product at review {in_prog['reviews_completed'] + 1}/{in_prog['total_reviews']}")
            
            logger.info("=" * 70)
            
            # Start browser with restart capability
            add_web_log('info', 'Launching browser...')
            browser_manager = BrowserManager()
            page = browser_manager.start()
            
            try:
                # Initialize components
                scraper = ProductScraper(page)
                generator = ReviewGenerator()
                poster = LooxReviewPoster(page)
                
                add_web_log('success', 'Browser launched successfully')
                
                # Step 1: Get homepage collections
                add_web_log('info', 'Scanning /collections page...')
                collections = scraper.get_homepage_collections(self.store_url)
                
                if not collections:
                    logger.error("No collections found on homepage!")
                    add_web_log('error', 'No collections found on homepage')
                    return
                
                logger.info(f"\n📦 Found {len(collections)} collections on homepage\n")
                add_web_log('success', f'Found {len(collections)} collections')
                
                # Step 2: Loop through all collections
                for coll_idx, collection_url in enumerate(collections, 1):
                    logger.info("=" * 70)
                    logger.info(f"COLLECTION {coll_idx}/{len(collections)}")
                    add_web_log('info', f'Processing collection {coll_idx}/{len(collections)}')
                    logger.info("=" * 70)
                    
                    try:
                        # Get products in this collection
                        products = scraper.get_products_from_collection(collection_url)
                        
                        if not products:
                            logger.warning("No products in this collection, skipping...")
                            add_web_log('warning', f'Collection {coll_idx} has no products, skipping')
                            continue
                        
                        self.stats['collections_processed'] += 1
                        self.stats['products_found'] += len(products)
                        add_web_log('success', f'Found {len(products)} products in collection {coll_idx}')

                        
                        # Step 3: Loop through products
                        for prod_idx, product_url in enumerate(products, 1):
                            logger.info("\n" + "=" * 70)
                            logger.info(f"PRODUCT {prod_idx}/{len(products)} in Collection {coll_idx}")
                            add_web_log('info', f'Processing product {prod_idx}/{len(products)} from collection {coll_idx}')
                            logger.info(f"🔍 {product_url}")
                            logger.info("=" * 70)
                            
                            try:
                                # Extract product data
                                product_data = scraper.extract_product_data(product_url)
                                
                                if not product_data:
                                    logger.warning("Skipping - no data extracted")
                                    add_web_log('warning', f'Skipped product {prod_idx} - no data')
                                    continue
                                
                                # Check if product already processed (resume support)
                                if self.progress.is_product_processed(product_url):
                                    logger.info(f"⏭️ Skipping - already processed in previous run")
                                    add_web_log('info', f'Skipped {product_data["name"]} - already done')
                                    continue
                                
                                self.stats['products_processed'] += 1
                                add_web_log('success', f'Extracted data for: {product_data["name"]}')
                                
                                # POST ALL REVIEWS FOR THIS PRODUCT (random count between min-max)
                                reviews_for_this_product = random.randint(
                                    settings.MIN_REVIEWS_PER_PRODUCT, 
                                    settings.MAX_REVIEWS_PER_PRODUCT
                                )
                                
                                # Get starting review number (may resume from previous run)
                                start_review_num = self.progress.start_product(
                                    product_url, 
                                    reviews_for_this_product,
                                    coll_idx,
                                    prod_idx
                                )
                                
                                if start_review_num > 1:
                                    logger.info(f"🔄 Resuming from review {start_review_num}/{reviews_for_this_product}")
                                    add_web_log('info', f'🔄 Resuming from review {start_review_num}/{reviews_for_this_product} for {product_data["name"]}')
                                else:
                                    logger.info(f"📊 Will post {reviews_for_this_product} reviews for this product")
                                    add_web_log('info', f'Will post {reviews_for_this_product} reviews for {product_data["name"]}')
                                
                                # Track images for this product
                                images_this_product = 0
                                
                                for review_num in range(start_review_num, reviews_for_this_product + 1):
                                    # Check for stop signal before each review
                                    check_stop_signal()
                                    
                                    logger.info(f"\n📝 REVIEW {review_num}/{reviews_for_this_product} FOR THIS PRODUCT")
                                    add_web_log('info', f'Generating review {review_num}/{reviews_for_this_product} for {product_data["name"]}')
                                    logger.info("-" * 50)
                                    
                                    # Generate review data with GPT-Image-1 workflow
                                    review_data = generator.generate(
                                        product_name=product_data['name'],
                                        product_description=product_data['description'],
                                        product_image_url=product_data['image_url'],  # ← Pass image URL
                                        with_image=settings.USE_AI_IMAGES  # ← Control image generation
                                    )
                                    
                                    # Check stop signal after generation (can take time)
                                    check_stop_signal()
                                    
                                    logger.info(f"⭐ Rating: {review_data['rating']} stars")
                                    logger.info(f"👤 Name: {review_data['first_name']} {review_data['last_name']}")
                                    logger.info(f"📧 Email: {review_data['email']}")
                                    logger.info(f"💬 Review: {review_data['text'][:80]}...")
                                    
                                    # Track image generation
                                    if review_data.get('image_path'):
                                        images_this_product += 1
                                        self.stats['images_generated'] += 1
                                        logger.info(f"📸 AI Image: {review_data['image_path'].name}")
                                        add_web_log('success', f'Generated AI image for review {review_num}')

                                    
                                    # Post review to Loox with browser recovery
                                    success = False
                                    max_post_retries = 3
                                    
                                    for post_attempt in range(max_post_retries):
                                        try:
                                            success = poster.post_review(
                                                review_data, 
                                                image_path=review_data.get('image_path')
                                            )
                                            break  # Success, exit retry loop
                                            
                                        except Exception as post_error:
                                            error_str = str(post_error).lower()
                                            recoverable = any(err in error_str for err in [
                                                'epipe', 'broken pipe', 'target closed',
                                                'browser has been closed', 'page closed',
                                                'connection closed', 'frame was detached'
                                            ])
                                            
                                            if recoverable and post_attempt < max_post_retries - 1:
                                                logger.warning(f"⚠️ Browser error during review post (attempt {post_attempt + 1}/{max_post_retries}): {post_error}")
                                                add_web_log('warning', f'Browser error, restarting... (attempt {post_attempt + 1})')
                                                
                                                # Restart browser
                                                try:
                                                    page = browser_manager.restart()
                                                    # Re-initialize components with new page
                                                    scraper = ProductScraper(page)
                                                    poster = LooxReviewPoster(page)
                                                    
                                                    # Navigate back to product page
                                                    logger.info(f"🔄 Navigating back to product: {product_url}")
                                                    page.goto(product_url, wait_until="domcontentloaded")
                                                    time.sleep(3)
                                                    
                                                except Exception as restart_error:
                                                    logger.error(f"❌ Browser restart failed: {restart_error}")
                                                    raise post_error  # Re-raise original error
                                            else:
                                                # Non-recoverable or max retries exceeded
                                                raise
                                    
                                    # Mark review done and save progress immediately
                                    self.progress.mark_review_done(success=success)
                                    
                                    # Reset restart count on successful operation
                                    browser_manager.reset_restart_count()
                                    
                                    # Check stop signal after posting (can take time)
                                    check_stop_signal()
                                    
                                    if success:
                                        self.stats['reviews_posted'] += 1
                                        logger.success(f"✅ Review {review_num}/{reviews_for_this_product} posted!")
                                        add_web_log('success', f'✅ Posted review {review_num}/{reviews_for_this_product} for {product_data["name"]}')
                                    else:
                                        self.stats['reviews_failed'] += 1
                                        logger.failure(f"❌ Review {review_num}/{reviews_for_this_product} failed")
                                        add_web_log('error', f'❌ Failed to post review {review_num}/{reviews_for_this_product}')

                                    
                                    # Cleanup temp image file
                                    if review_data.get('image_path') and review_data['image_path'].exists():
                                        try:
                                            review_data['image_path'].unlink()
                                            logger.debug(f"🗑️ Cleaned up: {review_data['image_path'].name}")
                                        except Exception as e:
                                            logger.warning(f"Could not cleanup image: {e}")
                                    
                                    # Delay between reviews on SAME PRODUCT
                                    if review_num < reviews_for_this_product:
                                        delay = random.uniform(settings.MIN_DELAY, settings.MAX_DELAY)
                                        logger.info(f"⏳ Waiting {delay:.1f}s before next review on this product...")
                                        time.sleep(delay)
                                        
                                        # Check stop signal after delay
                                        check_stop_signal()
                                    
                                    # Go back to product page for next review
                                    if review_num < reviews_for_this_product:
                                        logger.info("🔄 Returning to product page for next review...")
                                        try:
                                            page.goto(product_url, wait_until="domcontentloaded")
                                            time.sleep(2)
                                        except Exception as nav_error:
                                            # Handle navigation errors with browser restart
                                            logger.warning(f"⚠️ Navigation error: {nav_error}")
                                            page = browser_manager.restart()
                                            scraper = ProductScraper(page)
                                            poster = LooxReviewPoster(page)
                                            page.goto(product_url, wait_until="domcontentloaded")
                                            time.sleep(3)
                                
                                logger.success(f"✅ Completed all {reviews_for_this_product} reviews for this product!")
                                add_web_log('success', f'Completed all reviews for {product_data["name"]}')
                                
                                # Mark product as fully completed and clear in-progress state
                                self.progress.complete_current_product(images_generated=images_this_product)
                                
                                # Delay between PRODUCTS
                                if prod_idx < len(products):
                                    delay = random.uniform(settings.MIN_DELAY * 2, settings.MAX_DELAY * 2)
                                    logger.info(f"\n⏳ Waiting {delay:.1f}s before moving to next product...")
                                    time.sleep(delay)
                                
                            except Exception as e:
                                logger.failure(f"Error processing product: {e}")
                                add_web_log('error', f'Error on product {prod_idx}: {str(e)}')
                                self.stats['reviews_failed'] += 1
                                continue
                        
                        logger.success(f"✅ Completed collection {coll_idx}/{len(collections)}")
                        add_web_log('success', f'Completed collection {coll_idx}/{len(collections)}')
                        
                        # Delay between COLLECTIONS
                        if coll_idx < len(collections):
                            delay = random.uniform(settings.MIN_DELAY * 3, settings.MAX_DELAY * 3)
                            logger.info(f"\n⏳ Waiting {delay:.1f}s before next collection...")
                            time.sleep(delay)
                        
                    except Exception as e:
                        logger.failure(f"Error processing collection: {e}")
                        add_web_log('error', f'Error on collection {coll_idx}: {str(e)}')
                        continue
            
                # Print final stats
                self._print_stats()
                add_web_log('success', '🎉 Bot completed all tasks successfully!')
                
                # Clear progress on successful completion
                self.progress.clear_progress()
                add_web_log('info', '✨ Progress cleared - ready for next run')
                
            finally:
                # Always close the browser
                browser_manager.close()
            
        except KeyboardInterrupt:
            logger.warning("\n\n⚠️  Bot stopped by user")
            add_web_log('warning', 'Bot stopped by user')
            add_web_log('info', '💾 Progress saved - click Resume Bot to continue')
            self._print_stats()
            # Progress is already saved - don't clear it
        except Exception as e:
            logger.failure(f"Fatal error: {e}")
            add_web_log('error', f'❌ Fatal error: {str(e)}')
            add_web_log('info', '💾 Progress saved - click Resume Bot to continue from where it crashed')

            # Save current progress state before exiting
            self.progress.save_progress()
            self._print_stats()
            raise
    
    def _print_stats(self):
        """Print final statistics"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 FINAL STATISTICS")
        logger.info("=" * 70)
        logger.info(f"✅ Collections Processed: {self.stats['collections_processed']}")
        logger.info(f"✅ Products Processed: {self.stats['products_processed']}")
        logger.info(f"✅ Reviews Posted: {self.stats['reviews_posted']}")
        logger.info(f"❌ Reviews Failed: {self.stats['reviews_failed']}")
        logger.info(f"📸 AI Images Generated: {self.stats['images_generated']}")
        
        if self.stats['reviews_posted'] > 0:
            success_rate = (self.stats['reviews_posted'] / 
                          (self.stats['reviews_posted'] + self.stats['reviews_failed'])) * 100
            logger.info(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Calculate estimated costs
        if self.stats['images_generated'] > 0:
            image_cost = self.stats['images_generated'] * 0.044  # ~$0.044 per GPT-Image-1
            logger.info(f"💰 Estimated Image Cost: ${image_cost:.2f}")
        
        logger.info("=" * 70)
        
        # Send final stats to web interface
        add_web_log('info', f"Collections: {self.stats['collections_processed']}, Products: {self.stats['products_processed']}, Reviews Posted: {self.stats['reviews_posted']}, Images: {self.stats['images_generated']}")

def main():
    """Entry point"""
    bot = ReviewBot()
    bot.run()

if __name__ == "__main__":
    main()