"""
DIAGNOSTIC VERSION - Shows which selectors work for each step
Use this to identify the exact selectors to use in LooxReviewPoster
"""

from playwright.sync_api import sync_playwright
import time
from pathlib import Path
from datetime import datetime
import json

SCREENSHOTS_DIR = Path("test_screenshots")
SCREENSHOTS_DIR.mkdir(exist_ok=True)

STORES = [

'https://rubberco.co.uk/',
'https://slip-not.co.uk/',
'https://expressmatting.co.uk/',
'https://stairnosingsuk.co.uk/',
'https://pvcstripcurtainsuk.uk/',
'https://industrialsuppliesco.co.uk/',
 'https://industrialproducts-uk.co.uk/',
'https://www.floorsafetyuk.co.uk/,'

'https://tarpaulinscompany.co.uk/',
'https://tarpaulinsuk.uk/',
'https://barriersco.co.uk/',
'https://www.pondlinersco.co.uk/',
'https://rubberfloorings.co.uk/',
'https://rubbermatting-direct.co.uk/',
]

# Will store working selectors for each step
WORKING_SELECTORS = {
    'stars': None,
    'skip': None,
    'textarea': None,
    'next': None,
    'first_name': None,
    'last_name': None,
    'email': None,
    'done': None,
    'close': None
}

