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
import json
import copy
import logging
import streamlit as st

from voice_gallery import VoiceGalleryManager
from script_generator import ScriptGenerator
from voice_service import VoiceService, SUPPORTED_CONVERSATION_LANGUAGES, REQUIRED_CONSENT_SCRIPT, get_custom_voice_model_and_locale
from gcs_service import GCSService
from project_manager import ProjectManager
from scenarios import SCENARIOS, get_display_name_for_voice, adapt_dialogue_names_and_genders

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

# Streamlit Page Setup
st.set_page_config(
    page_title="Instant Custom Voice Demo for Customer Service",
    page_icon="☁️",
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
        padding: 12px 16px;
        font-size: 0.9rem;
        color: #174ea6;
        margin-bottom: 14px;
    }
    .section-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #202124;
        margin-top: 18px;
        margin-bottom: 12px;
        border-bottom: 2px solid #e8eaed;
        padding-bottom: 6px;
    }
    .subtitle-card {
        background: #ffffff;
        border-left: 4px solid #1a73e8;
        border-radius: 4px;
        padding: 10px 14px;
        margin-bottom: 10px;
        box-shadow: 0 1px 2px rgba(60,64,67,0.06);
    }
    .subtitle-card.customer {
        border-left: 4px solid #34a853;
        background: #fdfdfd;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 8px;
    }
    
    /* Compact, text-hugging Google Blue Action Buttons */
    div.stButton > button {
        background-color: #1a73e8 !important;
        color: #ffffff !important;
        border: 1px solid #1a73e8 !important;
        border-radius: 18px !important;
        padding: 4px 14px !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        min-height: unset !important;
        height: auto !important;
        width: auto !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 1px 2px rgba(60,64,67,0.3) !important;
        transition: background-color 0.2s, box-shadow 0.2s !important;
    }
    div.stButton > button:hover {
        background-color: #1765cc !important;
        border-color: #1765cc !important;
        color: #ffffff !important;
        box-shadow: 0 1px 3px rgba(60,64,67,0.3), 0 4px 8px 3px rgba(60,64,67,0.15) !important;
    }
    div.stButton > button:active {
        background-color: #1557b0 !important;
        border-color: #1557b0 !important;
        color: #ffffff !important;
    }
    div.stButton > button[kind="secondary"] {
        background-color: #ffffff !important;
        color: #1a73e8 !important;
        border: 1px solid #dadce0 !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #f8fafd !important;
        border-color: #1a73e8 !important;
        color: #1765cc !important;
    }
