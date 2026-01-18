import argparse
import glob
import json
import os
import hashlib

def build_category_tree(products):
    """
    Builds a hierarchical category tree from a list of products.
    Each product has a 'categories' list of strings (breadcrumb).
    
    Returns a list of root nodes.
    Node structure:
    {
        "id": "e5b7h... (last 16 chars of sha256 of full path)",
        "name": "Category Name",
        "count": 123,
        "children": [ ... nodes ... ]
    }
    """
    
    # helper to generate id
    def generate_id(path):
        path_str = "/".join(path)
        full_hash = hashlib.sha256(path_str.encode('utf-8')).hexdigest()
        return full_hash[-16:]

    # Helper to create a new node
    def new_node(name, path):
        return {
            "id": generate_id(path),
            "name": name, 
            "count": 0, 
            "children_map": {}
        }

    root_map = {} # Map of name -> node (with children_map)
    
    # Memoize ID generation to avoid re-hashing
    # path_tuple -> id
    id_cache = {}

    for p in products:
        cats = p.get('categories')
        if not cats:
            continue
            
        current_level = root_map
        current_path = []
        product_cat_ids = []
        
        for i, cat_name in enumerate(cats):
            current_path.append(cat_name)
            path_tuple = tuple(current_path)
            
            # Get or generate ID
            if path_tuple in id_cache:
                cat_id = id_cache[path_tuple]
            else:
                cat_id = generate_id(current_path)
                id_cache[path_tuple] = cat_id
            
            product_cat_ids.append(cat_id)
            
            if cat_name not in current_level:
                # We need to recreate the node if it's new (use the ID we just got)
                node = {
                    "id": cat_id,
                    "name": cat_name,
                    "count": 0,
                    "children_map": {}
                }
                current_level[cat_name] = node
            
            node = current_level[cat_name]
            node["count"] += 1
            
            # Prepare for next iteration
            current_level = node["children_map"]
        
        # Assign IDs to product
        p['category_ids'] = product_cat_ids

    # Convert the map-based tree to the list-based output format
    def convert_to_list(level_map):
        # Sort by name for consistency? Or by count?
        # Alphabetical by name seems standard for UI.
        
        # Sort keys
        sorted_keys = sorted(level_map.keys()) # locale sorting would be better but standard sort is okay for now
        
        result_list = []
        for key in sorted_keys:
            node_data = level_map[key]
            
            # Recurse
            children_list = convert_to_list(node_data["children_map"])
            
            # Build final node object
            final_node = {
                "id": node_data["id"],
                "name": node_data["name"],
                "count": node_data["count"],
                "children": children_list
            }
            result_list.append(final_node)
            
        return result_list

    return convert_to_list(root_map)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="processed", help="Suffix for input files")
    parser.add_argument("--output", default="processed", help="Suffix for output files (default: overwrite input)")
    parser.add_argument("--data-dir", default="data", help="Directory containing data files")
    args = parser.parse_args()

    input_suffix = f".{args.input}.json"
    output_suffix = f".{args.output}.json"
    
    files = glob.glob(os.path.join(args.data_dir, f"*{input_suffix}"))
    print(f"Found {len(files)} input files with suffix '{input_suffix}' in {args.data_dir}")

    for input_file in files:
        # Determine output filename
        if input_file.endswith(input_suffix):
             base_name = input_file[:-len(input_suffix)]
        else:
             base_name = input_file.replace(input_suffix, "")
             
        output_file = f"{base_name}{output_suffix}"
        
        print(f"Processing {input_file} ...")
        
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            products = []
            if isinstance(data, dict):
                products = data.get("products", [])
            elif isinstance(data, list):
                products = data
                # If it's a list, we can't easily add metadata unless we wrap it.
                # The schema says top level is object with products and metadata.
                # So we should upgrade it if it's a list.
                data = {"products": products, "metadata": {}}
            
            print(f"  Building category tree for {len(products)} products...")
            category_tree = build_category_tree(products)
            
            # Ensure metadata exists
            if "metadata" not in data:
                data["metadata"] = {}
                
            data["metadata"]["categories"] = category_tree
            
            # Also ensure other metadata fields are present if we converted from list
            if "total_products" not in data["metadata"]:
                data["metadata"]["total_products"] = len(products)
            
            print(f"  Saving to {output_file}...")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"  Error processing {input_file}: {e}")

if __name__ == "__main__":
    main()
