
import gzip
import re
import os
import sys
from bs4 import BeautifulSoup

def extract_prices(filepath):
    try:
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return None

    soup = BeautifulSoup(content, 'html.parser')
    modal = soup.select_one('[data-test-id="product-modal"]')
    if not modal:
        return None

    data = {}
    selectors = [
        "product-modal.price",
        "product-modal.discounted-price",
        "product-modal.original-price",
        "product-modal.total-price",
        "product-modal.unit-price"
    ]
    
    for sel in selectors:
        elem = modal.select_one(f'[data-test-id="{sel}"]')
        data[sel] = elem.get_text(strip=True) if elem else "N/A"
    
    return data

def main():
    import argparse
    import glob
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str, default='data/albert_raw', help="Directory with gzipped HTML files")
    args = parser.parse_args()

    files = glob.glob(os.path.join(args.dir, '*.html.gz'))
    if not files:
        print("No files found.")
        return

    results = []
    seen = set()
    
    for f in files:
        prices = extract_prices(f)
        if prices:
            # Create a tuple of the prices to check for uniqueness
            price_tuple = tuple(prices[sel] for sel in sorted(prices.keys()))
            if price_tuple not in seen:
                results.append(prices)
                seen.add(price_tuple)
        
        if len(results) >= 100: # Limit to 100 unique representative rows for the table
            break

    # Sort results to group similar things
    results.sort(key=lambda x: (x.get("product-modal.discounted-price") == "N/A", x.get("product-modal.price")))

    print("| Price | Discounted | Original | Total | Unit Price |")
    print("|-------|------------|----------|-------|------------|")
    for r in results:
        print(f"| {r['product-modal.price']} | {r['product-modal.discounted-price']} | {r['product-modal.original-price']} | {r['product-modal.total-price']} | {r['product-modal.unit-price']} |")

if __name__ == "__main__":
    main()
