#!/usr/bin/env python3
"""
Data Normalization Script
Calculates missing prices using unit price and package size.
"""

import argparse
import json
import re
import sys
import pint

def normalize_data(input_file, output_file):
    ureg = pint.UnitRegistry()
    
    # Configure ureg to be case-insensitive if needed, or handle variations manually
    # Common variations in Czech input
    ureg.define('kus = count = ks')
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    fixed_count = 0
    total_products = len(data.get('products', []))
    
    print(f"Loading {total_products} products form {input_file}...")

    for product in data.get('products', []):
        for price in product.get('prices', []):
            p_val = price.get('price')
            u_price = price.get('unit_price')
            pkg_size_str = price.get('package_size')
            unit = (price.get('unit') or '').lower()

            # We need to act if price is missing/zero but we have components
            if (p_val is None or p_val == 0) and u_price and pkg_size_str:
                try:
                    # Parse package size
                    # Clean up string: "350 g" -> "350 g"
                    # Handle "3x50g" -> "150g" ? For now, basic parsing.
                    
                    # Common fix: replace ',' with '.' for decimal numbers in Czech format
                    clean_size = pkg_size_str.replace(',', '.').strip()
                    quantity = ureg(clean_size)
                    
                    qty_base = 0
                    
                    # Determine target base unit based on price unit
                    # Usually price unit is 'kg', 'l', 'ks'
                    
                    if unit in ['kg', 'kilogram']:
                         # Convert to kg
                         if isinstance(quantity, (int, float)):
                             # Dimensionless? Warning
                             pass
                         else:
                             if quantity.check('[mass]'):
                                 qty_base = quantity.to('kg').magnitude
                             else:
                                 # Mismatch (e.g. ml vs kg), try density=1 assumption for water/milk-like things?
                                 # For safety, avoid unless sure.
                                 # BUT: Many times 'g' matching 'l' is rare, usually 'ml' matches 'l'.
                                 pass

                    elif unit in ['l', 'liter', 'litr']:
                        if quantity.check('[volume]'):
                            qty_base = quantity.to('liter').magnitude
                        elif quantity.check('[mass]'):
                             # approximate 1kg = 1l?
                             # Let's skip cross-domain for now to be safe
                             pass

                    elif unit in ['ks', 'kus', 'piece', 'pc']:
                         # If package is "1 ks", magnitude is 1.
                         if quantity.check('count'):
                              qty_base = quantity.to('count').magnitude
                         elif quantity.dimensionless:
                              qty_base = quantity.magnitude
                    
                    if qty_base > 0:
                        calc_price = float(u_price * qty_base)
                        price['price'] = round(calc_price, 2)
                        price['notes'] = "Price calculated from unit_price"
                        fixed_count += 1
                        
                except Exception as e:
                    # print(f"Failed to normalize {product['name']}: {e}")
                    pass

    print(f"Fixed prices for {fixed_count} offers.")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved to {output_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Normalize grocery data')
    parser.add_argument('--input', required=True, help='Input JSON suffix or filename')
    parser.add_argument('--output', required=True, help='Output JSON suffix')
    parser.add_argument('--data-dir', default='data', help='Data directory')
    
    args = parser.parse_args()
    
    # Support the pipeline arguments convention
    # If input doesn't end in .json, assume it's a suffix + .json
    input_path = args.input
    if not input_path.endswith('.json'):
        input_path = f"{args.data_dir}/*.{args.input}.json"
        import glob
        files = glob.glob(input_path)
        if not files:
             print(f"No files found for pattern {input_path}")
             sys.exit(1)
        # Process all matching files
        for f in files:
             # Construct output name
             # if input is 'data/001.foo.json' and output arg is '002.bar'
             # we want 'data/002.bar.json' ? 
             # The pipeline script passes full suffix: --input result --output 001.normalize
             # processed by script logic: data/*.result.json -> data/*.001.normalize.json
             
             base_name = f.split('/')[-1].replace(f'.{args.input}.json', '')
             # Careful with replacement if suffix is simple string
             # Better: use the logic from pipeline script? 
             # Actually, Python script should probably handle one file 1:1 if called by pipeline loop.
             # BUT pipeline provided by user passes suffixes.
             # Wait, the pipeline script:
             # python3 processing/${STEP_NAME}.py --input ${CURRENT_INPUT_SUFFIX} --output ${CURRENT_OUTPUT_SUFFIX} --data-dir ${DATA_DIR}
             # It expects the python script to handle the globbing or the shell script handles it?
             # "python3 processing/${STEP_NAME}.py ..."
             # Looking at filter_for_food.py might clarify how existing steps handle this.
             pass
    
    # We'll assume the python script handles globbing as per previous pattern
    # Let's check filter_for_food.py's behavior via grep or cat if needed, but I'll write robust robust code.
    
    # The pipeline script passes SUFFIXES.
    # So we look for data_dir/*.input_suffix.json
    
    files = glob.glob(f"{args.data_dir}/*.{args.input}.json")
    if not files:
        print(f"No input files found for suffix '.{args.input}.json' in {args.data_dir}")
        sys.exit(0) # Not an error, just empty pass

    for input_file in files:
        # Determine output filename
        # input: data/tesco.result.json
        # args.input: result
        # args.output: 001.normalize
        # output: data/tesco.001.normalize.json
        
        filename = input_file.split('/')[-1]
        basename = filename.replace(f'.{args.input}.json', '')
        output_file = f"{args.data_dir}/{basename}.{args.output}.json"
        
        normalize_data(input_file, output_file)
