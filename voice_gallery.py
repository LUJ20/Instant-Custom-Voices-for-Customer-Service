"""
Copyright 2026 Google LLC
Author: Layolin Jesudhass <layolin@google.com>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import time
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("voice_gallery")

MAX_GALLERY_SIZE = 25


class VoiceGalleryManager:
    """Manages custom voice profiles dynamically from metadata and audio assets."""

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self.assets_dir = os.path.join(base_dir, "assets")
        else:
            self.assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        
        os.makedirs(self.assets_dir, exist_ok=True)
        self.metadata_file = os.path.join(self.assets_dir, "gallery_metadata.json")
        self.voices: List[Dict[str, Any]] = []
        self._load_gallery()

    def _load_gallery(self):
        """Loads gallery metadata dynamically from disk or initializes defaults."""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        self.voices = data
                        return
            except Exception as e:
                logger.error("Error reading gallery metadata: %s", e)
        
        # Initialize default voices
        self.restore_default_voices()

    def _save_gallery(self):
        """Persists gallery metadata to disk."""
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.voices, f, indent=2)
        except Exception as e:
            logger.error("Error saving gallery metadata: %s", e)

    def restore_default_voices(self) -> List[Dict[str, Any]]:
        """Restores the standard bundled reference voice profiles."""
        existing_keys = {v.get("id"): v.get("voice_cloning_key") for v in self.voices if v.get("voice_cloning_key")}
        self.voices = [
            {
                "id": "voice_indian_female",
                "name": "Indian Female",
                "gender": "Female",
                "native_locale": "en-IN",
                "pitch": 0.0,
                "speaking_rate": 1.0,
                "audio_file": "layo_voice.mp3",
                "voice_cloning_key": existing_keys.get("voice_indian_female", "")
            },
            {
                "id": "voice_indian_male",
                "name": "Indian Male",
                "gender": "Male",
                "native_locale": "en-IN",
                "pitch": 0.0,
                "speaking_rate": 1.0,
                "audio_file": "rahul_voice.mp3",
                "voice_cloning_key": existing_keys.get("voice_indian_male", "")
            }
        ]
        self._save_gallery()
        return self.voices

    def get_all_voices(self) -> List[Dict[str, Any]]:
        """Returns all active custom voice profiles."""
        return self.voices

    def get_voice_by_id(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific custom voice profile by ID."""
        for v in self.voices:
            if v.get("id") == voice_id:
                return v
        return None

    def add_voice(
        self,
        name: str,
        audio_bytes: bytes,
        gender: str = "Female",
        native_locale: str = "en-IN",
        pitch: float = 0.0,
        speaking_rate: float = 1.0
    ) -> Optional[Dict[str, Any]]:
        """Adds a new custom voice profile to the gallery (up to MAX_GALLERY_SIZE)."""
        if len(self.voices) >= MAX_GALLERY_SIZE:
            logger.warning("Voice gallery full (max %d)", MAX_GALLERY_SIZE)
            return None

        clean_name = name.strip() or f"Custom Voice {len(self.voices) + 1}"
        voice_id = f"voice_{int(time.time() * 1000)}_{len(self.voices)}"
        filename = f"{voice_id}.mp3"
        filepath = os.path.join(self.assets_dir, filename)

        try:
            with open(filepath, "wb") as f:
                f.write(audio_bytes)
        except Exception as e:
            logger.error("Error saving voice audio file: %s", e)
            return None

        new_voice = {
            "id": voice_id,
            "name": clean_name,
            "gender": gender,
            "native_locale": native_locale,
            "pitch": pitch,
            "speaking_rate": speaking_rate,
            "audio_file": filename
        }
        self.voices.append(new_voice)
        self._save_gallery()
        return new_voice

    def update_voice_profile(self, voice_id: str, updates: Dict[str, Any]) -> bool:
        """Updates properties (e.g. name, gender, locale) of an existing custom voice profile."""
        for v in self.voices:
            if v.get("id") == voice_id:
                for key, val in updates.items():
                    if key not in ("id", "audio_file"):
                        v[key] = val
                self._save_gallery()
                return True
        return False

    def rename_voice(self, voice_id: str, new_name: str) -> bool:
        """Renames an existing voice profile."""
        clean = new_name.strip()
        if not clean:
            return False
        return self.update_voice_profile(voice_id, {"name": clean})

    def remove_voice(self, voice_id: str) -> bool:
        """Removes any custom voice profile from the gallery."""
        for i, v in enumerate(self.voices):
            if v.get("id") == voice_id:
                audio_file = v.get("audio_file", "")
                if audio_file and not audio_file.startswith(("layo_voice", "rahul_voice")):
                    audio_path = os.path.join(self.assets_dir, audio_file)
                    if os.path.exists(audio_path):
                        try:
                            os.remove(audio_path)
                        except Exception:
                            pass
                
                self.voices.pop(i)
                self._save_gallery()
                return True
        return False

    def get_audio_bytes(self, voice_id: str) -> Optional[bytes]:
        """Returns the raw reference audio bytes for a custom voice."""
        voice = self.get_voice_by_id(voice_id)
        if not voice:
            return None
        
        filepath = os.path.join(self.assets_dir, voice.get("audio_file", ""))
        if os.path.exists(filepath):
            try:
                with open(filepath, "rb") as f:
                    return f.read()
            except Exception as e:
                logger.error("Error reading audio for %s: %s", voice_id, e)
        return None
