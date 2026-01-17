#!/usr/bin/env python3
import argparse

from tesco.parser import TescoParser
from console import Console

def main():
    parser = argparse.ArgumentParser(description="Tesco Parser")
    parser.add_argument("--color", action="store_true", help="Show ANSI progress bar")
    args = parser.parse_args()

    console = Console(total=0, use_colors=args.color)
    console.start()
    
    try:
        parser = TescoParser(console=console)
        parser.run()
    finally:
        console.finish()

if __name__ == "__main__":
    main()
