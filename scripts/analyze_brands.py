
import json
import os
import glob
from collections import Counter
import re

def analyze_brands():
    data_dir = "data"
    all_brands = Counter()
    missing_brands_candidates = Counter()
    
    files = glob.glob(os.path.join(data_dir, "*.result.json"))
    
    # Simple regex to catch potential Capitalized words at start of string
    # e.g. "Coca-Cola Zero" -> "Coca-Cola"
    brand_pattern = re.compile(r"^([A-ZÅ-Ž][a-zå-ž]+(?:\s+[A-ZÅ-Ž][a-zå-ž]+)*)")

    total_products = 0
    products_with_brand = 0

    print(f"Analyzing {len(files)} files...")

    for filepath in files:
        with open(filepath, 'r') as f:
            try:
                data = json.load(f)
                products = data.get("products", [])
                
                for p in products:
                    total_products += 1
                    brand = p.get("brand")
                    name = p.get("name", "")
                    
                    if brand:
                        all_brands[brand] += 1
                        products_with_brand += 1
                    else:
                        # Heuristic: First 1-2 capitalized words might be a brand
                        # Excluding common generic words (simplified check)
                        match = brand_pattern.match(name)
                        if match:
                            candidate = match.group(1)
                            # Filter out single words that are likely generic if they appear too often in non-brand context?
                            # For now just collect all
                            if len(candidate) > 2: # Ignore 2 letter words
                                missing_brands_candidates[candidate] += 1
            except Exception as e:
                print(f"Error reading {filepath}: {e}")

    print(f"Total Products: {total_products}")
    print(f"With Brand: {products_with_brand} ({products_with_brand/total_products*100:.1f}%)")
    
    print("\nTop 50 Existing Brands:")
    for b, c in all_brands.most_common(50):
        print(f"{b}: {c}")

    print("\nTop 100 Potential Missing Brands (Capitalized start of name):")
    # Filter known brands from candidates to see what's truly missing/unrecognized
    known_set = set(all_brands.keys())
    
    filtered_candidates = []
    for cand, count in missing_brands_candidates.most_common(200):
        # weak check: if candidate is a substring of a known brand, might be valid logic failure
        # or if it's completely new.
        if cand not in known_set:
            filtered_candidates.append((cand, count))
            
    for b, c in filtered_candidates[:100]:
        print(f"{b}: {c}")

if __name__ == "__main__":
    analyze_brands()
