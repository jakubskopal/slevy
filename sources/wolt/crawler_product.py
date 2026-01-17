"""
Product page handling for Albert Wolt crawler.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from . import crawler_global


def wait_for_product_page_ready(driver, log_func=print):
    """
    Waits for the product page to fully load.
    """
    try:
        # Wait for product page elements
        WebDriverWait(driver, 10, 0.1).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'h1, [data-test-id*="product"], [data-testid*="product"]'))
        )
        
        if crawler_global.check_error_page(driver):
            log_func("Detected error page during product load")
            return False
        
        return True
    except:
        log_func("Timeout waiting for product page to load")
        return False


def extract_product_data(driver):
    """
    Extract product data from the Wolt product page.
    Returns a dictionary with product information.
    """
    data = {
        "name": None,
        "image_url": None,
        "price": None,
        "original_price": None,
        "unit_price": None,
        "description": None,
        "category": None,
        "breadcrumbs": []
    }
    
    # Extract product name (h1)
    try:
        h1 = driver.find_element(By.CSS_SELECTOR, "h1")
        data["name"] = h1.text.strip()
    except:
        pass
    
    # Extract price - Wolt typically shows price in a specific format
    try:
        # Try multiple selectors for price
        price_selectors = [
            '[data-test-id*="price"]',
            '[data-testid*="price"]',
            '[class*="price"]',
            'span[class*="Price"]'
        ]
        for selector in price_selectors:
            try:
                price_elem = driver.find_element(By.CSS_SELECTOR, selector)
                price_text = price_elem.text.strip()
                if price_text and ("Kč" in price_text or "," in price_text):
                    data["price"] = price_text
                    break
            except:
                continue
    except:
        pass
    
    # Extract image
    try:
        # Look for product image
        img_selectors = [
            'img[alt*="product"]',
            'img[class*="product"]',
            'img[class*="Product"]',
            'main img',
            'article img'
        ]
        for selector in img_selectors:
            try:
                img = driver.find_element(By.CSS_SELECTOR, selector)
                src = img.get_attribute("src")
                if src and ("http" in src or src.startswith("//")):
                    data["image_url"] = src
                    break
            except:
                continue
    except:
        pass
    
    # Extract description
    try:
        # Look for description text
        desc_selectors = [
            '[data-test-id*="description"]',
            '[data-testid*="description"]',
            'p[class*="description"]',
            '[class*="Description"]'
        ]
        for selector in desc_selectors:
            try:
                desc_elem = driver.find_element(By.CSS_SELECTOR, selector)
                desc_text = desc_elem.text.strip()
                if desc_text and len(desc_text) > 10:
                    data["description"] = desc_text
                    break
            except:
                continue
    except:
        pass
    
    # Extract breadcrumbs from URL or navigation
    try:
        # Parse from URL
        url = driver.current_url
        if "/venue/" in url:
            parts = url.split("/venue/")[1].split("/")
            if len(parts) > 1:
                # venue name
                data["breadcrumbs"].append(parts[0].replace("-", " ").title())
                # category if present
                if len(parts) > 2 and "items" in parts[1]:
                    cat_slug = parts[2].split("-itemid-")[0] if "-itemid-" in parts[2] else parts[2]
                    data["breadcrumbs"].append(cat_slug.replace("-", " ").title())
    except:
        pass
    
    # Try to extract unit price (per kg/l)
    try:
        # Look for unit price indicators
        all_text = driver.find_element(By.TAG_NAME, "body").text
        import re
        # Match patterns like "45,90 Kč/kg" or "12,50 Kč/l"
        unit_price_pattern = r'(\d+[,\.]\d+\s*Kč\s*/\s*(?:kg|l|ks))'
        matches = re.findall(unit_price_pattern, all_text)
        if matches:
            data["unit_price"] = matches[0]
    except:
        pass
    
    return data
