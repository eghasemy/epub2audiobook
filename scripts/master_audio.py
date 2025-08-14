#!/usr/bin/env python3
"""
Audio mastering script for loudness normalization and audio processing.
"""

import pathlib
import subprocess
import sys
import argparse


def run_ffmpeg_command(cmd, description=""):
    """Run ffmpeg command with error handling."""
    try:
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        print(f"Error {description}: {error_msg}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("Error: ffmpeg command not found. Please install ffmpeg.", file=sys.stderr)
        return False
    return True


def main():
    p = argparse.ArgumentParser(description="Master audio files with loudness normalization")
    p.add_argument("--wav_dir", default="data/work/wavs", 
                   help="Input directory containing WAV files")
    p.add_argument("--out_dir", default="data/work/wavs_master", 
                   help="Output directory for mastered files")
    p.add_argument("--lufs", type=float, default=-18.0, 
                   help="Target LUFS level for loudness normalization")
    p.add_argument("--true_peak", type=float, default=-1.0, 
                   help="True peak maximum level")
    p.add_argument("--lra", type=float, default=11.0, 
                   help="Loudness range target")
    p.add_argument("--deess", action="store_true", 
                   help="Apply light de-essing")
    p.add_argument("--deess_freq", type=float, default=5500.0, 
                   help="De-esser frequency")
    p.add_argument("--deess_threshold", type=float, default=0.5, 
                   help="De-esser threshold")
    args = p.parse_args()
    
    wav_dir = pathlib.Path(args.wav_dir)
    out_dir = pathlib.Path(args.out_dir)
    
    # Check input directory exists
    if not wav_dir.exists():
        print(f"Error: Input directory '{args.wav_dir}' not found", file=sys.stderr)
        sys.exit(1)
    
    # Create output directory
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Find WAV files
    wav_files = sorted(wav_dir.glob("chunk_*.wav"))
    if not wav_files:
        print(f"Warning: No chunk_*.wav files found in {args.wav_dir}")
        return
    
    print(f"Processing {len(wav_files)} audio files...")
    
    success_count = 0
    for wav in wav_files:
        print(f"Processing {wav.name}...")
        out_file = out_dir / wav.name
        
        # Build ffmpeg command for loudness normalization
        cmd = [
            "ffmpeg", "-y", "-i", str(wav),
            "-af", f"loudnorm=I={args.lufs}:TP={args.true_peak}:LRA={args.lra}",
            str(out_file)
        ]
        
        if run_ffmpeg_command(cmd, f"normalizing {wav.name}"):
            # Apply de-essing if requested
            if args.deess:
                temp_file = out_file.with_suffix('.temp.wav')
                deess_cmd = [
                    "ffmpeg", "-y", "-i", str(out_file),
                    "-af", f"deesser=f={args.deess_freq}:t={args.deess_threshold}",
                    str(temp_file)
                ]
                
                if run_ffmpeg_command(deess_cmd, f"de-essing {wav.name}"):
                    # Replace original with de-essed version
                    temp_file.replace(out_file)
                else:
                    # Clean up temp file if de-essing failed
                    if temp_file.exists():
                        temp_file.unlink()
            
            success_count += 1
        else:
            print(f"Failed to process {wav.name}")
    
    print(f"Mastered {success_count}/{len(wav_files)} files → {out_dir}")
    
    if success_count == 0:
        print("No files were successfully processed!", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()