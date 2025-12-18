from typing import List, Dict, Optional
from playwright.sync_api import Page
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re
from utils.logger import logger

class ProductScraper:
    """Scrapes product information from Shopify store - Homepage Collections"""
    
    def __init__(self, page: Page):
        self.page = page
    
    # def get_homepage_collections(self, store_url: str) -> List[str]:
    #     """Get all collection URLs from /collections page"""
    #     try:
    #         # Clean the store URL - remove query parameters
    #         parsed = urlparse(store_url)
    #         clean_store_url = f"{parsed.scheme}://{parsed.netloc}"
            
    #         # Go to /collections page instead of homepage
    #         collections_page_url = f"{clean_store_url}/collections"
    #         logger.info(f"🏠 Opening collections page: {collections_page_url}")
    #         self.page.goto(collections_page_url, wait_until="domcontentloaded", timeout=30000)
    #         time.sleep(4)
            
    #         # Find all collection links
    #         collection_urls = set()
    #         collections = self.page.query_selector_all('a[href*="/collections/"]:not([href="/collections"])')
            
    #         for col in collections:
    #             href = col.get_attribute('href')
    #             if href and '/collections/' in href:
    #                 # Filter: must have exactly one /collections/ and something after it
    #                 if href.count('/collections/') == 1 and href.split('/collections/')[-1].count('/') == 0:
    #                     # Make absolute URL
    #                     if not href.startswith('http'):
    #                         href = clean_store_url + href
                        
    #                     # Clean URL - remove query params and anchors
    #                     href = href.split('?')[0].split('#')[0]
    #                     collection_urls.add(href)
            
    #         # Remove duplicates
    #         collection_urls = list(collection_urls)
            
    #         logger.success(f"✅ Found {len(collection_urls)} collections")
    #         return collection_urls
            
    #     except Exception as e:
    #         logger.failure(f"Error getting collections: {e}")
    #         return []
    def get_homepage_collections(self, store_url: str) -> List[str]:
        """Get all collection URLs from /collections page"""
        try:
            # Clean the store URL - remove query parameters
            parsed = urlparse(store_url)
            clean_store_url = f"{parsed.scheme}://{parsed.netloc}"
            
            # Go to /collections page instead of homepage
            collections_page_url = f"{clean_store_url}/collections"
            logger.info(f"🏠 Opening collections page: {collections_page_url}")
            self.page.goto(collections_page_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(4)
            
            # Find all collection links
            collection_urls = set()
            all_links = []  # For debugging
            collections = self.page.query_selector_all('a[href*="/collections/"]')
            
            logger.info(f"🔍 Found {len(collections)} total anchor tags with /collections/")
            
            for col in collections:
                href = col.get_attribute('href')
                if not href:
                    continue
                
                # Store original for debugging
                original_href = href
                    
                # Make absolute URL first
                if not href.startswith('http'):
                    href = clean_store_url + href
                
                # Clean URL - remove query params and anchors
                href = href.split('?')[0].split('#')[0]
                
                # Parse the cleaned URL
                parsed_href = urlparse(href)
                path = parsed_href.path
                
                # Skip if it's just /collections or /collections/
                if path in ['/collections', '/collections/']:
                    continue
                
                # Must start with /collections/ and have something after
                if not path.startswith('/collections/'):
                    continue
                
                # Extract the part after /collections/
                collection_part = path.replace('/collections/', '', 1)
                
                # Skip if empty or contains additional slashes (pagination, subcategories)
                if not collection_part or '/' in collection_part:
                    all_links.append(f"SKIP (path): {original_href} -> {href}")
                    continue
                
                # Skip common non-collection pages
                skip_terms = ['all', 'page', 'vendors', 'types']
                if collection_part.lower() in skip_terms:
                    all_links.append(f"SKIP (term): {original_href} -> {href}")
                    continue
                
                all_links.append(f"KEEP: {original_href} -> {href}")
                collection_urls.add(href)
            
            # DEBUG: Print first 20 links to see pattern
            logger.info("📋 First 20 processed links:")
            for link in all_links[:20]:
                logger.info(f"  {link}")
            
            # Convert to sorted list
            collection_urls = sorted(list(collection_urls))
            
            # DEBUG: Print all unique collections found
            logger.info(f"📦 All {len(collection_urls)} unique collections:")
            for i, url in enumerate(collection_urls[:10], 1):
                logger.info(f"  {i}. {url}")
            if len(collection_urls) > 10:
                logger.info(f"  ... and {len(collection_urls) - 10} more")
            
            logger.success(f"✅ Found {len(collection_urls)} unique collections")
            return collection_urls
            
        except Exception as e:
            logger.failure(f"Error getting collections: {e}")
            return []
    # def get_products_from_collection(self, collection_url: str) -> List[str]:
    #     """Get all product URLs from a collection page"""
    #     try:
    #         # Clean collection URL
    #         parsed = urlparse(collection_url)
    #         clean_collection_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
    #         logger.info(f"🛍️ Visiting collection: {clean_collection_url}")
    #         self.page.goto(clean_collection_url, wait_until="domcontentloaded", timeout=30000)
    #         time.sleep(3)
            
    #         # Get all product links
    #         product_links = set()
    #         products = self.page.query_selector_all("a[href*='/products/']")
            
    #         base_url = f"{parsed.scheme}://{parsed.netloc}"
            
    #         for prod in products:
    #             href = prod.get_attribute("href")
    #             if href and '/products/' in href:
    #                 # Validate it's a direct product link
    #                 if href.count('/products/') == 1 and href.split('/products/')[-1]:
    #                     # Make absolute
    #                     if not href.startswith('http'):
    #                         href = base_url + href
    #                     # Clean
    #                     href = href.split('?')[0].split('#')[0]
    #                     product_links.add(href)
            
    #         product_links = list(product_links)
    #         logger.success(f"✅ Found {len(product_links)} products in collection")
    #         return product_links
            
    #     except Exception as e:
    #         logger.failure(f"Error getting products from collection: {e}")
    #         return []
    def get_products_from_collection(self, collection_url: str) -> List[str]:
        """Get all product URLs from a collection page"""
        try:
            # Clean collection URL
            parsed = urlparse(collection_url)
            clean_collection_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            logger.info(f"🛍️ Visiting collection: {clean_collection_url}")
            self.page.goto(clean_collection_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            product_links = set()
            
            # Strategy 1: Find the FIRST/MAIN product grid (not related products grids)
            # We'll look for grids in the main content area, not sidebars/footers
            
            # First, try to find grids specifically in main content
            main_content_selectors = [
                "main .product-grid",
                "#main-content .product-grid",
                ".main-content .product-grid",
                "[role='main'] .product-grid",
                "main .collection-products",
                "main .grid--view-items",
                "main [class*='product-list']"
            ]
            
            main_grid = None
            for selector in main_content_selectors:
                try:
                    grids = self.page.query_selector_all(selector)
                    if grids:
                        # Take the FIRST grid (usually the actual collection)
                        main_grid = grids[0]
                        logger.info(f"✓ Found main grid using: {selector}")
                        break
                except:
                    continue
            
            # Strategy 2: If no specific grid found, look for product count indicator
            if not main_grid:
                logger.info("🔍 Strategy 2: Looking for collection with product count...")
                # Many Shopify stores show "X products" - find the grid near that text
                try:
                    # Look for text like "1 product", "5 products", etc.
                    count_element = self.page.query_selector('[class*="product-count"], [class*="collection-count"]')
                    if count_element:
                        # Find the nearest product grid
                        main_grid = count_element.evaluate_handle('''(el) => {
                            // Look for product grid near the count
                            let current = el;
                            for (let i = 0; i < 5; i++) {
                                current = current.parentElement;
                                if (!current) break;
                                const grid = current.querySelector('.product-grid, [class*="product-list"], .grid--view-items');
                                if (grid) return grid;
                            }
                            return null;
                        }''').as_element()
                        if main_grid:
                            logger.info("✓ Found grid near product count indicator")
                except:
                    pass
            
            # Strategy 3: Get ALL grids and take the one with most products
            if not main_grid:
                logger.info("🔍 Strategy 3: Finding largest product grid...")
                all_grids = self.page.query_selector_all(".product-grid, [class*='product-list'], .grid--view-items")
                
                if all_grids:
                    # Count products in each grid, take the biggest one
                    largest_grid = None
                    max_products = 0
                    
                    for grid in all_grids:
                        product_count = len(grid.query_selector_all("a[href*='/products/']"))
                        
                        # Check if this grid is in an excluded section
                        is_excluded = grid.evaluate('''(el) => {
                            const excludes = ['footer', 'header', '[class*="recommend"]', '[class*="related"]'];
                            for (let selector of excludes) {
                                if (el.closest(selector)) return true;
                            }
                            return false;
                        }''')
                        
                        if not is_excluded and product_count > max_products:
                            max_products = product_count
                            largest_grid = grid
                    
                    if largest_grid:
                        main_grid = largest_grid
                        logger.info(f"✓ Found largest grid with {max_products} product links")
            
            # If still no grid found, try one more approach
            if not main_grid:
                logger.warning("🔍 Strategy 4: Fallback - looking in main tag...")
                main_tag = self.page.query_selector("main")
                if main_tag:
                    main_grid = main_tag
            
            # Now extract products from the identified grid
            if main_grid:
                products = main_grid.query_selector_all("a[href*='/products/']")
                logger.info(f"📦 Found {len(products)} product links in identified grid")
            else:
                logger.error("❌ Could not identify collection product grid")
                return []
            
            # Process products
            seen_slugs = set()
            for prod in products:
                href = prod.get_attribute("href")
                if not href or '/products/' not in href:
                    continue
                
                # Validate product URL structure
                if href.count('/products/') != 1:
                    continue
                
                product_slug = href.split('/products/')[-1].split('?')[0].split('#')[0]
                if not product_slug or '/' in product_slug:
                    continue
                
                # Skip duplicates
                if product_slug in seen_slugs:
                    continue
                seen_slugs.add(product_slug)
                
                # Make absolute
                if not href.startswith('http'):
                    href = base_url + href
                
                # Clean
                href = href.split('?')[0].split('#')[0]
                product_links.add(href)
            
            product_links = sorted(list(product_links))
            
            logger.success(f"✅ Found {len(product_links)} unique products in collection")
            
            # Show all products
            if product_links:
                logger.info(f"📦 Products in this collection:")
                for i, url in enumerate(product_links, 1):
                    product_name = url.split('/products/')[-1]
                    logger.info(f"  {i}. {product_name}")
            
            return product_links
            
        except Exception as e:
            logger.failure(f"Error getting products from collection: {e}")
            return []
        
    def extract_product_data(self, product_url: str) -> Optional[Dict]:
        """Extract detailed product information"""
        try:
            logger.info(f"🧩 Opening product: {product_url}")
            self.page.goto(product_url, wait_until="domcontentloaded", timeout=30000)
            
            # Wait for page to be ready - try multiple selectors
            page_ready = False
            ready_selectors = ['h1', '.product-single', '.product__title', 'main']
            
            for selector in ready_selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=5000)
                    page_ready = True
                    break
                except:
                    continue
            
            if not page_ready:
                logger.warning("Page loaded but standard selectors not found, continuing anyway...")
            
            time.sleep(2)
            
            product_data = {
                'url': product_url,
                'name': self._extract_name(),
                'description': self._extract_description(),
                'image_url': self._extract_image(),
                'price': self._extract_price()
            }
            logger.info(f"📝 Scraped Description: '{product_data['description'][:500] if product_data['description'] else 'EMPTY'}'")
            # Validate we got at least a name
            if not product_data['name'] or product_data['name'] == "Unknown Product":
                logger.warning(f"Could not extract product name from {product_url}")
            
            logger.success(f"✅ Extracted: {product_data['name'][:60]}...")
            return product_data
            
        except Exception as e:
            logger.failure(f"❌ Error extracting product data: {e}")
            return None
    
    def _extract_name(self) -> str:
        """Extract product name - try multiple selectors"""
        name_selectors = [
            'h1.product-single__title',
            'h1.product__title',
            'h1[class*="product"]',
            'h1',
            '.product-single__title',
            '.product__title'
        ]
        
        for selector in name_selectors:
            try:
                element = self.page.query_selector(selector)
                if element:
                    name = element.text_content().strip()
                    if name:
                        return name
            except:
                continue
        
        logger.warning("Could not find product name")
        return "Unknown Product"
    
    def _extract_description(self) -> str:
        """Extract product description - try multiple selectors"""
        description_selectors = [
            "div.rte.text--pull",
            ".product-single__description",
            ".product__description",
            "[class*='description']",
            ".rte"
        ]
        
        for selector in description_selectors:
            try:
                element = self.page.query_selector(selector)
                if element:
                    raw_html = element.inner_html()
                    cleaned_text = self._clean_description(raw_html)
                    if cleaned_text:
                        return cleaned_text[:500]  # Limit to 500 chars
            except:
                continue
        
        logger.debug("No description found")
        return ""
    
    def _clean_description(self, raw_html: str) -> str:
        """Clean product description HTML"""
        try:
            soup = BeautifulSoup(raw_html, "html.parser")
            
            # Remove all data-* attributes
            for tag in soup.find_all(True):
                for attr in list(tag.attrs):
                    if attr.startswith("data-"):
                        del tag.attrs[attr]
            
            # Extract text with newlines
            text = soup.get_text(separator="\n", strip=True)
            
            # Clean spacing and unwanted characters
            text = re.sub(r"\n{2,}", "\n", text)
            text = re.sub(r"\s{2,}", " ", text)
            text = text.replace("✅", "").replace("✔", "")
            text = text.strip()
            
            return text
        except:
            return ""
    
    def _extract_image(self) -> str:
        """Extract product image - try multiple selectors"""
        
        # Try og:image meta tag FIRST (most reliable for Shopify)
        try:
            og_image = self.page.query_selector("meta[property='og:image']")
            if og_image:
                content = og_image.get_attribute("content")
                if content:
                    # Handle protocol-relative URLs
                    if content.startswith('//'):
                        content = 'https:' + content
                    logger.success(f"✅ Extracted image via og:image: {content[:60]}...")
                    return content
        except Exception as e:
            logger.debug(f"og:image extraction failed: {e}")
        
        # Fallback to other image selectors
        image_selectors = [
            "img.product-gallery__image",
            "img[data-zoom]",
            ".product-single__media img",
            ".product__media img",
            ".product-image img",
            "img[src*='products']"
        ]
        
        for selector in image_selectors:
            try:
                image_el = self.page.query_selector(selector)
                if image_el:
                    # Try different attributes
                    image_url = (
                        image_el.get_attribute("data-zoom") or 
                        image_el.get_attribute("src") or 
                        image_el.get_attribute("data-src") or
                        image_el.get_attribute("srcset")
                    )
                    
                    if image_url:
                        # Handle srcset (might have multiple URLs)
                        if ' ' in image_url:
                            image_url = image_url.split(' ')[0]
                        
                        # Handle protocol-relative URLs
                        if image_url.startswith('//'):
                            image_url = 'https:' + image_url
                        
                        # Remove size parameters
                        image_url = image_url.split('?')[0]
                        
                        logger.success(f"✅ Extracted image: {image_url[:60]}...")
                        return image_url
            except:
                continue
        
        logger.warning("No product image found")
        return ""
    
    def _extract_price(self) -> str:
        """Extract product price - try multiple selectors"""
        price_selectors = [
            'span.price',
            '[itemprop="price"]',
            '.product-price',
            '.price__regular',
            '.product__price',
            '[class*="price"]'
        ]
        
        for selector in price_selectors:
            try:
                element = self.page.query_selector(selector)
                if element:
                    price = element.text_content().strip()
                    if price:
                        return price
            except:
                continue
        
        return ""