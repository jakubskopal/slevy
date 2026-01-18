#!/usr/bin/env python3
"""
Simple Nutritional Analysis Script
Analyzes processed grocery data for best protein, carb, and fat sources
"""

import json
import glob
import re
from collections import defaultdict

# Data directory
DATA_DIR = '/home/jakubs/Work/Me/agrty/data'
OUTPUT_FILE = '/home/jakubs/Work/Me/agrty/data/nutrition.analysis.md'

# Protein keywords (Czech & English)
PROTEIN_HIGH = [
    r'\bkuřec', r'\bkuře', r'\bslepic', r'\bchicken',  # Chicken
    r'\bvepř', r'\bpork', r'\bšunk', r'\bham',  # Pork
    r'\bhovězí', r'\bbeef',  # Beef
    r'\btuňák', r'\blosos', r'\bmakrela', r'\bfish', r'\brybí',  # Fish
    r'\bvajíč', r'\begg',  # Eggs
    r'\btvaroh', r'\bcottage',  # Cottage cheese
    r'\bčočk', r'\blentil', r'\bfazol', r'\bbean',  # Legumes
]

PROTEIN_EXCLUDE = [
    r'\bpečivo', r'\bchléb', r'\bbread',
    r'\bčokolád', r'\bchocolate',
    r'\bnápoj', r'\bdrink', r'\bdžus',
    r'\bomáčk', r'\bkečup',
]

# Carb keywords
CARB_HIGH = [
    r'\brýže', r'\brice',  # Rice
    r'\btěstovin', r'\bpasta', r'\bšpaget',  # Pasta
    r'\bbrambor', r'\bpotato',  # Potatoes
    r'\bchléb', r'\bbread', r'\brohlík',  # Bread
    r'\bováz', r'\boat', r'\bmüsli',  # Cereals
    r'\bmouka', r'\bflour',  # Flour
]

CARB_EXCLUDE = [
    r'\bprotein',
    r'\bmaso', r'\bmeat',
    r'\bnápoj', r'\bdrink',
]

# Fat keywords
FAT_HIGH = [
    r'\bolej', r'\boil',  # Oil
    r'\bmáslo', r'\bbutter',  # Butter
    r'\bořech', r'\bnut', r'\bmandl',  # Nuts
    r'\blosos', r'\bsalmon', r'\bmakrela',  # Fatty fish
    r'\bavokád', r'\bavocado',  # Avocado
]

FAT_EXCLUDE = [
    r'\bpečivo', r'\bbread',
    r'\bnápoj', r'\bdrink',
    r'\bmléko\s+0', r'\blight',
]


def matches_keywords(text, high_keywords, exclude_keywords):
    """Check if text matches keyword criteria"""
    if not text:
        return False, ''

    text_lower = text.lower()

    # Check exclusions
    for pattern in exclude_keywords:
        if re.search(pattern, text_lower):
            return False, 'excluded'

    # Check high priority
    for pattern in high_keywords:
        if re.search(pattern, text_lower):
            return True, 'high'

    return False, ''


def load_all_products():
    """Load all processed JSON files"""
    all_products = []
    pattern = f'{DATA_DIR}/*.processed.json'
    files = glob.glob(pattern)

    print(f"Loading from {len(files)} files...")

    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_products.extend(data['products'])
                print(f"  Loaded {len(data['products'])} products from {file_path.split('/')[-1]}")
        except Exception as e:
            print(f"  Error loading {file_path}: {e}")

    print(f"Total products: {len(all_products)}")
    return all_products


def analyze_category(products, high_kw, exclude_kw, category_name):
    """Analyze products for a specific macronutrient category"""
    results = []

    for product in products:
        # Check match
        match_name, priority = matches_keywords(product['name'], high_kw, exclude_kw)
        match_cat, _ = matches_keywords(' '.join(product.get('categories', [])), high_kw, exclude_kw)

        if not (match_name or match_cat):
            continue

        # Process price offers
        for offer in product.get('prices', []):
            if not offer.get('unit_price') or not offer.get('price'):
                continue

            unit_price = offer['unit_price']

            # Bonus for high priority
            value_score = unit_price * 0.7 if priority == 'high' else unit_price

            results.append({
                'name': product['name'],
                'brand': product.get('brand', 'N/A'),
                'category': ' > '.join(product.get('categories', ['Unknown'])),
                'store': offer['store_name'],
                'price': offer['price'],
                'unit_price': unit_price,
                'unit': offer.get('unit', ''),
                'package_size': offer.get('package_size', ''),
                'url': product.get('product_url'),
                'value_score': value_score,
                'priority': priority
            })

    # Sort by value score
    results.sort(key=lambda x: x['value_score'])

    print(f"{category_name}: Found {len(results)} products")
    return results


