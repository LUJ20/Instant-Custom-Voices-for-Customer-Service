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
import time
import uuid
import copy
import logging
from typing import Optional, Dict, Any, List, Union
import streamlit as st

from voice_service import (
    VoiceService,
    SUPPORTED_CONVERSATION_LANGUAGES,
    STANDARD_CLOUD_VOICES,
    REQUIRED_CONSENT_SCRIPT,
    get_standard_voice_model_for_language
)
from gcs_service import GCSService
from scenarios import DEFAULT_FLIGHT_DIALOGUE, adapt_dialogue_names_and_genders, get_display_name_for_voice

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

# Streamlit Page Setup
st.set_page_config(
    page_title="Instant Custom Voice Demo for Customer Service",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Enterprise CSS (Clean Google Cloud Styling)
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1a73e8;
        margin-bottom: 2px;
        letter-spacing: -0.5px;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #5f6368;
        margin-bottom: 16px;
    }
    .doc-banner {
        background-color: #f8f9fa;
        border-left: 5px solid #1a73e8;
        padding: 12px 18px;
        border-radius: 4px;
        margin-bottom: 22px;
        font-size: 0.95rem;
        color: #3c4043;
    }
    .doc-banner a {
        color: #1a73e8;
        font-weight: 600;
        text-decoration: none;
    }
    .doc-banner a:hover {
        text-decoration: underline;
    }
    .consent-box {
        background-color: #e8f0fe;
        border: 1px solid #d2e3fc;
        border-radius: 6px;
        padding: 14px 18px;
        font-size: 0.95rem;
        color: #174ea6;
        margin-bottom: 15px;
    }
    .step-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: #202124;
        margin-top: 18px;
        margin-bottom: 8px;
        padding-bottom: 6px;
        border-bottom: 2px solid #e8eaed;
    }
    .agent-bubble {
        background-color: #e8f0fe;
        border-left: 4px solid #1a73e8;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 10px;
    }
    .customer-bubble {
        background-color: #f1f3f4;
        border-left: 4px solid #5f6368;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 10px;
    }
    .speaker-tag-agent {
        font-weight: 700;
        color: #1a73e8;
        font-size: 0.88rem;
        margin-bottom: 4px;
    }
    .speaker-tag-customer {
        font-weight: 700;
        color: #3c4043;
        font-size: 0.88rem;
        margin-bottom: 4px;
    }
    .dialogue-text {
        font-size: 0.95rem;
        color: #202124;
        line-height: 1.45;
    }
    .custom-badge {
        display: inline-block;
        background-color: #e8f0fe;
        color: #1a73e8;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-left: 6px;
    }
    .standard-badge {
        display: inline-block;
        background-color: #f1f3f4;
        color: #5f6368;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-left: 6px;
    }
    div.stButton > button:first-child {
        background-color: #1a73e8 !important;
        border-color: #1a73e8 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 4px !important;
        padding: 8px 24px !important;
        box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15) !important;
    }
    div.stButton > button:hover {
        background-color: #1765cc !important;
        border-color: #1765cc !important;
        box-shadow: 0 1px 3px rgba(60,64,67,0.3), 0 4px 8px 3px rgba(60,64,67,0.15) !important;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Core Services
gcs_service = GCSService()


# Load Default Reference Audio as initial fallback
def get_default_reference_audio() -> bytes:
    ref_paths = [
        os.path.join(os.path.dirname(__file__), "assets", "layo_voice.mp3"),
        os.path.join(os.path.dirname(__file__), "assets", "rahul_voice.mp3")
    ]
    for p in ref_paths:
        if os.path.exists(p):
            try:
                with open(p, "rb") as f:
                    return f.read()
            except Exception:
                pass
    return b""


# Initialize Session State (Per-user session isolation)
if "agent_audio_bytes" not in st.session_state:
    st.session_state.agent_audio_bytes = get_default_reference_audio()
if "agent_voice_name" not in st.session_state:
    st.session_state.agent_voice_name = "Layolin Jesudhass (Reference Voice)"
if "agent_voice_gender" not in st.session_state:
    st.session_state.agent_voice_gender = "Female"
if "agent_gcs_uri" not in st.session_state:
    st.session_state.agent_gcs_uri = None
if "selected_conversation_language" not in st.session_state:
    st.session_state.selected_conversation_language = "English (US)"
if "dialogue_turns" not in st.session_state:
    st.session_state.dialogue_turns = copy.deepcopy(DEFAULT_FLIGHT_DIALOGUE)
if "generated_audio_mp3" not in st.session_state:
    st.session_state.generated_audio_mp3 = None
if "generated_timeline" not in st.session_state:
    st.session_state.generated_timeline = None


# Preset Customer Voice (Google Cloud Standard Journey-D)
PRESET_CUSTOMER_VOICE_ID = "std_journey_d"


# Sidebar Configuration
with st.sidebar:
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
    if not os.path.exists(logo_path):
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "gcp_logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown("### Google Cloud")

    st.markdown("### Cloud Configuration")
    detected_proj = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT") or ""
    if not detected_proj:
        try:
            import subprocess
            detected_proj = subprocess.check_output(
                ["gcloud", "config", "get-value", "project"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8").strip()
            if detected_proj == "(unset)":
                detected_proj = ""
        except Exception:
            detected_proj = ""

    project_id = st.text_input("GCP Project ID", value=detected_proj)
    detected_bucket = os.getenv("GCS_BUCKET_NAME") or (f"{project_id}-cust-service-voice" if project_id else "")
    gcs_bucket = st.text_input("GCS Storage Bucket", value=detected_bucket)

    st.markdown("---")
    st.markdown("### Active Session Voice Status")
    if st.session_state.agent_gcs_uri:
        st.success(f"🎙️ **Recorded Voice Saved in GCS:**\n`{st.session_state.agent_gcs_uri}`")
    else:
        st.info("🎙️ **Active Voice:** Using preloaded reference voice. Record below to clone your own voice!")

    if st.button("Reset to Default Reference Voice", use_container_width=True):
        st.session_state.agent_audio_bytes = get_default_reference_audio()
        st.session_state.agent_voice_name = "Layolin Jesudhass (Reference Voice)"
        st.session_state.agent_voice_gender = "Female"
        st.session_state.agent_gcs_uri = None
        st.session_state.dialogue_turns = copy.deepcopy(DEFAULT_FLIGHT_DIALOGUE)
        st.session_state.generated_audio_mp3 = None
        st.session_state.generated_timeline = None
        st.rerun()


# Top Header with Title
st.markdown("<div class='main-header'>Instant Custom Voice Demo for Customer Service</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>One-Way Custom Voice Cloning powered by Google Cloud Chirp 3 Instant Custom Voice & Standard Cloud TTS</div>", unsafe_allow_html=True)

# Product Documentation Banner
st.markdown("""
<div class='doc-banner'>
    <b>Product Technical Documentation:</b> Read the complete specifications for custom voice cloning at 
    <a href='https://docs.cloud.google.com/text-to-speech/docs/chirp3-instant-custom-voice' target='_blank'>Google Cloud Instant Custom Voice</a>.
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# STEP 1: RECORD CUSTOM AGENT VOICE (CHIRP 3 INSTANT CUSTOM VOICE)
# ==============================================================================
st.markdown("<div class='step-header'>1. Record Customer Care Agent Voice (Custom Cloned Voice)</div>", unsafe_allow_html=True)
st.caption("Record 5 to 10 seconds of clear speech to clone your voice for the Customer Care Agent. Your voice will automatically be saved in Google Cloud Storage under `voices/` and activated for this session.")

# Mandatory Consent Notice Box
st.markdown(f"""
<div class='consent-box'>
    <b>Mandatory Voice Consent Notice:</b><br>
    Please read the following consent statement aloud while recording:<br>
    <i>"{REQUIRED_CONSENT_SCRIPT}"</i>
</div>
""", unsafe_allow_html=True)

col_rec1, col_rec2 = st.columns([1, 1])

with col_rec1:
    st.markdown("##### 🎙️ Microphone Recording")
    recorded_audio = st.audio_input("Click record and read the consent statement (5-10s)")
    if recorded_audio:
        rec_bytes = recorded_audio.getvalue()
        if st.button("Save & Activate Recorded Voice", key="btn_save_rec", type="primary"):
            from voice_service import HAS_PYDUB, AudioSegment
            mp3_data = rec_bytes
            if HAS_PYDUB:
                try:
                    seg = AudioSegment.from_file(io.BytesIO(rec_bytes))
                    buf = io.BytesIO()
                    seg.export(buf, format="mp3")
                    mp3_data = buf.getvalue()
                except Exception:
                    pass

            # Upload to GCS under voices/
            blob_name = f"voices/agent_voice_{int(time.time())}_{uuid.uuid4().hex[:6]}.mp3"
            _, gcs_uri = gcs_service.upload_bytes(mp3_data, blob_name, content_type="audio/mpeg")

            st.session_state.agent_audio_bytes = mp3_data
            st.session_state.agent_voice_name = "My Recorded Voice"
            st.session_state.agent_voice_gender = "Female"
            st.session_state.agent_gcs_uri = gcs_uri
            st.session_state.generated_audio_mp3 = None
            st.session_state.generated_timeline = None
            st.success(f"✅ Voice recorded, saved to GCS (`{gcs_uri}`), and activated!")
            st.rerun()

with col_rec2:
    st.markdown("##### 📁 Or Upload Voice Sample")
    uploaded_file = st.file_uploader("Upload audio sample (.mp3 or .wav, <= 10s)", type=["mp3", "wav"], key="file_up")
    if uploaded_file:
        up_bytes = uploaded_file.getvalue()
        if st.button("Save & Activate Uploaded Voice", key="btn_save_up"):
            from voice_service import HAS_PYDUB, AudioSegment
            mp3_data = up_bytes
            if HAS_PYDUB:
                try:
                    seg = AudioSegment.from_file(io.BytesIO(up_bytes))
                    buf = io.BytesIO()
                    seg.export(buf, format="mp3")
                    mp3_data = buf.getvalue()
                except Exception:
                    pass

            blob_name = f"voices/agent_voice_{int(time.time())}_{uuid.uuid4().hex[:6]}.mp3"
            _, gcs_uri = gcs_service.upload_bytes(mp3_data, blob_name, content_type="audio/mpeg")

            st.session_state.agent_audio_bytes = mp3_data
            st.session_state.agent_voice_name = uploaded_file.name.rsplit(".", 1)[0]
            st.session_state.agent_gcs_uri = gcs_uri
            st.session_state.generated_audio_mp3 = None
            st.session_state.generated_timeline = None
            st.success(f"✅ Voice uploaded, saved to GCS (`{gcs_uri}`), and activated!")
            st.rerun()

# Active Voice Status Banner
if st.session_state.agent_audio_bytes:
    col_status1, col_status2 = st.columns([2, 1])
    with col_status1:
        gcs_label = f" • Saved in GCS (`{st.session_state.agent_gcs_uri}`)" if st.session_state.agent_gcs_uri else " • Preloaded Reference Sample"
        st.markdown(f"**Current Active Agent Voice:** `{st.session_state.agent_voice_name}` <span class='custom-badge'>Custom Cloned Voice (Chirp 3)</span>{gcs_label}", unsafe_allow_html=True)
    with col_status2:
        st.audio(st.session_state.agent_audio_bytes, format="audio/mp3")


# ==============================================================================
# STEP 2: AIRLINE FLIGHT REBOOKING CONVERSATION
# ==============================================================================
st.markdown("<div class='step-header'>2. Airline Flight Rebooking Conversation (SkyWays Premier Support)</div>", unsafe_allow_html=True)
st.caption("Pre-configured 7-turn customer service interaction between Customer Care Specialist and Customer David regarding flight rebooking.")

# Display clean conversation turns (Zero remove/delete clutter)
dialogue_turns = st.session_state.dialogue_turns
for idx, turn in enumerate(dialogue_turns):
    speaker = turn.get("speaker", "agent")
    if speaker == "agent":
        speaker_title = f"Customer Care Specialist ({turn.get('speaker_name', 'Sarah')})"
        st.markdown(f"""
        <div class='agent-bubble'>
            <div class='speaker-tag-agent'>🎙️ {speaker_title} <span class='custom-badge'>Custom Cloned Voice</span></div>
            <div class='dialogue-text'>{turn.get('text', '')}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        speaker_title = turn.get('speaker_name', 'Customer (David)')
        st.markdown(f"""
        <div class='customer-bubble'>
            <div class='speaker-tag-customer'>☁️ {speaker_title} <span class='standard-badge'>Standard Cloud Voice (Journey-D)</span></div>
            <div class='dialogue-text'>{turn.get('text', '')}</div>
        </div>
        """, unsafe_allow_html=True)


# ==============================================================================
# STEP 3: CONVERSATION SPOKEN LANGUAGE
# ==============================================================================
st.markdown("<div class='step-header'>3. Conversation Spoken Language</div>", unsafe_allow_html=True)
st.caption("Select the language for the multi-speaker customer service conversation. The Agent will speak in your cloned voice, and the Customer will speak in a natural standard cloud voice in the selected language.")

lang_options = list(SUPPORTED_CONVERSATION_LANGUAGES.keys())
cur_lang_idx = lang_options.index(st.session_state.selected_conversation_language) if st.session_state.selected_conversation_language in lang_options else 0

selected_language = st.selectbox(
    "Spoken Conversation Language",
    options=lang_options,
    index=cur_lang_idx,
    key="sel_lang_dropdown"
)
st.session_state.selected_conversation_language = selected_language

# Info Callout for Dual-Voice Architecture
st.info(f"🗣️ **Voice Assignment for {selected_language}:**\n• **Customer Care Agent:** `{st.session_state.agent_voice_name}` (*Custom Cloned Voice via Chirp 3*)\n• **Customer:** `Google Cloud Journey-D / Neural2` (*Standard Prebuilt Voice*)")


# ==============================================================================
# STEP 4: GENERATE MULTI-SPEAKER AUDIO & PLAYBACK
# ==============================================================================
st.markdown("<div class='step-header'>4. Generate Custom Voice Conversation & Master Playback</div>", unsafe_allow_html=True)

if st.button("🚀 Generate Custom Voice Conversation", key="btn_generate_audio", use_container_width=True):
    voice_service = VoiceService(project_id=project_id)
    
    # Build Agent Voice Info Dictionary
    agent_voice_dict = {
        "id": "custom_recorded_agent",
        "name": st.session_state.agent_voice_name,
        "gender": st.session_state.agent_voice_gender,
        "audio_bytes": st.session_state.agent_audio_bytes,
        "voice_type": "cloned"
    }

    # Customer Voice Info Dictionary (Standard Cloud Voice)
    cust_voice_dict = copy.deepcopy(STANDARD_CLOUD_VOICES.get(PRESET_CUSTOMER_VOICE_ID))

    with st.spinner(f"Synthesizing 7-turn flight conversation in {selected_language} using Chirp 3 Instant Custom Voice..."):
        try:
            full_mp3, timeline = voice_service.generate_full_conversation(
                dialogue_turns=st.session_state.dialogue_turns,
                agent_voice_info=agent_voice_dict,
                customer_voice_info=cust_voice_dict,
                conversation_language=selected_language
            )
            if full_mp3:
                st.session_state.generated_audio_mp3 = full_mp3
                st.session_state.generated_timeline = timeline
                st.success("✅ Multi-speaker customer service conversation generated successfully!")
            else:
                st.error("Synthesis completed but returned empty audio. Please verify your GCP project permissions.")
        except Exception as e:
            logger.error("Synthesis error: %s", e)
            st.error(f"Error during synthesis: {e}")

# Master Playback & Timeline
if st.session_state.generated_audio_mp3:
    st.markdown("---")
    st.markdown("### 🎧 Master Audio Playback")
    
    col_play1, col_play2 = st.columns([3, 1])
    with col_play1:
        st.audio(st.session_state.generated_audio_mp3, format="audio/mp3")
    with col_play2:
        st.download_button(
            label="⬇️ Download Full Audio (.mp3)",
            data=st.session_state.generated_audio_mp3,
            file_name=f"flight_rebooking_{selected_language.lower().replace(' ', '_')}.mp3",
            mime="audio/mpeg",
            use_container_width=True
        )

    if st.session_state.generated_timeline:
        st.markdown("#### 📝 Synchronized Subtitle Timeline")
        for item in st.session_state.generated_timeline:
            speaker = item.get("speaker", "agent")
            sp_name = item.get("speaker_name", "Speaker")
            badge = "<span class='custom-badge'>Custom Cloned Voice</span>" if speaker == "agent" else "<span class='standard-badge'>Standard Cloud Voice</span>"
            time_tag = f"`[{item.get('start_sec', 0.0):.1f}s - {item.get('end_sec', 0.0):.1f}s]`"
            st.markdown(f"• {time_tag} **{sp_name}** {badge}: {item.get('text', '')}", unsafe_allow_html=True)
