from playwright.sync_api import sync_playwright
import time

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(60000)

        # Go to home page
        page.goto("https://stairnosingsuk.co.uk", wait_until="domcontentloaded")
        print("🏠 Opened home page")

        # ✅ Get homepage collection links (accurate selector)
        page.wait_for_selector("a.promo-block.promo-block--bottom-center.promo-block--medium", timeout=20000)
        collection_links = [
            a.get_attribute("href")
            for a in page.query_selector_all("a.promo-block.promo-block--bottom-center.promo-block--medium")
            if a.get_attribute("href")
        ]
        collection_links = list(dict.fromkeys(collection_links))  # remove duplicates

        print(f"📦 Found {len(collection_links)} homepage collections")

        # ✅ Loop through all collections
        for collection_url in collection_links:
            if not collection_url.startswith("http"):
                collection_url = f"https://stairnosingsuk.co.uk{collection_url}"

            print(f"\n🛍️ Visiting collection: {collection_url}")
            page.goto(collection_url, wait_until="domcontentloaded")
            time.sleep(3)

            # ✅ Get all product URLs in this collection
            product_links = list(set(
                [a.get_attribute("href") for a in page.query_selector_all("a[href*='/products/']") if a.get_attribute("href")]
            ))
            print(f"🧾 Found {len(product_links)} product links in this collection")

            # ✅ Loop through products
            for product_url in product_links:
                if not product_url.startswith("http"):
                    product_url = f"https://stairnosingsuk.co.uk{product_url}"

                print(f"\n🧩 Opening product: {product_url}")
                try:
                    page.goto(product_url, wait_until="domcontentloaded")
                    page.wait_for_selector('h1', timeout=15000)

                    # ✅ Scroll to load iframe
                    for i in range(0, 10):
                        page.evaluate(f"window.scrollTo(0, {i * 400});")
                        time.sleep(0.3)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)

                    # ✅ Wait for Loox iframe
                    page.wait_for_selector('iframe#looxReviewsFrame', timeout=20000)
                    iframe_el = page.query_selector('iframe#looxReviewsFrame')
                    iframe = iframe_el.content_frame()

                    # ✅ Click “Write a Review”
                    iframe.wait_for_selector("#write", timeout=15000)
                    iframe.click("#write")
                    print("✅ Clicked Write a Review")
                    time.sleep(5)

                    # ✅ Wait for review form iframe
                    page.wait_for_selector('iframe#loox-review-form-ugc-dialog', timeout=20000)
                    iframe_element = page.query_selector('iframe#loox-review-form-ugc-dialog')
                    review_iframe = iframe_element.content_frame()

                    if not review_iframe:
                        print("❌ Could not access Loox review iframe.")
                        continue

                    review_iframe.wait_for_function("document.readyState === 'complete' && document.body !== null")
                    print("✅ Review form iframe loaded")

                    # ✅ Click 5 stars
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
                            print(f"✅ Found {count} stars using selector: {sel}")
                            break

                    if not stars or stars.count() == 0:
                        print("⚠️ No stars found — skipping product.")
                        continue

                    idx = min(4, stars.count() - 1)
                    stars.nth(idx).click(force=True)
                    print("🌟 Clicked 5-star rating successfully.")

                    # ✅ Click “Skip”
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
                            review_iframe.wait_for_selector(sel, timeout=2000)
                            review_iframe.click(sel, timeout=2000, force=True)
                            print(f"✅ Clicked Skip button with selector: {sel}")
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

                    # ✅ Fill review text
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
                            print(f"✅ Filled review textarea using selector: {sel}")
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
                        print("✅ JS fallback executed for textarea.")

                    # ✅ Click “Next”
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
                            print(f"✅ Clicked Next button with selector: {sel}")
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
                        print("✅ JS fallback executed for Next button.")

                    # ✅ Fill name/email
                    inputs = {
                        "first name": ["input[data-testid='first name field']", "input[autocomplete='given-name']"],
                        "last name": ["input[data-testid='last name field']", "input[autocomplete='family-name']"],
                        "email": ["input[data-testid='email field']", "input[autocomplete='email']"]
                    }

                    data = {"first name": "Jessica", "last name": "den", "email": "jessicaden@exe.com"}

                    for field, selectors in inputs.items():
                        for sel in selectors:
                            try:
                                review_iframe.wait_for_selector(sel, timeout=2000)
                                review_iframe.fill(sel, data[field])
                                print(f"✅ Filled {field} using selector: {sel}")
                                break
                            except Exception:
                                continue

                    # ✅ Click Done
                    done_selectors = [
                        "button[data-testid='done button']",
                        "button:has-text('Done')",
                        "text=Done",
                        "xpath=//button[contains(., 'Done')]"
                    ]

                    for sel in done_selectors:
                        try:
                            review_iframe.wait_for_selector(sel, timeout=2000)
                            review_iframe.click(sel, force=True)
                            print(f"✅ Clicked Done button using {sel}")
                            break
                        except Exception:
                            continue

                    print("🎯 Review submitted for this product.")
                    time.sleep(3)

                    # ✅ Try clicking the Close button after Done
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
                        "button[type='button'][data-testid='close button']"
                    ]

                    close_clicked = False
                    for sel in close_selectors:
                        try:
                            review_iframe.wait_for_selector(sel, timeout=2000)
                            review_iframe.click(sel, force=True)
                            time.sleep(10)
                            print(f"✅ Clicked Close button using selector: {sel}")
                            close_clicked = True
                            break
                        except Exception:
                            continue

                    if not close_clicked:
                        # JS fallback if all fail
                        review_iframe.evaluate("""
                            const btn = Array.from(document.querySelectorAll('button')).find(b =>
                                b.getAttribute('data-testid') === 'close button' ||
                                b.getAttribute('aria-label') === 'Exit' ||
                                b.textContent.trim() === '×'
                            );
                            if (btn) btn.click();
                        """)
                        print("✅ JS fallback executed for Close button.")


                except Exception as e:
                                        print(f"❌ Error on product: {e}")
                                        continue
            

        print("✅ Completed all homepage collections and products.")
        browser.close()

if __name__ == "__main__":
    main()
