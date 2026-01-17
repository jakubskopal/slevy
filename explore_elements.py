
import gzip
import os
import glob
import random
from bs4 import BeautifulSoup

import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str, default='data/albert_raw', help="Data directory")
    args = parser.parse_args()

    # Find gzipped HTML files in the data directory
    files = glob.glob(os.path.join(args.dir, "*.html.gz"))
    if not files:
        print("No files found.")
        return
    
    random_files = random.sample(files, min(500, len(files)))
    
    id_examples = {}
    
    for filepath in random_files:
        try:
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            # Find all elements with data-test-id starting with product-modal
            elements = soup.find_all(attrs={"data-test-id": lambda x: x and x.startswith("product-modal")})
            
            for el in elements:
                tid = el.get("data-test-id")
                # Clean up the HTML for display (truncate if too long, remove inner complexity if needed)
                # But here we want notable examples, so let's keep it relatively raw
                html_str = str(el)
                if tid not in id_examples:
                    id_examples[tid] = set()
                
                if len(id_examples[tid]) < 5: # Keep up to 5 unique examples
                    id_examples[tid].add(html_str)
        except:
            continue

    with open('product_modal_elements_exploration.md', 'w') as out:
        out.write("# Product Modal Elements Exploration\n\n")
        out.write("Extracted from 500 random files.\n\n")
        
        for tid in sorted(id_examples.keys()):
            out.write(f"## `{tid}`\n\n")
            for i, example in enumerate(sorted(id_examples[tid])):
                out.write(f"### Example {i+1}\n")
                out.write("```html\n")
                out.write(example + "\n")
                out.write("```\n\n")

    print("Done. Generated product_modal_elements_exploration.md")

if __name__ == "__main__":
    main()
