# import time
# import random
# from pathlib import Path
# from typing import Dict, Optional
# from playwright.sync_api import Page
# from utils.logger import logger

# class LooxReviewPoster:
#     """Posts reviews to Loox review system - Based on working test selectors"""
    
#     def __init__(self, page: Page):
#         self.page = page
    
#     def post_review(self, review_data: Dict, image_path: Optional[Path] = None) -> bool:
#         """Complete Loox review posting workflow"""
#         try:
#             logger.info("=" * 50)
#             logger.info("Starting Loox review submission...")
#             logger.info("=" * 50)
            
#             # Step 0: Close pop-ups and cookie banners
#             if not self._close_popups():
#                 logger.warning("Could not close all popups, continuing anyway...")
            
#             # Step 1: Scroll to load Loox iframe
#             if not self._scroll_to_reviews():
#                 return False
            
#             # Step 2: Switch to Loox reviews iframe
#             if not self._switch_to_loox_reviews_iframe():
#                 return False
            
#             # Step 3: Click "Write a Review" button
#             if not self._click_write_review():
#                 return False
            
#             # Step 4: Switch to review form iframe
#             if not self._switch_to_review_form_iframe():
#                 return False
            
#             # Step 5: Click star rating
#             if not self._click_star_rating(review_data['rating']):
#                 return False
            
#             # Step 6: Click Skip button (for photo upload step)
#             if not self._click_skip_button():
#                 return False
            
#             # Step 7: Fill review text
#             if not self._fill_review_text(review_data['text']):
#                 return False
            
#             # Step 8: Click Next button
#             if not self._click_next_button():
#                 return False
            
#             # Step 9: Fill name and email
#             if not self._fill_customer_info(review_data):
#                 return False
            
#             # Step 10: Click Done button
#             if not self._click_done_button():
#                 return False
            
#             # Step 11: Close the review modal
#             if not self._click_close_button():
#                 return False
            
#             logger.success("🎯 Review submitted successfully!")
#             return True
            
#         except Exception as e:
#             logger.failure(f"Error posting Loox review: {e}")
#             return False
    
#     def _close_popups(self) -> bool:
#         """Close popup banners, cookie notices, and promotional popups"""
#         try:
#             logger.info("🚫 Closing popups and banners...")
            
#             # Common popup close button selectors
#             close_selectors = [
#                 # Generic close buttons
#                 "button[aria-label='Close']",
#                 "button[aria-label='close']",
#                 "button.close",
#                 "button[class*='close']",
#                 ".modal-close",
#                 "[data-dismiss='modal']",
                
#                 # Cookie consent
#                 "button[id*='cookie']",
#                 "button[class*='cookie']",
#                 "button:has-text('Accept')",
#                 "button:has-text('Accept All')",
#                 "button:has-text('Accept Cookies')",
#                 "button:has-text('I Accept')",
#                 "button:has-text('Got it')",
#                 "button:has-text('OK')",
#                 "a:has-text('Accept')",
#                 "#CybotCookiebotDialogBodyButtonAccept",
                
#                 # Newsletter/Email popups
#                 "button[class*='dismiss']",
#                 "button[class*='cancel']",
#                 "[class*='popup'] button[aria-label='Close']",
#                 "[class*='modal'] button[aria-label='Close']",
#                 ".needsclick[aria-label='Close dialog 1']",
                
#                 # X buttons
#                 "button:has-text('×')",
#                 "button:has-text('✕')",
#                 "span:has-text('×') >> xpath=ancestor::button",
                
#                 # Specific classes
#                 ".klaviyo-close-form",
#                 "button[class*='CloseButton']",
#                 "[data-testid*='close']",
#                 "[data-testid*='dismiss']"
#             ]
            
#             closed_count = 0
            
#             # Try each selector
#             for selector in close_selectors:
#                 try:
#                     # Check if element exists and is visible
#                     elements = self.page.locator(selector)
#                     count = elements.count()
                    
#                     if count > 0:
#                         # Click all matching elements (might be multiple popups)
#                         for i in range(min(count, 3)):  # Max 3 to avoid infinite loops
#                             try:
#                                 elements.nth(i).click(timeout=1000, force=True)
#                                 closed_count += 1
#                                 logger.debug(f"Closed popup with: {selector}")
#                                 time.sleep(0.3)
#                             except:
#                                 continue
#                 except:
#                     continue
            
#             # Try to close popups inside iframes
#             try:
#                 iframes = self.page.query_selector_all('iframe[src*="klaviyo"], iframe[src*="popup"], iframe[src*="newsletter"]')
#                 for iframe in iframes:
#                     try:
#                         iframe_frame = iframe.content_frame()
#                         if iframe_frame:
#                             close_btn = iframe_frame.query_selector("button[aria-label='Close'], .close, [class*='close']")
#                             if close_btn:
#                                 close_btn.click(force=True)
#                                 closed_count += 1
#                                 logger.debug("Closed popup inside iframe")
#                                 time.sleep(0.3)
#                     except:
#                         continue
#             except:
#                 pass
            
