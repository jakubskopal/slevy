#!/usr/bin/env python3
"""
AI Categorization Script
Assigns AI-derived categories (ai_cats) to products based on keywords.
"""

import argparse
import json
import re
import sys
import glob

# Keywords for identifying protein sources
PROTEIN_KEYWORDS = {
    'Protein > Legumes': [
        r'\bčočk', r'\blentil', r'\bfazol', r'\bbean', r'\bcizrn', r'\bchickpea',
        r'\bhrach', r'\bhrách', r'\bpea\b'
    ],
    'Protein > Eggs': [
        r'\bvajíč', r'\bvejce', r'\begg'
    ],
    'Protein > Cottage Cheese': [
        r'\btvaroh', r'\bquark', r'\bcottage'
    ],
    'Protein > Chicken': [
        r'\bkuřec', r'\bkuře', r'\bslepic', r'\bdrůbež', r'\bchicken'
    ],
    'Protein > Meat Products': [
        r'\bšunk', r'\bham\b', r'\bsalám', r'\bklobás', r'\bpárk', r'\bpárek', r'\bbuřt', 
        r'\bsekan', r'\bpaštik', r'\bslanin', r'\buzen', r'\bburger', r'\bhot ?dog', r'\bprosciutto',
        r'\btlačenk', r'\bnuget', r'\bguláš', r'\bhamburger', r'\břízek', r'\břízk'
    ],
    'Protein > Meat': [
        r'\bvepř', r'\bpork', r'\bhovězí', r'\bbeef', r'\bsteak',
        r'\btelecí', r'\bzvěřin', r'\bjehně', r'\bkrálí', r'\bmaso\b', r'\bmasov',
        r'\bmeat', r'\bkotlet', r'\bplec', r'\bkýta', r'\bbok\b', r'\bkrkovic'
    ],
    'Protein > Fish': [
        r'\brybí', r'\btuňák', r'\blosos', r'\bmakrela', r'\bsardink', r'\bfish',
        r'\bsleď', r'\btuna\b'
    ],
    'Protein > Dairy': [
        r'\bmléko', r'\bmilk', r'\bsýr\b', r'\bcheese', r'\bjogurt', r'\byogurt',
        r'\bmozzarella', r'\bgouda', r'\bedam', r'\bchedar', r'\bparmezan',
        r'\beidam', r'\bniva', r'\bhermelín'
    ],
    'Protein > Plant Based': [
         r'\btofu', r'\btempeh', r'\bseitan', r'\brob\b', r'\bsojov'
    ]
}

# Keywords for identifying carbohydrate sources
CARB_KEYWORDS = {
    'Carbs > Rice': [
        r'\brýže', r'\brice', r'\brizoto', r'\brisotto'
    ],
    'Carbs > Pasta': [
        r'\btěstovin', r'\bpasta', r'\bšpaget', r'\bspaghetti', r'\bpenne', r'\bmakaron', r'\bfusilli',
        r'\bkolínk', r'\bfleky', r'\bnudle', r'\bnoodle', r'\bgnocchi'
    ],
    'Carbs > Flour': [
        r'\bmouka', r'\bflour'
    ],
    'Carbs > Potatoes': [
        r'\bbrambor', r'\bpotato', r'\bhranolk', r'\bfries', r'\bgnocchi'
    ],
    'Carbs > Bread': [
        r'\bchléb', r'\bbread', r'\brohlík', r'\bbageta', r'\bbaguette', r'\bpečivo',
        r'\bkaiserka', r'\bhouska'
    ],
    'Carbs > Oats & Cereals': [
        r'\bov(e|ě)s', r'\boat', r'\bmüsli', r'\bmuesli', r'\bcornflakes',
        r'\bvločky', r'\bgra?nola', r'\bcereál'
    ],
    'Carbs > Grains': [
         r'\bkusku', r'\bcouscous', r'\bbulg', r'\bquinoa', r'\bpohank'
    ]
}

# Keywords for identifying fat sources
FAT_KEYWORDS = {
    'Fats > Oil': [
        r'\bolej', r'\boil', r'\bslunečnic', r'\bsunflower', r'\bolivov', r'\bolive',
        r'\břepkov', r'\brapeseed'
    ],
    'Fats > Butter & Margarine': [
        r'\bmáslo', r'\bbutter', r'\bmargarín', r'\bmargarine', r'\brama\b', r'\bperla\b', r'\bflora\b',
        r'\bsádlo', r'\bškvark'
    ],
    'Fats > Nuts': [
        r'\bořech', r'\bnut', r'\bmandl', r'\balmond', r'\bkešu', r'\bcashew',
        r'\bpi?stáci', r'\bburák', r'\bpeanut', r'\bpara', r'\blískov'
    ],
    'Fats > Seeds': [
        r'\bsemínk', r'\bseed', r'\bčía', r'\bchia', r'\blněn', r'\bflax', r'\bsezam'
    ],
    'Fats > Avocado': [
         r'\bavokád', r'\bavocado'
    ],
    'Fats > Fatty Fish': [
        # Overlaps with Protein > Fish, but these are high fat
        r'\blosos', r'\bsalmon', r'\bmakrela', r'\bmackerel', r'\bsardink'
    ]
}

