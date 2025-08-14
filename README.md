# Local EPUB → Audiobook: Build Guide + Ready‑to‑Run Stack

This guide shows you how to build a **fully local** EPUB→audiobook system that rivals premium AI TTS services. It includes:

- Architecture overview
- Hardware & OS requirements
- Two TTS quality tiers (GPU “studio” and CPU “fast”)
- Docker Compose stack
- Python pipeline for EPUB parsing, text cleanup, SSML‑like prosody, and chapterized M4B output
- Pronunciation/dictionary control
- Audio mastering (loudness, de‑ess, breaths/pacing)
- Voice cloning (optional) & ethics note
- Performance tips & QA checklist

---

## 1) Architecture Overview

**Ingest → Clean → Narrate → Master → Package**

1. **Ingest**: Convert EPUB to clean Markdown or plain text with structure (chapters, headings, blockquotes).
2. **Clean**: Normalize punctuation, numbers, dates; fix hyphenation; expand abbreviations; insert SSML‑like cues for pauses & emphasis.
3. **Narrate (TTS)**: Choose a voice/model; generate per‑chunk WAVs with explicit pacing and pronunciation control.
4. **Master**: Loudness normalize (\~−18 LUFS mono / −16 LUFS stereo), de‑ess, light EQ, room tone, gap insertion.
5. **Package**: Chapterize and export **M4B** (or MP3), embed cover art & metadata, write cue/chapters.

---

## 2) Requirements

- **OS**: Linux (Ubuntu 22.04+), Windows 11, or macOS (Apple Silicon works, GPU features vary).
- **GPU (for “studio” quality)**: NVIDIA RTX 3060 12GB+ recommended; CUDA 12.x drivers. You can run CPU‑only with the “fast” tier.
- **Disk**: 10–30 GB for models & intermediates.
- **Python**: 3.10+.
- **Docker**: 24+ (optional but recommended for reproducibility).

---

## 3) Model Tiers

You can run both and switch per‑book.

### A) **Studio Quality (GPU, multilingual, expressive)**

- Modern neural TTS (e.g., **XTTS‑class** or **StyleTTS‑class** models) with high fidelity, emotion, and cross‑lingual support.
- Supports **reference voice** (3–10s) for cloning‑style timbre where permitted.
- Prosody controls via phonemes, durations, and paragraph/phrase breaks.

**Pros**: Premium feel, natural phrasing, robust for novels & non‑fiction.\
**Cons**: Requires decent GPU; slower than CPU‑fast.

### B) **Fast Tier (CPU‑friendly, lightweight)**

- Lightweight inference engines (e.g., **Piper‑class** models) that run realtime on CPU.
- Good baseline quality, especially with a well‑chosen speaker & a smoothing vocoder.

**Pros**: Simple, fast, low power.\
**Cons**: Less expressive; diction can be flatter.

---

## 4) Project Layout

```
epub2audiobook/
├─ docker-compose.yml
├─ .env
├─ models/                 # place downloaded models here (not in repo)
├─ data/
│  ├─ input/               # your .epub files
│  ├─ work/                # intermediates (markdown, chunks, wavs)
│  └─ output/              # final m4b/mp3
├─ scripts/
│  ├─ epub_to_md.py
│  ├─ clean_and_chunk.py
│  ├─ tts_generate.py
│  ├─ master_audio.py
│  └─ package_m4b.py
└─ resources/
   ├─ lexicon_user.txt     # custom pronunciations (word  phonemes)
   ├─ abbreviations.yml
   └─ cover.jpg
```

---

## 5) Docker Compose (GPU + CPU services)

