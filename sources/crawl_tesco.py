#!/usr/bin/env python3
import argparse
import os
from concurrent.futures import ThreadPoolExecutor
from functools import partial



from tesco.crawler import CATEGORIES, CrawlerState, GlobalCounter, run_worker
from drivers import create_driver
from console import Console

def main():
    """
    Main execution logic for the Tesco crawler.
    """
    parser = argparse.ArgumentParser(description="Tesco Crawler")
    parser.add_argument("--workers", type=int, default=3, help="Number of parallel windows")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--color", action="store_true", help="Show ANSI progress bar")
    parser.add_argument("--limit", type=int, default=0, help="Global limit of products to crawl")
    parser.add_argument("--browser", type=str, default="chrome", choices=["chrome", "firefox"], help="Browser to use")
    args = parser.parse_args()

    # Ensure output dir exists
    if not os.path.exists("data/tesco_raw"):
        os.makedirs("data/tesco_raw")

    state = CrawlerState()
    pending = CATEGORIES

    # Estimate 1000 products initially
    console = Console(total=1000, use_colors=args.color)
    console.start()
    
    console.log(f"Total categories: {len(CATEGORIES)}. Remaining: {len(pending)}")

    # Initialize with existing progress
    total_prod = len(state.data["processed_products"])
    console.update(total_prod, stats=f"Cats: --/{len(CATEGORIES)}")
    
    global_counter = GlobalCounter(args.limit)
    driver_factory = partial(create_driver, headless=args.headless, browser_type=args.browser)
    
    from drivers import DriverPool
    pool = DriverPool(driver_factory)

    try:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            executor.map(lambda x: run_worker(x[1], state, console, pool, global_counter, x[0], args.limit), enumerate(pending))
    finally:
        pool.quit_all()
        console.finish()
        console.log("All workers finished.")

if __name__ == "__main__":
    main()