#             # Press Escape key multiple times to close any remaining modals
#             try:
#                 for _ in range(3):
#                     self.page.keyboard.press('Escape')
#                     time.sleep(0.2)
#                 logger.debug("Pressed Escape keys")
#             except:
#                 pass
            
#             # Try JavaScript to remove overlays
#             try:
#                 self.page.evaluate("""
#                     // Remove common popup/modal overlays
#                     const overlays = document.querySelectorAll('[class*="overlay"], [class*="backdrop"], [class*="modal"]');
#                     overlays.forEach(el => {
#                         if (el.style.display !== 'none') {
#                             el.remove();
#                         }
#                     });
                    
#                     // Remove fixed/sticky elements that might be popups
#                     const fixed = document.querySelectorAll('[style*="position: fixed"]');
#                     fixed.forEach(el => {
#                         const rect = el.getBoundingClientRect();
#                         // If it covers a large portion of screen, might be a popup
#                         if (rect.width > window.innerWidth * 0.5 && rect.height > window.innerHeight * 0.5) {
#                             el.remove();
#                         }
#                     });
#                 """)
#                 logger.debug("Ran JS cleanup for overlays")
#             except:
#                 pass
            
#             if closed_count > 0:
#                 logger.success(f"✅ Closed {closed_count} popups/banners")
#             else:
#                 logger.info("No popups detected")
            
#             # Wait a bit for DOM to settle
#             time.sleep(1)
#             return True
            
#         except Exception as e:
#             logger.warning(f"Error closing popups: {e}")
#             return False
    
#     def _scroll_to_reviews(self) -> bool:
#         """Scroll to load Loox iframe"""
#         try:
#             logger.info("📜 Scrolling to load Loox iframe...")
            
#             for i in range(0, 10):
#                 self.page.evaluate(f"window.scrollTo(0, {i * 400});")
#                 time.sleep(0.3)
            
#             self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
#             time.sleep(2)
            
#             logger.success("Scrolled to reviews section")
#             return True
            
#         except Exception as e:
#             logger.error(f"Error scrolling: {e}")
#             return False
    
#     def _switch_to_loox_reviews_iframe(self) -> bool:
#         """Switch to Loox reviews iframe - iframe#looxReviewsFrame"""
#         try:
#             logger.info("🔄 Switching to Loox reviews iframe...")
            
#             self.page.wait_for_selector('iframe#looxReviewsFrame', timeout=20000)
#             iframe_el = self.page.query_selector('iframe#looxReviewsFrame')
#             self.loox_iframe = iframe_el.content_frame()
            
#             if not self.loox_iframe:
#                 logger.error("Could not access Loox reviews iframe")
#                 return False
            
#             logger.success("Switched to Loox reviews iframe")
#             return True
            
#         except Exception as e:
#             logger.error(f"Error switching to reviews iframe: {e}")
#             return False
    
#     def _click_write_review(self) -> bool:
#         """Click 'Write a Review' button - #write"""
#         try:
#             logger.info("✍️ Clicking 'Write a Review' button...")
            
#             self.loox_iframe.wait_for_selector("#write", timeout=15000)
#             self.loox_iframe.click("#write")
            
#             logger.success("Clicked 'Write a Review'")
#             time.sleep(5)
#             return True
            
#         except Exception as e:
#             logger.error(f"Error clicking write review: {e}")
#             return False
    
#     def _switch_to_review_form_iframe(self) -> bool:
#         """Switch to review form iframe - iframe#loox-review-form-ugc-dialog"""
#         try:
#             logger.info("🔄 Switching to review form iframe...")
            
#             self.page.wait_for_selector('iframe#loox-review-form-ugc-dialog', timeout=20000)
#             iframe_element = self.page.query_selector('iframe#loox-review-form-ugc-dialog')
#             self.review_iframe = iframe_element.content_frame()
            
#             if not self.review_iframe:
#                 logger.error("Could not access review form iframe")
#                 return False
            
#             self.review_iframe.wait_for_function("document.readyState === 'complete' && document.body !== null")
            
#             logger.success("Review form iframe loaded")
#             return True
            
#         except Exception as e:
#             logger.error(f"Error switching to form iframe: {e}")
#             return False
    
#     def _click_star_rating(self, rating: int) -> bool:
#         """Click star rating (5 stars)"""
#         try:
#             logger.info(f"🌟 Setting {rating}-star rating...")
            
#             # Try multiple star selectors
#             possible_selectors = [
#                 ".loox-star",
#                 "button[data-lx-fill]",
#                 "svg.lx-animation-stroke-star-color",
#                 "svg[xmlns='http://www.w3.org/2000/svg']",
#                 "div[class*='loox'] svg"
#             ]
            
#             stars = None
#             for sel in possible_selectors:
#                 count = self.review_iframe.locator(sel).count()
#                 if count > 0:
#                     stars = self.review_iframe.locator(sel)
#                     logger.debug(f"Found {count} stars using selector: {sel}")
#                     break
            
#             if not stars or stars.count() == 0:
#                 logger.error("No stars found")
#                 return False
            
#             # Click the nth star (0-indexed, so rating-1)
#             idx = min(rating - 1, stars.count() - 1)
#             stars.nth(idx).click(force=True)
            
#             logger.success(f"Clicked {rating}-star rating")
#             time.sleep(2)
#             return True
            