</style>
""", unsafe_allow_html=True)

# Instantiate Managers
gallery_mgr = VoiceGalleryManager()
proj_mgr = ProjectManager()

active_voices = gallery_mgr.get_all_voices()
default_agent_vid = active_voices[0]["id"] if active_voices else ""
default_cust_vid = active_voices[1]["id"] if len(active_voices) > 1 else (active_voices[0]["id"] if active_voices else "")

agent_voice_info = gallery_mgr.get_voice_by_id(default_agent_vid)
cust_voice_info = gallery_mgr.get_voice_by_id(default_cust_vid)

# Determine first default scenario (Banking)
default_scenario_key = list(SCENARIOS.keys())[0]
default_scenario = SCENARIOS[default_scenario_key]
initial_dialogue = adapt_dialogue_names_and_genders(
    default_scenario["dialogue"],
    agent_voice_info,
    cust_voice_info
)

# Distinct Customer Service Scenario Prompt for Gemini Generation
DEFAULT_CUSTOM_SCENARIO_PROMPT = "A customer calling telecom technical support to report an unexpected home fiber internet outage during remote work hours and requesting urgent router diagnostics and priority technician dispatch."

# Initialize Session State
if "dialogue_turns" not in st.session_state:
    st.session_state.dialogue_turns = initial_dialogue
if "scenario_prompt" not in st.session_state:
    st.session_state.scenario_prompt = DEFAULT_CUSTOM_SCENARIO_PROMPT
if "expand_dialogue_editor" not in st.session_state:
    st.session_state.expand_dialogue_editor = True
if "generated_audio_mp3" not in st.session_state:
    st.session_state.generated_audio_mp3 = None
if "generated_timeline" not in st.session_state:
    st.session_state.generated_timeline = None
if "gcs_audio_uri" not in st.session_state:
    st.session_state.gcs_audio_uri = None
if "selected_agent_voice_id" not in st.session_state:
    st.session_state.selected_agent_voice_id = default_agent_vid
if "selected_customer_voice_id" not in st.session_state:
    st.session_state.selected_customer_voice_id = default_cust_vid
if "selected_conversation_language" not in st.session_state:
    st.session_state.selected_conversation_language = "English (US)"


def reset_workspace():
    first_key = list(SCENARIOS.keys())[0]
    first_sc = SCENARIOS[first_key]
    agent_v = gallery_mgr.get_voice_by_id(default_agent_vid)
    cust_v = gallery_mgr.get_voice_by_id(default_cust_vid)
    st.session_state.dialogue_turns = adapt_dialogue_names_and_genders(first_sc["dialogue"], agent_v, cust_v)
    st.session_state.scenario_prompt = DEFAULT_CUSTOM_SCENARIO_PROMPT
    st.session_state.expand_dialogue_editor = True
    st.session_state.generated_audio_mp3 = None
    st.session_state.generated_timeline = None
    st.session_state.gcs_audio_uri = None
    st.session_state.selected_agent_voice_id = default_agent_vid
    st.session_state.selected_customer_voice_id = default_cust_vid
    st.session_state.selected_conversation_language = "English (US)"
    st.rerun()


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

    project_id = st.text_input(
        "GCP Project ID",
        value=detected_proj
    )
    detected_bucket = os.getenv("GCS_BUCKET_NAME") or (f"{project_id}-artifacts" if project_id else "")
    gcs_bucket = st.text_input(
        "GCS Storage Bucket",
        value=detected_bucket
    )
    # Ensure proj_mgr is updated with user-provided or detected bucket/project
    proj_mgr.set_gcs_config(bucket_name=gcs_bucket, project_id=project_id)
    
    st.markdown("---")
    st.markdown("### Saved Projects (Cloud Storage)")
    saved_projects = proj_mgr.list_projects()
    if saved_projects:
        proj_options = {
            f"{p['name']} ({p.get('formatted_date', 'Saved')})": p["project_id"]
            for p in saved_projects
        }
        sel_display_name = st.selectbox("Select Project to Load", options=list(proj_options.keys()))
        sel_proj_id = proj_options[sel_display_name]
        col_sb1, col_sb2 = st.columns(2)
        with col_sb1:
            if st.button("Load Project", use_container_width=True):
                p_data = proj_mgr.load_project(sel_proj_id)
                if p_data:
                    st.session_state.dialogue_turns = p_data.get("dialogue_turns", [])
                    st.session_state.scenario_prompt = p_data.get("scenario_prompt", "")
                    st.session_state.generated_timeline = p_data.get("timeline", None)
                    st.session_state.generated_audio_mp3 = proj_mgr.get_project_audio(sel_proj_id)
                    st.session_state.selected_agent_voice_id = p_data.get("agent_voice_id", default_agent_vid)
                    st.session_state.selected_customer_voice_id = p_data.get("customer_voice_id", default_cust_vid)
                    if "conversation_language" in p_data or "target_translation_lang" in p_data:
                        st.session_state.selected_conversation_language = p_data.get("conversation_language") or p_data.get("target_translation_lang")
                    st.success(f"Loaded '{p_data.get('name', sel_display_name)}'")
                    st.rerun()
        with col_sb2:
            if st.button("Delete Project", use_container_width=True):
                if proj_mgr.delete_project(sel_proj_id):
                    st.success("Deleted project")
                    st.rerun()
    else:
        st.caption("No saved projects found in GCS bucket.")


# Top Header with Title
st.markdown("<div class='main-header'>Instant Custom Voice Demo for Customer Service</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Multi-Speaker Custom Voice Cloning & Dynamic Dialogue Generation powered by Gemini Flash</div>", unsafe_allow_html=True)

# Product Documentation Banner
st.markdown("""
<div class='doc-banner'>
    <b>Product Technical Documentation:</b> Read the complete specifications for custom voice cloning at 
    <a href='https://docs.cloud.google.com/text-to-speech/docs/chirp3-instant-custom-voice' target='_blank'>Google Cloud Instant Custom Voice</a>.
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# SECTION 1: CUSTOM VOICE GALLERY (VOICE PROFILES)
# ==============================================================================
st.markdown("<div class='section-title'>1. Custom Voice Gallery (Voice Profiles)</div>", unsafe_allow_html=True)
st.caption("Manage custom voice profiles for Customer Service Agent and Customer roles. Edit voice profile names, listen to reference samples, or delete/add any custom voice.")

