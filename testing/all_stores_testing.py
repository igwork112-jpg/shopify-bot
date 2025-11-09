"""
Optimized test script for all stores - Tests full review submission flow
Uses proven review submission code with improved timing and scrolling
"""

from playwright.sync_api import sync_playwright
import time
from pathlib import Path
from datetime import datetime

# Create screenshots directory
SCREENSHOTS_DIR = Path("test_screenshots")
SCREENSHOTS_DIR.mkdir(exist_ok=True)

STORES = [
    "https://rubberco.co.uk",
    "https://slip-not.co.uk",
    "https://expressmatting.co.uk",
    "https://stairnosingsuk.co.uk",
    "https://pvcstripcurtainsuk.uk",
    "https://industrialsuppliesco.co.uk",
    "https://industrialproducts-uk.co.uk",
    "https://www.floorsafetyuk.co.uk",
    "https://tarpaulinscompany.co.uk",
    "https://tarpaulinsuk.uk",
    "https://barriersco.co.uk",
    "https://www.pondlinersco.co.uk",
    "https://rubberfloorings.co.uk",
    "https://rubbermatting-direct.co.uk"
]

def take_screenshot(page, store_name, step_name, success=False):
    """Take a screenshot"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    status = "SUCCESS" if success else "FAILED"
    filename = f"{store_name.replace('https://', '').replace('/', '_')}_{step_name}_{status}_{timestamp}.png"
    filepath = SCREENSHOTS_DIR / filename
    page.screenshot(path=str(filepath))
    return filepath

def smooth_scroll(page, target_height=None):
    """Smooth scroll with proper timing"""
    if target_height is None:
        target_height = page.evaluate("document.body.scrollHeight")
    
    # Scroll in chunks with slower pace
    current = 0
    chunk_size = 300
    while current < target_height:
        page.evaluate(f"window.scrollTo(0, {current});")
        time.sleep(0.5)
        current += chunk_size
    
    # Final scroll to bottom
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(2)

def test_complete_flow(page, store_url):
    """Test complete review submission flow"""
    store_name = store_url.replace('https://', '').replace('www.', '')
    
    print(f"\n{'='*80}", flush=True)
    print(f"TESTING: {store_url}", flush=True)
    print('='*80, flush=True)
    
    result = {
        'store': store_url,
        'step_reached': 'START',
        'success': False,
        'error': None,
        'screenshots': []
    }
    
    try:
        # STEP 1: Load /collections
        print(f"\n📍 STEP 1: Loading /collections", flush=True)
        collections_url = f"{store_url.rstrip('/')}/collections"
        page.goto(collections_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        result['step_reached'] = 'COLLECTIONS_PAGE'
        print("   ✅ Collections page loaded", flush=True)
        
        # STEP 2: Find collections
        print(f"\n📦 STEP 2: Finding collections", flush=True)
        collection_urls = set()
        collections = page.query_selector_all('a[href*="/collections/"]:not([href="/collections"])')
        
        for col in collections:
            href = col.get_attribute('href')
            if href and '/collections/' in href:
                if href.count('/collections/') == 1 and href.split('/collections/')[-1].count('/') == 0:
                    if not href.startswith('http'):
                        href = store_url.rstrip('/') + href
                    href = href.split('?')[0].split('#')[0]
                    collection_urls.add(href)
        
        collection_urls = list(collection_urls)
        print(f"   ✅ Found {len(collection_urls)} collections", flush=True)
        
        if not collection_urls:
            result['error'] = "No collections found"
            ss = take_screenshot(page, store_name, "no_collections")
            result['screenshots'].append(str(ss))
            return result
        
        # STEP 3: Load first collection
        print(f"\n🛍️ STEP 3: Loading first collection", flush=True)
        first_collection = collection_urls[0]
        print(f"   URL: {first_collection}", flush=True)
        page.goto(first_collection, wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        result['step_reached'] = 'COLLECTION_LOADED'
        print("   ✅ Collection loaded", flush=True)
        
        # STEP 4: Find products
        print(f"\n🧾 STEP 4: Finding products", flush=True)
        product_urls = set()
        products = page.query_selector_all('a[href*="/products/"]')
        
        for prod in products:
            href = prod.get_attribute('href')
            if href and '/products/' in href:
                if href.count('/products/') == 1 and href.split('/products/')[-1]:
                    if not href.startswith('http'):
                        href = store_url.rstrip('/') + href
                    href = href.split('?')[0].split('#')[0]
                    product_urls.add(href)
        
        product_urls = list(product_urls)
        print(f"   ✅ Found {len(product_urls)} products", flush=True)
        
        if not product_urls:
            result['error'] = "No products found in collection"
            ss = take_screenshot(page, store_name, "no_products")
            result['screenshots'].append(str(ss))
            return result
        
        # STEP 5: Load first product
        print(f"\n🧩 STEP 5: Loading first product", flush=True)
        first_product = product_urls[0]
        print(f"   URL: {first_product}", flush=True)
        page.goto(first_product, wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        result['step_reached'] = 'PRODUCT_LOADED'
        print("   ✅ Product page loaded", flush=True)
        
        # STEP 6: Scroll to load Loox iframe
        print(f"\n📜 STEP 6: Scrolling to load Loox", flush=True)
        smooth_scroll(page)
        time.sleep(4)
        print("   ✅ Scrolled page", flush=True)
        
        # STEP 7: Find Loox iframe and click Write a Review
        print(f"\n🔍 STEP 7: Finding Loox iframe", flush=True)
        try:
            page.wait_for_selector('iframe#looxReviewsFrame', timeout=20000)
            iframe_el = page.query_selector('iframe#looxReviewsFrame')
            iframe = iframe_el.content_frame()
            result['step_reached'] = 'LOOX_FOUND'
            print("   ✅ Loox iframe found", flush=True)
            
            # STEP 8: Click "Write a Review"
            print(f"\n✍️ STEP 8: Clicking 'Write a Review'", flush=True)
            iframe.wait_for_selector("#write", timeout=15000)
            iframe.click("#write")
            print("   ✅ Clicked Write a Review", flush=True)
            result['step_reached'] = 'WRITE_REVIEW_CLICKED'
            time.sleep(5)
            
        except Exception as e:
            result['error'] = f"Loox iframe error: {e}"
            ss = take_screenshot(page, store_name, "loox_iframe_failed")
            result['screenshots'].append(str(ss))
            print(f"   ❌ Failed: {e}", flush=True)
            return result
        
        # STEP 9: Wait for review form iframe
        print(f"\n📝 STEP 9: Waiting for review form", flush=True)
        try:
            page.wait_for_selector('iframe#loox-review-form-ugc-dialog', timeout=20000)
            iframe_element = page.query_selector('iframe#loox-review-form-ugc-dialog')
            review_iframe = iframe_element.content_frame()
            
            if not review_iframe:
                result['error'] = "Could not access Loox review iframe"
                ss = take_screenshot(page, store_name, "review_iframe_access_failed")
                result['screenshots'].append(str(ss))
                return result
            
            review_iframe.wait_for_function("document.readyState === 'complete' && document.body !== null")
            print("   ✅ Review form iframe loaded", flush=True)
            result['step_reached'] = 'REVIEW_FORM_LOADED'
            time.sleep(4)
            
        except Exception as e:
            result['error'] = f"Review form error: {e}"
            ss = take_screenshot(page, store_name, "review_form_failed")
            result['screenshots'].append(str(ss))
            print(f"   ❌ Failed: {e}", flush=True)
            return result
        
        # STEP 10: Click 5 stars
        print(f"\n⭐ STEP 10: Clicking 5-star rating", flush=True)
        try:
            possible_selectors = [
                ".loox-star",
                "button[data-lx-fill]",
                "svg.lx-animation-stroke-star-color",
                "svg[xmlns='http://www.w3.org/2000/svg']",
                "div[class*='loox'] svg"
            ]
            
            stars = None
            for sel in possible_selectors:
                count = review_iframe.locator(sel).count()
                if count > 0:
                    stars = review_iframe.locator(sel)
                    time.sleep(5)
                    print(f"   ✅ Found {count} stars using selector: {sel}", flush=True)
                    break
            
            if not stars or stars.count() == 0:
                result['error'] = "No stars found"
                ss = take_screenshot(page, store_name, "no_stars")
                result['screenshots'].append(str(ss))
                return result
            
            idx = min(4, stars.count() - 1)
            stars.nth(idx).click(force=True)
            print("   🌟 Clicked 5-star rating successfully", flush=True)
            result['step_reached'] = 'STARS_CLICKED'
            time.sleep(4)
            
        except Exception as e:
            result['error'] = f"Stars error: {e}"
            ss = take_screenshot(page, store_name, "stars_failed")
            result['screenshots'].append(str(ss))
            print(f"   ❌ Failed: {e}", flush=True)
            return result
        
        # STEP 11: Click "Skip"
        print(f"\n⏭️ STEP 11: Clicking Skip button", flush=True)
        try:
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
                    review_iframe.wait_for_selector(sel, timeout=20000)
                    review_iframe.click(sel, timeout=20000, force=True)
                    time.sleep(5)
                    print(f"   ✅ Clicked Skip button with selector: {sel}", flush=True)
                    skip_clicked = True
                    break
                except Exception:
                    continue
            
            if not skip_clicked:
                        review_iframe.evaluate("""
                            const btn = Array.from(document.querySelectorAll('button'))
                              .find(b => b.textContent.trim().toLowerCase() === 'skip');
                            if (btn) btn.click();
                        """)
                        print("✅ JS fallback executed for Skip button.")
            
            result['step_reached'] = 'SKIP_CLICKED'
            time.sleep(4)
            
        except Exception as e:
            result['error'] = f"Skip button error: {e}"
            ss = take_screenshot(page, store_name, "skip_failed")
            result['screenshots'].append(str(ss))
            print(f"   ❌ Failed: {e}", flush=True)
            return result
        
        # STEP 12: Fill review text
        print(f"\n💬 STEP 12: Filling review text", flush=True)
        try:
            textarea_selectors = [
                "textarea[data-testid='review field']",
                "textarea[aria-label='Tell us more!']",
                "form textarea",
                "textarea"
            ]
            
            review_text_entered = False
            for sel in textarea_selectors:
                try:
                    review_iframe.wait_for_selector(sel, timeout=2000)
                    review_iframe.fill(sel, "This product is really good. Highly recommended!")
                    time.sleep(5)
                    print(f"   ✅ Filled review textarea using selector: {sel}", flush=True)
                    review_text_entered = True
                    break
                except Exception:
                    continue
            
            if not review_text_entered:
                review_iframe.evaluate("""
                    const ta = document.querySelector('textarea');
                    if (ta) {
                        ta.value = "This product is really good. Highly recommended!";
                        ta.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                """)
                time.sleep(5)
                print("   ✅ JS fallback executed for textarea", flush=True)
            
            result['step_reached'] = 'REVIEW_TEXT_FILLED'
            time.sleep(4)
            
        except Exception as e:
            result['error'] = f"Textarea error: {e}"
            ss = take_screenshot(page, store_name, "textarea_failed")
            result['screenshots'].append(str(ss))
            print(f"   ❌ Failed: {e}", flush=True)
            return result
        
        # STEP 13: Click "Next"
        print(f"\n➡️ STEP 13: Clicking Next button", flush=True)
        try:
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
                    review_iframe.wait_for_selector(sel, timeout=2500)
                    review_iframe.wait_for_function(
                        """(selector) => {
                            const el = document.querySelector(selector);
                            return el && !el.disabled;
                        }""",
                        sel,
                        timeout=5000
                    )
                    review_iframe.click(sel, timeout=2000, force=True)
                    time.sleep(5)
                    print(f"   ✅ Clicked Next button with selector: {sel}", flush=True)
                    next_clicked = True
                    break
                except Exception:
                    continue
            
            if not next_clicked:
                review_iframe.evaluate("""
                    const btn = Array.from(document.querySelectorAll('button'))
                      .find(b => b.textContent && b.textContent.trim().toLowerCase() === 'next');
                    if (btn) {
                        btn.removeAttribute('disabled');
                        btn.click();
                    }
                """)
                time.sleep(5)
                print("   ✅ JS fallback executed for Next button", flush=True)
            
            result['step_reached'] = 'NEXT_CLICKED'
            time.sleep(4)
            
        except Exception as e:
            result['error'] = f"Next button error: {e}"
            ss = take_screenshot(page, store_name, "next_failed")
            result['screenshots'].append(str(ss))
            print(f"   ❌ Failed: {e}", flush=True)
            return result
        
        # STEP 14: Fill name and email
        print(f"\n👤 STEP 14: Filling name and email", flush=True)
        try:
            inputs = {
                "first name": ["input[data-testid='first name field']", "input[autocomplete='given-name']"],
                "last name": ["input[data-testid='last name field']", "input[autocomplete='family-name']"],
                "email": ["input[data-testid='email field']", "input[autocomplete='email']"]
            }
            
            data = {
                "first name": "Jessica",
                "last name": "den",
                "email": "jessicaden@exe.com"
            }
            
            for field, selectors in inputs.items():
                for sel in selectors:
                    try:
                        review_iframe.wait_for_selector(sel, timeout=2000)
                        review_iframe.fill(sel, data[field])
                        time.sleep(4)
                        print(f"   ✅ Filled {field} using selector: {sel}", flush=True)
                        time.sleep(2)
                        break
                    except Exception:
                        continue
            
            result['step_reached'] = 'INFO_FILLED'
            result['success'] = True
            time.sleep(4)
            
            # Take success screenshot
            ss = take_screenshot(page, store_name, "ready_to_submit", success=True)
            result['screenshots'].append(str(ss))
            print(f"\n✅ STEP 15: Review ready to submit!", flush=True)
            print("   ⚠️  Manual submission step - not clicking Done automatically", flush=True)
            
        except Exception as e:
            result['error'] = f"Info fill error: {e}"
            ss = take_screenshot(page, store_name, "info_failed")
            result['screenshots'].append(str(ss))
            print(f"   ❌ Failed: {e}", flush=True)
            return result
        
    except Exception as e:
        result['error'] = str(e)
        ss = take_screenshot(page, store_name, "unexpected_error")
        result['screenshots'].append(str(ss))
        print(f"\n❌ Unexpected error: {e}", flush=True)
    
    return result

def main():
    print("="*80, flush=True)
    print("OPTIMIZED REVIEW FLOW TEST - ALL STORES", flush=True)
    print("="*80, flush=True)
    print(f"Testing {len(STORES)} stores", flush=True)
    print(f"Screenshots will be saved to: {SCREENSHOTS_DIR.absolute()}\n", flush=True)
    
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_default_timeout(30000)
        
        for store in STORES:
            result = test_complete_flow(page, store)
            results.append(result)
            time.sleep(3)
        
        browser.close()
    
    # Print final summary
    print("\n" + "="*80, flush=True)
    print("FINAL SUMMARY", flush=True)
    print("="*80, flush=True)
    
    success_count = len([r for r in results if r['success']])
    print(f"\n✅ Successful: {success_count}/{len(STORES)}", flush=True)
    
    print("\n📊 DETAILED RESULTS:", flush=True)
    print("-"*80, flush=True)
    
    for r in results:
        status = "✅ SUCCESS" if r['success'] else f"❌ FAILED at {r['step_reached']}"
        print(f"\n{status}: {r['store']}", flush=True)
        if r['error']:
            print(f"   Error: {r['error']}", flush=True)
        if r['screenshots']:
            print(f"   Screenshots: {len(r['screenshots'])}", flush=True)
            for ss in r['screenshots']:
                print(f"      - {ss}", flush=True)
    
    print("\n" + "="*80, flush=True)
    print(f"✅ Test complete! Check screenshots in: {SCREENSHOTS_DIR.absolute()}", flush=True)
    print("="*80, flush=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted", flush=True)