#         except Exception as e:
#             logger.error(f"Error clicking stars: {e}")
#             return False
    
#     def _click_skip_button(self) -> bool:
#         """Click Skip button for photo upload"""
#         try:
#             logger.info("⏭️ Clicking Skip button...")
            
#             skip_selectors = [
#                 "button[aria-label='Skip']",
#                 "button[data-testid='mobile skip button']",
#                 "button:has-text('Skip')",
#                 "text=Skip",
#                 "xpath=//button[contains(., 'Skip')]"
#             ]
            
#             skip_clicked = False
#             for sel in skip_selectors:
#                 try:
#                     self.review_iframe.wait_for_selector(sel, timeout=2000)
#                     self.review_iframe.click(sel, timeout=2000, force=True)
#                     logger.success(f"Clicked Skip with: {sel}")
#                     skip_clicked = True
#                     break
#                 except Exception:
#                     continue
            
#             if not skip_clicked:
#                 # JS fallback
#                 self.review_iframe.evaluate("""
#                     const btn = Array.from(document.querySelectorAll('button'))
#                       .find(b => b.textContent.trim().toLowerCase() === 'skip');
#                     if (btn) btn.click();
#                 """)
#                 logger.success("Skip clicked via JS fallback")
            
#             time.sleep(2)
#             return True
            
#         except Exception as e:
#             logger.error(f"Error clicking skip: {e}")
#             return False
    
#     def _fill_review_text(self, review_text: str) -> bool:
#         """Fill review textarea"""
#         try:
#             logger.info("📝 Filling review text...")
            
#             textarea_selectors = [
#                 "textarea[data-testid='review field']",
#                 "textarea[aria-label='Tell us more!']",
#                 "form textarea",
#                 "textarea"
#             ]
            
#             review_text_entered = False
#             for sel in textarea_selectors:
#                 try:
#                     self.review_iframe.wait_for_selector(sel, timeout=2000)
#                     self.review_iframe.fill(sel, review_text)
#                     logger.success(f"Filled review text with: {sel}")
#                     review_text_entered = True
#                     break
#                 except Exception:
#                     continue
            
#             if not review_text_entered:
#                 # JS fallback
#                 self.review_iframe.evaluate(f"""
#                     const ta = document.querySelector('textarea');
#                     if (ta) {{
#                         ta.value = "{review_text.replace('"', '\\"')}";
#                         ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
#                     }}
#                 """)
#                 logger.success("Review text filled via JS fallback")
            
#             time.sleep(1)
#             return True
            
#         except Exception as e:
#             logger.error(f"Error filling review text: {e}")
#             return False
    
#     def _click_next_button(self) -> bool:
#         """Click Next button"""
#         try:
#             logger.info("➡️ Clicking Next button...")
            
#             next_selectors = [
#                 "button[data-testid='next button']",
#                 "button:has-text('Next')",
#                 "text=Next",
#                 "button[data-lxs-variant='primary']",
#                 "css=button._lxs-button_luvow_1",
#                 "css=button._button_33r16_43"
#             ]
            
#             next_clicked = False
#             for sel in next_selectors:
#                 try:
#                     self.review_iframe.wait_for_selector(sel, timeout=2500)
                    
#                     # Wait for button to be enabled
#                     self.review_iframe.wait_for_function(
#                         """(selector) => {
#                             const el = document.querySelector(selector);
#                             return el && !el.disabled;
#                         }""",
#                         sel,
#                         timeout=5000
#                     )
                    
#                     self.review_iframe.click(sel, timeout=2000, force=True)
#                     logger.success(f"Clicked Next with: {sel}")
#                     next_clicked = True
#                     time.sleep(5)
#                     break
#                 except Exception:
#                     continue
            
#             if not next_clicked:
#                 # JS fallback
#                 self.review_iframe.evaluate("""
#                     const btn = Array.from(document.querySelectorAll('button'))
#                       .find(b => b.textContent && b.textContent.trim().toLowerCase() === 'next');
#                     if (btn) {
#                         btn.removeAttribute('disabled');
#                         btn.click();
#                     }
#                 """)
#                 logger.success("Next clicked via JS fallback")
#                 time.sleep(5)
            
#             return True
            
#         except Exception as e:
#             logger.error(f"Error clicking next: {e}")
#             return False
    
#     def _fill_customer_info(self, review_data: Dict) -> bool:
#         """Fill first name, last name, and email fields"""
#         try:
#             logger.info("👤 Filling customer information...")
            
#             inputs = {
#                 "first name": [
#                     "input[data-testid='first name field']",
#                     "input[autocomplete='given-name']"
#                 ],
#                 "last name": [
#                     "input[data-testid='last name field']",
#                     "input[autocomplete='family-name']"
#                 ],
#                 "email": [
#                     "input[data-testid='email field']",
#                     "input[autocomplete='email']"
#                 ]
#             }
            
#             # Get first_name and last_name directly from review_data
#             data = {
#                 "first name": review_data['first_name'],
#                 "last name": review_data['last_name'],
#                 "email": review_data['email']
#             }
            
