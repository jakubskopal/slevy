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
import argparse
from console import Console

class TescoParser:
    def __init__(self, data_dir="data/tesco_raw"):
        self.data_dir = data_dir
        self.products = []

    def extract_json_ld(self, soup):
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

    def extract_preparsed_data(self, content):
        """Extract data injected by crawler."""
        try:
            # Look for <!-- META_JSON: { ... } --> at the beginning
            m = re.search(r'<!-- META_JSON: (\{.*?\}) -->', content[:2000]) # Limit search to start
            if m:
                return json.loads(m.group(1))
        except: pass
        return None

    def extract_apollo_state(self, content):
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

    def parse_product_file(self, filepath):
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            content = f.read()
        
        state = self.extract_apollo_state(content)
        if not state:
            return []

        # Preparsed Data (Crawler Injected)
        preparsed = {}
        meta_json = self.extract_preparsed_data(content)
        if meta_json and 'preparsed' in meta_json:
            preparsed = meta_json['preparsed']
        
        product_url = meta_json.get('origin_url') if meta_json else None

        # Entity lookup
        product_key = next((k for k in state if k.startswith("ProductType:")), None)
        p_data = state.get(product_key) if product_key else {}
        
        soup = BeautifulSoup(content, 'html.parser')
        json_ld = self.extract_json_ld(soup)
        
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
                        txt = price_elem.get_text(strip=True).replace('Kč', '').replace(',', '.').strip()
                        val = float(txt)
                        prices.append({
                            'store_name': 'Tesco',
                            'price': val,
                            'unit_price': val,
                            'unit': 'kus',
                            'package_size': None,
                            'condition': None
                        })
                    except: pass

        return [{
            'name': name,
            'brand': brand,
            'product_url': product_url,
            'image_url': image_url,
            'categories': categories,
            'prices': prices,
        }]

    def run(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--color", action="store_true", help="Show ANSI progress bar")
        args = parser.parse_args()

        files = glob.glob(os.path.join(self.data_dir, '*.html.gz'))
        total_files = len(files)
        print(f"Found {total_files} files in {self.data_dir}")
        
        product_map = {}
        console = Console(total=total_files, use_colors=args.color)
        console.start()

        for i, f in enumerate(files):
            try:
                items = self.parse_product_file(f)
                for item in items:
                    name = item['name']
                    if name not in product_map:
                        product_map[name] = item
            except Exception:
                pass
            console.update(i + 1, f"Parsed: {len(product_map)}")
        
        console.finish()

        output_data = {
            "products": list(product_map.values()),
            "metadata": {
                "total_products": len(product_map),
                "generated_at": datetime.now().isoformat(),
                "stores": {"Tesco": len(product_map)},
            }
        }

        output_path = 'data/tesco.result.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"Saved to {output_path}")

if __name__ == "__main__":
    parser = TescoParser()
    parser.run()
