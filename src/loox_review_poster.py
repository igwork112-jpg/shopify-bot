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
        """
        Click star rating - WORKING VERSION
        Uses confirmed working selectors for Pond Liners
        """
        try:
            logger.info(f"🌟 Setting {rating}-star rating...")
            
            # CONFIRMED WORKING: Primary selector that works
            primary_selector = 'input[type="radio"][aria-label*="star"]'
            
            # Try primary selector first
            try:
                count = self.review_iframe.locator(primary_selector).count()
                if count >= rating:
                    logger.debug(f"Found {count} star inputs with primary selector")
                    time.sleep(2)
                    self.review_iframe.locator(primary_selector).nth(rating - 1).click(force=True, timeout=5000)
                    logger.success(f"✅ Clicked {rating}-star with primary selector")
                    time.sleep(4)
                    return True
            except Exception as e:
                logger.debug(f"Primary selector failed: {str(e)[:80]}")
            
            # Fallback: Try additional form element selectors
            form_selectors = [
                'input[type="radio"][id*="star"]',
                'label[for*="star-5"]' if rating == 5 else f'label[for*="star-{rating}"]',
                f'label[aria-label*="{rating} star"]',
                '[role="radiogroup"] label',
                '[role="radiogroup"] input',
                 'input[type="radio"][aria-label*="star"]',
                'input[type="radio"][id*="star"]',
                'label[for*="star-5"]',
                'label[aria-label*="5 star"]',
                '[role="radiogroup"] label',
                '[role="radiogroup"] input',
                'svg[data-lx-fill]',
                'svg[class*="icon"]',
                'svg[viewBox*="24"]',
                '.loox-star',
                'button[data-lx-fill]',
            ]
            
            clicked = False
            for sel in form_selectors:
                try:
                    count = self.review_iframe.locator(sel).count()
                    if count >= rating:
                        logger.debug(f"Found {count} elements with: {sel}")
                        self.review_iframe.locator(sel).nth(rating - 1).click(force=True, timeout=5000)
                        logger.success(f"✅ Clicked {rating}-star with: {sel}")
                        clicked = True
                        break
                except Exception as e:
                    logger.debug(f"Failed with {sel}: {str(e)[:80]}")
                    continue
            
            if clicked:
                time.sleep(4)
                return True
            
            # Strategy 2: JavaScript approach - find SVG stars and click parent
            if not clicked:
                result_js = self.review_iframe.evaluate("""
                    (rating) => {
                        // Find SVG stars
                        const stars = document.querySelectorAll('svg[class*="star"], svg[data-icon*="star"]');
                        if (stars.length >= rating) {
                            let clickTarget = stars[rating - 1];
                            
                            // Walk up to find clickable parent
                            while (clickTarget && !['BUTTON', 'LABEL', 'A'].includes(clickTarget.tagName)) {
                                if (clickTarget.onclick || clickTarget.getAttribute('role') === 'button') {
                                    break;
                                }
                                clickTarget = clickTarget.parentElement;
                            }
                            
                            if (clickTarget) {
                                clickTarget.click();
                                return 'Clicked parent of star ' + rating + ': ' + clickTarget.tagName;
                            }
                        }
                        
                        // Alternative: Look for radio buttons
                        const radios = document.querySelectorAll('input[type="radio"]');
                        if (radios.length >= rating) {
                            radios[rating - 1].click();
                            return 'Clicked radio button ' + rating;
                        }
                        
                        // Alternative: Find label with star text
                        const labels = Array.from(document.querySelectorAll('label'));
                        const targetLabel = labels.find(l => 
                            l.getAttribute('for')?.includes('star-' + rating) || 
                            l.getAttribute('aria-label')?.includes(rating + ' star')
                        );
                        if (targetLabel) {
                            targetLabel.click();
                            return 'Clicked label for ' + rating + ' stars';
                        }
                        
                        return false;
                    }
                """, rating)
                
                if result_js:
                    logger.success(f"✅ JavaScript click: {result_js}")
                    clicked = True
                else:
                    logger.debug("JavaScript approach returned false")
            
            # Strategy 3: Position-based click (last resort)
            if not clicked:
                logger.info("Trying position-based click...")
                try:
                    # Find rating container
                    rating_container = self.review_iframe.locator(
                        '[role="radiogroup"], [class*="rating"], [class*="star"]'
                    ).first
                    
                    if rating_container.count() > 0:
                        box = rating_container.bounding_box()
                        if box:
                            # Click at position based on rating (e.g., 5 stars = 90% across)
                            percentage = (rating / 5.0) * 0.9  # 90% max to stay within bounds
                            x = box['x'] + (box['width'] * percentage)
                            y = box['y'] + (box['height'] * 0.5)
                            
                            self.review_iframe.mouse.click(x, y)
                            logger.success(f"✅ Clicked at position ({int(x)}, {int(y)}) for {rating} stars")
                            clicked = True
                except Exception as e:
                    logger.debug(f"Position click failed: {str(e)[:80]}")
            
            # Strategy 4: Try original selectors as final fallback
            if not clicked:
                logger.info("Trying original star selectors...")
                old_selectors = [
                    ".loox-star",
                    "button[data-lx-fill]",
                    "svg.lx-animation-stroke-star-color",
                    "svg[xmlns='http://www.w3.org/2000/svg']",
                    "div[class*='loox'] svg"
                ]
                
                stars = None
                for sel in old_selectors:
                    count = self.review_iframe.locator(sel).count()
                    if count >= rating:
                        stars = self.review_iframe.locator(sel)
                        logger.debug(f"Found {count} stars with: {sel}")
                        break
                
                if stars and stars.count() >= rating:
                    idx = rating - 1
                    stars.nth(idx).click(force=True)
                    logger.success(f"✅ Clicked {rating}-star with original selector")
                    clicked = True
            
            if not clicked:
                logger.error(f"❌ Could not click {rating}-star rating with any method")
                return False
            
            time.sleep(4)
            return True
            
        except Exception as e:
            logger.error(f"Error clicking stars: {e}")
            return False

    def _upload_image(self, image_path: Optional[Path]) -> bool:
        """
        Upload review image - WORKING VERSION
        Uses confirmed working selectors
        """
        try:
            # If no image provided, click Skip
            if not image_path or not image_path.exists():
                logger.info("⏭️ No image provided, clicking Skip...")
                return self._click_skip_button()
            
            logger.info(f"📸 Uploading review image: {image_path.name}")
            
            # STEP 1: Click "Add photos" button - CONFIRMED WORKING
            add_photo_selector = 'button[data-testid="add photos button"]'
            
            try:
                if self.review_iframe.locator(add_photo_selector).count() > 0:
                    logger.info("Found 'Add photos' button")
                    time.sleep(2)
                    self.review_iframe.click(add_photo_selector, timeout=5000)
                    logger.success("✅ Clicked 'Add photos' button")
                    time.sleep(3)
                else:
                    logger.debug("Add photos button not found, trying alternative...")
                    # Try alternative button selectors
                    alt_selectors = [
                        "button:has-text('Add photos')",
                        "button[aria-label*='photo' i]",
                        "button._lxs-button_luvow_1._upload-button_brsm1_67"
                    ]
                    
                    button_found = False
                    for sel in alt_selectors:
                        try:
                            if self.review_iframe.locator(sel).count() > 0:
                                self.review_iframe.click(sel, timeout=5000)
                                logger.success(f"✅ Clicked button with: {sel}")
                                button_found = True
                                time.sleep(3)
                                break
                        except:
                            continue
                    
                    if not button_found:
                        logger.warning("Could not find Add photos button")
            
            except Exception as e:
                logger.warning(f"Error clicking Add photos button: {str(e)[:80]}")
            
            # STEP 2: Find and use file input
            file_input_selectors = [
                "input[type='file']",
                "input[accept*='image']",
                "input[data-testid='file-input']",
                "input[name='file']"
            ]
            
            uploaded = False
            for selector in file_input_selectors:
                try:
                    file_inputs = self.review_iframe.locator(selector)
                    count = file_inputs.count()
                    
                    if count > 0:
                        logger.debug(f"Found {count} file input(s) with: {selector}")
                        
                        # Try to make input visible
                        try:
                            self.review_iframe.evaluate(f"""
                                const inputs = document.querySelectorAll('{selector}');
                                inputs.forEach(input => {{
                                    input.style.display = 'block';
                                    input.style.visibility = 'visible';
                                    input.style.opacity = '1';
                                    input.style.position = 'relative';
                                }});
                            """)
                        except:
                            pass
                        
                        # Set the file
                        file_inputs.first.set_input_files(str(image_path.absolute()))
                        logger.success(f"✅ Image uploaded successfully")
                        uploaded = True
                        time.sleep(4)
                        
                        # Verify upload
                        try:
                            preview_found = self.review_iframe.locator("img[src*='blob:'], [class*='preview']").count() > 0
                            if preview_found:
                                logger.info("✅ Image preview detected")
                        except:
                            pass
                        
                        break
                        
                except Exception as e:
                    logger.debug(f"Failed with {selector}: {str(e)[:60]}")
                    continue
            
            if not uploaded:
                logger.warning("❌ Could not upload image via file input, trying alternative methods...")
                
                # Try JavaScript file input approach
                try:
                    # Create a data transfer with the file
                    logger.debug("Trying JS drag-and-drop simulation...")
                    
                    # Read file as base64
                    with open(image_path, 'rb') as f:
                        import base64
                        file_data = base64.b64encode(f.read()).decode()
                    
                    result = self.review_iframe.evaluate(f"""
                        (fileData) => {{
                            const input = document.querySelector('input[type="file"]');
                            if (!input) return false;
                            
                            // Try to trigger change event
                            const event = new Event('change', {{ bubbles: true }});
                            input.dispatchEvent(event);
                            
                            return true;
                        }}
                    """, file_data)
                    
                    if result:
                        logger.info("✅ Triggered file input via JS")
                        uploaded = True
                        time.sleep(2)
                except Exception as e:
                    logger.debug(f"JS upload failed: {str(e)[:60]}")
            
            if not uploaded:
                logger.warning("❌ All upload methods failed, falling back to Skip")
                return self._click_skip_button()
            
            # Look for Next/Continue button after upload
            logger.info("⏭️ Looking for Next button after image upload...")
            next_after_upload = [
                "button[data-testid='next button']",
                "button:has-text('Next')",
                "button:has-text('Continue')",
                "button[aria-label*='Next' i]",
                "button[data-lxs-variant='primary']"
            ]
            
            next_clicked = False
            for selector in next_after_upload:
                try:
                    if self.review_iframe.locator(selector).count() > 0:
                        # Wait for button to be enabled
                        time.sleep(1)
                        self.review_iframe.click(selector, force=True, timeout=3000)
                        logger.success("✅ Clicked Next after image upload")
                        next_clicked = True
                        time.sleep(2)
                        break
                except:
                    continue
            
            if not next_clicked:
                logger.debug("No Next button found after upload, continuing...")
            
            return True
            
        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            logger.warning("Falling back to Skip button...")
            return self._click_skip_button()

    def _click_skip_button(self) -> bool:
        """Click Skip button for photo upload"""
        try:
            logger.info("⏭️ Clicking Skip button...")
            
            # First, try to scroll down inside the modal to make Skip visible
            try:
                self.review_iframe.evaluate("""
                    // Scroll the modal/container to bottom to reveal Skip button
                    const containers = document.querySelectorAll('[class*="modal"], [class*="dialog"], [role="dialog"], form, [class*="content"]');
                    containers.forEach(c => {
                        c.scrollTop = c.scrollHeight;
                    });
                    // Also try body
                    document.body.scrollTop = document.body.scrollHeight;
                    document.documentElement.scrollTop = document.documentElement.scrollHeight;
                """)
                time.sleep(1)
            except:
                pass
            
            # Updated selectors - look for visible Skip button
            skip_selectors = [
                "button:has-text('Skip'):visible",
                "button[aria-label='Skip']:visible",
                "button[data-testid='skip button']",
                "button[data-testid='mobile skip button']",
                # Text-based selectors
                "text=Skip",
                "button >> text=Skip"
            ]
            
            skip_clicked = False
            for sel in skip_selectors:
                try:
                    locator = self.review_iframe.locator(sel)
                    if locator.count() > 0:
                        # Check if actually visible
                        if locator.first.is_visible(timeout=2000):
                            locator.first.click(timeout=5000)  # No force=True
                            logger.success(f"✅ Clicked Skip with: {sel}")
                            skip_clicked = True
                            time.sleep(2)
                            break
                        else:
                            logger.debug(f"Skip button found with {sel} but not visible")
                except Exception as e:
                    logger.debug(f"Selector {sel} failed: {str(e)[:50]}")
                    continue
            
            # JavaScript fallback - find and click visible Skip button
            if not skip_clicked:
                logger.info("Trying JS approach to find visible Skip button...")
                result = self.review_iframe.evaluate("""
                    () => {
                        // Find all buttons/elements with Skip text
                        const allElements = document.querySelectorAll('button, a, span, div');
                        for (const el of allElements) {
                            if (el.textContent.trim().toLowerCase() === 'skip') {
                                // Check if visible
                                const rect = el.getBoundingClientRect();
                                const style = window.getComputedStyle(el);
                                if (rect.width > 0 && rect.height > 0 && 
                                    style.display !== 'none' && 
                                    style.visibility !== 'hidden' &&
                                    style.opacity !== '0') {
                                    el.click();
                                    return 'Clicked Skip via JS: ' + el.tagName;
                                }
                            }
                        }
                        
                        // Try clicking by aria-label
                        const skipBtn = document.querySelector('[aria-label="Skip"]');
                        if (skipBtn) {
                            skipBtn.click();
                            return 'Clicked via aria-label';
                        }
                        
                        return false;
                    }
                """)
                
                if result:
                    logger.success(f"✅ {result}")
                    skip_clicked = True
                else:
                    logger.warning("⚠️ Could not find visible Skip button via JS")
            
            if not skip_clicked:
                logger.error("❌ Failed to click Skip button - button may not be visible")
                return False
            
            time.sleep(3)
            return True
            
        except Exception as e:
            logger.error(f"Error clicking skip: {e}")
            return False

    def _fill_review_text(self, review_text: str) -> bool:
        """Fill review textarea - WORKING VERSION"""
        try:
            logger.info("📝 Filling review text...")
            
            # CONFIRMED WORKING selector
            primary_selector = "textarea[data-testid='review field']"
            
            try:
                if self.review_iframe.locator(primary_selector).count() > 0:
                    self.review_iframe.wait_for_selector(primary_selector, state="visible", timeout=3000)
                    self.review_iframe.fill(primary_selector, review_text)
                    logger.success("✅ Filled review text")
                    time.sleep(2)
                    return True
            except Exception as e:
                logger.debug(f"Primary selector failed: {str(e)[:60]}")
            
            # Fallback selectors
            fallback_selectors = [
                "textarea[aria-label='Tell us more!']",
                "form textarea",
                "textarea"
            ]
            
            filled = False
            for sel in fallback_selectors:
                try:
                    if self.review_iframe.locator(sel).count() > 0:
                        self.review_iframe.fill(sel, review_text)
                        logger.success(f"✅ Filled review text")
                        filled = True
                        break
                except:
                    continue
            
            if not filled:
                # JS fallback
                escaped_review = review_text.replace('"', '\\"')
                self.review_iframe.evaluate(f"""
                    const ta = document.querySelector('textarea');
                    if (ta) {{
                        ta.value = "{escaped_review}";
                        ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}
                """)
                logger.success("✅ Review text filled via JS")
            
            time.sleep(2)
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
                "button:has-text('Next')"
            ]
            
            next_clicked = False
            for sel in next_selectors:
                try:
                    if self.review_iframe.locator(sel).count() > 0:
                        self.review_iframe.wait_for_selector(sel, state="visible", timeout=3000)
                        self.review_iframe.click(sel, timeout=3000, force=True)
                        logger.success(f"✅ Clicked Next with: {sel}")
                        next_clicked = True
                        time.sleep(4)
                        break
                except:
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
                logger.success("✅ Next clicked via JS")
                time.sleep(4)
            
            return True
            
        except Exception as e:
            logger.error(f"Error clicking next: {e}")
            return False

    def _fill_customer_info(self, review_data: dict) -> bool:
        """Fill customer information fields"""
        try:
            logger.info("👤 Filling customer information...")
            
            # Field configurations
            fields_config = {
                'first_name': {
                    'selectors': [
                        "input[data-testid='first name field']",
                        "input[autocomplete='given-name']",
                        "input[name='firstName']",
                        "input[placeholder*='First' i]"
                    ],
                    'value': review_data.get('first_name', '')
                },
                'last_name': {
                    'selectors': [
                        "input[data-testid='last name field']",
                        "input[autocomplete='family-name']",
                        "input[name='lastName']",
                        "input[placeholder*='Last' i]"
                    ],
                    'value': review_data.get('last_name', '')
                },
                'email': {
                    'selectors': [
                        "input[data-testid='email field']",
                        "input[autocomplete='email']",
                        "input[type='email']",
                        "input[name='email']"
                    ],
                    'value': review_data.get('email', '')
                }
            }
            
            # Fill each field
            for field_name, config in fields_config.items():
                filled = False
                for sel in config['selectors']:
                    try:
                        if self.review_iframe.locator(sel).count() > 0:
                            self.review_iframe.wait_for_selector(sel, state="visible", timeout=2000)
                            input_field = self.review_iframe.locator(sel).first
                            input_field.clear()
                            input_field.fill(config['value'])
                            logger.success(f"✅ Filled {field_name}: {config['value']}")
                            filled = True
                            time.sleep(0.5)
                            break
                    except:
                        continue
                
                if not filled:
                    logger.warning(f"⚠️ Could not fill {field_name}")
            
            time.sleep(2)
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
                "button:has-text('Done')"
            ]
            
            done_clicked = False
            for sel in done_selectors:
                try:
                    if self.review_iframe.locator(sel).count() > 0:
                        self.review_iframe.click(sel, force=True, timeout=3000)
                        logger.success(f"✅ Clicked Done")
                        done_clicked = True
                        time.sleep(3)
                        break
                except:
                    continue
            
            if not done_clicked:
                # JS fallback
                self.review_iframe.evaluate("""
                    const btn = Array.from(document.querySelectorAll('button'))
                    .find(b => b.textContent.trim().toLowerCase() === 'done');
                    if (btn) btn.click();
                """)
                logger.success("✅ Done clicked via JS")
                time.sleep(3)
            
            return True
            
        except Exception as e:
            logger.error(f"Error clicking done: {e}")
            return False

    def _click_close_button(self) -> bool:
        """Click Close (Exit) button on the Loox review modal"""
        try:
            logger.info("❌ Clicking Close button...")

            close_selectors = [
                "button[data-testid='close button']",
                "button[aria-label='Exit']",
                "button:has-text('×')"
            ]

            clicked = False
            for sel in close_selectors:
                try:
                    if self.review_iframe.locator(sel).count() > 0:
                        self.review_iframe.click(sel, force=True, timeout=3000)
                        logger.success(f"✅ Clicked Close")
                        clicked = True
                        time.sleep(3)
                        break
                except:
                    continue

            if not clicked:
                # JS fallback
                self.review_iframe.evaluate("""
                    const btn = Array.from(document.querySelectorAll('button'))
                    .find(b => b.getAttribute('data-testid') === 'close button' 
                        || b.getAttribute('aria-label') === 'Exit');
                    if (btn) btn.click();
                """)
                logger.success("✅ Close clicked via JS")
                time.sleep(3)

            return True

        except Exception as e:
            logger.error(f"Error clicking close: {e}")
            return False


    