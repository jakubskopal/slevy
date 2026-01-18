#!/usr/bin/env python3
"""
Enriches product data by guessing brands from product names if the brand is missing.
Ported from Wolt parser logic.
"""

import json
import argparse
import glob
import os
import re

def extract_brand(name):
    if not name: return None
    
    # Known multi-word brands or prefixes that need continuation
    known_brands = [
        "Nature's Promise", "World's Market", "7Days", "Coca-Cola", "Dr. Oetker",
        "Česká chuť", "Česká Chuť", "Albert Excellent", "Bersi Dessert",
        "Ben & Jerry's", "Captain Morgan", "Jack Daniel's", "Johnnie Walker",
        "Rio Mare", "Fresh Bistro", "Garden Gourmet", "Rice Up", "Fine Crunchy",
        "A.T. International", "Bad Reichenhaller", "Bear Beer", "Brise de France",
        "Cavit Prosecco", "Château", "Cute Baby", "Day Up", "Golden Bay",
        "Habánské sklepy", "Maison Castel", "Pearl River Bridge", "Perfect Fit",
        "St. Dalfour", "Villa Garducci", "World´s Market", "World‘s Market", "World’s Market",
        "Franz Josef Kaiser", "Le & Co", "Le Coq", "La Bohéma", "La Bonta Italiana",
        "La Vida Bio", "Velkopopovický Kozel", "Pilsner Urquell", "Stará myslivecká",
        "Tatranský čaj", "Tatra", "Mlékárna Kunín", "Jihočeská Niva", "Billa", "Globus",
        # New additions
        "Váš Výběr", "Jeden Tag", "Bio Nebio", "Tesco Finest", "Tesco Standard", "My Price"
        # EXPLICIT EXCEPTION: "Šnek Bob" (Bob Snail) is NOT considered a brand per user request.
    ]
    for kb in known_brands:
        if name.lower().startswith(kb.lower()): return kb
        
    words = name.split()
    if not words: return None
    
    # Blacklist of generic terms that are never brands when appearing alone
    blacklist = [
        "Šnek", "Mléko", "Jogurt", "Voda", "Pivo", "Pečivo", "Rohlík", "Houska",
        "Bageta", "Brambory", "Croissant", "Kachna", "Kefírové", "Kuřecí", "Mrkev",
        "Okurky", "Originální", "Paprika", "Svíčka", "Těsto", "Vepřová", "Zlaté",
        "Salát", "Pomazánka", "Sýr", "Šunka", "Tvaroh", "Mléčný", "Čerstvá", "Bio",
        "Zelí", "Žluté",
        # New blacklist items (non-food/generic)
        "Vepřové", "Hovězí", "Krůtí",
        "Jídelní", "Sedací", "Konferenční", "Psací", "Noční", "Stolní", "Rohov", "Obývací",
        "Šatní", "Úložný", "Botník", "Předsíňov",
        "Zahradní", "Stropní", "Nástěnný", "Solární",
        "Sprchový", "Kuchyňsk", "Kuchyňský",
        "Plastový", "Plastové", "Nerezový", "Skleněn", "Kameninový",
        "Organizér", "Koš", "Pytle", "Svícen", "Taštička",
        "Herní", "Kancel", "Univerz", "Cestovní", "Sportovní",
        "Jarní", "Letní", "Podzimní", "Zimní",
        "Čerstvé", "Mražená", "Mražené",
        "Smažený", "Smažené", "Pečený", "Pečené",
        "Dětské", "Dětská"
    ]
    
    brand_parts = []
    for i, word in enumerate(words):
        clean = word.replace("´", "'").replace("‘", "'").strip(",.:\"'")
        if not clean: continue
        
        if clean.isupper() and len(clean) > 1:
            brand_parts.append(clean)
            continue
        elif not brand_parts:
            if clean in blacklist: break
            if clean[0].isupper() or clean[0].isdigit():
                brand_parts.append(clean)
                # Generic prefixes that might be part of a brand
                if clean.lower() in ["albert", "česká", "jihočeská", "billa", "globus"] and i+1 < len(words):
                    continue 
                break
            else:
                break
        else:
            if clean.isupper() and len(clean) > 1:
                brand_parts.append(clean)
                continue
            else:
                break
    
    return " ".join(brand_parts) if brand_parts else None

def process_file(input_path, output_path):
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        products = data.get('products', [])
        enriched_count = 0
        
        for p in products:
            if not p.get('brand'):
                guessed = extract_brand(p.get('name'))
                if guessed:
                    p['brand'] = guessed
                    enriched_count += 1
        
        # Preserve metadata but update counts if necessary or just save
        data['products'] = products
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"Processed {input_path} -> {output_path}")
        print(f"  Enriched {enriched_count} / {len(products)} products with brands.")
        
    except Exception as e:
        print(f"Error processing {input_path}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich products with missing brands.")
    parser.add_argument("--input", required=True, help="Input file suffix (e.g. result)")
    parser.add_argument("--output", required=True, help="Output file suffix (e.g. enriched)")
    parser.add_argument("--data-dir", required=True, help="Data directory")
    
    args = parser.parse_args()
    
    search_pattern = os.path.join(args.data_dir, f"*.{args.input}.json")
    files = glob.glob(search_pattern)
    
    if not files:
        print(f"No files found matching {search_pattern}")
        exit(0)
        
    print(f"Found {len(files)} files to process.")
    
    for input_file in files:
        # Determine output filename: base + output suffix
        # input: data/albert.result.json
        # output: data/albert.enriched.json
        
        # Remove input suffix
        base_name = input_file.rsplit(f".{args.input}.json", 1)[0]
        output_file = f"{base_name}.{args.output}.json"
        
        process_file(input_file, output_file)
