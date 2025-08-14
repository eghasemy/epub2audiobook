# Troubleshooting Guide

This guide helps you resolve common issues when setting up and running epub2audiobook.

## Build/Import Issues

### "ModuleNotFoundError: No module named 'flask'" (Line 16 in app.py)

**Problem**: You're seeing this error when trying to run `python app.py`:

```
Traceback (most recent call last):
  File "/app/app.py", line 16, in <module>
    from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
ModuleNotFoundError: No module named 'flask'
```

**Solution**: The Python dependencies haven't been installed. Choose one of these methods:

#### Method 1: Using Makefile (Recommended)
```bash
make install
```

#### Method 2: Using pip directly
```bash
pip install -r requirements.txt
```

#### Method 3: Using setup script
```bash
./setup.sh
```

#### Method 4: Install minimal dependencies
If you're having network issues, install just the essential web interface dependencies:
```bash
pip install Flask>=2.3.0 Werkzeug>=2.3.0
```

### Network/SSL Issues During Installation

**Problem**: Getting SSL certificate errors or timeouts during `pip install`:

```
SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED]
```

**Solutions**:

1. **Update pip and certificates**:
   ```bash
   pip install --upgrade pip
   pip install --upgrade certifi
   ```

2. **Use trusted hosts (temporary workaround)**:
   ```bash
   pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
   ```

3. **Try with different timeout**:
   ```bash
   pip install --timeout 60 -r requirements.txt
   ```

### Docker Build Issues

**Problem**: Docker build fails with dependency installation errors.

**Solution**: 
1. Check your internet connection
2. Try building with `--no-cache` flag:
   ```bash
   docker build --no-cache -t epub2audiobook .
   ```
3. If still failing, try the pre-built Docker Compose setup:
   ```bash
   docker-compose up
   ```

## Missing Dependencies

### System Dependencies

Make sure you have the required system packages:

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install python3-pip ffmpeg calibre
```

**macOS**:
```bash
brew install python ffmpeg
# Download Calibre from https://calibre-ebook.com/download
```

### Python Version

Ensure you're using Python 3.10 or newer:
```bash
python3 --version
```

If you're using an older version, update Python before installing dependencies.

## Web Interface Issues

### Port Already in Use

**Problem**: `Address already in use` error when starting the web interface.

**Solution**: 
1. Kill the existing process:
   ```bash
   lsof -ti:5000 | xargs kill -9
   ```
2. Or use a different port:
   ```bash
   PORT=5001 python app.py
   ```

### Permission Denied Errors

**Problem**: Can't create directories or write files.

**Solution**: 
1. Check file permissions:
   ```bash
   ls -la data/
   ```
2. Fix permissions if needed:
   ```bash
   chmod -R 755 data/ models/
   ```

## Getting Help

If you're still having issues:

1. **Check the main README.md** for setup instructions
2. **Verify all prerequisites** are installed
3. **Try the demo script** to test your setup:
   ```bash
   python demo.py
   ```
4. **Check system requirements** in the prerequisites section

For Docker-related issues, see the [Web Interface Guide](WEB_INTERFACE_GUIDE.md).