active_voices = gallery_mgr.get_all_voices()
if not active_voices:
    st.info("No voice profiles currently in gallery. You can add a new custom voice below or restore standard reference voices.")
else:
    num_cols = min(max(len(active_voices), 1), 4)
    cols = st.columns(num_cols)
    for idx, voice in enumerate(active_voices):
        col_idx = idx % num_cols
        with cols[col_idx]:
            # Single clean Voice Profile Name field (e.g. Indian Male, Indian Female)
            v_name_key = f"vname_{voice['id']}"
            edited_name = st.text_input(
                "Voice Profile Name",
                value=voice["name"],
                key=v_name_key,
                help="Edit custom voice profile name (e.g. Indian Male, Indian Female, Korean Female)"
            )

            # Automatically derive gender from name or preserve registered gender
            inferred_gender = voice.get("gender", "Female")
            lower_name = edited_name.lower()
            if "female" in lower_name or "woman" in lower_name or "girl" in lower_name:
                inferred_gender = "Female"
            elif "male" in lower_name or "man" in lower_name or "boy" in lower_name:
                inferred_gender = "Male"

            # Auto-save updates when name or inferred gender is modified
            if edited_name != voice["name"] or inferred_gender != voice.get("gender"):
                gallery_mgr.update_voice_profile(voice["id"], {"name": edited_name, "gender": inferred_gender})
                ag_v = gallery_mgr.get_voice_by_id(st.session_state.selected_agent_voice_id)
                cu_v = gallery_mgr.get_voice_by_id(st.session_state.selected_customer_voice_id)
                st.session_state.dialogue_turns = adapt_dialogue_names_and_genders(st.session_state.dialogue_turns, ag_v, cu_v)
                st.rerun()

            # Reference Audio Player
            aud_bytes = gallery_mgr.get_audio_bytes(voice["id"])
            if aud_bytes:
                st.audio(aud_bytes, format="audio/mp3")

            if st.button("Delete Voice", key=f"del_{voice['id']}", use_container_width=True):
                gallery_mgr.remove_voice(voice["id"])
                st.success(f"Removed '{voice['name']}'")
                st.rerun()

col_g1, col_g2 = st.columns([7, 3])
with col_g2:
    st.write("")
    if st.button("Restore Standard Voices", key="btn_restore_std_voices"):
        gallery_mgr.restore_default_voices()
        st.success("Restored standard Indian Female and Indian Male reference voices.")
        st.rerun()