def take_screenshot(page, store_name, step_name, success=False):
    """Take a screenshot"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    status = "SUCCESS" if success else "FAILED"
    filename = f"{store_name.replace('https://', '').replace('/', '_')}_{step_name}_{status}_{timestamp}.png"
    filepath = SCREENSHOTS_DIR / filename
    page.screenshot(path=str(filepath), full_page=True)
    return filepath

def smooth_scroll(page, target_height=None):
    """Smooth scroll with proper timing"""
    if target_height is None:
        target_height = page.evaluate("document.body.scrollHeight")
    
    current = 0
    chunk_size = 300
    while current < target_height:
        page.evaluate(f"window.scrollTo(0, {current});")
        time.sleep(0.5)
        current += chunk_size
    
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(2)

def test_complete_flow(page, store_url):
    """Test complete review submission flow and record working selectors"""
    store_name = store_url.replace('https://', '').replace('www.', '')
    
    print(f"\n{'='*80}", flush=True)
    print(f"🔬 DIAGNOSTIC TEST: {store_url}", flush=True)
    print('='*80, flush=True)
    
    result = {
        'store': store_url,
        'step_reached': 'START',
        'success': False,
        'error': None,
        'screenshots': [],
        'working_selectors': {}
    }
    
    try:
        # STEPS 1-5: Navigate to product page
        print(f"\n📍 STEPS 1-5: Navigating to product", flush=True)
        
        collections_url = f"{store_url.rstrip('/')}/collections"
        page.goto(collections_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        
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
        if not collection_urls:
            result['error'] = "No collections found"
            return result
        
        print(f"   ✅ Found {len(collection_urls)} collections", flush=True)
        
        page.goto(collection_urls[0], wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        
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
        if not product_urls:
            result['error'] = "No products found"
            return result
        
        print(f"   ✅ Found {len(product_urls)} products", flush=True)
        
        first_product = product_urls[0]
        print(f"   📦 Loading: {first_product}", flush=True)
        page.goto(first_product, wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        result['step_reached'] = 'PRODUCT_LOADED'
        
        # STEP 6: Scroll
        print(f"\n📜 STEP 6: Scrolling to load Loox", flush=True)
        smooth_scroll(page)
        time.sleep(5)
        
        # STEP 7: Find Loox iframe
        print(f"\n🔍 STEP 7: Finding main Loox iframe", flush=True)
        page.wait_for_selector('iframe#looxReviewsFrame', timeout=20000)
        iframe_el = page.query_selector('iframe#looxReviewsFrame')
        loox_iframe = iframe_el.content_frame()
        
        if not loox_iframe:
            result['error'] = "Could not access Loox iframe"
            return result
        
        result['step_reached'] = 'LOOX_FOUND'
        print(f"   ✅ Loox iframe found", flush=True)
        time.sleep(3)
        
        # STEP 8: Click Write Review
        print(f"\n✍️ STEP 8: Clicking 'Write a Review'", flush=True)
        
        if loox_iframe.locator('#write').count() > 0:
            loox_iframe.click('#write', timeout=5000)
            print(f"   ✅ Clicked Write a Review", flush=True)
            result['working_selectors']['write_review'] = '#write'
            WORKING_SELECTORS['write_review'] = '#write'
        else:
            result['error'] = "Write Review button not found"
            return result
        
        result['step_reached'] = 'WRITE_REVIEW_CLICKED'
        
        # STEP 9: Wait for review form
        print(f"\n📝 STEP 9: Waiting for review form iframe", flush=True)
        
        page.wait_for_selector('iframe#loox-review-form-ugc-dialog', timeout=30000)
        review_iframe_el = page.query_selector('iframe#loox-review-form-ugc-dialog')
        review_iframe = review_iframe_el.content_frame()
        
        if not review_iframe:
            result['error'] = "Could not access review form iframe"
            return result
        
        review_iframe.wait_for_load_state("domcontentloaded", timeout=10000)
        print(f"   ✅ Review form loaded", flush=True)
        result['step_reached'] = 'REVIEW_FORM_LOADED'
        time.sleep(4)
        
        # STEP 10: Click stars - DIAGNOSTIC VERSION
        print(f"\n⭐ STEP 10: Testing star selectors", flush=True)
        print(f"{'='*60}", flush=True)
        
        star_selector_groups = {
            "Radio/Label Selectors": [
                'input[type="radio"][aria-label*="star"]',
                'input[type="radio"][id*="star"]',
                'label[for*="star-5"]',
                'label[aria-label*="5 star"]',
                '[role="radiogroup"] label',
                '[role="radiogroup"] input',
            ],
            "SVG Selectors": [
                'svg[data-lx-fill]',
                'svg[class*="icon"]',
                'svg[viewBox*="24"]',
                '.loox-star',
                'button[data-lx-fill]',
            ]
        }
        
        clicked = False
        working_method = None
        
        # Try Strategy 1: Form elements
        for group_name, selectors in star_selector_groups.items():
            if clicked:
                break
            print(f"\n   Testing {group_name}:", flush=True)
            for sel in selectors:
                try:
                    count = review_iframe.locator(sel).count()
                    print(f"      {sel}: {count} found", flush=True)
                    
                    if count >= 5:
                        review_iframe.locator(sel).nth(4).click(force=True, timeout=3000)
                        print(f"      ✅ SUCCESS - Clicked 5th star with: {sel}", flush=True)
                        working_method = f"selector: {sel}"
                        WORKING_SELECTORS['stars'] = sel
                        result['working_selectors']['stars'] = sel
                        clicked = True
                        break
                except Exception as e:
                    print(f"      ❌ Failed: {str(e)[:60]}", flush=True)
        
        # Try Strategy 2: JavaScript
        if not clicked:
            print(f"\n   Testing JavaScript Approach:", flush=True)
            result_js = review_iframe.evaluate("""
                () => {
                    const stars = document.querySelectorAll('svg[data-lx-fill], svg[class*="icon"]');
                    
                    if (stars.length >= 5) {
                        const fifthStar = stars[4];
                        let clickTarget = fifthStar.parentElement;
                        
                        while (clickTarget && !['BUTTON', 'LABEL', 'A'].includes(clickTarget.tagName)) {
                            if (clickTarget.onclick || clickTarget.getAttribute('role') === 'button') {
                                break;
                            }
                            clickTarget = clickTarget.parentElement;
                        }
                        
                        if (clickTarget) {
                            clickTarget.click();
                            return 'Clicked parent of 5th star: ' + clickTarget.tagName;
                        }
                    }
                    
                    const radios = document.querySelectorAll('input[type="radio"]');
                    if (radios.length >= 5) {
                        radios[4].click();
                        return 'Clicked 5th radio button';
                    }
                    
                    return false;
                }
            """)
            
            if result_js:
                print(f"      ✅ SUCCESS - JavaScript: {result_js}", flush=True)
                working_method = f"javascript: {result_js}"
                WORKING_SELECTORS['stars'] = 'JAVASCRIPT_SVG_PARENT'
                result['working_selectors']['stars'] = 'JAVASCRIPT_SVG_PARENT'
                clicked = True
        
        if not clicked:
            print(f"      ❌ FAILED - Could not click stars", flush=True)
            result['error'] = "Stars clicking failed"
            return result
        
        print(f"\n   🎯 WORKING METHOD: {working_method}", flush=True)
        print(f"{'='*60}", flush=True)
        
        result['step_reached'] = 'STARS_CLICKED'
        time.sleep(5)
        
        # STEP 11: Click Skip - DIAGNOSTIC
        print(f"\n⏭️ STEP 11: Testing Skip button selectors", flush=True)
        print(f"{'='*60}", flush=True)
        
        skip_selectors = [
            "button[aria-label='Skip']",
            "button[data-testid='mobile skip button']",
            "button:has-text('Skip')",
            "button[data-testid*='skip']",
            "[aria-label='Skip']"
        ]
        
        skip_clicked = False
        for sel in skip_selectors:
            try:
                count = review_iframe.locator(sel).count()
                print(f"   {sel}: {count} found", flush=True)
                
                if count > 0:
                    review_iframe.click(sel, timeout=3000)
                    print(f"   ✅ SUCCESS - Clicked Skip with: {sel}", flush=True)
                    WORKING_SELECTORS['skip'] = sel
                    result['working_selectors']['skip'] = sel
                    skip_clicked = True
                    break
            except Exception as e:
                print(f"   ❌ Failed: {str(e)[:60]}", flush=True)
        
        if not skip_clicked:
            print(f"   Trying JavaScript fallback...", flush=True)
            review_iframe.evaluate("""
                const btn = Array.from(document.querySelectorAll('button'))
                    .find(b => b.textContent.toLowerCase().includes('skip'));
                if (btn) btn.click();
            """)
            print(f"   ✅ SUCCESS - JavaScript fallback worked", flush=True)
            WORKING_SELECTORS['skip'] = 'JAVASCRIPT_TEXT_SEARCH'
            result['working_selectors']['skip'] = 'JAVASCRIPT_TEXT_SEARCH'
        
        print(f"{'='*60}", flush=True)
        result['step_reached'] = 'SKIP_CLICKED'
        time.sleep(5)
        
        # STEP 12: Fill review text - DIAGNOSTIC
        print(f"\n💬 STEP 12: Testing textarea selectors", flush=True)
        print(f"{'='*60}", flush=True)
        
        textarea_selectors = [
            "textarea[data-testid='review field']",
            "textarea[aria-label='Tell us more!']",
            "form textarea",
            "textarea",
            "[data-testid*='review'] textarea"
        ]
        
        review_text = "This product is really good. Highly recommended!"
        filled = False
        
        for sel in textarea_selectors:
            try:
                count = review_iframe.locator(sel).count()
                print(f"   {sel}: {count} found", flush=True)
                
                if count > 0:
                    review_iframe.fill(sel, review_text)
                    print(f"   ✅ SUCCESS - Filled textarea with: {sel}", flush=True)
                    WORKING_SELECTORS['textarea'] = sel
                    result['working_selectors']['textarea'] = sel
                    filled = True
                    break
            except Exception as e:
                print(f"   ❌ Failed: {str(e)[:60]}", flush=True)
        
        if not filled:
            print(f"   Trying JavaScript fallback...", flush=True)
            review_iframe.evaluate(f"""
                const ta = document.querySelector('textarea');
                if (ta) {{
                    ta.value = "{review_text}";
                    ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
            """)
            print(f"   ✅ SUCCESS - JavaScript fallback worked", flush=True)
            WORKING_SELECTORS['textarea'] = 'JAVASCRIPT_GENERIC'
            result['working_selectors']['textarea'] = 'JAVASCRIPT_GENERIC'
        
        print(f"{'='*60}", flush=True)
        result['step_reached'] = 'REVIEW_TEXT_FILLED'
        time.sleep(5)
        
        # STEP 13: Click Next - DIAGNOSTIC
        print(f"\n➡️ STEP 13: Testing Next button selectors", flush=True)
        print(f"{'='*60}", flush=True)
        
        next_selectors = [
            "button[data-testid='next button']",
            "button:has-text('Next')",
            "button[type='submit']",
            "button[data-lxs-variant='primary']",
            "button._lxs-button_luvow_1",
            "button._button_33r16_43"
        ]
        
        next_clicked = False
        for sel in next_selectors:
            try:
                count = review_iframe.locator(sel).count()
                print(f"   {sel}: {count} found", flush=True)
                
                if count > 0:
                    review_iframe.wait_for_selector(sel, state="visible", timeout=3000)
                    review_iframe.click(sel, timeout=3000)
                    print(f"   ✅ SUCCESS - Clicked Next with: {sel}", flush=True)
                    WORKING_SELECTORS['next'] = sel
                    result['working_selectors']['next'] = sel
                    next_clicked = True
                    break
            except Exception as e:
                print(f"   ❌ Failed: {str(e)[:60]}", flush=True)
        
        if not next_clicked:
            print(f"   Trying JavaScript fallback...", flush=True)
            review_iframe.evaluate("""
                const btn = Array.from(document.querySelectorAll('button'))
                    .find(b => b.textContent.toLowerCase().includes('next'));
                if (btn) btn.click();
            """)
            print(f"   ✅ SUCCESS - JavaScript fallback worked", flush=True)
            WORKING_SELECTORS['next'] = 'JAVASCRIPT_TEXT_SEARCH'
            result['working_selectors']['next'] = 'JAVASCRIPT_TEXT_SEARCH'
        
        print(f"{'='*60}", flush=True)
        result['step_reached'] = 'NEXT_CLICKED'
        time.sleep(5)
        
        # STEP 14: Fill customer info - DIAGNOSTIC
        print(f"\n👤 STEP 14: Testing customer info field selectors", flush=True)
        print(f"{'='*60}", flush=True)
        
        input_fields = {
            "first name": {
                "selectors": [
                    "input[data-testid='first name field']",
                    "input[autocomplete='given-name']",
                    "input[name='firstName']",
                    "input[placeholder*='First' i]"
                ],
                "value": "Jessica"
            },
            "last name": {
                "selectors": [
                    "input[data-testid='last name field']",
                    "input[autocomplete='family-name']",
                    "input[name='lastName']",
                    "input[placeholder*='Last' i]"
                ],
                "value": "den"
            },
            "email": {
                "selectors": [
                    "input[data-testid='email field']",
                    "input[autocomplete='email']",
                    "input[type='email']",
                    "input[name='email']",
                    "input[placeholder*='email' i]"
                ],
                "value": "jessicaden@exe.com"
            }
        }
        
        for field_name, field_data in input_fields.items():
            print(f"\n   Testing {field_name.upper()} selectors:", flush=True)
            filled = False
            
            for sel in field_data['selectors']:
                try:
                    count = review_iframe.locator(sel).count()
                    print(f"      {sel}: {count} found", flush=True)
                    
                    if count > 0:
                        review_iframe.wait_for_selector(sel, state="visible", timeout=2000)
                        input_field = review_iframe.locator(sel).first
                        input_field.clear()
                        input_field.fill(field_data['value'])
                        
                        # Verify
                        filled_value = input_field.input_value()
                        if filled_value == field_data['value']:
                            print(f"      ✅ SUCCESS - Filled with: {sel}", flush=True)
                            WORKING_SELECTORS[field_name.replace(' ', '_')] = sel
                            result['working_selectors'][field_name.replace(' ', '_')] = sel
                            filled = True
                            time.sleep(1)
                            break
                except Exception as e:
                    print(f"      ❌ Failed: {str(e)[:60]}", flush=True)
            
            if not filled:
                print(f"      ⚠️ No selector worked for {field_name}", flush=True)
        
        print(f"{'='*60}", flush=True)
        result['step_reached'] = 'INFO_FILLED'
        result['success'] = True
        time.sleep(4)
        
        ss = take_screenshot(page, store_name, "ready_to_submit", success=True)
        result['screenshots'].append(str(ss))
        
        print(f"\n✅ SUCCESS: Review form completed!", flush=True)
        
    except Exception as e:
        result['error'] = str(e)
        ss = take_screenshot(page, store_name, "error")
        result['screenshots'].append(str(ss))
        print(f"\n❌ Error: {e}", flush=True)
    
    return result

def main():
    print("="*80, flush=True)
    print("🔬 DIAGNOSTIC TEST - IDENTIFIES WORKING SELECTORS", flush=True)
    print("="*80, flush=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()
        page.set_default_timeout(30000)
        
        for store in STORES:
            result = test_complete_flow(page, store)
            
            print("\n" + "="*80, flush=True)
            print("📊 DIAGNOSTIC RESULTS", flush=True)
            print("="*80, flush=True)
            
            status = "✅ SUCCESS" if result['success'] else f"❌ FAILED at {result['step_reached']}"
            print(f"\nStatus: {status}", flush=True)
            print(f"Store: {result['store']}", flush=True)
            
            if result['error']:
                print(f"Error: {result['error']}", flush=True)
            
            print(f"\n{'='*80}", flush=True)
            print("🎯 WORKING SELECTORS TO USE IN LOOXREVIEWPOSTER:", flush=True)
            print("="*80, flush=True)
            
            for step, selector in WORKING_SELECTORS.items():
                if selector:
                    print(f"   {step:20} -> {selector}", flush=True)
            
            print(f"\n{'='*80}", flush=True)
            print("📋 COPY-PASTE READY CODE:", flush=True)
            print("="*80, flush=True)
            print("\n# Update these in your LooxReviewPoster class:")
            print("# (Replace the selector lists with these working ones)")
            print()
            
            if WORKING_SELECTORS['stars']:
                if WORKING_SELECTORS['stars'] == 'JAVASCRIPT_SVG_PARENT':
                    print("# Stars: Use JavaScript approach (already in code)")
                else:
                    print(f"star_selectors = ['{WORKING_SELECTORS['stars']}']")
            
            if WORKING_SELECTORS['skip']:
                if WORKING_SELECTORS['skip'] == 'JAVASCRIPT_TEXT_SEARCH':
                    print("# Skip: Use JavaScript fallback (already in code)")
                else:
                    print(f"skip_selectors = ['{WORKING_SELECTORS['skip']}']")
            
            if WORKING_SELECTORS['textarea']:
                if WORKING_SELECTORS['textarea'] == 'JAVASCRIPT_GENERIC':
                    print("# Textarea: Use JavaScript fallback (already in code)")
                else:
                    print(f"textarea_selectors = ['{WORKING_SELECTORS['textarea']}']")
            
            if WORKING_SELECTORS['next']:
                if WORKING_SELECTORS['next'] == 'JAVASCRIPT_TEXT_SEARCH':
                    print("# Next: Use JavaScript fallback (already in code)")
                else:
                    print(f"next_selectors = ['{WORKING_SELECTORS['next']}']")
            
            if WORKING_SELECTORS.get('first_name'):
                print(f"first_name_selectors = ['{WORKING_SELECTORS['first_name']}']")
            
            if WORKING_SELECTORS.get('last_name'):
                print(f"last_name_selectors = ['{WORKING_SELECTORS['last_name']}']")
            
            if WORKING_SELECTORS.get('email'):
                print(f"email_selectors = ['{WORKING_SELECTORS['email']}']")
            
            print(f"\n{'='*80}", flush=True)
            
            # Save to JSON file
            json_path = SCREENSHOTS_DIR / "working_selectors.json"
            with open(json_path, 'w') as f:
                json.dump({
                    'store': result['store'],
                    'selectors': WORKING_SELECTORS,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            print(f"💾 Selectors saved to: {json_path}", flush=True)
        
        print("\n⏸️  Browser stays open for 30 seconds...", flush=True)
        time.sleep(30)
        browser.close()
    
    print("\n✅ Diagnostic complete!", flush=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted", flush=True)