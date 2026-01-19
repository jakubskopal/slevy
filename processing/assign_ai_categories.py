
import json
import re
import argparse
import glob
import os

def assign_findings(product, source):
    """
    Assigns 'findings' tags based on strict, expert-verified category paths.
    Currently only identifies 'egg'.
    """
    findings = []
    cats = product.get('categories', [])
    name = product.get('name', '').lower()
    
    # helper for safe access
    def get_cat(idx):
        return cats[idx] if len(cats) > idx else ""

    if 'hovězí' in name.lower() and 'uzené' not in name.lower():
         pass # Debug print removed


    # GLOBAL EXCLUSION: Quail Eggs (křepelčí)
    if 'křepelčí' in name:
        return []

    # Rule: Fresh Eggs
    is_egg = False
    
    if source == 'albert':
        # Path: MLÉČNÉ A CHLAZENÉ -> VEJCE A DROŽDÍ
        if 'VEJCE A DROŽDÍ' in cats:
            if 'droždí' not in name:
                is_egg = True
            
    elif source == 'tesco':
        # Path: Mléčné, vejce a margaríny -> Vejce a droždí -> Vejce
        if get_cat(2) == 'Vejce':
            is_egg = True

    elif source == 'kupi':
        # Path containing 'Vejce' (Level 1 in Kupi usually 'Mléčné výrobky a vejce', Level 2 'Vejce')
        if 'Vejce' in cats or get_cat(1) == 'Vejce':
            is_egg = True
            
    elif source == 'billa':
        # Path: MLÉČNÉ A CHLAZENÉ -> VEJCE & DROŽDÍ
        # Exclude 'droždí' in name
        if 'VEJCE & DROŽDÍ' in cats:
            if 'droždí' not in name:
                is_egg = True
                
    elif source == 'globus':
        # Path: MLÉČNÉ A CHLAZENÉ -> VEJCE A DROŽDÍ
        if 'VEJCE A DROŽDÍ' in cats:
            if 'droždí' not in name:
                is_egg = True

    if is_egg:
        findings.append('fresh-chicken-eggs')

    # --- FRESH MEAT ---

    # helper for exclusion
    def is_not_fresh_meat(name, cats_str):
        bad_words = ['uzené', 'uzeny', 'uzená', 'marinovan', 'mražen', 'mrazen', 'sušené', 'sušený', 'sušene']
        txt = (name + " " + cats_str).lower()
        return any(w in txt for w in bad_words)

    cats_str = " ".join(cats)
    if is_not_fresh_meat(name, cats_str):
        return findings

    meat_types = set()

    # Helper to analyze ground meat or generic items
    def analyze_meat_content(n):
        types = set()
        n = n.lower()
        if 'hovězí' in n or 'telecí' in n: types.add('beef')
        if 'vepřov' in n: types.add('pork')
        if 'kuřecí' in n or 'krůtí' in n or 'kachn' in n: types.add('poultry')
        return types

    ground_meat_keywords = ['mleté', 'mělněné']
    is_ground = any(k in name.lower() for k in ground_meat_keywords)

    if is_ground:
        detected = analyze_meat_content(name)
        if detected:
             meat_types.update(detected)
        # If ground but no specific meat detected in name, we wait for category to hint,
        # or fallback to 'other' at the end if strict logic needed.

    if source == 'albert':
        # Albert (Wolt) - UPPERCASE
        if 'MASO A RYBY' in cats:
            if 'HOVĚZÍ A TELECÍ' in cats: meat_types.add('beef')
            elif 'VEPŘOVÉ MASO' in cats: meat_types.add('pork')
            elif 'DRŮBEŽ' in cats: meat_types.add('poultry')
            elif 'MLETÉ MASO' in cats:
                 if not meat_types: meat_types.add('other')

    elif source == 'billa':
        # Billa (Wolt) - UPPERCASE
        if 'MASO A UZENINY' in cats:
            if 'HOVĚZÍ MASO' in cats: meat_types.add('beef')
            elif 'VEPŘOVÉ MASO' in cats: meat_types.add('pork')
            elif 'DRŮBEŽ' in cats: meat_types.add('poultry')
            elif 'JINÉ MASO' in cats:
                 if not meat_types: meat_types.add('other')

    elif source == 'globus':
        # Globus (Wolt) - UPPERCASE
        if 'MASO A RYBY' in cats and 'ŘEZNICTVÍ GLOBUS' in cats:
            # Generic
            if not meat_types:
                 detected = analyze_meat_content(name)
                 if detected: meat_types.update(detected)
                 else:
                     if 'zvěřin' in name.lower() or 'králí' in name.lower(): meat_types.add('other')

        # Fallback
        elif 'Maso, drůbež, ryby' in cats: 
             if 'Hovězí a telecí maso' in cats: meat_types.add('beef')
             elif 'Vepřové maso' in cats: meat_types.add('pork')
             elif 'Drůbež' in cats: meat_types.add('poultry')
             elif 'Mleté maso' in cats: 
                  if not meat_types: meat_types.add('other')


    elif source == 'kupi':
        # Kupi
        if 'Maso, uzeniny a ryby' in cats:
            if 'Hovězí maso' in cats: meat_types.add('beef')
            elif 'Vepřové maso' in cats: meat_types.add('pork')
            elif 'Drůbež' in cats: meat_types.add('poultry')
            elif 'Ostatní maso' in cats:
                 if not meat_types: meat_types.add('other')

    elif source == 'tesco':
        # Tesco
        if 'Maso, ryby a uzeniny' in cats or 'Maso a lahůdky' in cats:
             if 'Hovězí a telecí' in cats or 'Hovězí' in cats: meat_types.add('beef')
             elif 'Vepřové' in cats: meat_types.add('pork')
             elif 'Drůbež' in cats: meat_types.add('poultry')
             elif 'Mleté maso' in cats:
                 if not meat_types: meat_types.add('other')
             elif 'Jehněčí a králičí' in cats: meat_types.add('other')
             
             # Fallback
             if not meat_types and ('Maso' in cats or 'Maso, ryby a speciality' in cats):
                 detected = analyze_meat_content(name)
                 if detected: meat_types.update(detected)

    # Final cleanup: If we have multiple types, it's fine.
    # If is_ground is true, but meat_types is empty, default to 'other'?
    if is_ground and not meat_types and not is_not_fresh_meat(name, cats_str):
        # Only if we are sure it's fresh meat context.
        # But 'Mleté maso' usually is.
        meat_types.add('other')

    for mt in meat_types:
        findings.append(f'fresh-meat-{mt}')

    return findings

