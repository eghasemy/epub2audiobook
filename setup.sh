#!/bin/bash

# EPUB to Audiobook Setup Script
# Automates the initial setup of the epub2audiobook pipeline

set -e

echo "🎧 EPUB to Audiobook Pipeline Setup"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "scripts" ]; then
    echo "❌ Error: Please run this script from the epub2audiobook directory"
    exit 1
fi

# Check Python version
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
required_version="3.10"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
    echo "❌ Error: Python 3.10+ required. Found: $(python3 --version)"
    echo "   Please install Python 3.10 or newer"
    exit 1
fi
echo "✅ Python version OK: $(python3 --version)"

# Check for required system dependencies
echo "🔧 Checking system dependencies..."

check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        echo "✅ $1 is installed"
        return 0
    else
        echo "❌ $1 is not installed"
        return 1
    fi
}

# Check for ffmpeg
if ! check_command ffmpeg; then
    echo "   Install with: sudo apt install ffmpeg (Linux) or brew install ffmpeg (macOS)"
    missing_deps=true
fi

# Check for calibre (ebook-convert)
if ! check_command ebook-convert; then
    echo "   Install with: sudo apt install calibre (Linux) or download from calibre-ebook.com"
    missing_deps=true
fi

if [ "$missing_deps" = true ]; then
    echo ""
    echo "❌ Missing required dependencies. Please install them and run setup again."
    exit 1
fi

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p data/{input,work,output}
mkdir -p models/{studio,fast}
mkdir -p resources
echo "✅ Directory structure created"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install --user -r requirements.txt
    echo "✅ Python dependencies installed"
else
    echo "❌ requirements.txt not found"
    exit 1
fi

# Copy environment template if .env doesn't exist
if [ ! -f ".env" ] && [ -f ".env.template" ]; then
    echo "⚙️ Creating .env file from template..."
    cp .env.template .env
    echo "✅ .env file created (edit as needed)"
fi

# Create a sample input directory message
echo "📖 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Place your EPUB file in data/input/"
echo "2. Set up TTS models in models/studio/ or models/fast/"
echo "3. Run: make all"
echo ""
echo "Quick test:"
echo "  cp your_book.epub data/input/book.epub"
echo "  make all"
echo ""
echo "For more information, see the README.md file."
echo ""
echo "🎉 Ready to convert EPUBs to audiobooks!"