# Add / Record New Custom Voice Expander
with st.expander("Add or Record New Custom Voice to Gallery", expanded=False):
    st.markdown(f"""
    <div class='consent-box'>
        <b>Mandatory Voice Consent Script:</b><br/>
        <i>"{REQUIRED_CONSENT_SCRIPT}"</i>
    </div>
    """, unsafe_allow_html=True)

    tab_rec, tab_up = st.tabs(["Record Voice (Live Microphone)", "Upload Audio File (.mp3/.wav)"])

    with tab_rec:
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            rec_name = st.text_input("Voice Profile Name", value="Custom Voice", key="rec_name_input")
        with col_r2:
            rec_gender = st.selectbox("Voice Profile Gender", options=["Female", "Male"], index=0, key="rec_gender_input")

        st.write("Click below to record your voice reading the consent statement (<= 10s):")
        recorded_audio = st.audio_input("Record Voice Statement", key="mic_recorder")
        
        if recorded_audio:
            rec_bytes = recorded_audio.getvalue()
            st.audio(rec_bytes)
            if st.button("Save Recording to Voice Gallery", key="btn_save_recorded"):
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
                
                new_v = gallery_mgr.add_voice(
                    name=rec_name,
                    audio_bytes=mp3_data,
                    gender=rec_gender,
                    native_locale="en-IN",
                    pitch=0.0,
                    speaking_rate=1.0
                )
                if new_v:
                    st.session_state.selected_agent_voice_id = new_v["id"]
                    st.success(f"Added '{rec_name}' to Custom Voice Gallery!")
                    st.rerun()

    with tab_up:
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            up_name = st.text_input("Voice Profile Name", value="Custom Voice", key="up_name_input")
        with col_u2:
            up_gender = st.selectbox("Voice Profile Gender", options=["Female", "Male"], index=1, key="up_gender_input")

        uploaded_file = st.file_uploader("Upload Voice Sample (.mp3 or .wav, <= 10 seconds)", type=["mp3", "wav"], key="file_up_single")
        if uploaded_file:
            up_bytes = uploaded_file.getvalue()
            st.audio(up_bytes)
            if st.button("Save Upload to Voice Gallery", key="btn_save_upload"):
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
                
                new_v = gallery_mgr.add_voice(
                    name=up_name,
                    audio_bytes=mp3_data,
                    gender=up_gender,
                    native_locale="en-IN",
                    pitch=0.0,
                    speaking_rate=1.0
                )
                if new_v:
                    st.session_state.selected_customer_voice_id = new_v["id"]
                    st.success(f"Added '{up_name}' to Custom Voice Gallery!")
                    st.rerun()


# ==============================================================================
# SECTION 2: AI DIALOGUE SCRIPT GENERATOR (GEMINI FLASH)
# ==============================================================================
st.markdown("<div class='section-title'>2. Customer Service Dialogue Generator (Gemini Flash)</div>", unsafe_allow_html=True)

col_s1, col_or, col_s2 = st.columns([4.2, 0.8, 6.0])

with col_s1:
    st.markdown("##### Load Industry Template")
    scenario_keys = list(SCENARIOS.keys())
    selected_scenario = st.selectbox(
        "Choose Pre-configured Scenario",
        options=scenario_keys,
        index=0,
        label_visibility="collapsed"
    )
    if st.button("Load Template Dialogue", key="btn_load_template"):
        agent_v = gallery_mgr.get_voice_by_id(st.session_state.selected_agent_voice_id)
        cust_v = gallery_mgr.get_voice_by_id(st.session_state.selected_customer_voice_id)
        raw_dialogue = copy.deepcopy(SCENARIOS[selected_scenario]["dialogue"])
        st.session_state.dialogue_turns = adapt_dialogue_names_and_genders(raw_dialogue, agent_v, cust_v)
        st.session_state.expand_dialogue_editor = True
        st.rerun()

with col_or:
    st.markdown("<div style='text-align: center; margin-top: 32px; font-weight: bold; color: #5f6368; font-size: 1.05rem;'>OR</div>", unsafe_allow_html=True)

with col_s2:
    st.markdown("##### Describe Customer Scenario Prompt")
    st.markdown(f"<div class='example-box'><b>Example Prompt:</b> <i>{DEFAULT_CUSTOM_SCENARIO_PROMPT}</i></div>", unsafe_allow_html=True)
    
    scenario_prompt = st.text_area(
        "Scenario Prompt Description",
        value=st.session_state.scenario_prompt,
        height=75,
        placeholder="E.g., A customer calling telecom technical support to troubleshoot a fiber internet outage or a patient requesting prescription renewal.",
        label_visibility="collapsed",
        key="scenario_prompt_input"
    )
    st.session_state.scenario_prompt = scenario_prompt

    if st.button("Generate Dialogue", type="primary", key="btn_gen_dialogue"):
        with st.spinner("Generating customer service conversation via Gemini Flash..."):
            script_gen = ScriptGenerator(project_id=project_id)
            agent_v = gallery_mgr.get_voice_by_id(st.session_state.selected_agent_voice_id)
            cust_v = gallery_mgr.get_voice_by_id(st.session_state.selected_customer_voice_id)
            agent_name = get_display_name_for_voice(agent_v, role="agent")
            cust_name = get_display_name_for_voice(cust_v, role="customer")
            agent_gender = str(agent_v.get("gender", "Female") if agent_v else "Female").capitalize()
            cust_gender = str(cust_v.get("gender", "Male") if cust_v else "Male").capitalize()

            generated_script = script_gen.generate_script(
                user_scenario_prompt=scenario_prompt,
                agent_name=agent_name,
                customer_name=cust_name,
                agent_gender=agent_gender,
                customer_gender=cust_gender
            )
            if generated_script:
                st.session_state.dialogue_turns = generated_script
                st.session_state.expand_dialogue_editor = True
                st.success(f"Generated dialogue with {agent_name} ({agent_gender}) & {cust_name} ({cust_gender})!")
                st.rerun()
            else:
                st.error("Script generation failed. Please verify Vertex AI permissions.")

