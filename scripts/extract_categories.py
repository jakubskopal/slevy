import json
import glob
import os

def main():
    files = glob.glob("data/*.result.json")
    print(f"Found {len(files)} result files.")

    for fpath in files:
        store = os.path.basename(fpath).split('.')[0]
        print(f"\n--- {store.upper()} ---")
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                products = data.get('products', [])
                
                # Extract root categories
                roots = set()
                for p in products:
                    cats = p.get('categories', [])
                    if cats:
                        roots.add(cats[0])
                
                # Sort and print
                for r in sorted(roots):
                    print(f"- {r}")
                    
        except Exception as e:
            print(f"Error reading {fpath}: {e}")

if __name__ == "__main__":
    main()
