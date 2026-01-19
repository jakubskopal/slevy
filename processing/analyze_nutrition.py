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
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
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
    ai_cats: List[str]
    category_path: str
    value_score: float  # Lower is better (price per unit)
    product_url: Optional[str] = None
    
    # helper for density calculation
    nutrient_gram_per_100g: float = 0.0
    price_per_100g_nutrient: float = 0.0

class NutritionAnalyzer:
    """Analyzes grocery data for nutritional value using AI categories"""

    # Approximate nutrient content per 100g for estimations
    NUTRIENT_ESTIMATES = {
        # Protein (g per 100g)
        'Protein > Legumes': 22.0,
        'Protein > Eggs': 13.0, # ~6-7g per 50g egg
        'Protein > Egg Products': 10.0, # Spreads, salads
        'Protein > Cottage Cheese': 12.0,
        'Protein > Chicken': 23.0,
        'Protein > Meat': 20.0,
        'Protein > Meat Products': 16.0, # Ham, sausages (lower protein, higher fat/water)
        'Protein > Fish': 20.0,
        'Protein > Dairy': 3.4, # Milk average
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
                # Extract source from filename (e.g. data/kupi.processed.json -> kupi)
                source_name = os.path.basename(file_path).split('.')[0]
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    products = data.get('products', [])
                    # Inject source
                    for p in products:
                        p['source_file_key'] = source_name
                    
                    self.all_products.extend(products)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

        print(f"Loaded {len(self.all_products)} total products")

    def get_products_by_category(self, target_cat: str) -> List[NutritionScore]:
        """Find products belonging to a specific AI category"""
        matches = []
        
        nutrient_density = self.NUTRIENT_ESTIMATES.get(target_cat, 0.0)

        for product in self.all_products:
            ai_cats = product.get('ai_cats', [])
            if target_cat in ai_cats:
                
                for price_offer in product.get('prices', []):
                    # Normalized price check
                    p = price_offer.get('price')
                    up = price_offer.get('unit_price')
                    
                    if not up: continue
                    if not p: continue # Skip if price is truly 0 even after norm (unlikely)

                    unit = price_offer.get('unit', '').lower()
                    
                    # Normalize unit price to per kg/l for comparison
                    norm_unit_price = up
                    if unit in ['g', 'ml']:
                        norm_unit_price = up * 1000
                    
                    # Calculate price per 100g nutrient
                    cost_per_nutrient = 0.0
                    if nutrient_density > 0:
                        # norm_unit_price is price per kg (1000g)
                        # price per 1g product = norm_unit_price / 1000
                        # price per 100g product = norm_unit_price / 10
                        # nutrient in 100g product = nutrient_density
                        # cost per 1g nutrient = (price per 100g product) / nutrient_density
                        # cost per 100g nutrient = cost per 1g nutrient * 100
                        
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
                        ai_cats=ai_cats,
                        category_path=' > '.join(product.get('categories', [])),
                        value_score=norm_unit_price,
                        product_url=product.get('product_url'),
                        nutrient_gram_per_100g=nutrient_density,
                        price_per_100g_nutrient=cost_per_nutrient
                    ))
        print(f"DEBUG: Found {len(matches)} matches for {target_cat}. First URL: {matches[0].product_url if matches else 'None'}")
        
        # Sort by unit price (value)
        matches.sort(key=lambda x: x.value_score)
        return matches

    def generate_markdown_report(self, output_file: str = 'data/nutrition.analysis.md'):
        """
        Generates the markdown report with embedded product links.
        
        Nuts and Bolts:
        - Uses 'product://<store>|<url>' schema for links.
        - Both store and URL are URL-encoded.
        - React app intercepts these links to open the Product Detail Overlay.
        - Requires 'urllib.parse.quote' for encoding.
        """
        import urllib.parse
        
        report = []
        print("DEBUG: Starting report generation")
        
        date_str = datetime.date.today().isoformat()
        
        report.append("# Nutritional Value Analysis")
        report.append("")
        report.append("Analysis of grocery offers to identify cheap and high-quality sources of macronutrients.")
        report.append("")
        report.append(f"**Analysis Date:** {date_str}")
        report.append(f"**Total Products Analyzed:** {len(self.all_products)}")
        
        # Determine analyzed stores
        stores = set()
        for p in self.all_products:
             for pr in p.get('prices', []):
                 if pr.get('store_name'): stores.add(pr['store_name'])
        
        report.append(f"**Stores Analyzed:** {', '.join(sorted(list(stores)))}")
        print(f"DEBUG: Stores analyzed: {len(stores)}")

        report.append("")
        report.append("---")
        report.append("")

        # Executive Summary (Placeholder - difficult to generate dynamic text without LLM, using template)
        report.append("## Executive Summary")
        report.append("")
        report.append("This analysis identifies valid sources of macronutrients based on current price data.")
        report.append("")
        
        # Define categories to analyze
        protein_cats = [k for k in self.NUTRIENT_ESTIMATES.keys() if k.startswith('Protein')]
        carb_cats = [k for k in self.NUTRIENT_ESTIMATES.keys() if k.startswith('Carbs')]
        fat_cats = [k for k in self.NUTRIENT_ESTIMATES.keys() if k.startswith('Fats')]
        
        print(f"DEBUG: Categories defined. Protein: {len(protein_cats)}, Carb: {len(carb_cats)}, Fat: {len(fat_cats)}")

        # Helper to render category section
        def render_section(title, categories, metric_name="Unit Price"):
            print(f"DEBUG: Rendering section {title}")
            report.append(f"## {title}")
            report.append("")
            
            top_global = []

            for cat in categories:
                friendly_name = cat.split(' > ')[1]
                products = self.get_products_by_category(cat)
                
                if not products:
                    continue
                
                avg_price = sum(p.value_score for p in products) / len(products) if products else 0
                best_price = products[0].value_score if products else 0
                
                report.append(f"### {friendly_name}")
                report.append(f"**Estimated Density:** ~{self.NUTRIENT_ESTIMATES[cat]}g per 100g")
                report.append(f"**Average Price:** {avg_price:.2f} Kč/unit")
                report.append("")
                report.append("**Best Deals:**")
                report.append("| Product | Store | Price | Unit Price | Cost per 100g Nutrient |")
                report.append("|---------|-------|-------|------------|------------------------|")
                
                for p in products[:5]:
                    # Create Smart Link: product://<store>|<url>
                    # Ensure p.product_url is treated as string even if None
                    p_url = getattr(p, 'product_url', '') or ''
                    
                    # Ensure store is safe
                    # store_val = p.store if p.store else 'Unknown'
                    
                    # Use source for link
                    source_key = getattr(p, 'source', 'unknown')
                    
                    encoded_source = urllib.parse.quote(source_key)
                    encoded_url = urllib.parse.quote(p_url)
                    
                    link = f"product://{encoded_source}::{encoded_url}"
                    
                    # Truncate slightly longer for better readability if space allows
                    clean_name = p.product_name[:45]
                    product_link = f"[{clean_name}]({link})"
                    
                    report.append(f"| {product_link} | {p.store} | {p.price:.2f} | {p.unit_price:.2f}/{p.unit} | **{p.price_per_100g_nutrient:.2f} Kč** |")
                    top_global.append(p)
                
                report.append("")
            
            return top_global

        protein_top = render_section("Best Protein Sources", protein_cats)
        report.append("---")
        carb_top = render_section("Best Carbohydrate Sources", carb_cats)
        report.append("---")
        fat_top = render_section("Best Fat Sources", fat_cats)
        report.append("---")

        # Cost Analysis Summary
        report.append("## Cost Analysis Summary")
        report.append("")
        report.append("### Price Comparison by Nutrient Density")
        report.append("")
        
        def render_density_table(items, title):
             report.append(f"**{title} (Lowest Cost per 100g Nutrient):**")
             # Sort by cost per nutrient
             items_sorted = sorted(items, key=lambda x: x.price_per_100g_nutrient)
             
             # Deduplicate by name/store to show variety
             seen = set()
             unique_items = []
             for i in items_sorted:
                  key = f"{i.product_name}-{i.store}"
                  if key not in seen:
                       unique_items.append(i)
                       seen.add(key)
             
             for i, p in enumerate(unique_items[:10], 1):
                  cat = p.ai_cats[-1] if p.ai_cats else "Unknown"
                  
                  # Generate link here too
                  p_url = getattr(p, 'product_url', '') or ''
                  
                  # Use source, not store, for the link protocol so App switches context correctly
                  source_key = getattr(p, 'source', 'unknown')
                  
                  encoded_source = urllib.parse.quote(source_key)
                  encoded_url = urllib.parse.quote(p_url)
                  link = f"product://{encoded_source}::{encoded_url}"
                  product_link = f"[{p.product_name}]({link})"
                  
                  report.append(f"{i}. {product_link} ({p.store}) [{cat}]: **{p.price_per_100g_nutrient:.2f} Kč**")
             report.append("")

        render_density_table(protein_top, "Protein")
        render_density_table(carb_top, "Carbohydrates")
        render_density_table(fat_top, "Fats")
        
        report.append("---")
        report.append("")
        report.append("**Report Generated by:** Automated Nutrition Analyzer")
        report.append(f"**Generated At:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        print(f"Report generated: {output_file}")

def main():
    analyzer = NutritionAnalyzer()
    analyzer.load_data()
    analyzer.generate_markdown_report()

if __name__ == '__main__':
    main()
