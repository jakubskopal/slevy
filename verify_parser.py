from parser import KupiParser
import glob
import json
import os

def test():
    p = KupiParser()
    # Find one list view and one grid view file
    list_files = glob.glob("data/raw/**/sleva_*.gz", recursive=True)[:2]
    grid_files = glob.glob("data/raw/**/slevy_*.gz", recursive=True)[:2]
    
    files = list_files + grid_files
    print(f"Testing on {len(files)} files...")
    
    results = []
    for f in files:
        print(f"Parsing {f}...")
        res = p.parse_product_file(f)
        results.extend(res)
        
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    # Validation
    for item in results:
        print(f"\nProduct: {item['name']}")
        print(f"Categories: {item.get('categories')}")
        if not item.get('categories'):
             print("WARNING: No categories found")
             
        for price in item['prices']:
            pid = price.get('product_id')
            sid = price.get('shop_id')
            pct = price.get('discount_pct')
            orig = price.get('original_price')
            print(f"  - Store: {price['store_name']}")
            print(f"    IDs: Product={pid}, Shop={sid}")
            print(f"    Price: {price['price']} (Org: {orig}, Pct: {pct}%)")
            
            if not pid: print("    WARNING: Missing Product ID")
            if not pct and not orig: print("    NOTE: No discount info (might be normal)")

if __name__ == "__main__":
    test()
