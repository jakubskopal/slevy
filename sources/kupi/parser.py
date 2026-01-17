"""
Kupi Parser: Structured data extraction from raw HTML archives.

Overview:
Processes raw HTML (.html and .html.gz) files collected by the crawler into a single, 
deduplicated JSON profile (kupi.json). It merges data from different page types 
to create a comprehensive view of available deals.

Key Extraction Steps:
1. Dual-Path Parsing: Handles 'sleva_*.html' (Detailed price tables) and 
   'slevy_*.html' (Category grids).
2. Hierarchical Categories: Extracts parent-child relationships from breadcrumbs 
   (.bc_nav) to enable nested sidebar filtering.
3. Brand Detection: Attempts to resolve brand names via JSON-LD metadata for 
   enriched filtering.
4. Smart Metric Parsing: Normalizes Czech unit prices, package sizes, and 
   calculates original prices from discount percentages.
5. Date Normalization: Converts natural Czech dates (e.g., 'dnes končí', 
   'čt 15. 1. – ne 18. 1.') into ISO-standard validity ranges.
6. Product Merging: Deduplicates across files by product name, merging offers from 
   multiple stores into a single entry.
7. UI Metadata: Pre-calculates store, brand, and category counts to optimize 
   frontend performance.
"""
import gzip
import json
from bs4 import BeautifulSoup
import json
import os
import glob
import re
from datetime import datetime, timedelta
import gzip
from collections import Counter

