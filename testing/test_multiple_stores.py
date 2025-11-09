"""
Simple test script for multiple stores
"""

import sys
from playwright.sync_api import sync_playwright
import time

print("Starting test script...", flush=True)

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

def test_store(page, store_url):
    """Test one store"""
    print(f"\n{'='*60}", flush=True)
    print(f"Testing: {store_url}", flush=True)
    print('='*60, flush=True)
    
    result = {
        'store': store_url,
        'status': 'FAILED',
        'collections_page': False,
        'collections_found': 0,
        'products_found': 0,
        'has_loox': False
    }
    
    try:
        # Step 1: Go to /collections
        collections_url = f"{store_url.rstrip('/')}/collections"
        print(f"\n1. Loading: {collections_url}", flush=True)
        
        page.goto(collections_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)
        result['collections_page'] = True
        print("   ✅ Collections page loaded", flush=True)
        
        # Step 2: Find collections
        print("\n2. Finding collections...", flush=True)
        collections = page.query_selector_all('a[href*="/collections/"]:not([href="/collections"])')
        
        collection_urls = set()  # Use set to avoid duplicates
        for col in collections:
            href = col.get_attribute('href')
            if href and href != '/collections' and '/collections/' in href:
                # Skip if it has more paths after collection name (like /collections/name/products)
                if href.count('/collections/') == 1 and href.split('/collections/')[-1].count('/') == 0:
                    if not href.startswith('http'):
                        href = store_url.rstrip('/') + href
                    # Remove query parameters and fragments
                    href = href.split('?')[0].split('#')[0]
                    collection_urls.add(href)
        
        collection_urls = list(collection_urls)
        result['collections_found'] = len(collection_urls)
        print(f"   ✅ Found {len(collection_urls)} unique collections", flush=True)
        
        # Show first few collections
        for i, url in enumerate(collection_urls[:5]):
            print(f"      {i+1}. {url.split('/collections/')[-1]}", flush=True)
        
        if not collection_urls:
            print("   ❌ No collections found", flush=True)
            return result
        
        # Step 3: Load first collection
        first_collection = collection_urls[0]
        print(f"\n3. Loading collection: {first_collection}", flush=True)
        page.goto(first_collection, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)
        print("   ✅ Collection loaded", flush=True)
        
        # Step 4: Find products
        print("\n4. Finding products...", flush=True)
        products = page.query_selector_all('a[href*="/products/"]')
        
        product_urls = set()  # Use set to avoid duplicates
        for prod in products:
            href = prod.get_attribute('href')
            if href and '/products/' in href:
                # Basic validation - should have product name after /products/
                if href.count('/products/') == 1 and href.split('/products/')[-1]:
                    if not href.startswith('http'):
                        href = store_url.rstrip('/') + href
                    # Remove query parameters and fragments
                    href = href.split('?')[0].split('#')[0]
                    product_urls.add(href)
        
        product_urls = list(product_urls)
        result['products_found'] = len(product_urls)
        print(f"   ✅ Found {len(product_urls)} unique products", flush=True)
        
        # Show first few products
        for i, url in enumerate(product_urls[:3]):
            print(f"      {i+1}. {url.split('/products/')[-1][:50]}", flush=True)
        
        if not product_urls:
            print("   ❌ No products found", flush=True)
            return result
        
        # Step 5: Load first product
        first_product = product_urls[0]
        print(f"\n5. Loading product: {first_product}", flush=True)
        page.goto(first_product, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)
        print("   ✅ Product loaded", flush=True)
        
        # Step 6: Check for Loox
        print("\n6. Checking for Loox...", flush=True)
        
        # Scroll to load iframe
        for i in range(5):
            page.evaluate(f"window.scrollTo(0, {i * 500});")
            time.sleep(0.5)
        
        time.sleep(2)
        
        loox_iframe = page.query_selector('iframe#looxReviewsFrame')
        if loox_iframe:
            result['has_loox'] = True
            result['status'] = 'SUCCESS'
            print("   ✅ Loox found!", flush=True)
        else:
            print("   ❌ Loox not found", flush=True)
        
    except Exception as e:
        print(f"   ❌ Error: {e}", flush=True)
    
    return result

def main():
    print("\n" + "="*60, flush=True)
    print("MULTI-STORE TEST SCRIPT", flush=True)
    print("="*60, flush=True)
    print(f"Testing {len(STORES)} stores\n", flush=True)
    
    results = []
    
    try:
        print("Launching browser...", flush=True)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.set_default_timeout(30000)
            print("✅ Browser launched\n", flush=True)
            
            for store in STORES:
                result = test_store(page, store)
                results.append(result)
                time.sleep(2)
            
            print("\nClosing browser...", flush=True)
            browser.close()
        
        # Print summary
        print("\n" + "="*60, flush=True)
        print("SUMMARY", flush=True)
        print("="*60, flush=True)
        
        for r in results:
            status_icon = "✅" if r['status'] == 'SUCCESS' else "❌"
            print(f"\n{status_icon} {r['store']}", flush=True)
            print(f"   Collections: {r['collections_found']}", flush=True)
            print(f"   Products: {r['products_found']}", flush=True)
            print(f"   Loox: {'Yes' if r['has_loox'] else 'No'}", flush=True)
        
        print("\n" + "="*60, flush=True)
        compatible = [r for r in results if r['status'] == 'SUCCESS']
        print(f"✅ Compatible stores: {len(compatible)}/{len(STORES)}", flush=True)
        print("="*60, flush=True)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user", flush=True)
    except Exception as e:
        print(f"\n❌ Script error: {e}", flush=True)
        import traceback
        traceback.print_exc()
    finally:
        print("\n✅ Test script finished", flush=True)