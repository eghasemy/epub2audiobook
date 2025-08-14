# Makefile for epub2audiobook pipeline
# Usage: make help

.PHONY: help install setup clean convert-epub clean-text generate-tts master package all fast studio

# Default variables
EPUB_FILE ?= data/input/book.epub
VOICE ?= en_female_01
TIER ?= studio

help:
	@echo "EPUB to Audiobook Pipeline"
	@echo ""
	@echo "Usage:"
	@echo "  make install          Install Python dependencies"
	@echo "  make setup            Create directory structure"
	@echo "  make convert-epub     Convert EPUB to Markdown (requires EPUB_FILE)"
	@echo "  make clean-text       Clean and chunk text"
	@echo "  make generate-tts     Generate TTS audio (TIER=studio|fast)"
	@echo "  make master          Master audio files"
	@echo "  make package         Package into M4B"
	@echo "  make all             Run complete pipeline"
	@echo "  make studio          Run with studio quality TTS"
	@echo "  make fast            Run with fast CPU TTS"
	@echo "  make clean           Clean work files"
	@echo ""
	@echo "Variables:"
	@echo "  EPUB_FILE=$(EPUB_FILE)"
	@echo "  VOICE=$(VOICE)"
	@echo "  TIER=$(TIER)"

install:
	pip install -r requirements.txt

setup:
	mkdir -p data/{input,work,output} models/{studio,fast} resources
	@echo "Directory structure created"
	@echo "Place your EPUB file in data/input/"
	@echo "Place TTS models in models/studio/ or models/fast/"

convert-epub:
	@if [ ! -f "$(EPUB_FILE)" ]; then \
		echo "Error: EPUB file $(EPUB_FILE) not found"; \
		echo "Place your EPUB file in data/input/ or set EPUB_FILE variable"; \
		exit 1; \
	fi
	python scripts/epub_to_md.py "$(EPUB_FILE)"

clean-text:
	python scripts/clean_and_chunk.py

generate-tts:
	python scripts/tts_generate.py --tier $(TIER) --voice $(VOICE)

master:
	python scripts/master_audio.py

package:
	python scripts/package_m4b.py

all: convert-epub clean-text generate-tts master package

studio:
	$(MAKE) all TIER=studio

fast:
	$(MAKE) all TIER=fast

clean:
	rm -rf data/work/*
	@echo "Work files cleaned"

# Docker commands
docker-studio:
	docker-compose run --rm tts_gpu

docker-fast:
	docker-compose run --rm tts_cpu

docker-post:
	docker-compose run --rm post

# Development helpers
test-epub:
	@echo "Testing with sample EPUB conversion..."
	@if [ ! -f "data/input/book.epub" ]; then \
		echo "Error: No EPUB file found in data/input/"; \
		echo "Please place an EPUB file there to test"; \
		exit 1; \
	fi
	python scripts/epub_to_md.py data/input/book.epub
	python scripts/clean_and_chunk.py
	@echo "Text processing complete. Check data/work/ for results."

lint:
	@which black >/dev/null 2>&1 && black scripts/ || echo "black not installed"
	@which flake8 >/dev/null 2>&1 && flake8 scripts/ || echo "flake8 not installed"