#             for field, selectors in inputs.items():
#                 filled = False
#                 for sel in selectors:
#                     try:
#                         self.review_iframe.wait_for_selector(sel, timeout=2000)
#                         self.review_iframe.fill(sel, data[field])
#                         logger.success(f"Filled {field}: {data[field]}")
#                         filled = True
#                         time.sleep(0.5)
#                         break
#                     except Exception:
#                         continue
                
#                 if not filled:
#                     logger.warning(f"Could not fill {field}")
            
#             return True
            
#         except Exception as e:
#             logger.error(f"Error filling customer info: {e}")
#             return False
    
#     def _click_done_button(self) -> bool:
#         """Click Done button"""
#         try:
#             logger.info("✅ Clicking Done button...")
            
#             done_selectors = [
#                 "button[data-testid='done button']",
#                 "button:has-text('Done')",
#                 "text=Done",
#                 "xpath=//button[contains(., 'Done')]"
#             ]
            
#             done_clicked = False
#             for sel in done_selectors:
#                 try:
#                     self.review_iframe.wait_for_selector(sel, timeout=2000)
#                     self.review_iframe.click(sel, force=True)
#                     logger.success(f"Clicked Done with: {sel}")
#                     done_clicked = True
#                     time.sleep(3)
#                     break
#                 except Exception:
#                     continue
            
#             if not done_clicked:
#                 # JS fallback
#                 self.review_iframe.evaluate("""
#                     const btn = Array.from(document.querySelectorAll('button'))
#                       .find(b => b.textContent.trim().toLowerCase() === 'done');
#                     if (btn) btn.click();
#                 """)
#                 logger.success("Done clicked via JS fallback")
#                 time.sleep(3)
            
#             return True
            
#         except Exception as e:
#             logger.error(f"Error clicking done: {e}")
#             return False
    
#     def _click_close_button(self) -> bool:
#         """Click Close (Exit) button on the Loox review modal"""
#         try:
#             logger.info("❌ Attempting to click Close button...")

#             close_selectors = [
#                 "button[data-testid='close button']",
#                 "button[aria-label='Exit']",
#                 "button:has-text('×')",
#                 "xpath=//button[contains(., '×')]",
#                 "xpath=//button[@aria-label='Exit']",
#                 "button[class*='lxs-button']",
#                 "button[class*='_lxs-is-icon-only']",
#                 "button._lxs-button_luvow_1",
#                 "button._lxs-is-icon-only_luvow_139",
#                 "span._lxs-icon_6a8to_1 >> xpath=ancestor::button",
#                 "svg[viewBox='0 0 24 24'] >> xpath=ancestor::button",
#                 "xpath=//span[contains(@class,'_lxs-icon_6a8to_1')]/parent::button",
#                 "css=button[data-lxs-variant='text']",
#                 "button[type='button'][data-testid='close button']",
#             ]

#             clicked = False
#             for sel in close_selectors:
#                 try:
#                     self.review_iframe.wait_for_selector(sel, timeout=2000)
#                     self.review_iframe.click(sel, force=True)
#                     time.sleep(5)
#                     logger.info(f"Clicked Close with: {sel}")
#                     clicked = True
#                     break
#                 except Exception:
#                     continue

#             if not clicked:
#                 # JS fallback if all selectors fail
#                 self.review_iframe.evaluate("""
#                     const btn = Array.from(document.querySelectorAll('button'))
#                     .find(b => b.getAttribute('data-testid') === 'close button' 
#                         || b.getAttribute('aria-label') === 'Exit');
#                     if (btn) btn.click();
#                 """)
#                 time.sleep(5)
#                 logger.success("Close clicked via JS fallback")

#             time.sleep(5)
#             return True

#         except Exception as e:
#             logger.error(f"Error clicking close: {e}")
#             return False

import time
import random
from pathlib import Path
from typing import Dict, Optional
from playwright.sync_api import Page
from utils.logger import logger