# Interactive Turn Editor
with st.expander("Edit, Add or Remove Dialogue Turns", expanded=st.session_state.get("expand_dialogue_editor", True)):
    updated_turns = []
    for idx, turn in enumerate(st.session_state.dialogue_turns):
        c1, c2, c3, c4 = st.columns([2, 3, 6, 1])
        with c1:
            spk_type = st.selectbox(
                f"Speaker Type #{idx+1}",
                options=["agent", "customer"],
                index=0 if turn.get("speaker") == "agent" else 1,
                key=f"turn_spk_{idx}"
            )
        with c2:
            spk_name = st.text_input(
                f"Speaker Name #{idx+1}",
                value=turn.get("speaker_name", "Agent" if spk_type == "agent" else "Customer"),
                key=f"turn_name_{idx}"
            )
        with c3:
            spk_text = st.text_area(
                f"Dialogue Line #{idx+1}",
                value=turn.get("text", ""),
                height=68,
                key=f"turn_text_{idx}"
            )
        with c4:
            st.write("")
            st.write("")
            remove_turn = st.button("Remove", key=f"turn_del_{idx}")
        
        if not remove_turn:
            updated_turns.append({
                "speaker": spk_type,
                "speaker_name": spk_name,
                "text": spk_text
            })
    
    col_add1, col_add2 = st.columns([4, 8])
    with col_add1:
        if st.button("Add New Turn", use_container_width=True):
            agent_v = gallery_mgr.get_voice_by_id(st.session_state.selected_agent_voice_id)
            cust_v = gallery_mgr.get_voice_by_id(st.session_state.selected_customer_voice_id)
            ag_name = get_display_name_for_voice(agent_v, role="agent")
            cu_name = get_display_name_for_voice(cust_v, role="customer")
            next_spk = "agent" if len(updated_turns) % 2 == 0 else "customer"
            next_label = f"Customer Care Specialist ({ag_name})" if next_spk == "agent" else f"Customer ({cu_name})"
            updated_turns.append({
                "speaker": next_spk,
                "speaker_name": next_label,
                "text": "How can I assist you further?"
            })
            st.session_state.dialogue_turns = updated_turns
            st.rerun()

    st.session_state.dialogue_turns = updated_turns


# ==============================================================================
# SECTION 3: CUSTOM VOICE ASSIGNMENT & CONVERSATION LANGUAGE
# ==============================================================================
st.markdown("<div class='section-title'>3. Custom Voice Assignment & Conversation Language</div>", unsafe_allow_html=True)
st.caption("Select which custom voice speaks for the Customer Care Agent and which custom voice speaks for the Customer. Character names and speaker tags in the dialogue automatically synchronize with the selected voice genders.")

voice_options = {v["id"]: f"{v['name']} ({v.get('gender', 'Female')} Profile - Cloned Voice)" for v in active_voices}
voice_ids = list(voice_options.keys())

def on_agent_voice_change():
    new_vid = st.session_state.sel_agent_voice_widget
    st.session_state.selected_agent_voice_id = new_vid
    ag_v = gallery_mgr.get_voice_by_id(new_vid)
    cu_v = gallery_mgr.get_voice_by_id(st.session_state.selected_customer_voice_id)
    st.session_state.dialogue_turns = adapt_dialogue_names_and_genders(st.session_state.dialogue_turns, ag_v, cu_v)

def on_customer_voice_change():
    new_vid = st.session_state.sel_cust_voice_widget
    st.session_state.selected_customer_voice_id = new_vid
    ag_v = gallery_mgr.get_voice_by_id(st.session_state.selected_agent_voice_id)
    cu_v = gallery_mgr.get_voice_by_id(new_vid)
    st.session_state.dialogue_turns = adapt_dialogue_names_and_genders(st.session_state.dialogue_turns, ag_v, cu_v)