```yaml
version: "3.9"
services:
  # Optional: Calibre CLI in a tiny container for robust EPUB→MD
  calibre:
    image: linuxserver/calibre
    volumes:
      - ./data:/data
    entrypoint: ["/bin/sh","-lc"]
    command: >
      "ebook-convert /data/input/book.epub /data/work/book.md \
       --chapter '//*[(name()="h1" or name()="h2") and re:test(., "chapter|prologue|epilogue|part", "i")]' \
       --keep-links --pretty-print"

  # Studio-quality TTS (GPU). Swap in your preferred model server.
  tts_gpu:
    image: nvcr.io/nvidia/pytorch:24.01-py3
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    volumes:
      - ./scripts:/workspace/scripts
      - ./data:/workspace/data
      - ./models:/workspace/models
      - ./resources:/workspace/resources
    working_dir: /workspace
    command: ["python","scripts/tts_generate.py","--tier","studio"]

  # Fast CPU TTS
  tts_cpu:
    image: python:3.11-slim
    volumes:
      - ./scripts:/app/scripts
      - ./data:/app/data
      - ./models:/app/models
      - ./resources:/app/resources
    working_dir: /app
    command: ["python","scripts/tts_generate.py","--tier","fast"]

  # Post (mastering + packaging)
  post:
    image: python:3.11-slim
    volumes:
      - ./scripts:/app/scripts
      - ./data:/app/data
      - ./resources:/app/resources
    working_dir: /app
    command: ["/bin/bash","-lc","python scripts/master_audio.py && python scripts/package_m4b.py"]
```

> Tip: Run steps individually while you iterate. When satisfied, chain them in a Makefile.

---

## 6) Step‑by‑Step Pipeline Scripts

Below are reference implementations. They aim for clarity; you can optimize later.

### 6.1 EPUB → Markdown

```python
# scripts/epub_to_md.py
import argparse, subprocess, pathlib
p = argparse.ArgumentParser()
p.add_argument("epub")
p.add_argument("--out", default="data/work/book.md")
args = p.parse_args()
pathlib.Path("data/work").mkdir(parents=True, exist_ok=True)
subprocess.check_call([
    "ebook-convert", args.epub, args.out,
    "--keep-links", "--pretty-print",
    "--chapter", '//*[(name()="h1" or name()="h2") and re:test(., "chapter|prologue|epilogue|part", "i")]'
])
print("Wrote", args.out)
```

### 6.2 Clean & Chunk (SSML‑ish cues)

```python
# scripts/clean_and_chunk.py
import re, argparse, pathlib, json
from textwrap import dedent

p = argparse.ArgumentParser()
p.add_argument("--md", default="data/work/book.md")
p.add_argument("--max_chars", type=int, default=1200)
p.add_argument("--out_dir", default="data/work/chunks")
p.add_argument("--abbr", default="resources/abbreviations.yml")
p.add_argument("--lexicon", default="resources/lexicon_user.txt")
args = p.parse_args()

text = pathlib.Path(args.md).read_text(encoding="utf-8")

# Basic normalizations
text = text.replace("\u00A0", " ")
text = re.sub(r"([\p{L}\d])—([\p{L}\d])", r"\1 — \2", text)
text = re.sub(r"\s+", " ", text)

# Headings → strong pauses
text = re.sub(r"(^|\n)#{1,6} *(.*)", r"\n<break time=\"1200ms\"/><emphasis level=\"strong\">\2</emphasis>\n<break time=\"800ms\"/>", text)

# Paragraphs
paras = re.split(r"\n{2,}", text)

# Simple abbreviation expansion (load your YAML as needed)
ABBR = {"Mr.": "Mister", "Dr.": "Doctor", "e.g.": "for example"}

def split_into_chunks(paragraphs, max_chars):
    chunk, acc = [], 0
    for para in paragraphs:
        p = para.strip()
        if not p:
            continue
        for k,v in ABBR.items():
            p = p.replace(k, v)
        p += " <break time=\"250ms\"/>"
        if acc + len(p) > max_chars and chunk:
            yield " ".join(chunk)
            chunk, acc = [p], len(p)
        else:
            chunk.append(p); acc += len(p)
    if chunk:
        yield " ".join(chunk)

out = pathlib.Path(args.out_dir)
out.mkdir(parents=True, exist_ok=True)
manifest = []
for i, ch in enumerate(split_into_chunks(paras, args.max_chars)):
    fp = out / f"chunk_{i:04d}.txt"
    fp.write_text(ch, encoding="utf-8")
    manifest.append({"idx": i, "text_file": str(fp)})

(pathlib.Path("data/work/manifest.json").write_text(json.dumps(manifest, indent=2)))
print(f"Wrote {len(manifest)} chunks")
```

