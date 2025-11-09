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

        # ✅ Click first collection
        page.wait_for_selector('xpath=//*[@id="block-1555314133560-0"]/a')
        page.click('xpath=//*[@id="block-1555314133560-0"]/a')
        print("✅ Clicked first collection")

        # ✅ Click first product
        page.wait_for_selector('xpath=//*[@id="shopify-section-collection-template"]/section/div[1]/div[2]/div[2]/div/div/div/div[2]/div[1]/a')
        page.click('xpath=//*[@id="shopify-section-collection-template"]/section/div[1]/div[2]/div[2]/div/div/div/div[2]/div[1]/a')
        print("✅ Clicked first product")

        # ✅ Wait for product page
        page.wait_for_selector('h1')

        # ✅ Scroll
        for i in range(0, 10):
            page.evaluate(f"window.scrollTo(0, {i * 400});")
            time.sleep(0.3)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)

        # ✅ Wait for Loox iframe
        page.wait_for_selector('iframe#looxReviewsFrame', timeout=30000)
        iframe_el = page.query_selector('iframe#looxReviewsFrame')
        iframe = iframe_el.content_frame()

        # ✅ Click “Write a Review”
        iframe.wait_for_selector("#write", timeout=20000)
        iframe.click("#write")
        print("✅ Clicked Write a Review")
        time.sleep(5)

        # ✅ Wait for the review modal iframe
        page.wait_for_selector('iframe#loox-review-form-ugc-dialog', timeout=20000)
        iframe_element = page.query_selector('iframe#loox-review-form-ugc-dialog')
        review_iframe = iframe_element.content_frame()

        if not review_iframe:
            print("❌ Could not access Loox review iframe.")
            return

        review_iframe.wait_for_function("document.readyState === 'complete' && document.body !== null")
        print("✅ Review form iframe loaded")

        # ✅ Click stars
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

        if stars and stars.count() > 0:
            idx = min(4, stars.count() - 1)
            stars.nth(idx).click(force=True)
            print("🌟 Clicked 5-star rating successfully.")

            # ✅ Click “Skip”
            skip_selectors = [
                "button[aria-label='Skip']",
                "button[data-testid='mobile skip button']",
                "button:has-text('Skip')",
                "text=Skip",
                "button:has-text('skip')",
                "xpath=//button[contains(., 'Skip')]",
                "xpath=//button[@data-testid='mobile skip button']",
                "xpath=//button[@aria-label='Skip']",
                "xpath=//button[contains(@class, 'lxs-button')]",
                "xpath=//button[contains(@class, 'skip')]",
                "css=button.lxs-button_luovo1_1_button_phm27_71",
                "css=button[data-lxs-variant='text']",
                "button[type='button']:has-text('Skip')",
                "div[class*='mobile'] button",
                "button"
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

            # ✅ Enter review text
            print("📝 Trying to fill review textarea...")

            textarea_selectors = [
                "textarea[data-testid='review field']",
                "textarea[aria-label='Tell us more!']",
                "textarea[aria-required='true']",
                "textarea#react-aria8478918504-9_",
                "textarea._lxs-textarea_12x6n_1",
                "textarea._textarea_33r16_39",
                "form textarea",
                "div[class*='field'] textarea",
                "xpath=//textarea[@aria-label='Tell us more!']",
                "xpath=//textarea[@placeholder='Share your experience']",
                "xpath=//textarea[contains(@class,'textarea')]",
                "textarea[name='review']",
                "textarea[role='textbox']",
                "textarea",
                "xpath=//form//textarea"
            ]

            review_text_entered = False
            for sel in textarea_selectors:
                try:
                    review_iframe.wait_for_selector(sel, timeout=2000)
                    review_iframe.fill(sel, "This product is really good. Highly recommended!")
                    print(f"✅ Filled review textarea using selector: {sel}")
                    review_text_entered = True
                    break
                except Exception as e:
                    print(f"❌ Failed textarea selector: {sel} | {e}")

            if not review_text_entered:
                review_iframe.evaluate("""
                    const ta = document.querySelector('textarea');
                    if (ta) {
                        ta.value = "This product is really good. Highly recommended!";
                        ta.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                """)
                print("✅ JS fallback executed for textarea.")

            # ✅ Click “Next” button
            print("➡️ Trying to locate 'Next' button...")

            next_selectors = [
                "button[data-testid='next button']",
                "button:has-text('Next')",
                "text=Next",
                "button[form='idnADB8Kwf']",
                "button[type='submit']",
                "xpath=//button[contains(., 'Next')]",
                "xpath=//button[@data-testid='next button']",
                "xpath=//button[@form='idnADB8Kwf']",
                "xpath=//button[contains(@class, '_button_')]",
                "button[data-lxs-variant='primary']",
                "css=button._lxs-button_luvow_1",
                "css=button._button_33r16_43",
                "div[class*='footer'] button",
                "form button[type='submit']",
                "xpath=//form//button"
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
                    time.sleep(10)
                    print(f"✅ Clicked Next button with selector: {sel}")
                    next_clicked = True
                    break
                except Exception as e:
                    print(f"❌ Failed Next selector: {sel} | {e}")

            if not next_clicked:
                review_iframe.evaluate("""
                    const btn = Array.from(document.querySelectorAll('button'))
                      .find(b => b.textContent && b.textContent.trim().toLowerCase() === 'next');
                    if (btn) {
                        btn.removeAttribute('disabled');
                        btn.disabled = false;
                        btn.scrollIntoView({block:'center'});
                        btn.click();
                    }
                """)
                print("✅ JS fallback executed for Next button.")
                
            page.screenshot(path="next_click_debug.png", full_page=True)
            print("📸 Saved screenshot after Next button click.")

            # =====================================================================
            # ✅ NEW PART: Fill name, email, and click Done (added below Next logic)
            # =====================================================================

            print("👤 Filling first name, last name, and email fields...")

            inputs = {
                "first name": [
                    "input[data-testid='first name field']",
                    "input#M5sLgJ2vGZ-given-name",
                    "input[autocomplete='given-name']",
                    "xpath=//input[@data-testid='first name field']",
                    "xpath=//input[contains(@id,'given')]",
                    "input[enterkeyhint='next']",
                    "input[type='text']",
                    "input"
                ],
                "last name": [
                    "input[data-testid='last name field']",
                    "input#M5sLgJ2vGZ-family-name",
                    "input[autocomplete='family-name']",
                    "xpath=//input[@data-testid='last name field']",
                    "xpath=//input[contains(@id,'family')]",
                    "input[enterkeyhint='next']",
                    "input[type='text']",
                    "input"
                ],
                "email": [
                    "input[data-testid='email field']",
                    "input#M5sLgJ2vGZ-email",
                    "input[autocomplete='email']",
                    "xpath=//input[@data-testid='email field']",
                    "xpath=//input[contains(@id,'email')]",
                    "input[type='email']",
                    "input[aria-required='true']",
                    "input"
                ]
            }

            data = {
                "first name": "John",
                "last name": "Dee",
                "email": "john.dee@exe.com"
            }

            for field, selectors in inputs.items():
                filled = False
                for sel in selectors:
                    try:
                        review_iframe.wait_for_selector(sel, timeout=2000)
                        review_iframe.fill(sel, data[field])
                        time.sleep(10)
                        print(f"✅ Filled {field} using selector: {sel}")
                        filled = True
                        break
                    except Exception:
                        continue
                if not filled:
                    print(f"⚙️ JS fallback for {field}")
                    review_iframe.evaluate(
                        """([label, value]) => {
                            const inputs = document.querySelectorAll('input');
                            const el = Array.from(inputs).find(i =>
                                i.id?.toLowerCase().includes(label) ||
                                i.getAttribute('data-testid')?.includes(label)
                            );
                            if (el) {
                                el.value = value;
                                el.dispatchEvent(new Event('input', { bubbles: true }));
                            }
                        }""", [field, data[field]]
                    )

            print("🟩 Trying to click Done button...")

            done_selectors = [
                "button[data-testid='done button']",
                "button:has-text('Done')",
                "text=Done",
                "button[form='M5sLgJ2vGZ']",
                "xpath=//button[@data-testid='done button']",
                "xpath=//button[contains(., 'Done')]",
                "button[data-lxs-variant='primary']",
                "css=button._lxs-button_luvow_1",
                "css=button._button_1o1b6_58",
                "div[class*='footer'] button",
                "form button[type='submit']",
                "xpath=//form//button"
            ]

            done_clicked = False
            for sel in done_selectors:
                try:
                    review_iframe.wait_for_selector(sel, timeout=2000)
                    review_iframe.click(sel, force=True)
                    time.sleep(10)
                    print(f"✅ Clicked Done button using {sel}")
                    done_clicked = True
                    break
                except Exception:
                    continue

            if not done_clicked:
                print("⚙️ JS fallback for Done button...")
                review_iframe.evaluate("""
                    const btn = Array.from(document.querySelectorAll('button'))
                      .find(b => b.textContent.trim().toLowerCase() === 'done');
                    if (btn) btn.click();
                """)
                time.sleep(5)
                print("✅ JS fallback executed for Done button.")
            # =====================================================================

        else:
            print("⚠️ No clickable stars found.")

        time.sleep(5)
        browser.close()

if __name__ == "__main__":
    main()