def generate_report(protein_list, carb_list, fat_list, all_products_count):
    """Generate markdown report"""

    lines = []
    lines.append("# Nutritional Value Analysis")
    lines.append("")
    lines.append("Analysis of grocery offers to identify cheap and high-quality sources of macronutrients.")
    lines.append("")
    lines.append(f"**Analysis Date:** 2026-01-18")
    lines.append(f"**Total Products Analyzed:** {all_products_count}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Protein section
    lines.append("## Best Protein Sources")
    lines.append("")
    lines.append(f"Found **{len(protein_list)}** protein-rich products.")
    lines.append("")
    lines.append("### Top 50 by Value (Price per Unit)")
    lines.append("")
    lines.append("| Rank | Product | Brand | Store | Price | Unit Price | Package | Category |")
    lines.append("|------|---------|-------|-------|-------|------------|---------|----------|")

    for i, item in enumerate(protein_list[:50], 1):
        lines.append(
            f"| {i} | {item['name'][:45]} | {item['brand'][:15]} | {item['store']} | "
            f"{item['price']:.1f} Kč | {item['unit_price']:.1f} Kč/{item['unit']} | "
            f"{item['package_size'][:10]} | {item['category'][:35]} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    # Carb section
    lines.append("## Best Carbohydrate Sources")
    lines.append("")
    lines.append(f"Found **{len(carb_list)}** carbohydrate-rich products.")
    lines.append("")
    lines.append("### Top 50 by Value (Price per Unit)")
    lines.append("")
    lines.append("| Rank | Product | Brand | Store | Price | Unit Price | Package | Category |")
    lines.append("|------|---------|-------|-------|-------|------------|---------|----------|")

    for i, item in enumerate(carb_list[:50], 1):
        lines.append(
            f"| {i} | {item['name'][:45]} | {item['brand'][:15]} | {item['store']} | "
            f"{item['price']:.1f} Kč | {item['unit_price']:.1f} Kč/{item['unit']} | "
            f"{item['package_size'][:10]} | {item['category'][:35]} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    # Fat section
    lines.append("## Best Fat Sources")
    lines.append("")
    lines.append(f"Found **{len(fat_list)}** fat-rich products.")
    lines.append("")
    lines.append("### Top 50 by Value (Price per Unit)")
    lines.append("")
    lines.append("| Rank | Product | Brand | Store | Price | Unit Price | Package | Category |")
    lines.append("|------|---------|-------|-------|-------|------------|---------|----------|")

    for i, item in enumerate(fat_list[:50], 1):
        lines.append(
            f"| {i} | {item['name'][:45]} | {item['brand'][:15]} | {item['store']} | "
            f"{item['price']:.1f} Kč | {item['unit_price']:.1f} Kč/{item['unit']} | "
            f"{item['package_size'][:10]} | {item['category'][:35]} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    # Statistics
    lines.append("## Summary Statistics")
    lines.append("")

    # Store distribution
    def store_stats(items):
        stores = defaultdict(int)
        for item in items[:50]:
            stores[item['store']] += 1
        return stores

    lines.append("### Top Deals by Store (Top 50)")
    lines.append("")
    lines.append("#### Protein")
    for store, count in sorted(store_stats(protein_list).items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- **{store}**: {count} products")

    lines.append("")
    lines.append("#### Carbohydrates")
    for store, count in sorted(store_stats(carb_list).items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- **{store}**: {count} products")

    lines.append("")
    lines.append("#### Fats")
    for store, count in sorted(store_stats(fat_list).items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- **{store}**: {count} products")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Methodology
    lines.append("## Methodology")
    lines.append("")
    lines.append("Products were selected based on:")
    lines.append("1. **Keyword matching** - Product names and categories matched against nutrition-specific keywords")
    lines.append("2. **Priority scoring** - High-priority items receive 30% value bonus")
    lines.append("3. **Unit price ranking** - All items ranked by price per kilogram or liter")
    lines.append("4. **Exclusions** - Non-nutritious items filtered out")
    lines.append("")
    lines.append("**High Priority Proteins:** Chicken, fish, eggs, cottage cheese, legumes")
    lines.append("")
    lines.append("**High Priority Carbs:** Rice, pasta, potatoes, bread, oats, flour")
    lines.append("")
    lines.append("**High Priority Fats:** Oils, butter, nuts, fatty fish, avocado")
    lines.append("")

    return '\n'.join(lines)


def main():
    print("=== Nutritional Analysis ===")
    print()

    # Load data
    all_products = load_all_products()
    print()

    # Analyze each category
    print("Analyzing categories...")
    protein_sources = analyze_category(all_products, PROTEIN_HIGH, PROTEIN_EXCLUDE, "Protein")
    carb_sources = analyze_category(all_products, CARB_HIGH, CARB_EXCLUDE, "Carbohydrates")
    fat_sources = analyze_category(all_products, FAT_HIGH, FAT_EXCLUDE, "Fats")
    print()

    # Generate report
    print("Generating report...")
    report = generate_report(protein_sources, carb_sources, fat_sources, len(all_products))

    # Write report
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"Report saved to: {OUTPUT_FILE}")
    print()
    print("Summary:")
    print(f"  - Total products analyzed: {len(all_products)}")
    print(f"  - Protein sources found: {len(protein_sources)}")
    print(f"  - Carb sources found: {len(carb_sources)}")
    print(f"  - Fat sources found: {len(fat_sources)}")


if __name__ == '__main__':
    main()