class KupiParser:
    def __init__(self, data_dir="data/kupi_raw"):
        self.data_dir = data_dir
        self.products = []
        self.current_year = datetime.now().year

    def parse_unit_price_string(self, text):
        # Expected format: "33,80 Kč / 1 l" or "8,20 Kč / 100 g"
        if not text:
            return None, None
        
        # Regex to capture value before "Kč" and unit after "/"
        # value part might contain spaces (e.g. 1 200,50)
        match = re.search(r'([\d\s,.]+)\s*Kč\s*/\s*(.+)', text)
        if match:
            val_str = match.group(1).replace(' ', '').replace(',', '.')
            unit_str = match.group(2).strip()
            try:
                val = float(val_str)
                return val, unit_str
            except ValueError:
                pass
        return None, text 

    def parse_validity_dates(self, text):
        if not text:
            return None, None
        
        start_date = None
        end_date = None
        today = datetime.now().date()
        
        # Replace non-breaking spaces with regular ones
        clean_text = text.replace('\xa0', ' ').strip()
        lower_text = clean_text.lower()
        
        try:
            # Case 1: "zítra končí"
            if "zítra končí" in lower_text:
                end_date = today + timedelta(days=1)
            
            # Case 2: "dnes končí"
            elif "dnes končí" in lower_text:
                end_date = today

            # Case 3: Range "čt 15. 1. – ne 18. 1."
            # Allow arbitrary text between date 1 and dash, and between dash and date 2
            # Use dot matches newline just in case? No, usually single line.
            range_match = re.search(r'(\d+\.\s*\d+\.).*?[–-].*?(\d+\.\s*\d+\.)', clean_text)
            if range_match:
                start_str = range_match.group(1).replace(' ', '')
                end_str = range_match.group(2).replace(' ', '')
                start_date = datetime.strptime(f"{start_str}{self.current_year}", "%d.%m.%Y").date()
                end_date = datetime.strptime(f"{end_str}{self.current_year}", "%d.%m.%Y").date()
            
            else:
                # Case 4: "platí do 31. 1."
                # Allow 'do' then anything then date
                do_match = re.search(r'do\s+.*?(\d+\.\s*\d+\.)', lower_text)
                if do_match:
                    end_str = do_match.group(1).replace(' ', '')
                    end_date = datetime.strptime(f"{end_str}{self.current_year}", "%d.%m.%Y").date()

                # Case 5: "platí od 1. 1."
                od_match = re.search(r'od\s+.*?(\d+\.\s*\d+\.)', lower_text)
                if od_match:
                    start_str = od_match.group(1).replace(' ', '')
                    start_date = datetime.strptime(f"{start_str}{self.current_year}", "%d.%m.%Y").date()

        except Exception as e:
            # print(f"Date parse error for '{text}': {e}")
            pass

        return (start_date.isoformat() if start_date else None, 
                end_date.isoformat() if end_date else None)

    def parse_list_row_offers(self, soup):
        offers = []
        for discount_row in soup.select('.discount_row'):
            store_name_elem = discount_row.select_one('.discounts_shop_name a, .discounts_shop_name')
            price_elem = discount_row.select_one('.discount_price_value')
            unit_price_elem = discount_row.select_one('.price_per_unit')
            amount_elem = discount_row.select_one('.discount_amount')
            validity_elem = discount_row.select_one('.discounts_validity')
            
            store_name = store_name_elem.get_text(strip=True) if store_name_elem else "Unknown"
            # Normalize store name (collapse whitespace/newlines)
            store_name = " ".join(store_name.split())
            
            price = None
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_text = price_text.replace('Kč', '').replace(',', '.').replace(' ', '').strip()
                try:
                    price = float(price_text)
                except ValueError:
                    price = price_text

            unit_price = None
            unit = None
            if unit_price_elem:
                raw_unit_price = unit_price_elem.get_text(strip=True)
                unit_price, unit = self.parse_unit_price_string(raw_unit_price)

            package_size = None
            if amount_elem:
                package_size = amount_elem.get_text(strip=True).replace('/', '').strip()

            validity = None
            validity_start = None
            validity_end = None
            if validity_elem:
                validity = validity_elem.get_text(strip=True)
                validity_start, validity_end = self.parse_validity_dates(validity)

            conditions = []
            loyalty_elem = discount_row.select_one('.discounts_club')
            note_elem = discount_row.select_one('.discount_note')
            
            if loyalty_elem:
                conditions.append(loyalty_elem.get_text(strip=True))
            if note_elem:
                conditions.append(note_elem.get_text(strip=True))
            
            condition_text = " | ".join(conditions) if conditions else None

            # Extract IDs
            product_id = discount_row.get('data-product')
            shop_id = discount_row.get('data-shop')
            discount_id = discount_row.get('data-discount')
            
            # Discount Percentage
            discount_pct_elem = discount_row.select_one('.discount_percentage')
            discount_pct = None
            if discount_pct_elem:
                pct_text = discount_pct_elem.get_text(strip=True).replace('%', '').replace('–', '').replace('-', '').strip()
                try:
                    discount_pct = float(pct_text)
                except ValueError:
                    pass

            # Original Price Calculation
            original_price = None
            if price and isinstance(price, float) and discount_pct:
                # price = original * (1 - pct/100)  => original = price / (1 - pct/100)
                try:
                    factor = 1 - (discount_pct / 100.0)
                    if factor > 0:
                        original_price = round(price / factor, 2)
                except Exception:
                    pass

            offers.append({
                'store_name': store_name,
                'price': price,
                'original_price': original_price,
                'discount_pct': discount_pct,
                'unit_price': unit_price,
                'unit': unit,
                'package_size': package_size,
                'validity': validity,
                'validity_start': validity_start,
                'validity_end': validity_end,
                'condition': condition_text,
                'product_id': product_id,
                'shop_id': shop_id,
                'discount_id': discount_id
            })
        return offers

    def parse_grid_item(self, discount_div):
        try:
            overlay_links = discount_div.select('.grid_discounts_overlay_content a, .grid_discounts_overlay_btns a, a.product_link_history')
            is_detail_link = False
            for link in overlay_links:
                href = link.get('href')
                if href and href.startswith('/sleva/'):
                     is_detail_link = True
                     break
            
            if is_detail_link:
                return None
            
            # Name
            name_elem = discount_div.select_one('.grid_discounts_product_name')
            if not name_elem:
                return None
            name = name_elem.get_text(strip=True)

            # Store
            store_elem = discount_div.select_one('.grid_discounts_shop_name a, .grid_discounts_shop_name')
            store_name = store_elem.get_text(strip=True) if store_elem else "Unknown"
            # Normalize store name
            store_name = " ".join(store_name.split())

            # Image
            img_elem = discount_div.select_one('.grid_discounts_image img')
            image_url = None
            if img_elem:
                image_url = img_elem.get('data-src') or img_elem.get('src')

            # Price & Unit
            price_elem = discount_div.select_one('.grid_discounts_price')
            price = None
            unit_price = None
            unit = None
            package_size = None
            
            if price_elem:
                # Pack size is often in span of main price in grid
                unit_price_span = price_elem.select_one('span')
                if unit_price_span:
                    # In grid, that span corresponds to package size usually (e.g. / 0,5 l)
                    package_size = unit_price_span.get_text(strip=True).replace('/', '').strip()
                    
                    full_text = price_elem.get_text(strip=True)
                    price_text = full_text.replace(unit_price_span.get_text(strip=True), '').strip()
                else:
                    price_text = price_elem.get_text(strip=True)
                
                price_text = price_text.replace('Kč', '').replace(',', '.').replace(' ', '').strip()
                try:
                    price = float(price_text)
                except ValueError:
                    price = price_text

                except ValueError:
                    price = price_text

            # Extract IDs (try on main div or search children)
            product_id = discount_div.get('data-product') or discount_div.get('data-product-id')
            shop_id = discount_div.get('data-shop') or discount_div.get('data-shop-id')
            discount_id = discount_div.get('data-discount') or discount_div.get('data-discount-id')

            conditions = []
            validity = None
            validity_start = None
            validity_end = None
            
            discount_pct = None
            
            overlay_elem = discount_div.select_one('.grid_discounts_overlay_content p')
            if overlay_elem:
                cond_text = overlay_elem.get_text(strip=True)
                if cond_text:
                     conditions.append(cond_text)

            # Try to find discount percentage in grid
            # Usually it's not explicitly separate class in grid view snippet provided?
            # Step 173 output showed .amount_percentage in list view. 
            # Step 404 output didn't show perctange for grid.
            # Assuming it might be missing or inside price_elem?
            # Actually, standard Kupi grid often has a percentage badge.
            pct_elem = discount_div.select_one('.discount_value, .discount_percentage')
            if pct_elem:
                pct_text = pct_elem.get_text(strip=True).replace('%', '').replace('–', '').replace('-', '').strip()
                try:
                    discount_pct = float(pct_text)
                except ValueError:
                    pass
            
            # Original Price
            original_price = None
            if price and isinstance(price, float) and discount_pct:
                 try:
                    factor = 1 - (discount_pct / 100.0)
                    if factor > 0:
                        original_price = round(price / factor, 2)
                 except Exception:
                    pass

            validity_elem = discount_div.select_one('.grid_discounts_validity')
            if validity_elem:
                 validity = validity_elem.get_text(strip=True)
                 validity_start, validity_end = self.parse_validity_dates(validity)
            
            condition_text = " | ".join(conditions) if conditions else None

            offer = {
                'store_name': store_name,
                'price': price,
                'original_price': original_price,
                'discount_pct': discount_pct,
                'unit_price': unit_price, 
                'unit': unit,
                'package_size': package_size,
                'validity': validity,
                'validity_start': validity_start,
                'validity_end': validity_end,
                'condition': condition_text,
                'product_id': product_id,
                'shop_id': shop_id,
                'discount_id': discount_id
            }

            return {
                'name': name,
                'image_url': image_url,
                'offers': [offer]
            }
        except Exception:
            return None

    def parse_product_file(self, filepath):
        if filepath.endswith('.gz'):
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                content = f.read()
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
        # Extract product_url from comment
        product_url = None
        url_match = re.search(r"<!-- origin_url: (.*?) -->", content[:1000])
        if url_match:
            product_url = url_match.group(1)

        soup = BeautifulSoup(content, 'html.parser')
        
        filename = os.path.basename(filepath)

        # Extract Categories
        categories = []
        
        # Method 1: Try .bc_nav (Breadcrumbs) - Preferred for readable names and hierarchy
        bc_nav = soup.select_one('.bc_nav')
        if bc_nav:
            # Typically first link is "Slevy", we might want to skip it or keep it?
            # Example: Slevy > Oblečení a obuv > Spodní prádlo and plavky
            # We want ['Oblečení a obuv', 'Spodní prádlo a plavky']
            links = bc_nav.select('a')
            for link in links:
                text = link.get_text(strip=True)
                if text and text != "Slevy":
                    categories.append(text)
        
        # Method 2: Fallback to advSection variable (Slugs)
        if not categories:
            adv_match = re.search(r"var advSection\s*=\s*'([^']+)'", content)
            if adv_match:
                path = adv_match.group(1)
                # /category/subcategory/slevy -> ['category', 'subcategory']
                parts = [p for p in path.split('/') if p and p != 'slevy']
                categories = [p.capitalize() for p in parts]

        if filename.startswith('sleva_'):
            # It's a detail page - List View
            name_elem = soup.select_one('h1')
            name = name_elem.get_text(strip=True) if name_elem else "Unknown Product"
            
            img_elem = soup.select_one('.product_image img, .pd_image img')
            image_url = None
            if img_elem:
                image_url = img_elem.get('src')
            
            # Try to extract brand from JSON-LD
            brand = None
            try:
                ld_script = soup.find('script', {'type': 'application/ld+json'})
                if ld_script:
                    data = json.loads(ld_script.string)
                    
                    product_data = None
                    if isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'Product':
                                product_data = item
                                break
                    elif isinstance(data, dict):
                        if data.get('@type') == 'Product':
                            product_data = data
                            
                    if product_data:
                        raw_brand = product_data.get('brand')
                        if isinstance(raw_brand, dict):
                            brand = raw_brand.get('name')
                        elif isinstance(raw_brand, str):
                            brand = raw_brand
            except Exception:
                pass

            offers = self.parse_list_row_offers(soup)
            
            return [{
                'name': name,
                'brand': brand,
                'product_url': product_url,
                'image_url': image_url,
                'categories': categories,
                'prices': offers
            }]
            
        elif filename.startswith('slevy_'):
            # It's a category page - Grid View
            discount_divs = soup.select('.log_discount')
            products = []
            for div in discount_divs:
                parsed = self.parse_grid_item(div)
                if parsed:
                    products.append({
                        'name': parsed['name'],
                        'brand': None,
                        'image_url': parsed['image_url'],
                        'categories': categories,
                        'prices': parsed['offers']
                    })
            return products
        
        return []

    def run(self, console=None):
        # Recursively find all html and html.gz files
        files = glob.glob(os.path.join(self.data_dir, '**', '*.html*'), recursive=True)
        # Filter for specifically .html or .html.gz just in case
        files = [f for f in files if f.endswith('.html') or f.endswith('.html.gz')]
        
        total_files = len(files)
        print(f"Found {total_files} files to parse.")
        
        # Parallel Processing
        # CPU bound mostly (parsing), but some IO.
        print(f"Starting parsing sequentially...")
        
        processed_count = 0
        product_map = {}
        total_prices_count = 0
        
        # Use passed console or create basic one if None
        if console:
            console.total = total_files
            console.update(0, "Init...")
        
        for f in files:
            processed_count += 1
            
            try:
                parsed_items = self.parse_product_file(f)
                if parsed_items:
                    for item in parsed_items:
                        name = item['name']
                        if name not in product_map:
                            product_map[name] = {
                                'name': name,
                                'brand': item.get('brand'),
                                'image_url': item['image_url'],
                                'categories': item.get('categories', []),
                                'prices': []
                            }
                        
                        existing = product_map[name]
                        
                        # Merge product_url
                        if not existing.get('product_url') and item.get('product_url'):
                            existing['product_url'] = item['product_url']

                        # Merge brand
                        if not existing.get('brand') and item.get('brand'):
                            existing['brand'] = item['brand']
                        
                        # Merge image
                        if not existing['image_url'] and item['image_url']:
                            existing['image_url'] = item['image_url']
                            
                        # Merge categories (if existing is empty)
                        if not existing.get('categories') and item.get('categories'):
                            existing['categories'] = item['categories']

                        # Merge prices
                        for new_price in item['prices']:
                            is_duplicate = False
                            for p in existing['prices']:
                                ids_both_present = new_price.get('discount_id') and p.get('discount_id')
                                
                                if ids_both_present:
                                    if new_price['discount_id'] == p['discount_id']:
                                        is_duplicate = True
                                        break
                                else:
                                    # Fallback to loose check if IDs are missing
                                    if (p['store_name'] == new_price['store_name'] and 
                                        p['price'] == new_price['price']):
                                        is_duplicate = True
                                        break
                            
                            if not is_duplicate:
                                existing['prices'].append(new_price)
                                total_prices_count += 1
            except Exception:
                pass
            
            if console:
                stats = f"Prod: {len(product_map)} | Price: {total_prices_count}"
                console.update(processed_count, stats)
        
        self.products = list(product_map.values())
        print(f"Parsed {len(self.products)} unique products.")
        
        # Collect all unique store names and categories with counts
        store_counts = Counter()
        category_counts = Counter()
        brand_counts = Counter()
        
        for p in self.products:
            # Categories
            cats = p.get('categories', [])
            for c in cats:
                category_counts[c] += 1
                
            # Brands
            if p.get('brand'):
                brand_counts[p['brand']] += 1
                
            # Stores - count unique stores for this product once? 
            # Or count total offers per store? 
            # "value being number of products for that store" => Number of products available in that store.
            # So if a product has 3 offers from Albert, it counts as 1 product for Albert.
            
            product_stores = set()
            for price_item in p.get('prices', []):
                s_name = price_item.get('store_name')
                if s_name and s_name != "Unknown":
                    product_stores.add(s_name)
            
            for s in product_stores:
                store_counts[s] += 1
        
        output_data = {
            "products": self.products,
            "metadata": {
                "total_products": len(self.products),
                "generated_at": datetime.now().isoformat(),
                "stores": dict(sorted(store_counts.items(), key=lambda item: item[1], reverse=True)),
                "categories": dict(sorted(category_counts.items(), key=lambda item: item[1], reverse=True)),
                "brands": dict(sorted(brand_counts.items(), key=lambda item: item[1], reverse=True))
            }
        }

        output_path = 'data/kupi.result.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"Data saved to {output_path}")