col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    default_agent_idx = voice_ids.index(st.session_state.selected_agent_voice_id) if st.session_state.selected_agent_voice_id in voice_ids else 0
    selected_agent_id = st.selectbox(
        "Customer Care Agent Voice",
        options=voice_ids,
        format_func=lambda vid: voice_options[vid],
        index=default_agent_idx,
        key="sel_agent_voice_widget",
        on_change=on_agent_voice_change
    )
    st.session_state.selected_agent_voice_id = selected_agent_id
    cur_ag_v = gallery_mgr.get_voice_by_id(selected_agent_id)
    st.caption(f"Assigned Character: **Customer Care Specialist ({get_display_name_for_voice(cur_ag_v, 'agent')})**")

with col_v2:
    default_cust_idx = voice_ids.index(st.session_state.selected_customer_voice_id) if (st.session_state.selected_customer_voice_id in voice_ids and len(voice_ids) > 1) else min(1, len(voice_ids)-1)
    selected_cust_id = st.selectbox(
        "Customer Voice",
        options=voice_ids,
        format_func=lambda vid: voice_options[vid],
        index=default_cust_idx,
        key="sel_cust_voice_widget",
        on_change=on_customer_voice_change
    )
    st.session_state.selected_customer_voice_id = selected_cust_id
    cur_cu_v = gallery_mgr.get_voice_by_id(selected_cust_id)
    st.caption(f"Assigned Character: **Customer ({get_display_name_for_voice(cur_cu_v, 'customer')})**")

with col_v3:
    lang_options = list(SUPPORTED_CONVERSATION_LANGUAGES.keys())
    cur_lang_idx = lang_options.index(st.session_state.selected_conversation_language) if st.session_state.selected_conversation_language in lang_options else 0
    selected_conv_lang = st.selectbox(
        "Conversation Spoken Language",
        options=lang_options,
        index=cur_lang_idx
    )
    st.session_state.selected_conversation_language = selected_conv_lang
    st.caption(f"Cloned voices synthesize speech in **{selected_conv_lang}**")

# Execution Button
if st.button("Generate Custom Voice Conversation (.mp3)", use_container_width=True, type="primary"):
    with st.spinner(f"Generating conversation in {selected_conv_lang} with selected custom voices..."):
        prog_bar = st.progress(0.1)
        status_text = st.empty()

        def update_progress(msg, pct):
            status_text.write(msg)
            prog_bar.progress(pct)

        vs = VoiceService(project_id=project_id)
        gcs = GCSService(project_id=project_id, bucket_name=gcs_bucket)

        agent_voice_info = gallery_mgr.get_voice_by_id(selected_agent_id) or {}
        customer_voice_info = gallery_mgr.get_voice_by_id(selected_cust_id) or {}
        st.session_state.active_agent_voice_name = agent_voice_info.get("name", "Custom Voice")
        st.session_state.active_customer_voice_name = customer_voice_info.get("name", "Custom Voice")

        master_audio_bytes, timeline = vs.generate_full_conversation(
            dialogue=st.session_state.dialogue_turns,
            agent_voice_info=agent_voice_info,
            customer_voice_info=customer_voice_info,
            conversation_language=selected_conv_lang,
            progress_callback=update_progress
        )

        st.session_state.generated_audio_mp3 = master_audio_bytes
        st.session_state.generated_timeline = timeline

        # Persist to GCS
        try:
            filename = f"conversation_{int(time.time())}.mp3"
            gcs_uri = gcs.upload_audio_bytes(master_audio_bytes, filename)
            st.session_state.gcs_audio_uri = gcs_uri
        except Exception as e:
            logger.warning("GCS upload skipped: %s", e)

        prog_bar.empty()
        status_text.empty()
        st.success(f"Conversation synthesized successfully in {selected_conv_lang} with {agent_voice_info.get('name', 'Agent')} & {customer_voice_info.get('name', 'Customer')}!")
        st.rerun()


