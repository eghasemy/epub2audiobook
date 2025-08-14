#!/usr/bin/env python3
"""
Modern web interface for EPUB to Audiobook conversion.
Provides a user-friendly interface for the entire pipeline.
"""

import os
import sys
import json
import pathlib
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Check for required dependencies with helpful error messages
try:
    from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
    from werkzeug.utils import secure_filename
except ImportError as e:
    print("❌ Missing required dependencies!")
    print("")
    print("ERROR: " + str(e))
    print("")
    print("To fix this issue, run one of the following commands:")
    print("  make install")
    print("  pip install -r requirements.txt")
    print("  ./start.sh")
    print("")
    print("For more help, see TROUBLESHOOTING.md")
    print("")
    exit(1)

import threading

# Import enhanced TTS functionality
from tts_enhanced import model_manager, voice_cloner, tts_engine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configuration
UPLOAD_FOLDER = 'data/input'
WORK_FOLDER = 'data/work'
OUTPUT_FOLDER = 'data/output'
MODELS_FOLDER = 'models'
ALLOWED_EXTENSIONS = {'epub'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Ensure directories exist
for folder in [UPLOAD_FOLDER, WORK_FOLDER, OUTPUT_FOLDER, MODELS_FOLDER]:
    pathlib.Path(folder).mkdir(parents=True, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_system_status():
    """Get current system status"""
    status = {
        'gpu_available': False,
        'models_installed': {},
        'recent_jobs': []
    }
    
    # Check GPU availability
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        status['gpu_available'] = result.returncode == 0
    except:
        status['gpu_available'] = False
    
    # Check installed models
    studio_models = list(pathlib.Path(f'{MODELS_FOLDER}/studio').glob('*')) if pathlib.Path(f'{MODELS_FOLDER}/studio').exists() else []
    fast_models = list(pathlib.Path(f'{MODELS_FOLDER}/fast').glob('*')) if pathlib.Path(f'{MODELS_FOLDER}/fast').exists() else []
    
    status['models_installed'] = {
        'studio': len(studio_models),
        'fast': len(fast_models)
    }
    
    return status

@app.route('/')
def index():
    """Main dashboard"""
    status = get_system_status()
    return render_template('dashboard.html', status=status)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Handle EPUB file upload"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            flash(f'File {filename} uploaded successfully!', 'success')
            return redirect(url_for('process_book', filename=filename))
        else:
            flash('Invalid file type. Please upload an EPUB file.', 'error')
    
    return render_template('upload.html')

@app.route('/process/<filename>')
def process_book(filename):
    """Book processing interface"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        flash('File not found', 'error')
        return redirect(url_for('index'))
    
    # Get available models and voices
    available_models = get_available_models()
    voices = get_available_voices()
    
    return render_template('process.html', 
                         filename=filename, 
                         models=available_models,
                         voices=voices)

@app.route('/api/models')
def get_available_models():
    """Get list of available TTS models"""
    installed = model_manager.list_installed_models()
    return jsonify(installed)

@app.route('/api/voices')
def get_available_voices():
    """Get list of available voices"""
    voices = tts_engine.get_available_voices()
    return jsonify(voices)

@app.route('/api/convert', methods=['POST'])
def start_conversion():
    """Start the EPUB to audiobook conversion process"""
    data = request.get_json()
    
    filename = data.get('filename')
    settings = data.get('settings', {})
    
    if not filename:
        return jsonify({'error': 'No filename provided'}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    # Start conversion in background thread
    job_id = start_conversion_job(filepath, settings)
    
    return jsonify({
        'job_id': job_id,
        'status': 'started',
        'message': 'Conversion started successfully'
    })

@app.route('/api/jobs/<job_id>/status')
def get_job_status(job_id):
    """Get status of a conversion job"""
    # In a real implementation, this would check job status from a queue/database
    # For now, return a placeholder response
    return jsonify({
        'job_id': job_id,
        'status': 'running',
        'progress': 45,
        'current_step': 'Generating TTS audio',
        'estimated_time_remaining': '15 minutes'
    })

@app.route('/models')
def model_management():
    """Model management interface"""
    installed_models = model_manager.list_installed_models()
    available_models = model_manager.list_available_models()
    
    # Convert to the format expected by the template
    huggingface_models = []
    for tier, models in available_models.items():
        for model_name, model_info in models.items():
            huggingface_models.append({
                'name': model_name,
                'description': model_info['description'],
                'downloads': f"{model_info['size_gb']}GB",
                'type': tier
            })
    
    return render_template('models.html', 
                         installed=installed_models,
                         available=huggingface_models)

@app.route('/api/models/download', methods=['POST'])
def download_model():
    """Download a model from Hugging Face or other sources"""
    data = request.get_json()
    model_name = data.get('model_name')
    model_type = data.get('model_type', 'fast')
    
    if not model_name:
        return jsonify({'error': 'Model name required'}), 400
    
    # Start model download in background
    job_id = start_model_download(model_name, model_type)
    
    return jsonify({
        'job_id': job_id,
        'status': 'downloading',
        'message': f'Started downloading {model_name}'
    })

@app.route('/voice-cloning')
def voice_cloning():
    """Voice cloning interface"""
    return render_template('voice_cloning.html')

@app.route('/api/voice-clone', methods=['POST'])
def create_voice_clone():
    """Create a voice clone from uploaded audio"""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    voice_name = request.form.get('voice_name', 'custom_voice')
    
    if audio_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save the audio file
    filename = secure_filename(audio_file.filename)
    audio_path = os.path.join('data/voice_samples', filename)
    pathlib.Path('data/voice_samples').mkdir(parents=True, exist_ok=True)
    audio_file.save(audio_path)
    
    # Start voice cloning process
    job_id = start_voice_cloning(audio_path, voice_name)
    
    return jsonify({
        'job_id': job_id,
        'status': 'processing',
        'message': f'Started creating voice clone: {voice_name}'
    })

def get_folder_size(folder_path):
    """Get the size of a folder in MB"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return round(total_size / (1024 * 1024), 2)  # Convert to MB

def get_popular_hf_models():
    """Get list of popular TTS models from Hugging Face"""
    # In a real implementation, this would query the HF API
    return [
        {
            'name': 'microsoft/speecht5_tts',
            'description': 'SpeechT5 Text-to-Speech model',
            'downloads': '50k+',
            'type': 'fast'
        },
        {
            'name': 'coqui/XTTS-v2',
            'description': 'Multilingual TTS with voice cloning',
            'downloads': '100k+',
            'type': 'studio'
        },
        {
            'name': 'facebook/fastspeech2-en-ljspeech',
            'description': 'FastSpeech2 English TTS',
            'downloads': '25k+',
            'type': 'fast'
        }
    ]

def start_conversion_job(filepath, settings):
    """Start conversion job in background thread"""
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def run_conversion():
        try:
            # Run the conversion pipeline
            tier = settings.get('tier', 'fast')
            voice = settings.get('voice', 'en_female_01')
            
            # Convert EPUB to markdown
            subprocess.run([
                sys.executable, 'scripts/epub_to_md.py', filepath
            ], check=True)
            
            # Clean and chunk
            subprocess.run([
                sys.executable, 'scripts/clean_and_chunk.py'
            ], check=True)
            
            # Generate TTS
            subprocess.run([
                sys.executable, 'scripts/tts_generate.py',
                '--tier', tier,
                '--voice', voice
            ], check=True)
            
            # Master audio
            subprocess.run([
                sys.executable, 'scripts/master_audio.py'
            ], check=True)
            
            # Package
            subprocess.run([
                sys.executable, 'scripts/package_m4b.py'
            ], check=True)
            
            logger.info(f"Conversion job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Conversion job {job_id} failed: {e}")
    
    thread = threading.Thread(target=run_conversion)
    thread.daemon = True
    thread.start()
    
    return job_id

def start_model_download(model_name, model_type):
    """Start model download in background thread"""
    job_id = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def download_model():
        try:
            def progress_callback(message):
                logger.info(f"Download progress: {message}")
            
            success = model_manager.download_model(model_name, model_type, progress_callback)
            if success:
                logger.info(f"Model download job {job_id} completed successfully")
            else:
                logger.error(f"Model download job {job_id} failed")
            
        except Exception as e:
            logger.error(f"Model download job {job_id} failed: {e}")
    
    thread = threading.Thread(target=download_model)
    thread.daemon = True
    thread.start()
    
    return job_id

def start_voice_cloning(audio_path, voice_name):
    """Start voice cloning in background thread"""
    job_id = f"clone_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def clone_voice():
        try:
            def progress_callback(message):
                logger.info(f"Voice cloning progress: {message}")
            
            success = voice_cloner.create_voice_clone(
                audio_path, voice_name, progress_callback=progress_callback
            )
            if success:
                logger.info(f"Voice cloning job {job_id} completed successfully")
            else:
                logger.error(f"Voice cloning job {job_id} failed")
            
        except Exception as e:
            logger.error(f"Voice cloning job {job_id} failed: {e}")
    
    thread = threading.Thread(target=clone_voice)
    thread.daemon = True
    thread.start()
    
    return job_id

if __name__ == '__main__':
    # Check if we're in development or production
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    app.run(host=host, port=port, debug=debug_mode)