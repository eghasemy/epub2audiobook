#!/usr/bin/env python3
"""
EPUB to Markdown conversion script using Calibre's ebook-convert.
"""

import argparse
import subprocess
import pathlib
import sys


def main():
    p = argparse.ArgumentParser(description="Convert EPUB to Markdown using Calibre")
    p.add_argument("epub", help="Path to input EPUB file")
    p.add_argument("--out", default="data/work/book.md", help="Output Markdown file path")
    args = p.parse_args()
    
    # Ensure input file exists
    epub_path = pathlib.Path(args.epub)
    if not epub_path.exists():
        print(f"Error: EPUB file '{args.epub}' not found", file=sys.stderr)
        sys.exit(1)
    
    # Create output directory
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        subprocess.check_call([
            "ebook-convert", str(epub_path), str(out_path),
            "--keep-links", "--pretty-print",
            "--chapter", '//*[(name()="h1" or name()="h2") and re:test(., "chapter|prologue|epilogue|part", "i")]'
        ])
        print(f"Wrote {args.out}")
    except subprocess.CalledProcessError as e:
        print(f"Error running ebook-convert: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: ebook-convert command not found. Please install Calibre.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()