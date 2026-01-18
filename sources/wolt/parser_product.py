import gzip
import json
import re
from bs4 import BeautifulSoup

def parse_price(price_text):
    if not price_text or price_text == "N/A":
        return None
    # Match "95,60 Kč" or "95.60" etc.
    m = re.search(r'([\d\s,.]+)', price_text)
    if m:
        clean = m.group(1).replace(',', '.').replace('\xa0', '').replace(' ', '').strip()
        try:
            return float(clean)
        except ValueError:
            return None
    return None



def extract_preparsed_data(content):
    """Extract metadata injected by the crawler (META_JSON)."""
    try:
        m = re.search(r'<!-- META_JSON: (\{.*?\}) -->', content[:5000])
        if m:
            return json.loads(m.group(1))
    except:
        pass
    return None

def parse_product_file(filepath, store_name):
    try:
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return []

    meta = extract_preparsed_data(content) or {}
    soup = BeautifulSoup(content, 'html.parser')
    modal = soup.select_one('[data-test-id="product-modal"]')
    if not modal: return []

    # 1. Name
    name_elem = modal.select_one("h2") or modal.select_one('[data-test-id="ImageCentricProductCard.Title"]')
    name = name_elem.get_text(strip=True) if name_elem else "Unknown"

    # 2. Brand
    brand = None # Will be enriched in post-processing if missing

    # 3. Description
    desc_elem = modal.select_one('[data-test-id="product-modal.description"]') or modal.select_one('[class*="Description"]')
    description = desc_elem.get_text(strip=True) if desc_elem else None

    # 4. Image
    img_container = modal.select_one('[data-test-id="product-modal.main-image.product-image"]')
    if img_container:
        img_elem = img_container.find('img')
        image_url = img_elem.get('src') if img_elem else None
    else:
        image_url = None

    # 5. Prices and Tags
    tp_elem = modal.select_one('[data-test-id="product-modal.total-price"]') or modal.select_one('[data-test-id="product-modal.price"]')
    dp_elem = modal.select_one('[data-test-id="product-modal.discounted-price"]')
    orig_price_elem = modal.select_one('[data-test-id="product-modal.original-price"]')
    up_elem = modal.select_one('[data-test-id="product-modal.unit-price"]')
    ui_elem = modal.select_one('[data-test-id="product-modal.unit-info"]')

    price_text = (dp_elem or tp_elem).get_text(strip=True) if (dp_elem or tp_elem) else None
    price = parse_price(price_text)
    original_price = parse_price(orig_price_elem.get_text(strip=True)) if orig_price_elem else None
    
    unit_price = None
    unit = None
    if up_elem:
        up_text = up_elem.get_text(strip=True)
        unit_price = parse_price(up_text)
        m_unit = re.search(r'/\s*(\w+)', up_text)
        if m_unit: unit = m_unit.group(1)

    unit_info = ui_elem.get_text(strip=True) if ui_elem else None

    # Tags/Conditions
    conditions_list = []
    if orig_price_elem:
        conditions_list.append("Sleva")
    
    tag_selectors = [
        '.cb_Tag_Root_7dc[data-variant="secondaryWarning"]',
        '.cb_Tag_Root_7dc[data-variant="primaryNeutral"]'
    ]
    for selector in tag_selectors:
        tag_elems = modal.select(selector)
        for tag in tag_elems:
            tag_text = tag.get_text(strip=True)
            if tag_text and tag_text not in conditions_list:
                conditions_list.append(tag_text)
    
    # 6. Categories
    categories = meta.get("category", [])
    if not categories:
        # Fallback to active links in navigation bar (may be multiple for hierarchy)
        active_links = soup.select('[data-test-id="navigation-bar-active-link"]')
        for link in active_links:
            nav_title = link.select_one('[data-test-id="NavigationListItem-title"]')
            if nav_title:
                cat_name = nav_title.get_text(strip=True)
                if cat_name not in categories:
                    categories.append(cat_name)

    prices = [{
        'store_name': store_name,
        'price': price,
        'original_price': original_price,
        'unit_price': unit_price,
        'unit': unit,
        'package_size': unit_info,
        'condition': ", ".join(conditions_list) if conditions_list else None
    }]

    return [{
        'name': name,
        'brand': brand,
        'product_url': meta.get("origin_url"),
        'image_url': image_url,
        'categories': categories,
        'prices': prices,
        'description': description
    }]
