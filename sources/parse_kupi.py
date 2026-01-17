#!/usr/bin/env python3
import argparse
from kupi.parser import KupiParser
from console import Console

def main():
    parser = argparse.ArgumentParser(description="Kupi Parser")
    parser.add_argument("--color", action="store_true", help="Show ANSI progress bar")
    args = parser.parse_args()

    console = Console(total=0, use_colors=args.color)
    console.start()

    try:
        parser = KupiParser()
        parser.run(console=console)
    finally:
        console.finish()

if __name__ == "__main__":
    main()
