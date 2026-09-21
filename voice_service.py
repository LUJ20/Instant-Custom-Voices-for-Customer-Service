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
import io
import json
import base64
import logging
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import google.auth
from google.auth.transport.requests import AuthorizedSession

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False

logger = logging.getLogger("voice_service")

REQUIRED_CONSENT_SCRIPT = (
    "I am the owner of this voice and I consent to Google using this voice "
    "to create a synthetic voice model."
)

SUPPORTED_CONVERSATION_LANGUAGES = {
    "English (US)": {"code": "en-US", "trans_code": None, "native_name": "English"},
    "English (India)": {"code": "en-IN", "trans_code": None, "native_name": "Indian English"},
    "English (UK)": {"code": "en-GB", "trans_code": None, "native_name": "British English"},
    "Spanish (Español)": {"code": "es-US", "trans_code": "es", "native_name": "Español"},
    "French (Français)": {"code": "fr-FR", "trans_code": "fr", "native_name": "Français"},
    "German (Deutsch)": {"code": "de-DE", "trans_code": "de", "native_name": "Deutsch"},
    "Hindi (हिन्दी)": {"code": "hi-IN", "trans_code": "hi", "native_name": "हिन्दी"},
    "Japanese (日本語)": {"code": "ja-JP", "trans_code": "ja", "native_name": "日本語"},
    "Italian (Italiano)": {"code": "it-IT", "trans_code": "it", "native_name": "Italiano"},
    "Portuguese (Português)": {"code": "pt-BR", "trans_code": "pt", "native_name": "Português"},
    "Chinese Mandarin (中文)": {"code": "cmn-CN", "trans_code": "zh", "native_name": "中文"},
    "Korean (한국어)": {"code": "ko-KR", "trans_code": "ko", "native_name": "한국어"},
    "Arabic (العربية)": {"code": "ar-XA", "trans_code": "ar", "native_name": "العربية"}
}

# Curated Google Cloud Standard & Prebuilt Voices
STANDARD_CLOUD_VOICES = {
    "std_journey_d": {
        "id": "std_journey_d",
        "name": "Standard Journey-D (Natural Male)",
        "voice_type": "standard",
        "gender": "Male",
        "native_locale": "en-US",
        "timbre": "Journey-D",
        "pitch": 0.0,
        "speaking_rate": 1.0,
        "description": "Google Cloud natural, conversational male voice (Standard Cloud Voice)"
    },
    "std_journey_f": {
        "id": "std_journey_f",
        "name": "Standard Journey-F (Warm Female)",
        "voice_type": "standard",
        "gender": "Female",
        "native_locale": "en-US",
        "timbre": "Journey-F",
        "pitch": 0.0,
        "speaking_rate": 1.0,
        "description": "Google Cloud warm, expressive female voice (Standard Cloud Voice)"
    },
    "std_neural2_f": {
        "id": "std_neural2_f",
        "name": "Standard Neural2-F (Clear Female)",
        "voice_type": "standard",
        "gender": "Female",
        "native_locale": "en-US",
        "timbre": "Neural2-F",
        "pitch": 0.0,
        "speaking_rate": 1.0,
        "description": "Google Cloud Neural2 female studio voice (Standard Cloud Voice)"
    },
    "std_neural2_d": {
        "id": "std_neural2_d",
        "name": "Standard Neural2-D (Professional Male)",
        "voice_type": "standard",
        "gender": "Male",
        "native_locale": "en-US",
        "timbre": "Neural2-D",
        "pitch": 0.0,
        "speaking_rate": 1.0,
        "description": "Google Cloud Neural2 male professional voice (Standard Cloud Voice)"
    },
    "std_studio_o": {
        "id": "std_studio_o",
        "name": "Standard Studio-O (Empathetic Female)",
        "voice_type": "standard",
        "gender": "Female",
        "native_locale": "en-US",
        "timbre": "Studio-O",
        "pitch": 0.0,
        "speaking_rate": 1.0,
        "description": "Google Cloud high-fidelity Studio female voice (Standard Cloud Voice)"
    },
    "std_studio_q": {
        "id": "std_studio_q",
        "name": "Standard Studio-Q (Authoritative Male)",
        "voice_type": "standard",
        "gender": "Male",
        "native_locale": "en-US",
        "timbre": "Studio-Q",
        "pitch": 0.0,
        "speaking_rate": 1.0,
        "description": "Google Cloud high-fidelity Studio male voice (Standard Cloud Voice)"
    },
    "std_in_neural2_a": {
        "id": "std_in_neural2_a",
        "name": "Standard Indian Neural2-A (Female)",
        "voice_type": "standard",
        "gender": "Female",
        "native_locale": "en-IN",
        "timbre": "Neural2-A",
        "pitch": 0.0,
        "speaking_rate": 1.0,
        "description": "Google Cloud Indian English Neural2 female voice (Standard Cloud Voice)"
    },
    "std_in_neural2_b": {
        "id": "std_in_neural2_b",
        "name": "Standard Indian Neural2-B (Male)",
        "voice_type": "standard",
        "gender": "Male",
        "native_locale": "en-IN",
        "timbre": "Neural2-B",
        "pitch": 0.0,
        "speaking_rate": 1.0,
        "description": "Google Cloud Indian English Neural2 male voice (Standard Cloud Voice)"
    }
}


