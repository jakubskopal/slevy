import gzip
import argparse
from bs4 import BeautifulSoup

def extract_nav(filepath):
    try:
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return

    soup = BeautifulSoup(content, 'html.parser')
    nav = soup.select_one('[data-test-id="venue-breadcrumbs"]')
    if nav:
        print("VENUE BREADCRUMBS:")
        print(nav.prettify())
    else:
        print("Venue breadcrumbs not found")
        
    active_link = soup.select_one('[data-test-id="navigation-bar-active-link"]')
    if active_link:
        print("\nACTIVE LINK:")
        print(active_link.prettify())

def main():
    parser = argparse.ArgumentParser(description="Debug navigation breadcrumbs from product HTML.")
    parser.add_argument("file", type=str, help="Path to gzipped HTML file")
    args = parser.parse_args()
    
    extract_nav(args.file)

if __name__ == "__main__":
    main()
