#!/usr/bin/env python3
import argparse
from functools import partial

from wolt.crawler import WoltCrawler, VENUES
from drivers import create_driver
from console import Console

def run(store_name=None):
    parser = argparse.ArgumentParser(description="Wolt Crawler")
    parser.add_argument("--store", type=str, choices=VENUES.keys(), help="Predefined store alias")
    parser.add_argument("--url", type=str, help="Custom Wolt venue URL")
    parser.add_argument("--dir", type=str, help="Custom raw data directory")
    parser.add_argument("--workers", type=int, default=2, help="Number of parallel windows")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--color", action="store_true", help="Show ANSI progress bar")
    parser.add_argument("--limit", type=int, default=0, help="Global limit of products to crawl")
    parser.add_argument("--browser", type=str, default="chrome", choices=["chrome", "firefox"], help="Browser to use")
    args = parser.parse_args()

    # Determine URL and directory
    start_url = args.url
    raw_data_dir = args.dir
    
    # Priority: Function arg > CLI arg > Config
    target_store = store_name or args.store

    if target_store:
        if target_store not in VENUES:
             parser.error(f"Store '{target_store}' not found in configuration.")
        venue_config = VENUES[target_store]
        start_url = start_url or venue_config["url"]
        raw_data_dir = raw_data_dir or venue_config["dir"]

    if not start_url or not raw_data_dir:
        parser.error("You must specify --store or both --url and --dir")

    # Create driver factory
    driver_factory = partial(create_driver, headless=args.headless, browser_type=args.browser)

    # Initialize console
    console = Console(total=0, use_colors=args.color)
    console.start()

    try:
        crawler = WoltCrawler(
            start_url=start_url,
            raw_data_dir=raw_data_dir,
            driver_factory=driver_factory,
            workers=args.workers,
            limit=args.limit,
            console=console
        )
        crawler.run()
    finally:
        console.finish()
        console.log("All workers finished.")

if __name__ == "__main__":
    run()
