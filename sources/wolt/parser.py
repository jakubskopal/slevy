#!/usr/bin/env python3
"""
Albert Parser: Extracts product data from gzipped HTML files.
"""
from datetime import datetime
from collections import Counter
import os
import glob
import json

try:
    from .parser_product import parse_product_file
except ImportError:
    from parser_product import parse_product_file



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

    # Methods moved to parser_product.py


    def run(self, workers=None, limit=None):
        import concurrent.futures
        import multiprocessing

        if workers is None:
            workers = max(1, multiprocessing.cpu_count() // 2)

        files = glob.glob(os.path.join(self.data_dir, '*.html.gz'))
        if limit:
            files = files[:limit]
            
        total_files = len(files)
        if self.console:
             log_func = self.console.log
        else:
             log_func = print

        log_func(f"Found {len(glob.glob(os.path.join(self.data_dir, '*.html.gz')))} total files in {self.data_dir}, processing {total_files} (using {workers} workers)")
        
        product_map = {}
        
        if self.console and self.console.total == 0:
             self.console.total = total_files

        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
            # Submit all files for parsing
            future_to_file = {executor.submit(parse_product_file, f, self.store_name): f for f in files}
            
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

        # Metadata Aggregation
        brands = Counter()
        categories = Counter()
        stores = Counter()

        # Re-iterate product map to aggregate metadata (safe in main thread)
        for product in product_map.values():
             if product.get('brand'):
                 brands[product['brand']] += 1

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

                "brands": dict(sorted(brands.items()))
            }
        }

        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        if self.console:
            self.console.log(f"Saved to {self.output_path}")
        else:
            print(f"Saved to {self.output_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", help="Store to parse (albert, billa, globus)")
    parser.add_argument("--limit", type=int, help="Limit number of files to process")
    args = parser.parse_args()
    
    if args.store and args.store in VENUES:
        c = VENUES[args.store]
        parser = WoltParser(c["dir"], c["name"], c["output"])
        parser.run(limit=args.limit)
    else:
        print("Available stores:", list(VENUES.keys()))
