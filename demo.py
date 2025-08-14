#!/usr/bin/env python3
"""
Demonstration script for the epub2audiobook pipeline.
Creates sample data and runs through the complete pipeline.
"""

import os
import sys
import pathlib
import tempfile
import shutil


def create_sample_markdown():
    """Create a sample markdown file to test the pipeline."""
    sample_content = """# The Adventure of the Empty House

## Chapter 1: The Return

It was in the spring of the year 1894 that all London was interested, and the fashionable world dismayed, by the murder of the Honourable Ronald Adair under most unusual and inexplicable circumstances.

The public has already learned those particulars of the crime which came out in the police investigation; but a good deal was suppressed upon that trial which is now revealed for the first time.

Dr. Watson was walking down Baker Street when he encountered his old friend.

"Holmes!" he exclaimed. "You're alive!"

## Chapter 2: The Investigation

The investigation proceeded with the usual methodical approach that had made Sherlock Holmes famous throughout the U.K.

Mr. Holmes examined the evidence carefully. The API of deduction, as he often called it, required precise observation.

### The Evidence

Several key pieces of evidence were discovered:

- A peculiar footprint measuring approx. 10.5 inches
- A cigar ash from a rare Cuban variety  
- GPS coordinates written on a scrap of paper: 51.5074° N, 0.1278° W
- A mysterious note mentioning the FBI and CIA

The investigation would prove that even in 1894, international intrigue was not uncommon in London.

## Chapter 3: The Solution

"Elementary, my dear Watson," said Holmes. "The solution was obvious from the beginning."

And indeed, as Holmes explained the case, it became clear that the murderer had left a trail of clues as obvious as a URL in a web browser.

The case was closed by 3:30 PM that very day, much to the satisfaction of Scotland Yard and the public at large.

---

*End of Sample Story*
"""
    
    work_dir = pathlib.Path("data/work")
    work_dir.mkdir(parents=True, exist_ok=True)
    
    md_file = work_dir / "sample_book.md"
    md_file.write_text(sample_content, encoding="utf-8")
    return md_file


def main():
    print("🎧 EPUB to Audiobook Pipeline Demo")
    print("===================================")
    
    # Check if we're in the right directory
    if not pathlib.Path("scripts").exists() or not pathlib.Path("README.md").exists():
        print("❌ Error: Please run this script from the epub2audiobook directory")
        sys.exit(1)
    
    print("📝 Creating sample content...")
    sample_file = create_sample_markdown()
    print(f"✅ Sample content created: {sample_file}")
    
    print("\n🧹 Step 1: Cleaning and chunking text...")
    os.system(f"python scripts/clean_and_chunk.py --md {sample_file} --max_chars 800")
    
    # Check if chunks were created
    chunks_dir = pathlib.Path("data/work/chunks")
    if chunks_dir.exists():
        chunk_files = list(chunks_dir.glob("chunk_*.txt"))
        print(f"✅ Created {len(chunk_files)} text chunks")
        
        # Show first chunk as example
        if chunk_files:
            first_chunk = chunk_files[0].read_text(encoding="utf-8")
            print(f"\n📄 Sample chunk content:")
            print(f"File: {chunk_files[0].name}")
            print(f"Content (first 200 chars): {first_chunk[:200]}...")
    
    print("\n🎤 Step 2: Generating TTS audio (placeholder)...")
    os.system("python scripts/tts_generate.py --tier fast")
    
    # Check if audio was generated
    wavs_dir = pathlib.Path("data/work/wavs")
    if wavs_dir.exists():
        audio_files = list(wavs_dir.glob("chunk_*.*"))
        print(f"✅ Generated {len(audio_files)} audio files (placeholder)")
    
    print("\n🎛️ Step 3: Audio mastering...")
    print("ℹ️  Skipped (requires ffmpeg and actual audio files)")
    
    print("\n📦 Step 4: Packaging...")
    print("ℹ️  Skipped (requires ffmpeg and actual audio files)")
    
    print(f"\n✅ Demo complete!")
    print(f"\nGenerated files:")
    print(f"- Markdown: {sample_file}")
    print(f"- Chunks: data/work/chunks/")
    print(f"- Manifest: data/work/manifest.json")
    if wavs_dir.exists():
        print(f"- Audio: data/work/wavs/")
    
    print(f"\n📖 To run with real TTS:")
    print(f"1. Install TTS models (see README)")
    print(f"2. Update scripts/tts_generate.py with your TTS implementation")
    print(f"3. Install ffmpeg: sudo apt install ffmpeg")
    print(f"4. Run: make all")
    
    print(f"\n🎉 Ready for real audiobook production!")


if __name__ == "__main__":
    main()