import argparse
import glob
import json
import os

FOOD_KEYWORDS = [
    "potraviny",
    "ovoce", "zelenina", "bylinky", "houby",
    "maso", "ryby", "drůbež", "uzeniny", "šunka", "salám", "klobás", "párky", "paštiky",
    "mléč", "sýr", "jogurt", "tvaroh", "máslo", "tuky", "vejce", "smetan",
    "pečivo", "pekárn", "chléb", "chleb", "rohlík", "koláč", "bábovk", "baget",
    "trvanlivé", "konzerv", "zavař", "džem", "med", "sirup",
    "vaření", "pečení", "těstoviny", "rýže", "luštěniny", "mouka", "cukr", "sůl", "olej", "ocet", "koření",
    "lahůdky", "pomazán", "salát",
    "mražené", "zmrzlin", "hotová jídla", "polotovary", "pizza",
    "zdravá výživa", "speciální výživa", "cereálie", "müsli", "kaše",
    "naplňte svou ledničku"
]

NON_FOOD_KEYWORDS = [
    "krmivo", "zvířata", "psi", "kočky", "pes", "kočka", "mazlíčci",
    "drogerie", "kosmetika", "hygiena", "domácnost", "úklid", "papír", "tablety", "ubrousky",
    "sladkosti", "cukrovinky", "bonbony", "čokoláda", "oplatky", "sušenky",
    "protein", "čajové", "sladké"
]

def is_food_category(category_path):
    # category_path is often a list of strings in the JSON (e.g. ["Potraviny", "Mléčné výrobky"])
    # or sometimes a single string. Let's handle both or assume a joined string.
    # The browser code effectively checks if ANY part of the category string path matches.
    
    if isinstance(category_path, list):
        # Join them to check the whole path context? Or check each?
        # The browser code takes `category: string`.
        # Let's assume we check the full path string.
        category_str = " ".join(category_path)
    else:
        category_str = str(category_path)

    lower = category_str.lower()

    # Check exclusion first
    if any(kw in lower for kw in NON_FOOD_KEYWORDS):
        return False

    # Check inclusion
    return any(kw in lower for kw in FOOD_KEYWORDS)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="result", help="Suffix for input files (e.g., 'result' for *.result.json)")
    parser.add_argument("--output", default="processed", help="Suffix for output files (e.g., 'processed' for *.processed.json)")
    parser.add_argument("--data-dir", default="data", help="Directory containing data files")
    args = parser.parse_args()

    input_suffix = f".{args.input}.json"
    output_suffix = f".{args.output}.json"
    
    files = glob.glob(os.path.join(args.data_dir, f"*{input_suffix}"))
    print(f"Found {len(files)} input files with suffix '{input_suffix}' in {args.data_dir}")

    for input_file in files:
        # Determine output filename
        # e.g. data/kupi.result.json -> data/kupi.processed.json
        # We replace the LAST occurrence of the input suffix
        base_name = input_file[:-len(input_suffix)]
        output_file = f"{base_name}{output_suffix}"
        
        print(f"Processing {input_file} -> {output_file}")
        
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # We expect a list of products
        # But wait, looking at generate_index.py and general usage, the result.json might be a list of product objects.
        # Let's verify structure. The browser/src/utils/categories.ts logic applies to a "category" string.
        # We need to know where the category is in the product object.
        # Usually it's in `category` field which might be a list.
        
        filtered_products = []
        skipped_count = 0
        
        # Determine if data is a list or dict with a key
        products = data
        if isinstance(data, dict) and "products" in data:
            products = data["products"]
        
        if not isinstance(products, list):
            print(f"  Warning: {input_file} does not contain a list of products. Skipping.")
            continue

        for p in products:
            # We assume 'categories' field exists (plural)
            cat = p.get("categories", [])
            # Also check 'name' sometimes? The browser logic is `isFoodCategory` which implies checking category names.
            
            if is_food_category(cat):
                filtered_products.append(p)
            else:
                skipped_count += 1
        
        # Save output
        # If the input was a dict wrapper, we might want to preserve it?
        # For now, let's write out the list or the same structure if possible.
        # If simple list:
        output_data = filtered_products
        
        # If it was a wrapper dict, we should probably preserve wrapper but update products list
        if isinstance(data, dict) and "products" in data:
            output_data = data.copy()
            output_data["products"] = filtered_products
            
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
            
        print(f"  Kept {len(filtered_products)} products, removed {skipped_count}.")

if __name__ == "__main__":
    main()
