"""
Tesco Parser: Extracts data from rendered Tesco product pages using Apollo Cache.
"""
import gzip
import json
from bs4 import BeautifulSoup
import os
import glob
import re
from datetime import datetime
from collections import Counter
import concurrent.futures

# --- Top-Level Parsing Functions (Must be picklable) ---

def extract_json_ld(soup):
    """Extract product data from JSON-LD scripts."""
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        if not script.string: continue
        try:
            data = json.loads(script.string)
            # Normalise to list
            items = data if isinstance(data, list) else [data]
            
            for item in items:
                if item.get('@type') == 'Product':
                    return item
                # detailed graph structure check
                if '@graph' in item:
                    for g_item in item['@graph']:
                        if g_item.get('@type') == 'Product':
                            return g_item
        except: continue
    return None

def extract_preparsed_data(content):
    """Extract data injected by crawler."""
    try:
        # Look for <!-- META_JSON: { ... } --> at the beginning
        m = re.search(r'<!-- META_JSON: (\{.*?\}) -->', content[:2000]) # Limit search to start
        if m:
            return json.loads(m.group(1))
    except: pass
    return None

def extract_apollo_state(content):
    """Extract the apolloCache object from the HTML."""
    # Find the start of apolloCache
    start_marker = '"apolloCache":'
    start_idx = content.find(start_marker)
    if start_idx == -1:
        return None
    
    # We start looking after the marker
    start_idx += len(start_marker)
    
    # Find the matching closing brace for the object
    brace_count = 0
    end_idx = -1
    for i in range(start_idx, len(content)):
        if content[i] == '{':
            brace_count += 1
        elif content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break
    
    if end_idx != -1:
        try:
            state_str = content[start_idx:end_idx]
            return json.loads(state_str)
        except Exception as e:
            # print(f"JSON parsing error: {e}")
            pass
    return None

