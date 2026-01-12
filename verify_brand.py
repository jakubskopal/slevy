import json
import os

def verify():
    if not os.path.exists('output.json'):
        print("output.json not found yet.")
        return

    try:
        with open('output.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        products = data.get('products', [])
        total = len(products)
        branded = [p for p in products if p.get('brand')]
        branded_count = len(branded)
        
        print(f"Total Products: {total}")
        print(f"Products with Brand: {branded_count}")
        if total > 0:
            print(f"Brand Coverage: {branded_count/total*100:.2f}%")
        
        if branded_count > 0:
            print("\nSample Brands found:")
            brands = sorted(list(set(p['brand'] for p in branded if p['brand'])))
            for b in brands[:20]:
                print(f" - {b}")
                
            print(f"\nTotal unique brands: {len(brands)}")
        else:
            print("\nNO BRANDS FOUND.")
            
    except Exception as e:
        print(f"Error reading/parsing output.json: {e}")

if __name__ == "__main__":
    verify()
