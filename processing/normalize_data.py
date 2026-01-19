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

# Global unit registry
ureg = pint.UnitRegistry()
# Configure ureg to be case-insensitive if needed, or handle variations manually
# Common variations in Czech input
ureg.define('kus = count = ks = piece = pc = stk')

def normalize_base_unit(price):
    """
    Phase 1: Normalize units to base (kg, l, ks) and scale unit_price.
    Returns True if changed.
    """
    unit_str = (price.get('unit') or '').lower().strip()
    u_price = price.get('unit_price')
    
    if not unit_str or not u_price:
        return False

    try:
        # Clean up unit string
        clean_unit_str = unit_str.replace(',', '.')
        
        # Parse using pint
        qty = ureg(clean_unit_str)
        
        new_unit = None
        scale_factor = 1.0
        
        if qty.check('[mass]'):
            base_qty = qty.to('kg')
            new_unit = 'kg'
            if base_qty.magnitude > 0:
                scale_factor = 1.0 / base_qty.magnitude
                
        elif qty.check('[volume]'):
            base_qty = qty.to('liter')
            new_unit = 'l'
            if base_qty.magnitude > 0:
                scale_factor = 1.0 / base_qty.magnitude
                
        elif qty.check('count') or unit_str in ['ks', 'kus', 'piece', 'pc', 'stk']:
             new_unit = 'ks'
             # Normalization for count is usually 1:1 unless specific "10ks" unit string
             if getattr(qty, 'units', None) == ureg.count or qty.dimensionless:
                 if qty.magnitude > 0:
                     scale_factor = 1.0 / qty.magnitude
        
        if new_unit and new_unit != unit_str:
             price['unit'] = new_unit
             price['unit_price'] = round(u_price * scale_factor, 2)
             return True
             
    except Exception:
        pass
        
    return False

def compute_missing_size(price):
    """
    Phase 2: Compute Missing Package Size using Price / Unit_Price.
    Returns True if computed.
    """
    p_val = price.get('price')
    u_price = price.get('unit_price')
    pkg_size_str = price.get('package_size')
    unit_str = (price.get('unit') or '')

    if (not pkg_size_str) and p_val and u_price and unit_str:
         try:
             amount = round(p_val / u_price, 2)
             # Format: "0.5 kg", "1.25 l" - dropped trailing zeros via :g
             new_size = f"{amount:g} {unit_str}"
             price['package_size'] = new_size
             price['notes'] = (price.get('notes', '') + " Size calc from price/unit").strip()
             return True
         except Exception:
             pass
    return False

def compute_missing_price(price):
    """
    Phase 3: Compute Missing Price from Package Size * Unit Price.
    Returns True if computed.
    """
    p_val = price.get('price')
    u_price = price.get('unit_price')
    pkg_size_str = price.get('package_size')
    unit_str = (price.get('unit') or '').lower()

    if (p_val is None or p_val == 0) and u_price and pkg_size_str:
        try:
            clean_size = pkg_size_str.replace(',', '.').strip()
            quantity = ureg(clean_size)
            
            qty_base = 0
            
            if unit_str in ['kg', 'kilogram']:
                 if quantity.check('[mass]'):
                     qty_base = quantity.to('kg').magnitude
            elif unit_str in ['l', 'liter', 'litr']:
                if quantity.check('[volume]'):
                    qty_base = quantity.to('liter').magnitude
            elif unit_str in ['ks', 'kus', 'piece', 'pc']:
                 if quantity.check('count') or quantity.dimensionless:
                      if getattr(quantity, 'units', None) == ureg.count:
                          qty_base = quantity.to('count').magnitude
                      else:
                          qty_base = quantity.magnitude
            
            if qty_base > 0:
                calc_price = float(u_price * qty_base)
                price['price'] = round(calc_price, 2)
                price['notes'] = (price.get('notes', '') + " Price calc from unit").strip()
                return True
                
        except Exception:
            pass
    return False

def normalize_data(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Track stats
    fixed_price_count = 0
    fixed_size_count = 0
    normalized_count = 0

    total_products = len(data.get('products', []))
    print(f"Loading {total_products} products form {input_file}...")

    for product in data.get('products', []):
        for price in product.get('prices', []):
            
            # Phase 1: Normalize base unit
            if normalize_base_unit(price):
                normalized_count += 1
            
            # Phase 2: Compute missing package size
            if compute_missing_size(price):
                fixed_size_count += 1
                
            # Phase 3: Compute missing price
            if compute_missing_price(price):
                fixed_price_count += 1

    print(f"Stats: Normalized {normalized_count} units, Fixed {fixed_size_count} sizes, Fixed {fixed_price_count} prices.")

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
    input_path = args.input
    if not input_path.endswith('.json'):
        input_path = f"{args.data_dir}/*.{args.input}.json"
        import glob
        files = glob.glob(input_path)
        if not files:
             print(f"No files found for pattern {input_path}")
             sys.exit(1)
        for f in files:
             filename = f.split('/')[-1]
             basename = filename.replace(f'.{args.input}.json', '')
             output_file = f"{args.data_dir}/{basename}.{args.output}.json"
             normalize_data(f, output_file)
    else:
        # Direct file processing if full path provided
        files = glob.glob(f"{args.data_dir}/*.{args.input}.json")
        if not files:
            print(f"No input files found for suffix '.{args.input}.json' in {args.data_dir}")
            sys.exit(0)

        for input_file in files:
            filename = input_file.split('/')[-1]
            basename = filename.replace(f'.{args.input}.json', '')
            output_file = f"{args.data_dir}/{basename}.{args.output}.json"
            normalize_data(input_file, output_file)
