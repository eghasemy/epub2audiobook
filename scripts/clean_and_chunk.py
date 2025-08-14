#!/usr/bin/env python3
"""
Clean and chunk text for TTS processing with SSML-like cues.
"""

import re
import argparse
import pathlib
import json
import yaml
import sys
from textwrap import dedent


def load_abbreviations(abbr_file):
    """Load abbreviations from YAML file."""
    try:
        if pathlib.Path(abbr_file).exists():
            with open(abbr_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Warning: Could not load abbreviations from {abbr_file}: {e}")
    
    # Default abbreviations
    return {"Mr.": "Mister", "Dr.": "Doctor", "e.g.": "for example"}


def split_into_chunks(paragraphs, max_chars, abbreviations):
    """Split paragraphs into chunks of specified maximum character length."""
    chunk, acc = [], 0
    for para in paragraphs:
        p = para.strip()
        if not p:
            continue
        
        # Apply abbreviation expansions
        for k, v in abbreviations.items():
            p = p.replace(k, v)
        
        # Add pause after paragraph
        p += " <break time=\"250ms\"/>"
        
        if acc + len(p) > max_chars and chunk:
            yield " ".join(chunk)
            chunk, acc = [p], len(p)
        else:
            chunk.append(p)
            acc += len(p)
    
    if chunk:
        yield " ".join(chunk)


def main():
    p = argparse.ArgumentParser(description="Clean and chunk text for TTS")
    p.add_argument("--md", default="data/work/book.md", help="Input Markdown file")
    p.add_argument("--max_chars", type=int, default=1200, help="Maximum characters per chunk")
    p.add_argument("--out_dir", default="data/work/chunks", help="Output directory for chunks")
    p.add_argument("--abbr", default="resources/abbreviations.yml", help="Abbreviations YAML file")
    p.add_argument("--lexicon", default="resources/lexicon_user.txt", help="User lexicon file")
    args = p.parse_args()
    
    # Check input file exists
    md_path = pathlib.Path(args.md)
    if not md_path.exists():
        print(f"Error: Markdown file '{args.md}' not found", file=sys.stderr)
        sys.exit(1)
    
    # Read input text
    text = md_path.read_text(encoding="utf-8")
    
    # Basic normalizations
    text = text.replace("\u00A0", " ")  # Replace non-breaking spaces
    text = re.sub(r"([\w\d])—([\w\d])", r"\1 — \2", text)  # Add spaces around em-dashes
    text = re.sub(r"\s+", " ", text)  # Normalize whitespace
    
    # Headings → strong pauses (process line by line to avoid greedy matching)
    lines = text.split('\n')
    processed_lines = []
    for line in lines:
        # Check if line is a heading
        if re.match(r'^#{1,6}\s+', line):
            # Extract heading text without the # symbols
            heading_text = re.sub(r'^#{1,6}\s+', '', line)
            processed_lines.append(f'<break time="1200ms"/><emphasis level="strong">{heading_text}</emphasis><break time="800ms"/>')
        else:
            processed_lines.append(line)
    text = '\n'.join(processed_lines)
    
    # Split into paragraphs
    paras = re.split(r"\n{2,}", text)
    
    # Load abbreviations
    abbreviations = load_abbreviations(args.abbr)
    
    # Create output directory
    out = pathlib.Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    # Generate chunks
    manifest = []
    for i, ch in enumerate(split_into_chunks(paras, args.max_chars, abbreviations)):
        fp = out / f"chunk_{i:04d}.txt"
        fp.write_text(ch, encoding="utf-8")
        manifest.append({"idx": i, "text_file": str(fp)})
    
    # Write manifest
    manifest_path = pathlib.Path("data/work/manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    
    print(f"Wrote {len(manifest)} chunks")


if __name__ == "__main__":
    main()