### 6.3 TTS Generation (Studio vs Fast)

Replace the `# TODO` sections with your chosen local model loaders. The interface is the same: input text with simple SSML‑like tags, output WAV.

```python
# scripts/tts_generate.py
import argparse, json, pathlib, soundfile as sf
from tqdm import tqdm

p = argparse.ArgumentParser()
p.add_argument("--tier", choices=["studio","fast"], default="studio")
p.add_argument("--voice", default="en_female_01")
p.add_argument("--ref_audio", default=None)  # optional for cloning
p.add_argument("--rate", type=float, default=1.0) # global speed
p.add_argument("--pitch", type=float, default=0.0)
p.add_argument("--manifest", default="data/work/manifest.json")
p.add_argument("--out_dir", default="data/work/wavs")
args = p.parse_args()

# --- Load model(s) ---
if args.tier == "studio":
    # TODO: load a high‑quality GPU model (e.g., XTTS‑class / StyleTTS‑class)
    # model = load_studio_model(model_dir="models/studio", device="cuda")
    pass
else:
    # TODO: load a fast CPU model (e.g., Piper‑class)
    # model = load_fast_model(model_dir="models/fast", device="cpu")
    pass

# --- SSML-ish parser: convert <break> and <emphasis> to model‑specific controls ---
import re
BREAK = re.compile(r"<break time=\"(\d+)ms\"/>")
EMPH  = re.compile(r"<emphasis level=\"(\w+)\">(.*?)</emphasis>")

def synthesize(text: str):
    # Example: strip tags for basic engines; advanced engines can consume them
    pauses = [int(ms) for ms in BREAK.findall(text)]
    plain = BREAK.sub(" ", text)
    plain = EMPH.sub(lambda m: m.group(2).upper() if m.group(1)=="strong" else m.group(2), plain)
    # TODO: y = model.tts(plain, rate=args.rate, pitch=args.pitch, voice=args.voice, ref=args.ref_audio)
    y = None  # placeholder
    assert y is not None, "Implement your model synth here"
    return y

manifest = json.loads(pathlib.Path(args.manifest).read_text())
pathlib.Path(args.out_dir).mkdir(parents=True, exist_ok=True)

for it in tqdm(manifest):
    txt = pathlib.Path(it["text_file"]).read_text()
    audio = synthesize(txt)
    sf.write(f"{args.out_dir}/chunk_{it['idx']:04d}.wav", audio, 24000)  # or 22050/44100 per model
```

### 6.4 Mastering (Loudness, De‑Ess, Room Tone)

```python
# scripts/master_audio.py
import pathlib, subprocess, json

WAV_DIR = pathlib.Path("data/work/wavs")
OUT_DIR = pathlib.Path("data/work/wavs_master")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 1) Normalize to -18 LUFS mono (or -16 stereo) with ffmpeg loudnorm
for wav in sorted(WAV_DIR.glob("chunk_*.wav")):
    out = OUT_DIR / wav.name
    subprocess.check_call([
        "ffmpeg","-y","-i",str(wav),
        "-af","loudnorm=I=-18:TP=-1.0:LRA=11",
        str(out)
    ])

# 2) Optional: light de-ess
# subprocess.check_call(["ffmpeg","-y","-i",str(out),"-af","deesser=f=5500:t=0.5", str(out)])

print("Mastered WAVs →", OUT_DIR)
```

### 6.5 Package into Chapterized M4B

```python
# scripts/package_m4b.py
import json, pathlib, subprocess

chapters = json.loads(pathlib.Path("data/work/manifest.json").read_text())
wavs = sorted(pathlib.Path("data/work/wavs_master").glob("chunk_*.wav"))
concat = pathlib.Path("data/work/concat.txt")
concat.write_text("\n".join([f"file '{w.as_posix()}'" for w in wavs]))

# Merge WAVs
merged = pathlib.Path("data/work/book_merged.wav")
subprocess.check_call(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(merged)])

# Chapters: s
```
