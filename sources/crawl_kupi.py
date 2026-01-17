#!/usr/bin/env python3
import argparse
from kupi.crawler import KupiCrawler
from console import Console

def main():
    parser = argparse.ArgumentParser(description="Kupi Crawler")
    parser.add_argument("--color", action="store_true", help="Show ANSI progress bar")
    parser.add_argument("--workers", type=int, help="Number of worker threads (default: CPU*2)")
    args = parser.parse_args()

    console = Console(total=0, use_colors=args.color)
    console.start()
    
    try:
        # KupiCrawler init currently takes base_dir, defaulting to data/kupi_raw. 
        # Leaving default for now as it wasn't exposed in original main either.
        crawler = KupiCrawler()
        crawler.run(console=console, workers=args.workers)
    finally:
        console.finish()

if __name__ == "__main__":
    main()