def parse_product_file(filepath):
    """
    Worker function to parse a single file.
    Returns a list of parsed product dicts for that file.
    """
    try:
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return []
    
    state = extract_apollo_state(content)
    if not state:
        return []

    # Preparsed Data (Crawler Injected)
    preparsed = {}
    meta_json = extract_preparsed_data(content)
    if meta_json and 'preparsed' in meta_json:
        preparsed = meta_json['preparsed']
    
    product_url = meta_json.get('origin_url') if meta_json else None

    # Entity lookup
    product_key = next((k for k in state if k.startswith("ProductType:")), None)
    p_data = state.get(product_key) if product_key else {}
    
    soup = BeautifulSoup(content, 'html.parser')
    json_ld = extract_json_ld(soup)
    
    # 1. Name
    name = preparsed.get('name')
    if not name: name = p_data.get('title')
    if not name and json_ld:
        name = json_ld.get('name')
    if not name:
        name_elem = soup.select_one('h1.ddsweb-heading, h1')
        name = name_elem.get_text(strip=True) if name_elem else "Unknown"

    # 2. Brand
    brand = preparsed.get('brand')
    if not brand: brand = p_data.get('brandName')
    if not brand and json_ld:
        # json_ld brand can be string or object
        b_val = json_ld.get('brand')
        if isinstance(b_val, dict):
            brand = b_val.get('name')
        elif isinstance(b_val, str):
            brand = b_val
    
    if not brand:
        brand_ref = p_data.get('brand')
        if isinstance(brand_ref, dict) and '__ref' in brand_ref:
            brand_obj = state.get(brand_ref['__ref'])
            brand = brand_obj.get('name') if brand_obj else None
    
    if not brand:
        # Fallback to DOM
        brand_header = soup.select_one('button[id*="brand-details-panel"]')
        if brand_header:
            panel_id = brand_header.get('aria-controls')
            if panel_id:
                panel = soup.find(id=panel_id)
                if panel:
                    brand = panel.get_text(strip=True)[:100]
    
    # 3. Image
    image_url = preparsed.get('image_url')
    if not image_url: image_url = p_data.get('defaultImageUrl')
    if not image_url and json_ld:
        imgs = json_ld.get('image')
        if isinstance(imgs, list) and len(imgs) > 0:
            image_url = imgs[0]
        elif isinstance(imgs, str):
            image_url = imgs
            
    if not image_url:
        image_url = p_data.get('image')
    
    if not image_url:
        img_elem = soup.select_one('img.product-image, .ddsweb-responsive-image__image')
        if img_elem:
            image_url = img_elem.get('src')
    
    # 4. Categories
    categories = preparsed.get('breadcrumbs', [])
    if not categories:
        bc_links = soup.select('a.ddsweb-breadcrumb__list-item-link')
        for link in bc_links:
            text = link.get_text(strip=True)
            if text and text not in ["Domů", "Potraviny", "Tesco Groceries"]:
                categories.append(text)

    # 5. Prices
    prices = []
    if preparsed.get('price'):
        # Convert crawler price string to float
        try:
            p_str = preparsed['price'].replace('Kč', '').replace(',', '.').replace(' ', '').strip()
            val = float(p_str)
            prices.append({
                'store_name': 'Tesco',
                'price': val,
                'unit_price': val,
                'unit': 'kus',
                'package_size': None,
                'condition': None
            })
        except: pass

    if not prices:
        price_info = p_data.get('price')
        if price_info:
            actual = price_info.get('actual')
            unit_price = price_info.get('unitPrice')
            uom = price_info.get('unitOfMeasure')
            
            offer = {
                'store_name': 'Tesco',
                'price': actual,
                'unit_price': unit_price,
                'unit': uom,
                'package_size': None,
                'condition': None
            }
            
            # DisplayType and Weight
            display_type = p_data.get('displayType')
            avg_weight = p_data.get('averageWeight')
            if display_type == "QuantityOrWeight" and avg_weight:
                offer['package_size'] = f"~{avg_weight} {uom}"

            # Promotion
            promo_ref = p_data.get('promotions')
            if promo_ref and isinstance(promo_ref, list) and len(promo_ref) > 0:
                promo_obj = state.get(promo_ref[0].get('__ref'))
                if promo_obj and promo_obj.get('isClubcard'):
                    offer['condition'] = 'Clubcard'
            
            prices.append(offer)
        elif json_ld:
            # Fallback to JSON-LD prices
            offers = json_ld.get('offers')
            if isinstance(offers, dict):
                try:
                    price_val = float(offers.get('price', 0))
                    if price_val > 0:
                        prices.append({
                            'store_name': 'Tesco',
                            'price': price_val,
                            'unit_price': price_val, # Approx
                            'unit': 'kus', # Default
                            'package_size': None,
                            'condition': None
                        })
                except: pass
        else:
            # Fallback for prices via DOM
            price_elem = soup.select_one('.gyT8MW_priceText')
            if price_elem:
                try:
                    # Main Price (e.g. "1,34 Kč")
                    txt = price_elem.get_text(strip=True).replace('Kč', '').replace(',', '.').strip()
                    price_val = float(txt)
                    
                    unit_price_val = price_val
                    unit_str = 'kus'
                    
                    # Unit Price (e.g. "9,90 Kč/kg")
                    # Look for the subtext element
                    unit_elem = soup.select_one('.ddsweb-price__subtext')
                    if unit_elem:
                        unit_txt = unit_elem.get_text(strip=True)
                        m = re.search(r'([\d,.\s]+)[\s\xa0]*Kč[\s\xa0]*/[\s\xa0]*(\w+)', unit_txt)
                        if m:
                            up_str = m.group(1).replace(',', '.').replace(' ', '').strip()
                            unit_price_val = float(up_str)
                            unit_str = m.group(2)
                    
                    prices.append({
                        'store_name': 'Tesco',
                        'price': price_val,
                        'unit_price': unit_price_val,
                        'unit': unit_str,
                        'package_size': None,
                        'condition': None
                    })
                except: pass
    
    # Refine Unit from DOM (Always Run for standard prices with default unit)
    for p in prices:
        if p.get('condition') is None and p.get('unit') == 'kus':
            try:
                unit_elem = soup.select_one('.ddsweb-price__subtext')
                if unit_elem:
                    unit_txt = unit_elem.get_text(strip=True)
                    m_up = re.search(r'([\d,.\s]+)[\s\xa0]*Kč[\s\xa0]*/[\s\xa0]*(\w+)', unit_txt)
                    if m_up:
                            up_str = m_up.group(1).replace(',', '.').replace(' ', '').strip()
                            p['unit_price'] = float(up_str)
                            p['unit'] = m_up.group(2)
            except: pass

    # Check for Clubcard Price via DOM (Text Search) - Always Run
    try:
        # Strategy: Find elements with text matching the pattern
        clubcard_elems = soup.find_all(string=re.compile(r"s Clubcard", re.IGNORECASE))
        for c_text in clubcard_elems:
            # Pattern: "19,90 Kč s Clubcard"
            m = re.search(r'(\d+[,.]\d{2})[\s\xa0]*Kč[\s\xa0]*s[\s\xa0]*Clubcard', c_text, re.IGNORECASE)
            if m:
                val_str = m.group(1).replace(',', '.').replace(' ', '').strip()
                cc_price = float(val_str)
                
                cc_unit_price = cc_price
                cc_unit = 'kus'
                
                # Try to find unit price in siblings
                parent = c_text.parent
                if parent:
                    for sib in parent.next_siblings:
                        if hasattr(sib, 'get_text'):
                            sib_txt = sib.get_text(strip=True)
                            m_up = re.search(r'([\d,.\s]+)\s*Kč\s*/\s*(\w+)', sib_txt)
                            if m_up:
                                cc_up_str = m_up.group(1).replace(',', '.').replace(' ', '').strip()
                                cc_unit_price = float(cc_up_str)
                                cc_unit = m_up.group(2)
                                break
                
                prices.append({
                    'store_name': 'Tesco',
                    'price': cc_price,
                    'unit_price': cc_unit_price,
                    'unit': cc_unit,
                    'package_size': None,
                    'condition': 'Clubcard'
                })
                break 
    except: pass

    return [{
        'name': name,
        'brand': brand,
        'product_url': product_url,
        'image_url': image_url,
        'categories': categories,
        'prices': prices,
    }]


