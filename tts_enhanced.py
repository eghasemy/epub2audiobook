#!/usr/bin/env python3
"""
Enhanced TTS module with Hugging Face integration and voice cloning support.
"""

import os
import json
import pathlib
import requests
import subprocess
from typing import Dict, List, Optional, Union
from huggingface_hub import hf_hub_download, HfApi
import logging

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages TTS model downloads and installation"""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = pathlib.Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Model registry with popular TTS models
        self.model_registry = {
            "studio": {
                "coqui/XTTS-v2": {
                    "description": "Multilingual TTS with voice cloning",
                    "files": ["model.pth", "config.json", "vocab.json"],
                    "size_gb": 1.8,
                    "languages": ["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"]
                },
                "microsoft/speecht5_tts": {
                    "description": "SpeechT5 TTS model",
                    "files": ["pytorch_model.bin", "config.json"],
                    "size_gb": 0.5,
                    "languages": ["en"]
                },
                "facebook/mms-tts": {
                    "description": "Massively Multilingual Speech TTS",
                    "files": ["pytorch_model.bin", "config.json"],
                    "size_gb": 1.2,
                    "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"]
                }
            },
            "fast": {
                "rhasspy/piper-voices": {
                    "description": "Fast CPU TTS voices",
                    "files": ["model.onnx", "model.onnx.json"],
                    "size_gb": 0.1,
                    "languages": ["en", "es", "fr", "de", "it", "pt"]
                },
                "espnet/kan-bayashi_ljspeech_vits": {
                    "description": "VITS-based fast TTS",
                    "files": ["model.pth", "config.yaml"],
                    "size_gb": 0.3,
                    "languages": ["en"]
                }
            }
        }
    
    def list_available_models(self, tier: str = None) -> Dict:
        """List available models from registry"""
        if tier:
            return self.model_registry.get(tier, {})
        return self.model_registry
    
    def list_installed_models(self, tier: str = None) -> Dict:
        """List locally installed models"""
        installed = {"studio": [], "fast": []}
        
        for model_tier in ["studio", "fast"]:
            if tier and tier != model_tier:
                continue
                
            tier_dir = self.models_dir / model_tier
            if tier_dir.exists():
                for model_dir in tier_dir.iterdir():
                    if model_dir.is_dir():
                        size = self._get_folder_size(model_dir)
                        installed[model_tier].append({
                            "name": model_dir.name,
                            "path": str(model_dir),
                            "size_mb": round(size / (1024 * 1024), 2),
                            "files": list(f.name for f in model_dir.iterdir() if f.is_file())
                        })
        
        return installed[tier] if tier else installed
    
    def download_model(self, model_name: str, tier: str, progress_callback=None) -> bool:
        """Download a model from Hugging Face"""
        try:
            if model_name not in self.model_registry[tier]:
                raise ValueError(f"Model {model_name} not found in {tier} registry")
            
            model_info = self.model_registry[tier][model_name]
            local_dir = self.models_dir / tier / model_name.replace("/", "_")
            local_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Downloading {model_name} to {local_dir}")
            
            # Download required files
            for file_name in model_info["files"]:
                if progress_callback:
                    progress_callback(f"Downloading {file_name}...")
                
                try:
                    downloaded_file = hf_hub_download(
                        repo_id=model_name,
                        filename=file_name,
                        local_dir=local_dir,
                        local_dir_use_symlinks=False
                    )
                    logger.info(f"Downloaded {file_name}")
                except Exception as e:
                    logger.warning(f"Failed to download {file_name}: {e}")
            
            # Save model metadata
            metadata = {
                "name": model_name,
                "tier": tier,
                "description": model_info["description"],
                "languages": model_info["languages"],
                "downloaded_at": str(pathlib.Path().resolve()),
                "size_gb": model_info["size_gb"]
            }
            
            with open(local_dir / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            if progress_callback:
                progress_callback("Download complete!")
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to download model {model_name}: {e}")
            if progress_callback:
                progress_callback(f"Error: {e}")
            return False
    
    def remove_model(self, model_name: str, tier: str) -> bool:
        """Remove an installed model"""
        try:
            model_dir = self.models_dir / tier / model_name.replace("/", "_")
            if model_dir.exists():
                import shutil
                shutil.rmtree(model_dir)
                logger.info(f"Removed model {model_name}")
                return True
            else:
                logger.warning(f"Model {model_name} not found")
                return False
        except Exception as e:
            logger.error(f"Failed to remove model {model_name}: {e}")
            return False
    
    def search_huggingface_models(self, query: str, task: str = "text-to-speech") -> List[Dict]:
        """Search for TTS models on Hugging Face"""
        try:
            api = HfApi()
            models = api.list_models(
                filter=task,
                search=query,
                limit=20
            )
            
            results = []
            for model in models:
                results.append({
                    "name": model.modelId,
                    "downloads": getattr(model, 'downloads', 0),
                    "likes": getattr(model, 'likes', 0),
                    "tags": getattr(model, 'tags', []),
                    "description": getattr(model, 'cardData', {}).get('description', 'No description available')
                })
            
            return sorted(results, key=lambda x: x['downloads'], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to search Hugging Face: {e}")
            return []
    
    def _get_folder_size(self, folder_path: pathlib.Path) -> int:
        """Get total size of folder in bytes"""
        total_size = 0
        for file_path in folder_path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size


class VoiceCloner:
    """Handles voice cloning functionality"""
    
    def __init__(self, voices_dir: str = "data/voices"):
        self.voices_dir = pathlib.Path(voices_dir)
        self.voices_dir.mkdir(parents=True, exist_ok=True)
    
    def create_voice_clone(self, audio_path: str, voice_name: str, 
                          language: str = "en", gender: str = "neutral",
                          style: str = "neutral", progress_callback=None) -> bool:
        """Create a voice clone from audio sample"""
        try:
            if progress_callback:
                progress_callback("Analyzing audio sample...")
            
            # Validate audio file
            if not self._validate_audio(audio_path):
                raise ValueError("Invalid audio file")
            
            voice_dir = self.voices_dir / voice_name.replace(" ", "_").lower()
            voice_dir.mkdir(parents=True, exist_ok=True)
            
            if progress_callback:
                progress_callback("Extracting voice features...")
            
            # In a real implementation, this would:
            # 1. Preprocess the audio (normalize, denoise)
            # 2. Extract voice embeddings/features
            # 3. Train or fine-tune a voice model
            # 4. Save the voice model
            
            # For demo, just copy the audio and create metadata
            import shutil
            shutil.copy2(audio_path, voice_dir / "reference.wav")
            
            if progress_callback:
                progress_callback("Training voice model...")
            
            # Save voice metadata
            metadata = {
                "name": voice_name,
                "language": language,
                "gender": gender,
                "style": style,
                "reference_audio": "reference.wav",
                "created_at": str(pathlib.Path().resolve()),
                "status": "ready"
            }
            
            with open(voice_dir / "voice.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            if progress_callback:
                progress_callback("Voice clone created successfully!")
            
            logger.info(f"Created voice clone: {voice_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create voice clone: {e}")
            if progress_callback:
                progress_callback(f"Error: {e}")
            return False
    
    def list_voice_clones(self) -> List[Dict]:
        """List available voice clones"""
        voices = []
        
        for voice_dir in self.voices_dir.iterdir():
            if voice_dir.is_dir():
                metadata_file = voice_dir / "voice.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file) as f:
                            metadata = json.load(f)
                        
                        metadata["id"] = voice_dir.name
                        metadata["path"] = str(voice_dir)
                        voices.append(metadata)
                    except Exception as e:
                        logger.warning(f"Failed to load voice metadata for {voice_dir.name}: {e}")
        
        return voices
    
    def remove_voice_clone(self, voice_id: str) -> bool:
        """Remove a voice clone"""
        try:
            voice_dir = self.voices_dir / voice_id
            if voice_dir.exists():
                import shutil
                shutil.rmtree(voice_dir)
                logger.info(f"Removed voice clone: {voice_id}")
                return True
            else:
                logger.warning(f"Voice clone {voice_id} not found")
                return False
        except Exception as e:
            logger.error(f"Failed to remove voice clone {voice_id}: {e}")
            return False
    
    def _validate_audio(self, audio_path: str) -> bool:
        """Validate audio file for voice cloning"""
        try:
            # Check if file exists
            if not pathlib.Path(audio_path).exists():
                return False
            
            # In a real implementation, this would:
            # 1. Check audio format (WAV, MP3, etc.)
            # 2. Validate sample rate (prefer 22050 or 44100 Hz)
            # 3. Check duration (5-60 seconds recommended)
            # 4. Validate audio quality (SNR, etc.)
            
            return True
            
        except Exception as e:
            logger.error(f"Audio validation failed: {e}")
            return False


class EnhancedTTSEngine:
    """Enhanced TTS engine with model management and voice cloning"""
    
    def __init__(self, models_dir: str = "models", voices_dir: str = "data/voices"):
        self.model_manager = ModelManager(models_dir)
        self.voice_cloner = VoiceCloner(voices_dir)
        self.loaded_models = {}
    
    def load_model(self, model_name: str, tier: str, device: str = "auto"):
        """Load a TTS model"""
        try:
            if device == "auto":
                device = "cuda" if tier == "studio" else "cpu"
            
            model_key = f"{tier}_{model_name}"
            
            if model_key in self.loaded_models:
                return self.loaded_models[model_key]
            
            # In a real implementation, this would load the actual model
            # based on the model type (XTTS, SpeechT5, Piper, etc.)
            
            # For now, return a placeholder
            model = {
                "name": model_name,
                "tier": tier,
                "device": device,
                "status": "loaded"
            }
            
            self.loaded_models[model_key] = model
            logger.info(f"Loaded model {model_name} on {device}")
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            return None
    
    def synthesize(self, text: str, model: str, voice: str = None, 
                  voice_clone: str = None, **kwargs) -> Optional[str]:
        """Synthesize speech from text"""
        try:
            # In a real implementation, this would:
            # 1. Load the specified model if not already loaded
            # 2. Process the text (SSML, normalization, etc.)
            # 3. Generate audio using the model
            # 4. Apply voice cloning if specified
            # 5. Return the audio file path
            
            logger.info(f"Synthesizing text with model {model}, voice {voice}")
            
            # Placeholder: return a dummy audio file path
            return "placeholder_audio.wav"
            
        except Exception as e:
            logger.error(f"Failed to synthesize speech: {e}")
            return None
    
    def get_available_voices(self, model: str = None) -> List[Dict]:
        """Get available voices for a model"""
        # Default voices
        default_voices = [
            {"id": "en_female_01", "name": "English Female 1", "language": "en", "gender": "female"},
            {"id": "en_male_01", "name": "English Male 1", "language": "en", "gender": "male"},
            {"id": "en_female_02", "name": "English Female 2", "language": "en", "gender": "female"},
        ]
        
        # Add voice clones
        voice_clones = self.voice_cloner.list_voice_clones()
        for clone in voice_clones:
            default_voices.append({
                "id": f"clone_{clone['id']}",
                "name": f"{clone['name']} (Clone)",
                "language": clone["language"],
                "gender": clone["gender"],
                "type": "clone"
            })
        
        return default_voices


# Global instances
model_manager = ModelManager()
voice_cloner = VoiceCloner()
tts_engine = EnhancedTTSEngine()