# Exclusions to prevent false positives
EXCLUSIONS = [
    r'\bčokolád', r'\bchocolate', r'\bcukr', r'\bsugar', r'\bsušenk', r'\bcookie', r'\bbiscuit',
    r'\bnápoj', r'\bdrink', r'\bdžus', r'\bjuice', r'\bnektar', r'\bsirup',
    r'\bpolévk', r'\bsoup', r'\bbujón', r'\bvývar',
    r'\bomáčk', r'\bsauce', r'\bdresing', r'\bkečup', r'\bhořčic', r'\bmayonnaise', r'\bmajolk',
    r'\bchips', r'\bkmín', r'\bpepř', r'\bkoření', r'\bsalt', r'\bsůl'
]

def matches_any(text, patterns):
    text_lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, text_lower):
            return True
    return False

def assign_categories(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    count_assigned = 0
    total_products = len(data.get('products', []))
    print(f"Assigning categories for {total_products} products in {input_file}...")

    for product in data.get('products', []):
        name = product.get('name', '')
        cats = product.get('categories', [])
        cat_str = ' '.join(cats)
        text_to_search = f"{name} {cat_str}"
        
        # Sanitize text to avoid category names triggering false positives
        # "Mléčné výrobky a vejce" -> triggers 'vejce' matches for all dairy.
        text_to_search = re.sub(r'mléčné výrobky a vejce', '', text_to_search, flags=re.IGNORECASE)
        
        # Check exclusions first
        if matches_any(text_to_search, EXCLUSIONS):
             # Ensure we don't accidentally tag exclusion items unless really sure?
             # For now, if excluded, don't tag at all.
             product['ai_cats'] = []
             continue

        ai_cats = set()
        
        # Check Protein
        for cat_name, patterns in PROTEIN_KEYWORDS.items():
            if matches_any(text_to_search, patterns):
                ai_cats.add('Protein')
                ai_cats.add(cat_name)
        
        # Check Carbs
        for cat_name, patterns in CARB_KEYWORDS.items():
            if matches_any(text_to_search, patterns):
                ai_cats.add('Carbs')
                ai_cats.add(cat_name)

        # Check Fats
        for cat_name, patterns in FAT_KEYWORDS.items():
            if matches_any(text_to_search, patterns):
                ai_cats.add('Fats')
                ai_cats.add(cat_name)
        
        # Post-process Refinement
        
        # 1. Meat Products Priority
        if 'Protein > Meat Products' in ai_cats:
            ai_cats.discard('Protein > Meat')
            ai_cats.discard('Protein > Chicken')

        # 2. Fish Priority (Smoke mackerel is Fish, not Meat Product)
        if 'Protein > Fish' in ai_cats:
            ai_cats.discard('Protein > Meat Products')
            ai_cats.discard('Protein > Meat')
            
        # 3. Lard is Fat, not Meat (Sádlo)
        if re.search(r'\bsádlo', text_to_search, re.IGNORECASE):
             ai_cats.discard('Protein > Meat')
             ai_cats.discard('Protein > Meat Products')

        # 4. Eggs Priority / Exclusion
        # If 'Protein > Chicken' matched but text has 'vejce' (e.g. 'Vejce slepic'), remove Chicken.
        # Only if 'Protein > Eggs' is ALSO there (likely) or just purely if Vejce is there.
        if 'Protein > Chicken' in ai_cats:
             if re.search(r'\bvejce', text_to_search, re.IGNORECASE):
                 ai_cats.discard('Protein > Chicken')

        # 5. Egg Products Refinement
        if 'Protein > Eggs' in ai_cats:
             if re.search(r'\bpomazánk|\bsalát|\bmajolk|\bmajon', text_to_search, re.IGNORECASE):
                  ai_cats.remove('Protein > Eggs')
                  ai_cats.add('Protein > Egg Products')
        
        if ai_cats:
            product['ai_cats'] = sorted(list(ai_cats))
            count_assigned += 1
        else:
             product['ai_cats'] = []

    print(f"Assigned categories to {count_assigned} products.")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved to {output_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Assign AI categories')
    parser.add_argument('--input', required=True, help='Input JSON suffix or filename')
    parser.add_argument('--output', required=True, help='Output JSON suffix')
    parser.add_argument('--data-dir', default='data', help='Data directory')
    
    args = parser.parse_args()
    
    # Wildcard handling consistent with pipeline
    files = glob.glob(f"{args.data_dir}/*.{args.input}.json")
    if not files:
        print(f"No input files found for suffix '.{args.input}.json' in {args.data_dir}")
        sys.exit(0)

    for input_file in files:
        filename = input_file.split('/')[-1]
        basename = filename.replace(f'.{args.input}.json', '')
        output_path = f"{args.data_dir}/{basename}.{args.output}.json"
        
        assign_categories(input_file, output_path)
