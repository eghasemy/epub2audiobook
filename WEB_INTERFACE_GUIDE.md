# EPUB to Audiobook - Enhanced Web Interface

**Version 2.0 - Now with Modern Web Interface, Voice Cloning & Unraid Support**

## 🆕 What's New

This enhanced version adds a complete web interface to the original EPUB to audiobook conversion pipeline, making it accessible to users who prefer a graphical interface over command-line tools.

### Key Enhancements

1. **🌐 Modern Web Interface**
   - User-friendly dashboard
   - Drag & drop file uploads
   - Real-time conversion progress
   - Mobile-responsive design

2. **🤖 Automated Model Management**
   - Browse and install TTS models from Hugging Face
   - One-click model downloads
   - Storage management and cleanup
   - Support for custom model uploads

3. **🎙️ Voice Cloning Capabilities**
   - Create custom voices from audio samples
   - Advanced voice configuration options
   - Voice testing and preview
   - Voice library management

4. **📦 Full Unraid Support**
   - Docker container optimized for Unraid
   - Community Applications template
   - Proper volume mapping
   - Web UI integration

## 🚀 Quick Start Guide

### Option 1: Unraid Installation

1. **Install from Community Applications**:
   - Search for "EPUB to Audiobook" in Community Applications
   - Click Install and configure paths

2. **Manual Docker Installation**:
   ```bash
   docker run -d \
     --name epub2audiobook \
     -p 5000:5000 \
     -v /mnt/user/appdata/epub2audiobook/data:/app/data \
     -v /mnt/user/appdata/epub2audiobook/models:/app/models \
     ghcr.io/eghasemy/epub2audiobook:latest
   ```

3. **Access Web Interface**:
   - Open `http://YOUR-UNRAID-IP:5000` in your browser

### Option 2: Docker Compose

```bash
git clone https://github.com/eghasemy/epub2audiobook.git
cd epub2audiobook
docker-compose up epub2audiobook
```

### Option 3: Local Installation

```bash
git clone https://github.com/eghasemy/epub2audiobook.git
cd epub2audiobook
make install  # Install Python dependencies
python app.py  # Start the web interface
```

> **Build Error?** If you see `ModuleNotFoundError: No module named 'flask'`, the Python dependencies aren't installed. Run `make install` or `pip install -r requirements.txt` first. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more help.

## 🖥️ Using the Web Interface

### 1. Dashboard Overview

The dashboard provides:
- **System Status**: GPU availability, model counts
- **Quick Actions**: Access to all main features
- **Recent Conversions**: Track your audiobook projects
- **System Information**: Version, features, support links

### 2. Model Management

**Installing Models**:
1. Go to the "Models" page
2. Browse available models in the "Available Models" section
3. Click "Install" on your desired model
4. Wait for download and installation to complete

**Popular Models**:
- **XTTS-v2**: Best for voice cloning and multilingual support
- **SpeechT5**: Good quality English TTS
- **Piper Voices**: Fast CPU processing

### 3. Voice Cloning

**Creating a Voice Clone**:
1. Go to the "Voice Cloning" page
2. Enter a name for your voice
3. Upload 10-30 seconds of clear audio
4. Configure language and style settings
5. Click "Create Voice Clone"

**Best Practices**:
- Use high-quality, noise-free audio
- 15-30 seconds of natural speech works best
- Consistent volume and pace
- Avoid background noise

### 4. Converting Books

**Step-by-Step Process**:
1. Go to "Upload Book"
2. Drag and drop your EPUB file or click "Browse Files"
3. Configure conversion settings:
   - Choose quality tier (Studio or Fast)
   - Select voice (built-in or your clones)
   - Adjust speech rate and other parameters
4. Click "Start Conversion"
5. Monitor progress in real-time
6. Download your finished audiobook

## 🔧 Configuration Options

### Quality Tiers

**Studio Quality** (GPU Recommended):
- High-quality neural TTS models
- Voice cloning support
- Multilingual capabilities
- Requires GPU with 6GB+ VRAM

**Fast CPU**:
- Lightweight models optimized for CPU
- Good quality with faster processing
- Lower resource requirements
- No GPU needed

### Voice Settings

- **Speech Rate**: 0.5x to 2.0x normal speed
- **Pitch Adjustment**: ±12 semitones
- **Voice Selection**: Choose from installed voices or clones
- **Advanced Options**: Chunk size, processing parameters

## 📁 File Organization

The web interface automatically manages files in these directories:

```
data/
├── input/          # Upload your EPUB files here
├── work/           # Temporary processing files
├── output/         # Finished audiobook files
└── voices/         # Your voice clones

models/
├── studio/         # High-quality TTS models
└── fast/           # Fast CPU TTS models
```

## 🔗 API Access

The web interface provides REST API endpoints for automation:

```bash
# List available models
curl http://localhost:5000/api/models

# Start conversion
curl -X POST http://localhost:5000/api/convert \
  -H "Content-Type: application/json" \
  -d '{"filename": "book.epub", "settings": {"tier": "fast"}}'

# Check job status
curl http://localhost:5000/api/jobs/{job_id}/status
```

## 🚨 Troubleshooting

### Common Issues

**Web interface not loading**:
- Check that port 5000 is accessible
- Verify the container is running: `docker ps`
- Check firewall settings

**Models not downloading**:
- Ensure internet connectivity
- Verify sufficient disk space
- Check Hugging Face service status

**GPU not detected**:
- Install NVIDIA Docker runtime
- Add `--gpus all` to docker run command
- Verify CUDA drivers are installed

**Voice cloning fails**:
- Check audio file format (WAV, MP3, M4A)
- Ensure audio is 10-30 seconds
- Try with different audio sample

### Performance Tips

**For Studio Quality**:
- Use GPU with 8GB+ VRAM
- Allocate sufficient Docker memory
- Use SSD storage for models

**For Fast Processing**:
- Ensure 4GB+ RAM available
- Use Piper models for best CPU performance
- Process smaller books for faster response

## 🔄 Migration from CLI Version

The web interface is fully compatible with the original CLI pipeline:

1. **Existing Models**: Place in `models/studio/` or `models/fast/`
2. **Existing Scripts**: All CLI scripts remain functional
3. **Configuration**: Environment variables still supported
4. **Data**: Existing `data/` directory structure is preserved

You can use both interfaces simultaneously - the web UI for ease of use and CLI for automation/scripting.

## 🤝 Support

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Full API documentation available
- **Community**: Join discussions in GitHub Discussions

---

**Ready to create your first audiobook with the web interface? 🎧**

1. Access the web interface at `http://localhost:5000`
2. Download a TTS model from the Models page
3. Upload your EPUB file
4. Configure your settings
5. Start the conversion and download your audiobook!