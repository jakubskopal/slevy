#!/usr/bin/env python3
"""
Nutritional Analysis Script

Analyzes processed grocery data to identify cheap and high-quality sources of:
- Protein
- Carbohydrates
- Fats

Outputs a comprehensive markdown report.
"""

import json
import glob
import re
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class NutritionScore:
    """Score for a product based on nutritional value per price"""
    product_name: str
    brand: Optional[str]
    category: str
    store: str
    price: float
    unit_price: float
    unit: str
    package_size: str
    product_url: Optional[str]
    value_score: float  # Lower is better (price per nutrition benefit)
    notes: str


class NutritionAnalyzer:
    """Analyzes grocery data for nutritional value"""

    # Keywords for identifying protein sources (meat, fish, dairy, legumes, eggs)
    PROTEIN_KEYWORDS = {
        'high': [
            r'\bkuřec', r'\bcurry', r'\bkuře', r'\bslepic', r'\bdrůbež',  # Chicken
            r'\bvepř', r'\bpork', r'\bklobás', r'\bsal[aá]m', r'\bšunk',  # Pork
            r'\bhovězí', r'\bbeef', r'\bsteak',  # Beef
            r'\brybí', r'\btuňák', r'\blosos', r'\bmakrela', r'\bsardink', r'\bfish',  # Fish
            r'\bvajíč', r'\bejce', r'\begg',  # Eggs
            r'\btvaroh', r'\bquark', r'\bcottage',  # Cottage cheese
            r'\bprotein', r'\bproteín',  # Protein products
            r'\bčočk', r'\blentil', r'\bfazol', r'\bbean', r'\bcizrn', r'\bchickpea',  # Legumes
            r'\bkrevet', r'\bshrimp', r'\bkrab',  # Seafood
            r'\btofu', r'\btempeh', r'\bseitan',  # Plant protein
        ],
        'medium': [
            r'\bmléko', r'\bmilk', r'\bsýr', r'\bcheese',  # Dairy
            r'\bjogurt', r'\byogu?rt',  # Yogurt
            r'\bmozzarella', r'\bgouda', r'\bedam', r'\bchedar', r'\bparmezan',  # Cheese types
            r'\bořech', r'\bnut', r'\bmandl', r'\balmond',  # Nuts
        ],
        'exclude': [
            r'\bpečivo', r'\bchléb', r'\bsušenk', r'\bcookie', r'\bbiscuit',  # Bakery
            r'\bčokolád', r'\bchocolate', r'\bcukr', r'\bsugar',  # Sweets
            r'\bomáčk', r'\bsauce', r'\bpolévk', r'\bsoup',  # Prepared
            r'\bnápoj', r'\bdrink', r'\bdžus', r'\bjuice',  # Drinks
            r'\bkečup', r'\bmayonnaise', r'\bhořčic',  # Condiments
        ]
    }

    # Keywords for identifying carbohydrate sources (grains, pasta, rice, potatoes, bread)
    CARB_KEYWORDS = {
        'high': [
            r'\brýže', r'\brice', r'\brizoto', r'\brisotto',  # Rice
            r'\btěstovin', r'\bpasta', r'\bšpaget', r'\bspaghetti', r'\bpenne', r'\bmakaron',  # Pasta
            r'\bbrambor', r'\bpotato', r'\bhranolk', r'\bfries',  # Potatoes
            r'\bchléb', r'\bbread', r'\brohlík', r'\bbageta', r'\bbaguette',  # Bread
            r'\bováz', r'\boat', r'\bmüsli', r'\bmuesli', r'\bcornflakes',  # Cereals
            r'\bkrupic', r'\bkaš', r'\bporridge',  # Porridge
            r'\bmouka', r'\bflour',  # Flour
            r'\bkusku', r'\bcouscous', r'\bbulg', r'\bquinoa',  # Grains
        ],
        'medium': [
            r'\bpečivo', r'\bbakery', r'\bsušenk', r'\bcookie',  # Bakery
            r'\bkruasan', r'\bcroissant', r'\bmuffin',  # Pastries
        ],
        'exclude': [
            r'\bprotein', r'\bproteín',  # Protein products
            r'\bmaso', r'\bmeat', r'\bryb', r'\bfish',  # Meat
            r'\bnápoj', r'\bdrink', r'\bdžus', r'\bjuice',  # Drinks
            r'\bomáčk', r'\bsauce',  # Sauces
        ]
    }

    # Keywords for identifying fat sources (oils, butter, nuts, fatty fish, avocado)
    FAT_KEYWORDS = {
        'high': [
            r'\bolej', r'\boil', r'\bslunečnic', r'\bsunflower', r'\bolivov', r'\bolive',  # Oils
            r'\bmáslo', r'\bbutter', r'\bmargarín', r'\bmargarine',  # Butter
            r'\bořech', r'\bnut', r'\bmandl', r'\balmond', r'\bkešu', r'\bcashew',  # Nuts
            r'\blosos', r'\bsalmon', r'\bmakrela', r'\bmackerel', r'\bsardink', r'\bsardin',  # Fatty fish
            r'\bavokád', r'\bavocado',  # Avocado
            r'\bsemínk', r'\bseed', r'\bčía', r'\bchia', r'\blněn', r'\bflax',  # Seeds
            r'\bsádlo', r'\blard', r'\bškvark',  # Animal fat
            r'\bkokos', r'\bcoconut',  # Coconut products
        ],
        'medium': [
            r'\bsýr', r'\bcheese',  # Cheese
            r'\bsmetana', r'\bcream', r'\bcrème',  # Cream
            r'\bmajone', r'\bmayo',  # Mayonnaise
        ],
        'exclude': [
            r'\bpečivo', r'\bbread', r'\bchléb',  # Bread
            r'\bpolévk', r'\bsoup',  # Soups
            r'\bnápoj', r'\bdrink', r'\bdžus', r'\bjuice',  # Drinks
            r'\bmléko\s+0', r'\bskim', r'\blight',  # Low-fat
        ]
    }

    def __init__(self, data_dir: str = '/home/jakubs/Work/Me/agrty/data'):
        self.data_dir = data_dir
        self.all_products = []

    def load_data(self):
        """Load all processed JSON files"""
        pattern = f'{self.data_dir}/*.processed.json'
        files = glob.glob(pattern)

        print(f"Found {len(files)} processed data files")

        for file_path in files:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.all_products.extend(data['products'])

        print(f"Loaded {len(self.all_products)} total products")

    def matches_keywords(self, text: str, keywords: Dict[str, List[str]]) -> Tuple[bool, str]:
        """Check if text matches keyword criteria"""
        if not text:
            return False, ''

        text_lower = text.lower()

        # Check exclusions first
        for pattern in keywords.get('exclude', []):
            if re.search(pattern, text_lower):
                return False, 'excluded'

        # Check high priority matches
        for pattern in keywords.get('high', []):
            if re.search(pattern, text_lower):
                return True, 'high'

        # Check medium priority matches
        for pattern in keywords.get('medium', []):
            if re.search(pattern, text_lower):
                return True, 'medium'

        return False, ''

    def analyze_protein_sources(self) -> List[NutritionScore]:
        """Find best protein sources by price"""
        protein_products = []

        for product in self.all_products:
            # Check product name and categories
            match_name, priority_name = self.matches_keywords(product['name'], self.PROTEIN_KEYWORDS)
            match_cat, priority_cat = self.matches_keywords(
                ' '.join(product.get('categories', [])),
                self.PROTEIN_KEYWORDS
            )

            if not (match_name or match_cat):
                continue

            priority = priority_name if match_name else priority_cat

            # Analyze each price offer
            for price_offer in product.get('prices', []):
                if not price_offer.get('unit_price') or not price_offer.get('price'):
                    continue

                # For protein, we prefer by kg/l pricing
                unit_price = price_offer['unit_price']
                unit = price_offer.get('unit', '')

                # Bonus for high-priority protein sources
                priority_multiplier = 0.7 if priority == 'high' else 1.0
                value_score = unit_price * priority_multiplier

                category = ' > '.join(product.get('categories', ['Unknown']))

                protein_products.append(NutritionScore(
                    product_name=product['name'],
                    brand=product.get('brand'),
                    category=category,
                    store=price_offer['store_name'],
                    price=price_offer['price'],
                    unit_price=unit_price,
                    unit=unit,
                    package_size=price_offer.get('package_size', ''),
                    product_url=product.get('product_url'),
                    value_score=value_score,
                    notes=f'Priority: {priority}'
                ))

        # Sort by value score (lower is better)
        protein_products.sort(key=lambda x: x.value_score)
        return protein_products

    def analyze_carb_sources(self) -> List[NutritionScore]:
        """Find best carbohydrate sources by price"""
        carb_products = []

        for product in self.all_products:
            match_name, priority_name = self.matches_keywords(product['name'], self.CARB_KEYWORDS)
            match_cat, priority_cat = self.matches_keywords(
                ' '.join(product.get('categories', [])),
                self.CARB_KEYWORDS
            )

            if not (match_name or match_cat):
                continue

            priority = priority_name if match_name else priority_cat

            for price_offer in product.get('prices', []):
                if not price_offer.get('unit_price') or not price_offer.get('price'):
                    continue

                unit_price = price_offer['unit_price']
                unit = price_offer.get('unit', '')

                # Bonus for high-priority carb sources (grains, pasta, rice)
                priority_multiplier = 0.7 if priority == 'high' else 1.0
                value_score = unit_price * priority_multiplier

                category = ' > '.join(product.get('categories', ['Unknown']))

                carb_products.append(NutritionScore(
                    product_name=product['name'],
                    brand=product.get('brand'),
                    category=category,
                    store=price_offer['store_name'],
                    price=price_offer['price'],
                    unit_price=unit_price,
                    unit=unit,
                    package_size=price_offer.get('package_size', ''),
                    product_url=product.get('product_url'),
                    value_score=value_score,
                    notes=f'Priority: {priority}'
                ))

        carb_products.sort(key=lambda x: x.value_score)
        return carb_products

    def analyze_fat_sources(self) -> List[NutritionScore]:
        """Find best fat sources by price"""
        fat_products = []

        for product in self.all_products:
            match_name, priority_name = self.matches_keywords(product['name'], self.FAT_KEYWORDS)
            match_cat, priority_cat = self.matches_keywords(
                ' '.join(product.get('categories', [])),
                self.FAT_KEYWORDS
            )

            if not (match_name or match_cat):
                continue

            priority = priority_name if match_name else priority_cat

            for price_offer in product.get('prices', []):
                if not price_offer.get('unit_price') or not price_offer.get('price'):
                    continue

                unit_price = price_offer['unit_price']
                unit = price_offer.get('unit', '')

                # Bonus for high-priority fat sources (oils, nuts)
                priority_multiplier = 0.7 if priority == 'high' else 1.0
                value_score = unit_price * priority_multiplier

                category = ' > '.join(product.get('categories', ['Unknown']))

                fat_products.append(NutritionScore(
                    product_name=product['name'],
                    brand=product.get('brand'),
                    category=category,
                    store=price_offer['store_name'],
                    price=price_offer['price'],
                    unit_price=unit_price,
                    unit=unit,
                    package_size=price_offer.get('package_size', ''),
                    product_url=product.get('product_url'),
                    value_score=value_score,
                    notes=f'Priority: {priority}'
                ))

        fat_products.sort(key=lambda x: x.value_score)
        return fat_products

    def generate_markdown_report(self, output_file: str = '/home/jakubs/Work/Me/agrty/data/nutrition.analysis.md'):
        """Generate comprehensive markdown report"""

        protein_sources = self.analyze_protein_sources()
        carb_sources = self.analyze_carb_sources()
        fat_sources = self.analyze_fat_sources()

        # Generate report
        report = []
        report.append("# Nutritional Value Analysis")
        report.append("")
        report.append("Analysis of grocery offers to identify cheap and high-quality sources of macronutrients.")
        report.append("")
        report.append(f"**Analysis Date:** 2026-01-18")
        report.append(f"**Total Products Analyzed:** {len(self.all_products)}")
        report.append("")
        report.append("---")
        report.append("")

        # Protein Section
        report.append("## Best Protein Sources")
        report.append("")
        report.append(f"Found **{len(protein_sources)}** protein-rich products.")
        report.append("")
        report.append("### Top 30 by Value (Price per Unit)")
        report.append("")
        report.append("| Rank | Product | Brand | Store | Price | Unit Price | Package | Category | Notes |")
        report.append("|------|---------|-------|-------|-------|------------|---------|----------|-------|")

        for i, item in enumerate(protein_sources[:30], 1):
            brand = item.brand or 'N/A'
            report.append(
                f"| {i} | {item.product_name[:50]} | {brand[:20]} | {item.store} | "
                f"{item.price:.2f} Kč | {item.unit_price:.2f} Kč/{item.unit} | "
                f"{item.package_size} | {item.category[:40]} | {item.notes} |"
            )

        report.append("")
        report.append("---")
        report.append("")

        # Carbohydrates Section
        report.append("## Best Carbohydrate Sources")
        report.append("")
        report.append(f"Found **{len(carb_sources)}** carbohydrate-rich products.")
        report.append("")
        report.append("### Top 30 by Value (Price per Unit)")
        report.append("")
        report.append("| Rank | Product | Brand | Store | Price | Unit Price | Package | Category | Notes |")
        report.append("|------|---------|-------|-------|-------|------------|---------|----------|-------|")

        for i, item in enumerate(carb_sources[:30], 1):
            brand = item.brand or 'N/A'
            report.append(
                f"| {i} | {item.product_name[:50]} | {brand[:20]} | {item.store} | "
                f"{item.price:.2f} Kč | {item.unit_price:.2f} Kč/{item.unit} | "
                f"{item.package_size} | {item.category[:40]} | {item.notes} |"
            )

        report.append("")
        report.append("---")
        report.append("")

        # Fats Section
        report.append("## Best Fat Sources")
        report.append("")
        report.append(f"Found **{len(fat_sources)}** fat-rich products.")
        report.append("")
        report.append("### Top 30 by Value (Price per Unit)")
        report.append("")
        report.append("| Rank | Product | Brand | Store | Price | Unit Price | Package | Category | Notes |")
        report.append("|------|---------|-------|-------|-------|------------|---------|----------|-------|")

        for i, item in enumerate(fat_sources[:30], 1):
            brand = item.brand or 'N/A'
            report.append(
                f"| {i} | {item.product_name[:50]} | {brand[:20]} | {item.store} | "
                f"{item.price:.2f} Kč | {item.unit_price:.2f} Kč/{item.unit} | "
                f"{item.package_size} | {item.category[:40]} | {item.notes} |"
            )

        report.append("")
        report.append("---")
        report.append("")

        # Summary Statistics
        report.append("## Summary Statistics")
        report.append("")

        # Store distribution for protein
        protein_by_store = defaultdict(int)
        for item in protein_sources[:30]:
            protein_by_store[item.store] += 1

        report.append("### Top Protein Deals by Store")
        for store, count in sorted(protein_by_store.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- **{store}**: {count} products in top 30")
        report.append("")

        # Store distribution for carbs
        carb_by_store = defaultdict(int)
        for item in carb_sources[:30]:
            carb_by_store[item.store] += 1

        report.append("### Top Carb Deals by Store")
        for store, count in sorted(carb_by_store.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- **{store}**: {count} products in top 30")
        report.append("")

        # Store distribution for fats
        fat_by_store = defaultdict(int)
        for item in fat_sources[:30]:
            fat_by_store[item.store] += 1

        report.append("### Top Fat Deals by Store")
        for store, count in sorted(fat_by_store.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- **{store}**: {count} products in top 30")
        report.append("")

        report.append("---")
        report.append("")

        # Methodology
        report.append("## Methodology")
        report.append("")
        report.append("### Selection Criteria")
        report.append("")
        report.append("Products were selected based on:")
        report.append("1. **Keyword matching** - Product names and categories matched against nutrition-specific keywords")
        report.append("2. **Priority scoring** - High-priority items (e.g., chicken, rice, oils) receive 30% bonus")
        report.append("3. **Unit price** - All items ranked by price per kilogram or liter")
        report.append("4. **Exclusions** - Products like drinks, condiments, and sweets are filtered out")
        report.append("")
        report.append("### Priority Categories")
        report.append("")
        report.append("**High Priority Proteins:**")
        report.append("- Chicken, fish, eggs, cottage cheese, legumes")
        report.append("")
        report.append("**High Priority Carbohydrates:**")
        report.append("- Rice, pasta, potatoes, bread, oats, flour")
        report.append("")
        report.append("**High Priority Fats:**")
        report.append("- Cooking oils, butter, nuts, fatty fish, avocado")
        report.append("")

        # Write report
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))

        print(f"\nReport generated: {output_file}")
        print(f"- Protein sources: {len(protein_sources)}")
        print(f"- Carb sources: {len(carb_sources)}")
        print(f"- Fat sources: {len(fat_sources)}")


def main():
    analyzer = NutritionAnalyzer()
    analyzer.load_data()
    analyzer.generate_markdown_report()


if __name__ == '__main__':
    main()
