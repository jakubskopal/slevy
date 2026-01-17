
import gzip
import os
import re
from bs4 import BeautifulSoup

def explore_tags(directory):
    import glob
    files = glob.glob(os.path.join(directory, '*.html.gz'))
    
    tag_examples = {}
    
    for filepath in files:
        try:
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            modal = soup.select_one('[data-test-id="product-modal"]')
            
            if modal:
                tags = modal.select('.cb_Tag_Root_7dc')
                for tag in tags:
                    text = tag.get_text(strip=True)
                    if text not in tag_examples:
                        tag_examples[text] = []
                    if len(tag_examples[text]) < 3:
                        tag_examples[text].append(tag.prettify())
        except Exception as e:
            continue
            
    return tag_examples

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str, default='data/albert_raw', help="Directory to search")
    args = parser.parse_args()

    tags = explore_tags(args.dir)
    with open('tag_exploration_results.txt', 'w') as f:
        for text, examples in tags.items():
            f.write(f"TAG TEXT: {text}\n")
            for ex in examples:
                f.write(f"HTML:\n{ex}\n")
            f.write("-" * 40 + "\n")
