#!/usr/bin/env python3
"""
Remove Expired Offers
Filters out price offers where 'validity_end' is in the past.
"""

import argparse
import json
import glob
import sys
from datetime import datetime

def remove_expired_offers(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle different root structures (list vs dict)
    products = []
    if isinstance(data, list):
        products = data
    elif isinstance(data, dict) and 'products' in data:
        products = data['products']
    else:
        print(f"Warning: Unexpected data structure in {input_file}")
        return

    now = datetime.now()
    # Normalize to date only for comparison if needed, or keep full timestamp.
    # Schema says validity_end is ISO 8601 date (string).
    # e.g. "2023-12-31" or "2023-12-31T23:59:59"
    
    total_cleaned = 0
    total_removed_prices = 0

    for product in products:
        valid_prices = []
        original_count = len(product.get('prices', []))
        
        for price in product.get('prices', []):
            validity_end_str = price.get('validity_end')
            
            if not validity_end_str:
                # No expiry date, assume valid
                valid_prices.append(price)
                continue
                
            try:
                # Attempt to parse ISO date
                # Handle both full datetime and just date
                if 'T' in validity_end_str:
                    expiry_dt = datetime.fromisoformat(validity_end_str)
                else:
                    expiry_dt = datetime.fromisoformat(validity_end_str).replace(hour=23, minute=59, second=59)
                
                if expiry_dt >= now:
                    valid_prices.append(price)
                else:
                    total_removed_prices += 1
                    
            except ValueError:
                # Failed to parse, assume valid to be safe or log warning
                # print(f"Warning: Could not parse validity_end '{validity_end_str}'")
                valid_prices.append(price)
        
        if len(valid_prices) < original_count:
            total_cleaned += 1
            
        product['prices'] = valid_prices

    print(f"Processed {len(products)} products. Removed {total_removed_prices} expired prices from {total_cleaned} products.")

    # Preserve structure
    output_data = data
    if isinstance(data, dict) and 'products' in data:
        output_data['products'] = products
    else:
        output_data = products

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"Saved to {output_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Remove expired price offers')
    parser.add_argument('--input', required=True, help='Input JSON suffix')
    parser.add_argument('--output', required=True, help='Output JSON suffix')
    parser.add_argument('--data-dir', default='data', help='Data directory')
    
    args = parser.parse_args()
    
    # Pipeline support logic (standard across processing scripts)
    input_pattern = f"{args.data_dir}/*.{args.input}.json"
    files = glob.glob(input_pattern)
    
    if not files:
        print(f"No files found for pattern {input_pattern}")
        sys.exit(0) # Exit 0 to not break pipeline if just no files match
        
    for f in files:
        filename = f.split('/')[-1]
        basename = filename.replace(f'.{args.input}.json', '')
        output_file = f"{args.data_dir}/{basename}.{args.output}.json"
        
        print(f"Processing {f} -> {output_file}")
        remove_expired_offers(f, output_file)
