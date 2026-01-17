#!/usr/bin/env python3
import argparse
import sys
import os

from wolt.parser import WoltParser, VENUES
from console import Console

def run(store_name=None):
    parser = argparse.ArgumentParser(description="Wolt Parser")
    parser.add_argument("--store", type=str, choices=VENUES.keys(), help="Predefined store alias")
    parser.add_argument("--dir", type=str, help="Custom raw data directory")
    parser.add_argument("--name", type=str, help="Custom store display name")
    parser.add_argument("--output", type=str, help="Custom output JSON path")
    parser.add_argument("--workers", type=int, help="Number of parallel processes (default: CPU/2)")
    parser.add_argument("--color", action="store_true", help="Show ANSI progress bar")
    args = parser.parse_args()

    # Determine params
    data_dir = args.dir
    args_store_name = args.name
    output_path = args.output

    # Priority: Function arg > CLI arg > Config
    target_store = store_name or args.store

    if target_store:
        if target_store not in VENUES:
             parser.error(f"Store '{target_store}' not found in configuration.")
        venue_config = VENUES[target_store]
        data_dir = data_dir or venue_config["dir"]
        args_store_name = args_store_name or venue_config["name"]
        output_path = output_path or venue_config["output"]

    if not data_dir or not args_store_name or not output_path:
        parser.error("You must specify --store or all of --dir, --name, and --output")

    console = Console(total=0, use_colors=args.color)
    console.start()

    try:
        wolt_parser = WoltParser(
            data_dir=data_dir,
            store_name=args_store_name,
            output_path=output_path,
            console=console
        )
        wolt_parser.run(workers=args.workers)
    finally:
        console.finish()

if __name__ == "__main__":
    run()