class LooxReviewPoster:
    """Posts reviews to Loox review system - Based on working test selectors"""
    
    def __init__(self, page: Page):
        self.page = page
    
    def post_review(self, review_data: Dict, image_path: Optional[Path] = None) -> bool:
        """Complete Loox review posting workflow"""
        try:
            logger.info("=" * 50)
            logger.info("Starting Loox review submission...")
            logger.info("=" * 50)
            
            # Step 0: Close pop-ups and cookie banners
            if not self._close_popups():
                logger.warning("Could not close all popups, continuing anyway...")
            
            # Step 1: Scroll to load Loox iframe
            if not self._scroll_to_reviews():
                return False
            
            # Step 2: Switch to Loox reviews iframe
            if not self._switch_to_loox_reviews_iframe():
                return False
            
            # Step 3: Click "Write a Review" button
            if not self._click_write_review():
                return False
            
            # Step 4: Switch to review form iframe
            if not self._switch_to_review_form_iframe():
                return False
            
            # Step 5: Click star rating
            if not self._click_star_rating(review_data['rating']):
                return False
            
            # Step 6: Upload image or click Skip
            if not self._upload_image(image_path):
                return False
            
            # Step 7: Fill review text
            if not self._fill_review_text(review_data['text']):
                return False
            
            # Step 8: Click Next button
            if not self._click_next_button():
                return False
            
            # Step 9: Fill name and email
            if not self._fill_customer_info(review_data):
                return False
            
            # Step 10: Click Done button
            if not self._click_done_button():
                return False
            
            # Step 11: Close the review modal
            if not self._click_close_button():
                return False
            
            logger.success("🎯 Review submitted successfully!")
            return True
            
        except Exception as e:
            logger.failure(f"Error posting Loox review: {e}")
            return False
    
    def _close_popups(self) -> bool:
        """Close popup banners, cookie notices, and promotional popups with better targeting"""
        try:
            logger.info("🚫 Closing popups and banners...")
            
            # Organized selectors by priority and specificity
            popup_selectors = {
                # Cookie consent (highest priority - most common)
                'cookie_consent': [
                    "#CybotCookiebotDialogBodyButtonAccept",
                    "button[id*='cookie'][id*='accept' i]",
                    "button[class*='cookie'][class*='accept' i]",
                    "button:has-text('Accept All Cookies')",
                    "button:has-text('Accept Cookies')",
                    "button:has-text('Accept All')",
                ],
                
                # Newsletter/Email popups
                'newsletter': [
                    ".klaviyo-close-form",
                    ".needsclick[aria-label='Close dialog 1']",
                    "[class*='newsletter'] button[aria-label*='Close' i]",
                    "[class*='email-popup'] button[aria-label*='Close' i]",
                ],
                
                # Modal dialogs
                'modals': [
                    "[role='dialog'] button[aria-label*='Close' i]",
                    "[role='dialog'] button[data-dismiss='modal']",
                    ".modal button[aria-label*='Close' i]",
                    ".modal .close",
                    "[data-testid='modal'] [data-testid*='close' i]",
                ],
                
                # Generic close buttons (last resort)
                'generic': [
                    "button[aria-label='Close']",
                    "button.close:visible",
                    "[data-testid='close-button']",
                    "button[title*='Close' i]",
                ]
            }
            
            closed_count = 0
            max_attempts_per_selector = 2  # Reduced from 3
            
            # Process selectors by priority
            for category, selectors in popup_selectors.items():
                for selector in selectors:
                    try:
                        elements = self.page.locator(selector)
                        count = elements.count()
                        
                        if count > 0:
                            logger.debug(f"Found {count} element(s) matching {category}: {selector}")
                            
                            for i in range(min(count, max_attempts_per_selector)):
                                try:
                                    element = elements.nth(i)
                                    
                                    # Verify element is actually visible and clickable
                                    if element.is_visible(timeout=500):
                                        # Get element info for logging
                                        try:
                                            elem_text = element.inner_text(timeout=500)[:50]
                                        except:
                                            elem_text = "unknown"
                                        
                                        element.click(timeout=1000, force=False)  # Don't force click
                                        closed_count += 1
                                        logger.debug(f"✓ Closed {category} popup: '{elem_text}'")
                                        time.sleep(0.5)  # Wait for animation
                                        
                                except Exception as e:
                                    logger.debug(f"Could not click element {i}: {str(e)[:50]}")
                                    continue
                                    
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {str(e)[:50]}")
                        continue
            
            # Handle iframes (common for third-party popups)
            closed_count += self._close_iframe_popups()
            
            # Gentle escape key presses for any remaining modals
            if closed_count == 0:
                try:
                    self.page.keyboard.press('Escape')
                    time.sleep(0.3)
                    logger.debug("Pressed Escape key")
                except:
                    pass
            
            # Conservative JavaScript cleanup (only obvious overlays)
            try:
                removed = self.page.evaluate("""
                    () => {
                        let removed = 0;
                        
                        // Only remove elements explicitly marked as overlays/backdrops
                        const selectors = [
                            '[class*="modal-overlay"]',
                            '[class*="modal-backdrop"]', 
                            '[id*="popup-overlay"]',
                            '[class*="cookie-banner"][style*="fixed"]'
                        ];
                        
                        selectors.forEach(sel => {
                            document.querySelectorAll(sel).forEach(el => {
                                const style = window.getComputedStyle(el);
                                if (style.position === 'fixed' || style.position === 'absolute') {
                                    el.remove();
                                    removed++;
                                }
                            });
                        });
                        
                        return removed;
                    }
                """)
                
                if removed > 0:
                    closed_count += removed
                    logger.debug(f"Removed {removed} overlay elements via JS")
                    
            except Exception as e:
                logger.debug(f"JS cleanup failed: {str(e)[:50]}")
            
            # Report results
            if closed_count > 0:
                logger.success(f"✅ Closed {closed_count} popup(s)")
            else:
                logger.info("No popups detected")
            
            time.sleep(0.5)  # Brief settle time
            return True
            
        except Exception as e:
            logger.warning(f"Error closing popups: {e}")
            return False


    def _close_iframe_popups(self) -> int:
        """Handle popups inside iframes"""
        closed = 0
        try:
            # Target specific known iframe popup providers
            iframe_selectors = [
                'iframe[src*="klaviyo"]',
                'iframe[src*="mailchimp"]', 
                'iframe[title*="popup" i]',
                'iframe[title*="dialog" i]'
            ]
            
            for selector in iframe_selectors:
                try:
                    iframes = self.page.query_selector_all(selector)
                    
                    for iframe in iframes[:2]:  # Max 2 iframes
                        try:
                            iframe_frame = iframe.content_frame()
                            if iframe_frame:
                                # Look for close button in iframe
                                close_btn = iframe_frame.query_selector(
                                    "button[aria-label*='Close' i], .close, [class*='close-button']"
                                )
                                if close_btn and close_btn.is_visible():
                                    close_btn.click(timeout=1000)
                                    closed += 1
                                    logger.debug(f"Closed popup in iframe: {selector}")
                                    time.sleep(0.3)
                        except:
                            continue
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Iframe popup handling failed: {str(e)[:50]}")
    
        return closed
    
    def _scroll_to_reviews(self) -> bool:
        """Scroll to load Loox iframe"""
        try:
            logger.info("📜 Scrolling to load Loox iframe...")
            
            for i in range(0, 10):
                self.page.evaluate(f"window.scrollTo(0, {i * 400});")
                time.sleep(0.3)
            
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            
            logger.success("Scrolled to reviews section")
            return True
            
        except Exception as e:
            logger.error(f"Error scrolling: {e}")
            return False
    
    def _switch_to_loox_reviews_iframe(self) -> bool:
        """Switch to Loox reviews iframe - iframe#looxReviewsFrame"""
        try:
            logger.info("🔄 Switching to Loox reviews iframe...")
            
            self.page.wait_for_selector('iframe#looxReviewsFrame', timeout=20000)
            iframe_el = self.page.query_selector('iframe#looxReviewsFrame')
            self.loox_iframe = iframe_el.content_frame()
            
            if not self.loox_iframe:
                logger.error("Could not access Loox reviews iframe")
                return False
            
            logger.success("Switched to Loox reviews iframe")
            return True
            
        except Exception as e:
            logger.error(f"Error switching to reviews iframe: {e}")
            return False
    
    def _click_write_review(self) -> bool:
        """Click 'Write a Review' button - #write"""
        try:
            logger.info("✍️ Clicking 'Write a Review' button...")
            
            self.loox_iframe.wait_for_selector("#write", timeout=15000)
            self.loox_iframe.click("#write")
            
            logger.success("Clicked 'Write a Review'")
            time.sleep(5)
            return True
            
        except Exception as e:
            logger.error(f"Error clicking write review: {e}")
            return False
    
    def _switch_to_review_form_iframe(self) -> bool:
        """Switch to review form iframe - iframe#loox-review-form-ugc-dialog"""
        try:
            logger.info("🔄 Switching to review form iframe...")
            
            self.page.wait_for_selector('iframe#loox-review-form-ugc-dialog', timeout=20000)
            iframe_element = self.page.query_selector('iframe#loox-review-form-ugc-dialog')
            self.review_iframe = iframe_element.content_frame()
            
            if not self.review_iframe:
                logger.error("Could not access review form iframe")
                return False
            
            self.review_iframe.wait_for_function("document.readyState === 'complete' && document.body !== null")
            
            logger.success("Review form iframe loaded")
            return True
            
        except Exception as e:
            logger.error(f"Error switching to form iframe: {e}")
            return False
    
    def _click_star_rating(self, rating: int) -> bool:
        """Click star rating (5 stars)"""
        try:
            logger.info(f"🌟 Setting {rating}-star rating...")
            
            # Try multiple star selectors
            possible_selectors = [
                ".loox-star",
                "button[data-lx-fill]",
                "svg.lx-animation-stroke-star-color",
                "svg[xmlns='http://www.w3.org/2000/svg']",
                "div[class*='loox'] svg",
                "input[type='radio'][aria-label*='star']"
            ]
            
            stars = None
            for sel in possible_selectors:
                count = self.review_iframe.locator(sel).count()
                if count > 0:
                    stars = self.review_iframe.locator(sel)
                    logger.debug(f"Found {count} stars using selector: {sel}")
                    break
            
            if not stars or stars.count() == 0:
                logger.error("No stars found")
                return False
            
            # Click the nth star (0-indexed, so rating-1)
            idx = min(rating - 1, stars.count() - 1)
            stars.nth(idx).click(force=True)
            
            logger.success(f"Clicked {rating}-star rating")
            time.sleep(2)
            return True
            
        except Exception as e:
            logger.error(f"Error clicking stars: {e}")
            return False
    
    def _upload_image(self, image_path: Optional[Path]) -> bool:
        """Upload review image or click Skip if no image provided"""
        try:
            # If no image provided, click Skip
            if not image_path or not image_path.exists():
                logger.info("⏭️ No image provided, clicking Skip...")
                return self._click_skip_button()
            
            logger.info(f"📸 Uploading review image: {image_path.name}")
            
            # Find file input for image upload
            file_input_selectors = [
                "input[type='file']",
                "input[accept*='image']",
                "input[data-testid='file-input']",
                "input[name='file']",
                "input[class*='file']"
            ]
            
            uploaded = False
            for selector in file_input_selectors:
                try:
                    # Check if file input exists
                    file_inputs = self.review_iframe.locator(selector)
                    if file_inputs.count() > 0:
                        # Set the file
                        file_inputs.first.set_input_files(str(image_path.absolute()))
                        logger.success(f"✅ Image uploaded with selector: {selector}")
                        uploaded = True
                        time.sleep(3)  # Wait for upload to process
                        break
                except Exception as e:
                    logger.debug(f"Failed with {selector}: {e}")
                    continue
            
            if not uploaded:
                logger.warning("⚠️ Could not find file input, trying alternative method...")
                
                # Try clicking "Add photos" button first, then upload
                add_photo_selectors = [
                    "button:has-text('Add photos')",
                    "button[aria-label='Add photos']",
                    "text=Add photos",
                    "[data-testid='add-photo-button']"
                ]
                
                for selector in add_photo_selectors:
                    try:
                        if self.review_iframe.locator(selector).count() > 0:
                            self.review_iframe.click(selector)
                            logger.info("Clicked 'Add photos' button")
                            time.sleep(1)
                            
                            # Now try file input again
                            for file_sel in file_input_selectors:
                                try:
                                    file_inputs = self.review_iframe.locator(file_sel)
                                    if file_inputs.count() > 0:
                                        file_inputs.first.set_input_files(str(image_path.absolute()))
                                        logger.success(f"✅ Image uploaded after clicking button")
                                        uploaded = True
                                        time.sleep(3)
                                        break
                                except:
                                    continue
                            
                            if uploaded:
                                break
                    except:
                        continue
            
            if not uploaded:
                logger.warning("❌ Could not upload image, falling back to Skip")
                return self._click_skip_button()
            
            # After successful upload, look for Next/Continue button
            logger.info("⏭️ Looking for Next button after image upload...")
            next_after_upload_selectors = [
                "button[data-testid='next button']",
                "button:has-text('Next')",
                "button:has-text('Continue')",
                "text=Next",
                "button[data-lxs-variant='primary']"
            ]
            
            next_clicked = False
            for selector in next_after_upload_selectors:
                try:
                    if self.review_iframe.locator(selector).count() > 0:
                        self.review_iframe.wait_for_selector(selector, timeout=3000)
                        self.review_iframe.click(selector, force=True)
                        logger.success("✅ Clicked Next after image upload")
                        next_clicked = True
                        time.sleep(2)
                        break
                except:
                    continue
            
            if not next_clicked:
                logger.warning("⚠️ Could not find Next button, continuing anyway...")
            
            return True
            
        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            # Fallback to skip if upload fails
            logger.warning("Falling back to Skip button...")
            return self._click_skip_button()
    
    def _click_skip_button(self) -> bool:
        """Click Skip button for photo upload"""
        try:
            logger.info("⏭️ Clicking Skip button...")
            
            skip_selectors = [
                "button[aria-label='Skip']",
                "button[data-testid='mobile skip button']",
                "button:has-text('Skip')",
                "text=Skip",
                "xpath=//button[contains(., 'Skip')]"
            ]
            
            skip_clicked = False
            for sel in skip_selectors:
                try:
                    self.review_iframe.wait_for_selector(sel, timeout=2000)
                    self.review_iframe.click(sel, timeout=2000, force=True)
                    logger.success(f"Clicked Skip with: {sel}")
                    skip_clicked = True
                    break
                except Exception:
                    continue
            
            if not skip_clicked:
                # JS fallback
                self.review_iframe.evaluate("""
                    const btn = Array.from(document.querySelectorAll('button'))
                      .find(b => b.textContent.trim().toLowerCase() === 'skip');
                    if (btn) btn.click();
                """)
                logger.success("Skip clicked via JS fallback")
            
            time.sleep(2)
            return True
            
        except Exception as e:
            logger.error(f"Error clicking skip: {e}")
            return False
    
    def _fill_review_text(self, review_text: str) -> bool:
        """Fill review textarea"""
        try:
            logger.info("📝 Filling review text...")
            
            textarea_selectors = [
                "textarea[data-testid='review field']",
                "textarea[aria-label='Tell us more!']",
                "form textarea",
                "textarea"
            ]
            
            review_text_entered = False
            for sel in textarea_selectors:
                try:
                    self.review_iframe.wait_for_selector(sel, timeout=2000)
                    self.review_iframe.fill(sel, review_text)
                    logger.success(f"Filled review text with: {sel}")
                    review_text_entered = True
                    break
                except Exception:
                    continue
            
            if not review_text_entered:
                # JS fallback
                self.review_iframe.evaluate(f"""
                    const ta = document.querySelector('textarea');
                    if (ta) {{
                        ta.value = "{review_text.replace('"', '\\"')}";
                        ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}
                """)
                logger.success("Review text filled via JS fallback")
            
            time.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"Error filling review text: {e}")
            return False
    
    def _click_next_button(self) -> bool:
        """Click Next button"""
        try:
            logger.info("➡️ Clicking Next button...")
            
            next_selectors = [
                "button[data-testid='next button']",
                "button:has-text('Next')",
                "text=Next",
                "button[data-lxs-variant='primary']",
                "css=button._lxs-button_luvow_1",
                "css=button._button_33r16_43"
            ]
            
            next_clicked = False
            for sel in next_selectors:
                try:
                    self.review_iframe.wait_for_selector(sel, timeout=2500)
                    
                    # Wait for button to be enabled
                    self.review_iframe.wait_for_function(
                        """(selector) => {
                            const el = document.querySelector(selector);
                            return el && !el.disabled;
                        }""",
                        sel,
                        timeout=5000
                    )
                    
                    self.review_iframe.click(sel, timeout=2000, force=True)
                    logger.success(f"Clicked Next with: {sel}")
                    next_clicked = True
                    time.sleep(5)
                    break
                except Exception:
                    continue
            
            if not next_clicked:
                # JS fallback
                self.review_iframe.evaluate("""
                    const btn = Array.from(document.querySelectorAll('button'))
                      .find(b => b.textContent && b.textContent.trim().toLowerCase() === 'next');
                    if (btn) {
                        btn.removeAttribute('disabled');
                        btn.click();
                    }
                """)
                logger.success("Next clicked via JS fallback")
                time.sleep(5)
            
            return True
            
        except Exception as e:
            logger.error(f"Error clicking next: {e}")
            return False
    
    def _fill_customer_info(self, review_data: Dict) -> bool:
        """Fill first name, last name, and email fields"""
        try:
            logger.info("👤 Filling customer information...")
            
            inputs = {
                "first name": [
                    "input[data-testid='first name field']",
                    "input[autocomplete='given-name']"
                ],
                "last name": [
                    "input[data-testid='last name field']",
                    "input[autocomplete='family-name']"
                ],
                "email": [
                    "input[data-testid='email field']",
                    "input[autocomplete='email']"
                ]
            }
            
            # Get first_name and last_name directly from review_data
            data = {
                "first name": review_data['first_name'],
                "last name": review_data['last_name'],
                "email": review_data['email']
            }
            
            for field, selectors in inputs.items():
                filled = False
                for sel in selectors:
                    try:
                        self.review_iframe.wait_for_selector(sel, timeout=2000)
                        self.review_iframe.fill(sel, data[field])
                        logger.success(f"Filled {field}: {data[field]}")
                        filled = True
                        time.sleep(0.5)
                        break
                    except Exception:
                        continue
                
                if not filled:
                    logger.warning(f"Could not fill {field}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error filling customer info: {e}")
            return False
    
    def _click_done_button(self) -> bool:
        """Click Done button"""
        try:
            logger.info("✅ Clicking Done button...")
            
            done_selectors = [
                "button[data-testid='done button']",
                "button:has-text('Done')",
                "text=Done",
                "xpath=//button[contains(., 'Done')]"
            ]
            
            done_clicked = False
            for sel in done_selectors:
                try:
                    self.review_iframe.wait_for_selector(sel, timeout=2000)
                    self.review_iframe.click(sel, force=True)
                    logger.success(f"Clicked Done with: {sel}")
                    done_clicked = True
                    time.sleep(3)
                    break
                except Exception:
                    continue
            
            if not done_clicked:
                # JS fallback
                self.review_iframe.evaluate("""
                    const btn = Array.from(document.querySelectorAll('button'))
                      .find(b => b.textContent.trim().toLowerCase() === 'done');
                    if (btn) btn.click();
                """)
                logger.success("Done clicked via JS fallback")
                time.sleep(3)
            
            return True
            
        except Exception as e:
            logger.error(f"Error clicking done: {e}")
            return False
    
    def _click_close_button(self) -> bool:
        """Click Close (Exit) button on the Loox review modal"""
        try:
            logger.info("❌ Attempting to click Close button...")

            close_selectors = [
                "button[data-testid='close button']",
                "button[aria-label='Exit']",
                "button:has-text('×')",
                "xpath=//button[contains(., '×')]",
                "xpath=//button[@aria-label='Exit']",
                "button[class*='lxs-button']",
                "button[class*='_lxs-is-icon-only']",
                "button._lxs-button_luvow_1",
                "button._lxs-is-icon-only_luvow_139",
                "span._lxs-icon_6a8to_1 >> xpath=ancestor::button",
                "svg[viewBox='0 0 24 24'] >> xpath=ancestor::button",
                "xpath=//span[contains(@class,'_lxs-icon_6a8to_1')]/parent::button",
                "css=button[data-lxs-variant='text']",
                "button[type='button'][data-testid='close button']",
            ]

            clicked = False
            for sel in close_selectors:
                try:
                    self.review_iframe.wait_for_selector(sel, timeout=2000)
                    self.review_iframe.click(sel, force=True)
                    time.sleep(5)
                    logger.info(f"Clicked Close with: {sel}")
                    clicked = True
                    break
                except Exception:
                    continue

            if not clicked:
                # JS fallback if all selectors fail
                self.review_iframe.evaluate("""
                    const btn = Array.from(document.querySelectorAll('button'))
                    .find(b => b.getAttribute('data-testid') === 'close button' 
                        || b.getAttribute('aria-label') === 'Exit');
                    if (btn) btn.click();
                """)
                time.sleep(5)
                logger.success("Close clicked via JS fallback")

            time.sleep(5)
            return True

        except Exception as e:
            logger.error(f"Error clicking close: {e}")
            return False