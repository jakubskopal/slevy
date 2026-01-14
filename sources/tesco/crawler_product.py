from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

def wait_for_product_page_ready(driver, log_func=print):
    """
    Waits for pivotal elements on the product page (like the main heading) to ensure
    the page is fully loaded and ready for data extraction.
    """
    # Wait for typical product page elements
    try:
        WebDriverWait(driver, 10, 0.1).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.ddsweb-heading'))
        )
        return True
    except:
        log_func(f"Timeout waiting for product page to load")
        return False

def extract_product_data(driver):
    """Extract data directly from the rendered page to avoid parsing issues later."""
    data = {
        "name": None,
        "image_url": None,
        "price": None,
        "brand": None,
        "breadcrumbs": []
    }
    
    # Breadcrumbs
    try:
        WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a.ddsweb-breadcrumb__list-item-link')))
        bc_items = driver.find_elements(By.CSS_SELECTOR, 'a.ddsweb-breadcrumb__list-item-link')
        for bc in bc_items:
            text = bc.get_attribute("innerText").strip()
            if text and text not in ["Domů", "Potraviny", ""]:
                data["breadcrumbs"].append(text)
    except: pass
    
    # Name
    try:
        h1 = driver.find_element(By.CSS_SELECTOR, "h1")
        data["name"] = h1.text.strip()
    except: pass
    
    # Price
    try:
        price_elem = driver.find_element(By.CSS_SELECTOR, ".gyT8MW_priceText")
        data["price"] = price_elem.text.strip()
    except: pass
    
    # Image
    try:
        img = driver.find_element(By.CSS_SELECTOR, "img.product-image, .ddsweb-responsive-image__image")
        data["image_url"] = img.get_attribute("src")
    except: pass

    # Brand and other details via JSON-LD if available
    try:
        scripts = driver.find_elements(By.CSS_SELECTOR, "script[type='application/ld+json']")
        for script in scripts:
            content = script.get_attribute("innerText")
            if "Product" in content:
                ld = json.loads(content)
                items = ld if isinstance(ld, list) else [ld]
                for item in items:
                    # Check root
                    if item.get("@type") == "Product":
                        if not data["name"]: data["name"] = item.get("name")
                        if not data["image_url"] and item.get("image"):
                            imgs = item.get("image")
                            data["image_url"] = imgs[0] if isinstance(imgs, list) else imgs
                        if not data["brand"] and item.get("brand"):
                            b = item.get("brand")
                            data["brand"] = b.get("name") if isinstance(b, dict) else b
                        if not data["price"] and item.get("offers"):
                            o = item.get("offers")
                            if isinstance(o, dict) and o.get("price"):
                                data["price"] = str(o.get("price"))
                        
                    # Check graph
                    if "@graph" in item:
                        for g_item in item["@graph"]:
                            if g_item.get("@type") == "Product":
                                if not data["name"]: data["name"] = g_item.get("name")
                                if not data["image_url"] and g_item.get("image"):
                                    imgs = g_item.get("image")
                                    data["image_url"] = imgs[0] if isinstance(imgs, list) else imgs
                                if not data["brand"] and g_item.get("brand"):
                                    b = g_item.get("brand")
                                    data["brand"] = b.get("name") if isinstance(b, dict) else b
                                if not data["price"] and g_item.get("offers"):
                                    o = g_item.get("offers")
                                    if isinstance(o, dict) and o.get("price"):
                                        data["price"] = str(o.get("price"))
    except: pass
    
    return data
