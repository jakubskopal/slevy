
import gzip
import os
import re
from bs4 import BeautifulSoup

def find_18_plus_in_modal(directory):
    files = [f for f in os.listdir(directory) if f.endswith('.html.gz')]
    results = []
    
    for filename in files:
        filepath = os.path.join(directory, filename)
        try:
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                content = f.read()
            
            if '18+' not in content:
                continue
                
            soup = BeautifulSoup(content, 'html.parser')
            modal = soup.select_one('[data-test-id="product-modal"]')
            
            if modal and '18+' in modal.get_text():
                # Find the specific element containing 18+
                elements = modal.find_all(string=re.compile(r'18\+'))
                for el in elements:
                    # Look for parents with data-test-id
                    parent = el.parent
                    found_tid = None
                    curr = parent
                    while curr and curr.name != '[document]':
                        if curr.get('data-test-id'):
                            found_tid = curr.get('data-test-id')
                            break
                        curr = curr.parent
                        
                    results.append({
                        'file': filename,
                        'html': parent.prettify() if parent else "N/A",
                        'parent_html': parent.parent.prettify() if parent and parent.parent else "N/A",
                        'tag_tid': found_tid,
                        'tag_attrs': parent.parent.attrs if parent and parent.parent else {}
                    })
                if len(results) >= 10:
                    break
        except Exception as e:
            continue
            
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str, default='data/albert_raw', help="Directory to search")
    args = parser.parse_args()

    found = find_18_plus_in_modal(args.dir)
    for item in found:
        print(f"FILE: {item['file']}")
        print(f"NEAREST TEST-ID: {item['tag_tid']}")
        print(f"PARENT ATTRS: {item['tag_attrs']}")
        print(f"PARENT HTML:\n{item['parent_html']}\n")
        print("-" * 40)