# ==============================================================================
# SECTION 4: MASTER PLAYBACK & SYNCHRONIZED SUBTITLES
# ==============================================================================
if st.session_state.generated_audio_mp3:
    st.markdown("<div class='section-title'>4. Master Conversation Playback & Synchronized Subtitles</div>", unsafe_allow_html=True)
    
    agent_display = st.session_state.get("active_agent_voice_name", "Agent Custom Voice")
    cust_display = st.session_state.get("active_customer_voice_name", "Customer Custom Voice")
    lang_display = st.session_state.get("selected_conversation_language", "English (US)")

    st.markdown(f"""
    <div style='background: #e8f0fe; border-left: 4px solid #1a73e8; padding: 10px 14px; border-radius: 6px; margin-bottom: 16px;'>
        <div style='font-size:0.95rem; font-weight: 600; color: #1a73e8; margin-bottom: 4px;'>🎙️ Active Cloned Custom Voices</div>
        <div style='font-size:0.88rem; color: #202124;'>
            <span><b>Agent Voice:</b> {agent_display} (Custom Cloned Voice)</span> &nbsp;|&nbsp;
            <span><b>Customer Voice:</b> {cust_display} (Custom Cloned Voice)</span> &nbsp;|&nbsp;
            <span style='color: #5f6368;'><b>Language:</b> {lang_display}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_p1, col_p2 = st.columns([7, 3])
    with col_p1:
        st.audio(st.session_state.generated_audio_mp3, format="audio/mp3")
    with col_p2:
        st.download_button(
            label="Download Master Conversation (.mp3)",
            data=st.session_state.generated_audio_mp3,
            file_name="customer_service_conversation.mp3",
            mime="audio/mp3",
            use_container_width=True
        )

    # Subtitle Display
    if st.session_state.generated_timeline:
        st.markdown("##### Synchronized Spoken Dialogue")
        for t in st.session_state.generated_timeline:
            card_class = "subtitle-card customer" if t["speaker"] == "customer" else "subtitle-card"
            badge = "Customer Care Specialist" if t["speaker"] == "agent" else "Customer"
            v_label = t.get("custom_voice_name", agent_display if t["speaker"] == "agent" else cust_display)
            
            sub_html = f"<div class='{card_class}'>"
            sub_html += f"<div style='font-size:0.82rem; color:#5f6368; font-weight:600;'>[{t['start_time_s']}s - {t['end_time_s']}s] • {t['speaker_name']} ({badge}) • 🎙️ {v_label} (Custom Cloned Voice)</div>"
            sub_html += f"<div style='font-size:1.0rem; color:#202124; margin-top:3px;'><b>Spoken:</b> {t.get('spoken_text', t.get('text', ''))}</div>"
            if t.get("original_text") and t.get("original_text") != t.get("spoken_text"):
                sub_html += f"<div style='font-size:0.9rem; color:#5f6368; margin-top:2px;'><b>Original (English):</b> {t['original_text']}</div>"
            sub_html += "</div>"
            st.markdown(sub_html, unsafe_allow_html=True)

    # Save Project Toolbar
    st.markdown("---")
    col_sv1, col_sv2 = st.columns([8, 2])
    with col_sv1:
        save_p_name = st.text_input("Save this Conversation as a Project", value="Customer Support Demo", key="save_proj_name")
    with col_sv2:
        st.write("")
        st.write("")
        if st.button("Save Project", use_container_width=True):
            proj_mgr.set_gcs_config(bucket_name=gcs_bucket, project_id=project_id)
            proj_mgr.save_project(
                name=save_p_name,
                scenario_prompt=st.session_state.scenario_prompt,
                dialogue_turns=st.session_state.dialogue_turns,
                timeline=st.session_state.generated_timeline,
                audio_bytes=st.session_state.generated_audio_mp3,
                agent_voice_id=st.session_state.selected_agent_voice_id,
                customer_voice_id=st.session_state.selected_customer_voice_id,
                conversation_language=st.session_state.selected_conversation_language
            )
            st.success(f"Saved project '{save_p_name}' successfully to Cloud Storage!")
            st.rerun()

    # Reset Button at the End to start a different conversation
    st.markdown("---")
    if st.button("Reset Conversation (Start New Scenario)", use_container_width=True):
        reset_workspace()