class TescoParser:
    def __init__(self, data_dir="data/tesco_raw", console=None):
        self.data_dir = data_dir
        self.console = console

    def run(self, workers=None):
        files = glob.glob(os.path.join(self.data_dir, '*.html.gz'))
        total_files = len(files)
        
        if self.console:
            log_func = self.console.log
        else:
             log_func = print

        log_func(f"Found {total_files} files in {self.data_dir}")
        log_func(f"Starting parallel parsing with {workers or 'default'} workers...")
        
        product_map = {}
        
        if self.console and self.console.total == 0:
             self.console.total = total_files

        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
            # Submit all files
            future_to_file = {executor.submit(parse_product_file, f): f for f in files}
            
            for i, future in enumerate(concurrent.futures.as_completed(future_to_file)):
                try:
                    items = future.result()
                    for item in items:
                        name = item['name']
                        if name not in product_map:
                            product_map[name] = item
                except Exception as e:
                    # log_func(f"Error parsing file: {e}")
                    pass
                
                if self.console:
                    self.console.update(i + 1, f"Parsed: {len(product_map)}")

        # Metadata Aggregation
        brands = Counter()
        categories = Counter()
        stores = Counter()

        for product in product_map.values():
             if product.get('brand'):
                 brands[product['brand']] += 1
             if product.get('categories'):
                 for cat in product['categories']:
                     categories[cat] += 1
             if product.get('prices'):
                 for p in product['prices']:
                     if p.get('store_name'):
                         stores[p['store_name']] += 1

        output_data = {
            "products": list(product_map.values()),
            "metadata": {
                "total_products": len(product_map),
                "generated_at": datetime.now().isoformat(),
                "stores": dict(sorted(stores.items())),
                "categories": dict(sorted(categories.items())),
                "brands": dict(sorted(brands.items()))
            }
        }

        output_path = 'data/tesco.result.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        # Make a copy for browser/public if needed, or just standard path
        
        if self.console:
            self.console.log(f"Saved to {output_path}")
        else:
            print(f"Saved to {output_path}")

if __name__ == "__main__":
    parser = TescoParser()
    parser.run()
