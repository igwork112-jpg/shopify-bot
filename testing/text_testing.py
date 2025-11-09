from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

def clean_product_description(raw_html):
    """Cleans and formats product description HTML into readable text."""
    soup = BeautifulSoup(raw_html, "html.parser")

    # Remove all data-* attributes
    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            if attr.startswith("data-"):
                del tag.attrs[attr]

    # Extract text with newlines
    text = soup.get_text(separator="\n", strip=True)

    # Clean spacing and unwanted characters
    text = re.sub(r"\n{2,}", "\n", text)   # Collapse multiple newlines
    text = re.sub(r"\s{2,}", " ", text)    # Collapse multiple spaces
    text = text.replace("✅", "").replace("✔", "")  # Remove emojis if unwanted
    text = text.strip()

    return text


def extract_product_description(page):
    """Extracts and cleans product description from a product page."""
    try:
        # Wait for the product description container
        page.wait_for_selector("div.rte.text--pull", timeout=10000)
        description_element = page.query_selector("div.rte.text--pull")

        if description_element:
            raw_html = description_element.inner_html()
            cleaned_text = clean_product_description(raw_html)
            print("🧾 PRODUCT DESCRIPTION TEXT:\n", cleaned_text)
            return cleaned_text
        else:
            print("⚠️ Product description not found.")
            return None

    except Exception as e:
        print("❌ Error extracting description:", e)
        return None


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://stairnosingsuk.co.uk/products/aluminium-stair-nosing-for-carpet-and-wooden-stairs")

        # Extract & clean product description
        extract_product_description(page)

        browser.close()


if __name__ == "__main__":
    main()
