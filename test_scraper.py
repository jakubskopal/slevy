from scraper import KupiScraper
import json
import sys

# Monkeypatch verify
def test_run():
    scraper = KupiScraper()
    # Limit categories for test
    scraper.fetch_categories = lambda: [{'name': 'Alkohol', 'url': 'https://www.kupi.cz/slevy/alkohol'}]
    
    # Run
    scraper.scrape_category({'name': 'Alkohol', 'url': 'https://www.kupi.cz/slevy/alkohol'})
    
    # Dump to stdout
    print(json.dumps(scraper.products[:2], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_run()
