#!/usr/bin/env python3
"""
Package audio chunks into a chapterized M4B audiobook file.
"""

import json
import pathlib
import subprocess
import sys
import argparse
from datetime import timedelta


def get_audio_duration(wav_file):
    """Get duration of audio file using ffprobe."""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
            "-of", "csv=p=0", str(wav_file)
        ], capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return 0.0


def format_timestamp(seconds):
    """Format seconds as HH:MM:SS.mmm for chapter timestamps."""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    milliseconds = int((td.total_seconds() - total_seconds) * 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def create_chapters_file(wav_files, output_path):
    """Create ffmpeg chapters file."""
    chapters = []
    current_time = 0.0
    
    for i, wav_file in enumerate(wav_files):
        duration = get_audio_duration(wav_file)
        
        chapter = f"""[CHAPTER]
TIMEBASE=1/1000
START={int(current_time * 1000)}
END={int((current_time + duration) * 1000)}
title=Chapter {i + 1}
"""
        chapters.append(chapter)
        current_time += duration
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(";FFMETADATA1\n")
        f.write("title=Audiobook\n")
        f.write("artist=TTS Generated\n")
        f.write("album=EPUB Conversion\n")
        f.write("\n".join(chapters))


def main():
    p = argparse.ArgumentParser(description="Package audio into M4B audiobook")
    p.add_argument("--wav_dir", default="data/work/wavs_master", 
                   help="Directory containing mastered WAV files")
    p.add_argument("--manifest", default="data/work/manifest.json", 
                   help="Chunk manifest JSON file")
    p.add_argument("--output", default="data/output/audiobook.m4b", 
                   help="Output M4B file path")
    p.add_argument("--title", default="Audiobook", 
                   help="Book title for metadata")
    p.add_argument("--artist", default="TTS Generated", 
                   help="Artist/author for metadata")
    p.add_argument("--album", default="EPUB Conversion", 
                   help="Album for metadata")
    p.add_argument("--cover", default="resources/cover.jpg", 
                   help="Cover image file")
    p.add_argument("--bitrate", default="64k", 
                   help="Audio bitrate for M4B encoding")
    args = p.parse_args()
    
    wav_dir = pathlib.Path(args.wav_dir)
    
    # Check input directory exists
    if not wav_dir.exists():
        print(f"Error: WAV directory '{args.wav_dir}' not found", file=sys.stderr)
        sys.exit(1)
    
    # Find WAV files
    wav_files = sorted(wav_dir.glob("chunk_*.wav"))
    if not wav_files:
        print(f"Error: No chunk_*.wav files found in {args.wav_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Create work directory and output directory
    work_dir = pathlib.Path("data/work")
    work_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Packaging {len(wav_files)} audio files into M4B...")
    
    # Create concat file for ffmpeg
    concat_file = work_dir / "concat.txt"
    with open(concat_file, 'w', encoding='utf-8') as f:
        for wav in wav_files:
            f.write(f"file '{wav.resolve()}'\n")
    
    # Create chapters metadata file
    chapters_file = work_dir / "chapters.txt"
    create_chapters_file(wav_files, chapters_file)
    
    # Merge WAVs into single file
    merged_wav = work_dir / "book_merged.wav"
    print("Merging audio files...")
    
    try:
        subprocess.check_call([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
            "-i", str(concat_file), "-c", "copy", str(merged_wav)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error merging audio files: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: ffmpeg command not found. Please install ffmpeg.", file=sys.stderr)
        sys.exit(1)
    
    # Convert to M4B with chapters and metadata
    print("Converting to M4B with chapters...")
    
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", str(merged_wav),
        "-i", str(chapters_file),
        "-map_metadata", "1",
        "-c:a", "aac",
        "-b:a", args.bitrate,
        "-f", "mp4",
        "-metadata", f"title={args.title}",
        "-metadata", f"artist={args.artist}",
        "-metadata", f"album={args.album}",
        "-metadata", "genre=Audiobook"
    ]
    
    # Add cover art if available
    cover_path = pathlib.Path(args.cover)
    if cover_path.exists():
        ffmpeg_cmd.extend(["-i", str(cover_path), "-map", "2", "-c:v", "copy", "-disposition:v", "attached_pic"])
    
    ffmpeg_cmd.append(str(output_path))
    
    try:
        subprocess.check_call(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error creating M4B file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Clean up intermediate files
    merged_wav.unlink(missing_ok=True)
    concat_file.unlink(missing_ok=True)
    chapters_file.unlink(missing_ok=True)
    
    print(f"Successfully created M4B audiobook: {args.output}")
    
    # Show file info
    file_size = output_path.stat().st_size / (1024 * 1024)  # MB
    print(f"File size: {file_size:.1f} MB")


if __name__ == "__main__":
    main()