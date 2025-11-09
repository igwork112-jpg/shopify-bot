"""
Debug script for failed stores
"""

from playwright.sync_api import sync_playwright
import time

FAILED_STORES = [
    "https://expressmatting.co.uk",
    "https://www.floorsafetyuk.co.uk",
    "https://barriersco.co.uk"
]

def debug_store(page, store_url):
    """Deep debug of a store"""
    print(f"\n{'='*80}", flush=True)
    print(f"DEBUGGING: {store_url}", flush=True)
    print('='*80, flush=True)
    
    try:
        # Step 1: Go to /collections
        collections_url = f"{store_url.rstrip('/')}/collections"
        print(f"\n📍 Loading: {collections_url}", flush=True)
        
        page.goto(collections_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        print("✅ Collections page loaded", flush=True)
        
        # Step 2: Find ALL collection links
        print(f"\n🔍 Finding collection links...", flush=True)
        
        all_links = page.query_selector_all('a')
        print(f"   Total links on page: {len(all_links)}", flush=True)
        
        collection_links = []
        for link in all_links:
            href = link.get_attribute('href')
            if href and '/collections/' in href and href != '/collections':
                if not href.startswith('http'):
                    href = store_url.rstrip('/') + href
                href = href.split('?')[0].split('#')[0]
                if href not in collection_links:
                    collection_links.append(href)
        
        print(f"   Collection links found: {len(collection_links)}", flush=True)
        
        if not collection_links:
            print("   ❌ No collection links found!", flush=True)
            return
        
        # Show first 5 collections
        print(f"\n📋 First 5 collections:", flush=True)
        for i, url in enumerate(collection_links[:5]):
            print(f"   {i+1}. {url}", flush=True)
        
        # Step 3: Try loading first collection
        first_collection = collection_links[0]
        print(f"\n🛍️ Loading first collection: {first_collection}", flush=True)
        
        page.goto(first_collection, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        print("✅ Collection page loaded", flush=True)
        
        # Step 4: Debug product finding
        print(f"\n🔍 Debugging product search...", flush=True)
        
        # Try multiple selectors
        product_selectors = [
            'a[href*="/products/"]',
            '.product-item a',
            '.product-card a',
            '.grid-item a',
            'a.product-link',
            '[class*="product"] a[href*="/products/"]',
        ]
        
        for selector in product_selectors:
            try:
                elements = page.query_selector_all(selector)
                if elements:
                    print(f"   Selector: {selector}", flush=True)
                    print(f"   Found: {len(elements)} elements", flush=True)
                    
                    # Check first element
                    if elements:
                        href = elements[0].get_attribute('href')
                        print(f"   First href: {href}", flush=True)
            except Exception as e:
                print(f"   Error with {selector}: {e}", flush=True)
        
        # Try getting ALL links and filtering
        print(f"\n📊 Analyzing all links on collection page...", flush=True)
        all_links = page.query_selector_all('a')
        print(f"   Total links: {len(all_links)}", flush=True)
        
        product_links = []
        for link in all_links:
            href = link.get_attribute('href')
            if href and '/products/' in href:
                if not href.startswith('http'):
                    href = store_url.rstrip('/') + href
                href = href.split('?')[0].split('#')[0]
                if href not in product_links:
                    product_links.append(href)
        
        print(f"   Product links found: {len(product_links)}", flush=True)
        
        if not product_links:
            print("   ❌ NO PRODUCTS FOUND!", flush=True)
            print("   Possible reasons:", flush=True)
            print("   - Collection is empty", flush=True)
            print("   - Products use different URL structure", flush=True)
            print("   - Need to scroll/load more", flush=True)
            
            # Try scrolling
            print(f"\n🔄 Trying to scroll and load more...", flush=True)
            for i in range(10):
                page.evaluate(f"window.scrollTo(0, {i * 500});")
                time.sleep(0.5)
            
            time.sleep(2)
            
            # Try again
            all_links = page.query_selector_all('a')
            product_links = []
            for link in all_links:
                href = link.get_attribute('href')
                if href and '/products/' in href:
                    if not href.startswith('http'):
                        href = store_url.rstrip('/') + href
                    href = href.split('?')[0].split('#')[0]
                    if href not in product_links:
                        product_links.append(href)
            
            print(f"   After scrolling: {len(product_links)} products", flush=True)
        
        if product_links:
            print(f"\n📦 First 3 products:", flush=True)
            for i, url in enumerate(product_links[:3]):
                print(f"   {i+1}. {url}", flush=True)
            
            # Step 5: Load product and check for Loox
            first_product = product_links[0]
            print(f"\n🧩 Loading product: {first_product}", flush=True)
            
            page.goto(first_product, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            print("✅ Product page loaded", flush=True)
            
            # Check for Loox
            print(f"\n🔍 Checking for review systems...", flush=True)
            
            # Scroll to load reviews
            for i in range(10):
                page.evaluate(f"window.scrollTo(0, {i * 500});")
                time.sleep(0.5)
            
            time.sleep(3)
            
            # Check for Loox
            loox_iframe = page.query_selector('iframe#looxReviewsFrame')
            if loox_iframe:
                print("   ✅ LOOX FOUND!", flush=True)
            else:
                print("   ❌ Loox not found", flush=True)
                
                # Check for other review systems
                print(f"\n🔍 Checking for other review iframes...", flush=True)
                all_iframes = page.query_selector_all('iframe')
                print(f"   Total iframes: {len(all_iframes)}", flush=True)
                
                for i, iframe in enumerate(all_iframes):
                    iframe_id = iframe.get_attribute('id') or 'no-id'
                    iframe_src = iframe.get_attribute('src') or 'no-src'
                    print(f"   {i+1}. ID: {iframe_id}, SRC: {iframe_src[:60]}...", flush=True)
        
    except Exception as e:
        print(f"\n❌ Error: {e}", flush=True)
        import traceback
        traceback.print_exc()

def main():
    print("="*80, flush=True)
    print("DEBUGGING FAILED STORES", flush=True)
    print("="*80, flush=True)
    print(f"Investigating {len(FAILED_STORES)} stores\n", flush=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_default_timeout(30000)
        
        for store in FAILED_STORES:
            debug_store(page, store)
            print(f"\n{'='*80}", flush=True)
            input("Press Enter to continue to next store...")
        
        browser.close()
    
    print("\n✅ Debug complete!", flush=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user", flush=True)