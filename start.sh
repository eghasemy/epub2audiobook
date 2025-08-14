#!/bin/bash
set -e

echo "🚀 Starting EPUB to Audiobook with Web Interface"
echo "================================================"

# Create required directories
mkdir -p data/{input,work,output,voices} models/{studio,fast} resources

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "📦 Running in Docker container"
    # Install any missing dependencies in container
    pip install -r requirements.txt
else
    echo "💻 Running locally"
    # Check if virtual environment should be created
    if [ ! -d "venv" ]; then
        echo "🔧 Creating virtual environment..."
        python3 -m venv venv
    fi
    
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
    
    echo "📋 Installing dependencies..."
    pip install -r requirements.txt
fi

echo "🌐 Starting web interface..."
echo "   Access at: http://localhost:5000"
echo "   For Unraid: Use your server IP instead of localhost"
echo ""

# Set environment variables for production
export FLASK_ENV=production
export FLASK_DEBUG=false

# Start the application
python app.py