def get_standard_voice_model_for_language(voice_info: Dict[str, Any], lang_info: Dict[str, Any]) -> Tuple[str, str]:
    """Resolves standard Cloud TTS voice model name and locale for the selected conversation language."""
    gender = voice_info.get("gender", "Female").capitalize()
    lang_code = lang_info.get("code", "en-US")

    # Language-specific voice model lookup table
    std_language_map = {
        "en-US": {
            "Female": "en-US-Journey-F",
            "Male": "en-US-Journey-D"
        },
        "en-IN": {
            "Female": "en-IN-Neural2-A",
            "Male": "en-IN-Neural2-B"
        },
        "en-GB": {
            "Female": "en-GB-Neural2-A",
            "Male": "en-GB-Neural2-B"
        },
        "es-US": {
            "Female": "es-US-Neural2-A",
            "Male": "es-US-Neural2-B"
        },
        "fr-FR": {
            "Female": "fr-FR-Neural2-A",
            "Male": "fr-FR-Neural2-B"
        },
        "de-DE": {
            "Female": "de-DE-Neural2-F",
            "Male": "de-DE-Neural2-B"
        },
        "hi-IN": {
            "Female": "hi-IN-Neural2-A",
            "Male": "hi-IN-Neural2-B"
        },
        "ja-JP": {
            "Female": "ja-JP-Neural2-B",
            "Male": "ja-JP-Neural2-C"
        },
        "it-IT": {
            "Female": "it-IT-Neural2-A",
            "Male": "it-IT-Neural2-C"
        },
        "pt-BR": {
            "Female": "pt-BR-Neural2-A",
            "Male": "pt-BR-Neural2-B"
        },
        "cmn-CN": {
            "Female": "cmn-CN-Standard-A",
            "Male": "cmn-CN-Standard-B"
        },
        "ko-KR": {
            "Female": "ko-KR-Neural2-A",
            "Male": "ko-KR-Neural2-C"
        },
        "ar-XA": {
            "Female": "ar-XA-Standard-A",
            "Male": "ar-XA-Standard-B"
        }
    }

    if lang_code == "en-US" and voice_info.get("timbre"):
        timbre = voice_info.get("timbre")
        return "en-US", f"en-US-{timbre}"

    models_for_lang = std_language_map.get(lang_code, std_language_map["en-US"])
    voice_name = models_for_lang.get(gender, models_for_lang.get("Female", "en-US-Journey-F"))
    return lang_code, voice_name


