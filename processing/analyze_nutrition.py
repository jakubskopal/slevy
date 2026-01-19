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
import datetime
import urllib.parse
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class NutritionScore:
    """Score for a product based on nutritional value per price"""
    product_name: str
    brand: Optional[str]
    store: str
    source: str
    price: float
    unit_price: float
    unit: str
    package_size: str
    ai_findings: List[str]
    category_path: str
    value_score: float  # Lower is better (price per unit)
    product_url: Optional[str] = None
    
    # helper for density calculation
    nutrient_gram_per_100g: float = 0.0
    price_per_100g_nutrient: float = 0.0

class NutritionAnalyzer:
    """Analyzes grocery data for nutritional value using AI findings"""

    # Approximate nutrient content per 100g for estimations
    NUTRIENT_ESTIMATES = {
        # Protein (g per 100g)
        'Protein > Eggs': 13.0, 
        'Protein > Beef': 20.0, # ~20-22g
        'Protein > Pork': 17.0, # ~16-18g (varies by cut)
        'Protein > Poultry': 23.0, # ~23g (chicken breast)
        'Protein > Other Meat': 19.0, # Avg
        
        # Kept for future mappings
        'Protein > Legumes': 22.0,
        'Protein > Cottage Cheese': 12.0,
        'Protein > Fish': 20.0,
        'Protein > Dairy': 3.4,
        'Protein > Plant Based': 15.0,
        
        # Carbs (g per 100g)
        'Carbs > Rice': 80.0,
        'Carbs > Pasta': 71.0,
        'Carbs > Flour': 76.0,
        'Carbs > Potatoes': 17.0,
        'Carbs > Bread': 49.0,
        'Carbs > Oats & Cereals': 66.0,
        'Carbs > Grains': 70.0,
        
        # Fats (g per 100g)
        'Fats > Oil': 100.0,
        'Fats > Butter & Margarine': 81.0,
        'Fats > Nuts': 50.0,
        'Fats > Seeds': 40.0,
        'Fats > Avocado': 15.0,
        'Fats > Fatty Fish': 14.0
    }
    
    # Map AI Findings to Categories
    FINDING_MAP = {
        'fresh-chicken-eggs': ['Protein > Eggs'],
        'fresh-meat-beef': ['Protein > Beef'],
        'fresh-meat-pork': ['Protein > Pork'],
        'fresh-meat-poultry': ['Protein > Poultry'],
        'fresh-meat-other': ['Protein > Other Meat']
    }

    def __init__(self, data_dir: str = 'data'):
        self.data_dir = data_dir
        self.all_products = []

    def load_data(self):
        """Load all processed JSON files"""
        pattern = f'{self.data_dir}/*.processed.json'
        files = glob.glob(pattern)
        print(f"Found {len(files)} processed data files")
        import os

        for file_path in files:
            try:
                # Extract source from filename
                source_name = os.path.basename(file_path).split('.')[0]
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    products = data.get('products', [])
                    for p in products:
                        p['source_file_key'] = source_name
                    
                    self.all_products.extend(products)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

        print(f"Loaded {len(self.all_products)} total products")

    def get_products_by_category(self, target_cat: str) -> List[NutritionScore]:
        """Find products belonging to a specific category via findings"""
        matches = []
        nutrient_density = self.NUTRIENT_ESTIMATES.get(target_cat, 0.0)

        for product in self.all_products:
            ai_findings = product.get('ai_findings', [])
            
            # Check if any finding maps to this category
            # Reverse check: Does this target_cat exist in the mappings for the product's findings?
            is_match = False
            for finding in ai_findings:
                if target_cat in self.FINDING_MAP.get(finding, []):
                    is_match = True
                    break
            
            if is_match:
                for price_offer in product.get('prices', []):
                    # Normalized price check
                    p = price_offer.get('price')
                    up = price_offer.get('unit_price')
                    
                    if not up: continue
                    if not p: continue

                    unit = price_offer.get('unit', '').lower()
                    
                    # Normalize unit price to per kg/l
                    norm_unit_price = up
                    if unit in ['g', 'ml']:
                        norm_unit_price = up * 1000
                    
                    cost_per_nutrient = 0.0
                    if nutrient_density > 0:
                        # price per 100g product = norm_unit_price / 10
                        price_per_100g_product = norm_unit_price / 10
                        cost_per_nutrient = (price_per_100g_product / nutrient_density) * 100

                    matches.append(NutritionScore(
                        product_name=product['name'],
                        brand=product.get('brand'),
                        store=price_offer['store_name'],
                        source=product.get('source_file_key', 'unknown'),
                        price=p,
                        unit_price=norm_unit_price,
                        unit='kg' if unit in ['g', 'kg'] else 'l' if unit in ['ml', 'l', 'liter'] else unit,
                        package_size=price_offer.get('package_size', ''),
                        ai_findings=ai_findings,
                        category_path=' > '.join(product.get('categories', [])),
                        value_score=norm_unit_price,
                        product_url=product.get('product_url'),
                        nutrient_gram_per_100g=nutrient_density,
                        price_per_100g_nutrient=cost_per_nutrient
                    ))
        
        # Sort by unit price (value)
        matches.sort(key=lambda x: x.value_score)
        return matches

    def generate_markdown_report(self, output_file: str = 'data/nutrition.analysis.md'):
        report = []
        print("DEBUG: Starting report generation")
        
        date_str = datetime.date.today().isoformat()
        
        report.append("# Nutritional Value Analysis")
        report.append("")
        report.append(f"**Analysis Date:** {date_str}")
        report.append(f"**Total Products Analyzed:** {len(self.all_products)}")
        
        stores = set()
        for p in self.all_products:
             for pr in p.get('prices', []):
                 if pr.get('store_name'): stores.add(pr['store_name'])
        
        report.append(f"**Stores Analyzed:** {', '.join(sorted(list(stores)))}")
        report.append("")
        report.append("---")
        report.append("")

        report.append("## Executive Summary")
        report.append("")
        report.append("This analysis identifies valid sources of macronutrients based on current price data.")
        report.append("**Note:** Categorization is currently strictly limited to **Fresh Eggs** based on expert verification.")
        report.append("")
        
        protein_cats = [k for k in self.NUTRIENT_ESTIMATES.keys() if k.startswith('Protein')]
        # Only analyze eggs for now based on user request? Or just run all (others will be empty)
        # We run all to maintain structure, empty ones will show "No products found" or be skipped.
        
        def render_section(title, categories):
            report.append(f"## {title}")
            report.append("")
            
            top_global = []

            for cat in categories:
                products = self.get_products_by_category(cat)
                
                if not products:
                    continue
                    
                friendly_name = cat.split(' > ')[1]
                avg_price = sum(p.value_score for p in products) / len(products) if products else 0
                
                report.append(f"### {friendly_name}")
                report.append(f"**Estimated Density:** ~{self.NUTRIENT_ESTIMATES[cat]}g per 100g")
                report.append(f"**Average Price:** {avg_price:.2f} Kč/unit")
                report.append("")

                # Split Products
                kupi_products = [p for p in products if p.source == 'kupi']
                shop_products = [p for p in products if p.source != 'kupi']

                def render_table(sub_title, items):
                    if not items: return
                    report.append(f"**{sub_title}:**")
                    report.append("| Product | Store | Price | Unit Price |")
                    report.append("|---------|-------|-------|------------|")
                    
                    for p in items[:5]:
                        p_url = getattr(p, 'product_url', '') or ''
                        source_key = getattr(p, 'source', 'unknown')
                        encoded_source = urllib.parse.quote(source_key)
                        encoded_url = urllib.parse.quote(p_url)
                        link = f"product://{encoded_source}::{encoded_url}"
                        clean_name = p.product_name[:45]
                        product_link = f"[{clean_name}]({link})"
                        
                        report.append(f"| {product_link} | {p.store} | {p.price:.2f} | {p.unit_price:.2f}/{p.unit} |")
                        top_global.append(p)
                    report.append("")

                render_table("Best Deals (Shops)", shop_products)
                render_table("Best Deals (Flyers)", kupi_products)
            
            return top_global

        protein_top = render_section("Best Protein Sources", protein_cats)
        
        # Only protein is populated for now
        # report.append("---")
        # carb_top = render_section("Best Carbohydrate Sources", carb_cats) ...

        report.append("## Cost Analysis Summary")
        report.append("")

        if protein_top:
            report.append(f"**Protein (Lowest Cost per 100g Nutrient):**")
            items_sorted = sorted(protein_top, key=lambda x: x.price_per_100g_nutrient)
            seen = set()
            unique_items = []
            for i in items_sorted:
                 key = f"{i.product_name}-{i.store}"
                 if key not in seen:
                      unique_items.append(i)
                      seen.add(key)
            
            for i, p in enumerate(unique_items[:10], 1):
                 cat = "Eggs" # Hardcoded since only eggs supported
                 p_url = getattr(p, 'product_url', '') or ''
                 source_key = getattr(p, 'source', 'unknown')
                 encoded_source = urllib.parse.quote(source_key)
                 encoded_url = urllib.parse.quote(p_url)
                 link = f"product://{encoded_source}::{encoded_url}"
                 product_link = f"[{p.product_name}]({link})"
                 
                 report.append(f"{i}. {product_link} ({p.store}) [{cat}]: **{p.price_per_100g_nutrient:.2f} Kč**")
            report.append("")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        print(f"Report generated: {output_file}")

def main():
    analyzer = NutritionAnalyzer()
    analyzer.load_data()
    analyzer.generate_markdown_report()

if __name__ == '__main__':
    main()
