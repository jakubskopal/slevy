#!/usr/bin/env python3
"""
Albert Parser: Extracts product data from gzipped HTML files.
"""
import gzip
import json
import os
import glob
import re
from datetime import datetime
from bs4 import BeautifulSoup



VENUES = {
    "albert": {
        "name": "Albert",
        "dir": "data/albert_raw",
        "output": "data/albert.result.json"
    },
    "billa": {
        "name": "Billa",
        "dir": "data/billa_raw",
        "output": "data/billa.result.json"
    },
    "globus": {
        "name": "Globus",
        "dir": "data/globus_raw",
        "output": "data/globus.result.json"
    }
}


class WoltParser:
    def __init__(self, data_dir, store_name, output_path, console=None):
        self.data_dir = data_dir
        self.store_name = store_name
        self.output_path = output_path
        self.console = console
        self.products = []

    def parse_price(self, price_text):
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

    def extract_brand(self, name):
        if not name: return None
        
        # Known multi-word brands or prefixes that need continuation
        known_brands = [
            "Nature's Promise", "World's Market", "7Days", "Coca-Cola", "Dr. Oetker",
            "Česká chuť", "Česká Chuť", "Albert Excellent", "Bersi Dessert",
            "Ben & Jerry's", "Captain Morgan", "Jack Daniel's", "Johnnie Walker",
            "Rio Mare", "Fresh Bistro", "Garden Gourmet", "Rice Up", "Fine Crunchy",
            "A.T. International", "Bad Reichenhaller", "Bear Beer", "Brise de France",
            "Cavit Prosecco", "Château", "Cute Baby", "Day Up", "Golden Bay",
            "Habánské sklepy", "Maison Castel", "Pearl River Bridge", "Perfect Fit",
            "St. Dalfour", "Villa Garducci", "World´s Market", "World‘s Market", "World’s Market",
            "Franz Josef Kaiser", "Le & Co", "Le Coq", "La Bohéma", "La Bonta Italiana",
            "La Vida Bio", "Velkopopovický Kozel", "Pilsner Urquell", "Stará myslivecká",
            "Tatranský čaj", "Tatra", "Mlékárna Kunín", "Jihočeská Niva", "Billa", "Globus"
        ]
        for kb in known_brands:
            if name.lower().startswith(kb.lower()): return kb
            
        words = name.split()
        if not words: return None
        
        # Blacklist of generic terms that are never brands when appearing alone
        blacklist = [
            "Šnek", "Mléko", "Jogurt", "Voda", "Pivo", "Pečivo", "Rohlík", "Houska",
            "Bageta", "Brambory", "Croissant", "Kachna", "Kefírové", "Kuřecí", "Mrkev",
            "Okurky", "Originální", "Paprika", "Svíčka", "Těsto", "Vepřová", "Zlaté",
            "Salát", "Pomazánka", "Sýr", "Šunka", "Tvaroh", "Mléčný", "Čerstvá", "Bio",
            "Zelí", "Žluté"
        ]
        
        brand_parts = []
        for i, word in enumerate(words):
            clean = word.replace("´", "'").replace("‘", "'").strip(",.:\"'")
            if not clean: continue
            
            if clean.isupper() and len(clean) > 1:
                brand_parts.append(clean)
                continue
            elif not brand_parts:
                if clean in blacklist: break
                if clean[0].isupper() or clean[0].isdigit():
                    brand_parts.append(clean)
                    # Generic prefixes that might be part of a brand
                    if clean.lower() in ["albert", "česká", "jihočeská", "billa", "globus"] and i+1 < len(words):
                        continue 
                    break
                else:
                    break
            else:
                if clean.isupper() and len(clean) > 1:
                    brand_parts.append(clean)
                    continue
                else:
                    break
        
        return " ".join(brand_parts) if brand_parts else None

    def extract_preparsed_data(self, content):
        """Extract metadata injected by the crawler (META_JSON)."""
        try:
            m = re.search(r'<!-- META_JSON: (\{.*?\}) -->', content[:5000])
            if m:
                return json.loads(m.group(1))
        except:
            pass
        return None

    def parse_product_file(self, filepath):
        try:
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return []

        meta = self.extract_preparsed_data(content) or {}
        soup = BeautifulSoup(content, 'html.parser')
        modal = soup.select_one('[data-test-id="product-modal"]')
        if not modal: return []

        # 1. Name
        name_elem = modal.select_one("h2") or modal.select_one('[data-test-id="ImageCentricProductCard.Title"]')
        name = name_elem.get_text(strip=True) if name_elem else "Unknown"

        # 2. Brand
        brand = self.extract_brand(name)

        # 3. Description
        desc_elem = modal.select_one('[data-test-id="product-modal.description"]') or modal.select_one('[class*="Description"]')
        description = desc_elem.get_text(strip=True) if desc_elem else None

        # 4. Image
        img_elem = modal.select_one('[data-test-id="product-modal.main-image.product-image"]')
        image_url = img_elem.get('src') if img_elem else None

        # 5. Prices and Tags
        tp_elem = modal.select_one('[data-test-id="product-modal.total-price"]') or modal.select_one('[data-test-id="product-modal.price"]')
        dp_elem = modal.select_one('[data-test-id="product-modal.discounted-price"]')
        orig_price_elem = modal.select_one('[data-test-id="product-modal.original-price"]')
        up_elem = modal.select_one('[data-test-id="product-modal.unit-price"]')
        ui_elem = modal.select_one('[data-test-id="product-modal.unit-info"]')

        price_text = (dp_elem or tp_elem).get_text(strip=True) if (dp_elem or tp_elem) else None
        price = self.parse_price(price_text)
        original_price = self.parse_price(orig_price_elem.get_text(strip=True)) if orig_price_elem else None
        
        unit_price = None
        unit = None
        if up_elem:
            up_text = up_elem.get_text(strip=True)
            unit_price = self.parse_price(up_text)
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
            'store_name': self.store_name,
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

    def run(self, workers=None):
        import concurrent.futures
        import multiprocessing

        if workers is None:
            workers = max(1, multiprocessing.cpu_count() // 2)

        files = glob.glob(os.path.join(self.data_dir, '*.html.gz'))
        total_files = len(files)
        if self.console:
             log_func = self.console.log
        else:
             log_func = print

        log_func(f"Found {total_files} files in {self.data_dir} (using {workers} workers)")
        
        product_map = {}
        
        if self.console and self.console.total == 0:
             self.console.total = total_files

        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
            # Submit all files for parsing
            future_to_file = {executor.submit(self.parse_product_file, f): f for f in files}
            
            for i, future in enumerate(concurrent.futures.as_completed(future_to_file)):
                try:
                    items = future.result()
                    for item in items:
                        # Use URL as unique key if available
                        key = item['product_url'] or item['name']
                        if key not in product_map:
                            product_map[key] = item
                except Exception as e:
                    pass
                if self.console:
                    self.console.update(i + 1, f"Parsed: {len(product_map)}")

        output_data = {
            "products": list(product_map.values()),
            "metadata": {
                "total_products": len(product_map),
                "generated_at": datetime.now().isoformat(),
                "stores": {self.store_name: len(product_map)},
            }
        }

        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        if self.console:
            self.console.log(f"Saved to {self.output_path}")
        else:
            print(f"Saved to {self.output_path}")