def get_custom_voice_model_and_locale(voice_info: Dict[str, Any], lang_info: Dict[str, Any]) -> Tuple[str, str]:
    """Dynamically resolves the custom voice model and language locale for any chosen language."""
    gender = voice_info.get("gender", "Female").lower()
    custom_timbre = voice_info.get("timbre")
    if not custom_timbre:
        custom_timbre = "Aoede" if gender == "female" else "Fenrir"
    
    lang_code = lang_info.get("code", "en-US")
    # If English is chosen, respect voice's native English accent (e.g. en-IN, en-US, en-GB)
    if lang_code.startswith("en"):
        native_locale = voice_info.get("native_locale", lang_code)
        return native_locale, f"{native_locale}-Chirp3-HD-{custom_timbre}"
    
    # For non-English target languages, synthesize using the custom voice's timbre in the target locale
    return lang_code, f"{lang_code}-Chirp3-HD-{custom_timbre}"


class VoiceService:
    """Orchestrates custom voice cloning synthesis and multi-language conversation stitching."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        auth_account: Optional[str] = None
    ):
        self.project_id = (
            project_id
            or os.getenv("GOOGLE_CLOUD_PROJECT")
            or os.getenv("GCP_PROJECT")
            or os.getenv("TTS_PROJECT_ID")
            or self._get_gcloud_config_project()
        )
        self.location = (
            location
            or os.getenv("GOOGLE_CLOUD_LOCATION")
            or os.getenv("GCP_REGION")
            or "us-central1"
        )
        self.auth_account = auth_account or os.getenv("GCP_AUTH_ACCOUNT")
        self.session = None
        self.genai_client = None
        self._init_session()

    @staticmethod
    def _get_gcloud_config_project() -> Optional[str]:
        try:
            import subprocess
            proj = subprocess.check_output(
                ["gcloud", "config", "get-value", "project"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8").strip()
            if proj and proj != "(unset)":
                return proj
        except Exception:
            pass
        return None

    def _get_auth_headers(self) -> Dict[str, str]:
        """Dynamically retrieves authorized headers targeting the configured project."""
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        if self.project_id:
            headers["x-goog-user-project"] = self.project_id

        # 1. If explicit auth_account is configured, query access token for that identity
        if self.auth_account:
            try:
                import subprocess
                token = subprocess.check_output(
                    ["gcloud", "auth", "print-access-token", f"--account={self.auth_account}"],
                    stderr=subprocess.DEVNULL
                ).decode("utf-8").strip()
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                    return headers
            except Exception:
                pass

        # 2. Try default google auth credentials
        try:
            credentials, default_project = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            credentials.refresh(google.auth.transport.requests.Request())
            if credentials.token:
                headers["Authorization"] = f"Bearer {credentials.token}"
                if not self.project_id and default_project:
                    self.project_id = default_project
                    headers["x-goog-user-project"] = default_project
                return headers
        except Exception:
            pass

        # 3. Fallback to active gcloud access token
        try:
            import subprocess
            token = subprocess.check_output(
                ["gcloud", "auth", "print-access-token"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8").strip()
            if token:
                headers["Authorization"] = f"Bearer {token}"
                return headers
        except Exception:
            pass

        return headers

    def _init_session(self):
        try:
            credentials, default_project = google.auth.default()
            self.session = AuthorizedSession(credentials)
            if not self.project_id and default_project:
                self.project_id = default_project
        except Exception as e:
            logger.warning("Google Auth session initialization fallback: %s", e)
            self.session = None

        if HAS_GENAI and self.project_id:
            try:
                self.genai_client = genai.Client(
                    vertexai=True,
                    project=self.project_id,
                    location=self.location
                )
            except Exception as e:
                logger.warning("Gemini GenAI client init error: %s", e)
                self.genai_client = None

    def create_custom_voice_key(self, voice_info: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """Creates a Chirp 3 Instant Custom Voice cloning key from reference audio and consent script.
        
        Conforms to Google Cloud Text-to-Speech Instant Custom Voice specification.
        """
        if voice_info.get("voice_cloning_key"):
            return voice_info["voice_cloning_key"], None

        # Resolve reference audio bytes
        audio_bytes = voice_info.get("audio_bytes")
        if not audio_bytes and voice_info.get("audio_file"):
            path = os.path.join(os.path.dirname(__file__), "assets", voice_info["audio_file"])
            if os.path.exists(path):
                with open(path, "rb") as f:
                    audio_bytes = f.read()

        if not audio_bytes:
            return None, "No reference audio sample provided"

        import tempfile
        import subprocess

        with tempfile.TemporaryDirectory(prefix="cv_clone_") as tmpdir:
            src_file = os.path.join(tmpdir, "ref_raw.audio")
            with open(src_file, "wb") as f:
                f.write(audio_bytes)

            conv_file = os.path.join(tmpdir, "ref_linear16.wav")
            # Convert to 24kHz 16-bit mono WAV trimmed to 9.5s (API requirement)
            res = subprocess.run(
                ["ffmpeg", "-y", "-i", src_file, "-t", "9.5", "-ar", "24000", "-ac", "1", "-sample_fmt", "s16", conv_file],
                capture_output=True, text=True
            )
            if not os.path.exists(conv_file) or os.path.getsize(conv_file) < 1000:
                return None, f"FFmpeg audio preparation failed: {res.stderr[:200] if res.stderr else 'unknown'}"

            with open(conv_file, "rb") as f:
                ref_b64 = base64.b64encode(f.read()).decode("utf-8")

        url = "https://texttospeech.googleapis.com/v1beta1/voices:generateVoiceCloningKey"
        headers = self._get_auth_headers()
        body = {
            "reference_audio": {
                "audio_config": {"audio_encoding": "LINEAR16"},
                "content": ref_b64,
            },
            "voice_talent_consent": {
                "audio_config": {"audio_encoding": "LINEAR16"},
                "content": ref_b64,
            },
            "consent_script": REQUIRED_CONSENT_SCRIPT,
            "language_code": "en-US",
        }

        try:
            import requests
            resp = requests.post(url, headers=headers, json=body, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                vkey = data.get("voiceCloningKey")
                if vkey:
                    voice_info["voice_cloning_key"] = vkey
                    logger.info("Created Chirp 3 voice cloning key: %s...", vkey[:8])
                    return vkey, None
            logger.warning("Voice cloning API status %d: %s", resp.status_code, resp.text[:200])
        except Exception as e:
            logger.warning("Voice cloning exception: %s", e)

        return None, "Voice cloning key creation unavailable in current project scope"

    def synthesize_gemini_tts(
        self,
        text: str,
        voice_info: Optional[Dict[str, Any]] = None,
        speaker_role: str = "agent",
        conversation_language: str = "English (US)"
    ) -> bytes:
        """Synthesizes dialogue turn using Gemini 2.5 Flash Preview TTS with rich speaker persona conditioning."""
        if not HAS_GENAI or not self.genai_client:
            return b""

        v_info = voice_info or {}
        v_name = v_info.get("name", "Priya" if speaker_role == "agent" else "Rahul")
        gender = v_info.get("gender", "Female" if speaker_role == "agent" else "Male")
        native_locale = v_info.get("native_locale", "en-IN")
        timbre = "Aoede" if gender.lower() == "female" else "Fenrir"
        
        accent_desc = "Indian" if ("in" in native_locale.lower() or "indian" in v_name.lower()) else "natural"

        if speaker_role == "agent":
            prompt = (
                f"You are {v_name}, a helpful and empathetic customer service specialist with a natural {accent_desc} accent. "
                f"Read this dialogue turn with warmth, patience, and professional customer care pacing in {conversation_language}:\n\n{text}"
            )
        else:
            prompt = (
                f"You are {v_name}, a customer speaking with customer service with a natural {accent_desc} accent. "
                f"Read this dialogue turn in an expressive, conversational, natural tone in {conversation_language}:\n\n{text}"
            )

        try:
            resp = self.genai_client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=timbre)
                        )
                    ),
                ),
            )
            if resp.candidates and resp.candidates[0].content.parts:
                raw_pcm = resp.candidates[0].content.parts[0].inline_data.data
                if raw_pcm:
                    import subprocess
                    cmd = ["ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", "-", "-f", "mp3", "-b:a", "192k", "-"]
                    p = subprocess.run(cmd, input=raw_pcm, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                    if p.stdout and len(p.stdout) > 500:
                        return p.stdout
        except Exception as e:
            logger.warning("Gemini TTS synthesis exception: %s", e)

        return b""

    def synthesize_line(
        self,
        text: str,
        voice_model_name: str = "en-IN-Neural2-A",
        language_code: str = "en-IN",
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        voice_cloning_key: Optional[str] = None,
        voice_info: Optional[Dict[str, Any]] = None,
        speaker_role: str = "agent",
        conversation_language: str = "English (US)"
    ) -> bytes:
        """Synthesizes text using Instant Custom Voice cloning, Standard Cloud TTS, Chirp 3 HD, or Gemini TTS."""
        import requests
        headers = self._get_auth_headers()
        is_standard = (voice_info and voice_info.get("voice_type") == "standard") or (voice_model_name and not voice_cloning_key and not (voice_info and voice_info.get("audio_bytes")))

        # 1. If this is a Standard Cloud Voice, use Google Cloud TTS Standard/Journey/Neural2 directly
        if is_standard:
            url = "https://texttospeech.googleapis.com/v1beta1/text:synthesize"
            payload = {
                "input": {"text": text.strip()},
                "voice": {
                    "languageCode": language_code,
                    "name": voice_model_name
                },
                "audioConfig": {
                    "audioEncoding": "MP3",
                    "speakingRate": speaking_rate,
                    "pitch": pitch,
                    "sampleRateHertz": 24000
                }
            }
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    if "audioContent" in data:
                        return base64.b64decode(data["audioContent"])
                else:
                    logger.warning("Standard Cloud TTS status %d: %s", resp.status_code, resp.text[:200])
            except Exception as e:
                logger.warning("Standard Cloud TTS exception: %s", e)

        # 2. If voice cloning key is available or voice_info is provided (and not standard), use Cloud TTS Instant Custom Voice
        if not is_standard:
            if not voice_cloning_key and voice_info:
                voice_cloning_key = voice_info.get("voice_cloning_key")

            if not voice_cloning_key and voice_info:
                voice_cloning_key, _ = self.create_custom_voice_key(voice_info)

            if voice_cloning_key:
                url = "https://texttospeech.googleapis.com/v1beta1/text:synthesize"
                payload = {
                    "input": {"text": text.strip()},
                    "voice": {
                        "language_code": "en-US",
                        "voice_clone": {"voice_cloning_key": voice_cloning_key}
                    },
                    "audioConfig": {
                        "audioEncoding": "MP3",
                        "sample_rate_hertz": 24000
                    }
                }
                try:
                    resp = requests.post(url, headers=headers, json=payload, timeout=25)
                    if resp.status_code == 200:
                        data = resp.json()
                        if "audioContent" in data:
                            return base64.b64decode(data["audioContent"])
                    else:
                        logger.warning("Voice clone synthesis status %d: %s", resp.status_code, resp.text[:200])
                except Exception as e:
                    logger.warning("Voice clone synthesis exception: %s", e)

        # 3. Next, try high-fidelity Chirp 3 HD synthesis
        url = "https://texttospeech.googleapis.com/v1beta1/text:synthesize"
        payload = {
            "input": {"text": text.strip()},
            "voice": {
                "languageCode": language_code,
                "name": voice_model_name
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": speaking_rate,
                "sampleRateHertz": 24000
            }
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                if "audioContent" in data:
                    return base64.b64decode(data["audioContent"])
        except Exception as e:
            logger.warning("Chirp 3 HD synthesis exception: %s", e)

        # 4. Fallback to Gemini 2.5 Flash Preview TTS
        gemini_audio = self.synthesize_gemini_tts(
            text=text,
            voice_info=voice_info,
            speaker_role=speaker_role,
            conversation_language=conversation_language
        )
        if gemini_audio:
            return gemini_audio

        # 5. Fallback to standard Cloud TTS endpoint
        if self.session:
            v1_url = "https://texttospeech.googleapis.com/v1/text:synthesize"
            v1_payload = {
                "input": {"text": text},
                "voice": {
                    "languageCode": language_code,
                    "name": voice_model_name
                },
                "audioConfig": {
                    "audioEncoding": "MP3",
                    "speakingRate": speaking_rate,
                    "pitch": pitch,
                    "sampleRateHertz": 24000
                }
            }
            try:
                v1_resp = self.session.post(v1_url, json=v1_payload, timeout=20)
                if v1_resp.status_code == 200:
                    return base64.b64decode(v1_resp.json()["audioContent"])
            except Exception as e:
                logger.error("Cloud TTS fallback exception: %s", e)

        return b""

    def batch_translate_texts(
        self,
        texts: List[str],
        target_language: str
    ) -> List[str]:
        """Translates multiple texts in a single batch request to Cloud Translation API."""
        if not target_language or not self.session or not texts:
            return texts

        url = "https://translation.googleapis.com/language/translate/v2"
        params = {
            "q": texts,
            "target": target_language,
            "format": "text"
        }
        try:
            resp = self.session.post(url, json=params, timeout=15)
            if resp.status_code == 200:
                res_data = resp.json()
                translations = res_data.get("data", {}).get("translations", [])
                if len(translations) == len(texts):
                    return [t.get("translatedText", orig) for t, orig in zip(translations, texts)]
        except Exception as e:
            logger.warning("Batch translation failed: %s", e)

        return texts

    def generate_full_conversation(
        self,
        dialogue: List[Dict[str, Any]],
        agent_voice_info: Dict[str, Any],
        customer_voice_info: Dict[str, Any],
        conversation_language: str = "English (US)",
        progress_callback: Optional[Any] = None
    ) -> Tuple[bytes, List[Dict[str, Any]]]:
        """Synthesizes all dialogue turns in parallel using chosen voices and spoken language."""
        total_turns = len(dialogue)
        if total_turns == 0:
            return b"", []

        lang_info = SUPPORTED_CONVERSATION_LANGUAGES.get(conversation_language, SUPPORTED_CONVERSATION_LANGUAGES["English (US)"])
        trans_code = lang_info.get("trans_code")

        if progress_callback:
            progress_callback(f"Preparing conversation in {conversation_language}...", 0.2)

        # 1. Translate dialogue turns into target spoken language if non-English
        original_texts = [turn.get("text", "") for turn in dialogue]
        if trans_code:
            spoken_texts = self.batch_translate_texts(original_texts, trans_code)
        else:
            spoken_texts = original_texts

        # 2. Pre-generate Chirp 3 custom voice cloning keys for cloned voices only
        if agent_voice_info and agent_voice_info.get("voice_type") != "standard" and not agent_voice_info.get("voice_cloning_key"):
            self.create_custom_voice_key(agent_voice_info)
        if customer_voice_info and customer_voice_info.get("voice_type") != "standard" and not customer_voice_info.get("voice_cloning_key"):
            self.create_custom_voice_key(customer_voice_info)

        # 3. Parallel audio synthesis using ThreadPoolExecutor
        def _synth_turn(idx: int, turn_data: Dict[str, Any], spoken_text: str) -> Tuple[int, bytes]:
            spk = turn_data.get("speaker", "agent")
            v_info = agent_voice_info if spk == "agent" else customer_voice_info
            is_std = (v_info.get("voice_type") == "standard")
            
            if is_std:
                v_locale, v_model = get_standard_voice_model_for_language(v_info, lang_info)
                v_key = None
            else:
                v_locale, v_model = get_custom_voice_model_and_locale(v_info, lang_info)
                v_key = v_info.get("voice_cloning_key", None)

            v_rate = float(v_info.get("speaking_rate", 1.0))
            v_pitch = float(v_info.get("pitch", 0.0))

            aud_bytes = self.synthesize_line(
                text=spoken_text,
                voice_model_name=v_model,
                language_code=v_locale,
                speaking_rate=v_rate,
                pitch=v_pitch,
                voice_cloning_key=v_key,
                voice_info=v_info,
                speaker_role=spk,
                conversation_language=conversation_language
            )
            return idx, aud_bytes

        turn_audios: Dict[int, bytes] = {}
        with ThreadPoolExecutor(max_workers=min(8, total_turns)) as executor:
            future_to_idx = {
                executor.submit(_synth_turn, i, turn, spoken_texts[i]): i
                for i, turn in enumerate(dialogue)
            }
            for future in as_completed(future_to_idx):
                idx, aud_bytes = future.result()
                turn_audios[idx] = aud_bytes

        if progress_callback:
            progress_callback("Audio synthesis complete! Stitching audio and computing exact timeline...", 0.8)

        # 3. Stitch audio with exact duration calculation and 400ms pauses
        timeline = []
        turn_audio_segments = []
        current_time_s = 0.0

        for i, turn in enumerate(dialogue):
            speaker_type = turn.get("speaker", "agent")
            active_v_info = agent_voice_info if speaker_type == "agent" else customer_voice_info
            default_spk_name = active_v_info.get("name", "Agent" if speaker_type == "agent" else "Customer")
            speaker_name = turn.get("speaker_name", default_spk_name)
            orig_text = original_texts[i]
            spoken_text = spoken_texts[i]

            raw_bytes = turn_audios.get(i, b"")
            seg = None
            duration_s = 2.0
            if HAS_PYDUB and raw_bytes:
                try:
                    seg = AudioSegment.from_file(io.BytesIO(raw_bytes), format="mp3")
                    duration_s = seg.duration_seconds
                except Exception:
                    seg = None

            if not seg and raw_bytes:
                word_count = max(1, len(spoken_text.split()))
                duration_s = max(1.5, word_count * 0.38)

            start_s = current_time_s
            end_s = current_time_s + duration_s
            active_v_name = active_v_info.get("name", "Custom Voice")
            v_type = active_v_info.get("voice_type", "cloned")

            timeline.append({
                "turn_index": i + 1,
                "speaker": speaker_type,
                "speaker_name": speaker_name,
                "voice_type": v_type,
                "custom_voice_name": active_v_name,
                "spoken_text": spoken_text,
                "original_text": orig_text,
                "language": conversation_language,
                "start_time_s": round(start_s, 2),
                "end_time_s": round(end_s, 2),
                "duration_s": round(duration_s, 2)
            })

            if seg:
                turn_audio_segments.append(seg)

            current_time_s = end_s + 0.4  # 400ms pause between turns

        # Combine into master MP3
        master_mp3 = b""
        if HAS_PYDUB and turn_audio_segments:
            master = AudioSegment.empty()
            pause = AudioSegment.silent(duration=400)
            for idx, seg in enumerate(turn_audio_segments):
                master += seg
                if idx < len(turn_audio_segments) - 1:
                    master += pause
            out_buf = io.BytesIO()
            master.export(out_buf, format="mp3", bitrate="192k")
            master_mp3 = out_buf.getvalue()
        else:
            master_mp3 = b"".join(turn_audios.get(i, b"") for i in range(total_turns))

        if progress_callback:
            progress_callback("Conversation generation complete!", 1.0)

        return master_mp3, timeline