def process_file(input_path, output_path, source):
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        products = data.get('products', [])
        count = 0
        for p in products:
            # Remove old
            if 'ai_cats' in p:
                del p['ai_cats']
            
            # Add new
            findings = assign_findings(p, source)
            if findings:
                p['ai_findings'] = findings
                count += 1
            else:
                 if 'ai_findings' in p:
                     del p['ai_findings']

        # Ensure metadata exists
        if 'metadata' not in data:
            data['metadata'] = {}

        data['products'] = products
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"[{source}] Processed {input_path} -> {output_path}")
        print(f"  Assigned findings to {count} products.")
        
    except Exception as e:
        print(f"Error processing {input_path}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assign AI findings/categories.")
    parser.add_argument("--input", required=True, help="Input file suffix")
    parser.add_argument("--output", required=True, help="Output file suffix")
    parser.add_argument("--data-dir", required=True, help="Data directory")
    
    args = parser.parse_args()
    
    search_pattern = os.path.join(args.data_dir, f"*.{args.input}.json")
    files = glob.glob(search_pattern)
    
    if not files:
        print(f"No files found matching {search_pattern}")
        exit(0)
        
    print(f"Found {len(files)} files to process.")
    
    for input_file in files:
        # data/albert.result.json -> albert
        # Remove input suffix
        base_name_path = input_file.rsplit(f".{args.input}.json", 1)[0]
        output_file = f"{base_name_path}.{args.output}.json"
        
        source = os.path.basename(base_name_path)
        
        process_file(input_file, output_file, source)
