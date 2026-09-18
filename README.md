# Instant Custom Voice Demo for Customer Service

A production-ready Google Cloud reference architecture and interactive Streamlit application demonstrating zero-shot multi-speaker voice cloning using **Google Cloud Text-to-Speech Chirp 3 Instant Custom Voice** and **Vertex AI Gemini 3.8 Flash**.

[![Official Documentation](https://img.shields.io/badge/Google_Cloud-Chirp_3_Docs-4285F4?logo=googlecloud&logoColor=white)](https://docs.cloud.google.com/text-to-speech/docs/chirp3-instant-custom-voice)
[![Google Cloud Run](https://img.shields.io/badge/Deploy-Cloud_Run-4285F4?logo=googlecloud&logoColor=white)](https://cloud.google.com/run)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

---

## Architecture & Solution Overview

This solution allows enterprise customer experience and contact center teams to author, simulate, and generate multi-speaker customer service conversations powered by high-fidelity zero-shot voice cloning:

```
+---------------------------------------------------------------------------------------------+
|                                STREAMLIT FRONTEND / UI                                      |
+---------------------------------------------------------------------------------------------+
   |                                  |                                       |
   v                                  v                                       v
[1. Voice Profile Gallery]   [2. Scenario & Dialogue AI]          [3. GCS Project Management]
   • Consent Audio Ingestion    • Gemini 3.8 Flash Generator         • Save / Load Manifests
   • Voice Key Creation         • Multi-turn script editor           • Audio blob persistence
   • Live Audio Preview         • Culture-aware name mapping         • GCS REST JSON integration
   |                                  |                                       |
   +----------------------------------+---------------------------------------+
                                      |
                                      v
                      +-------------------------------+
                      |   4. Chirp 3 Synthesis Engine |
                      +-------------------------------+
                                      |
       +------------------------------+------------------------------+
       |                                                             |
       v                                                             v
[Cloud TTS Chirp 3 Instant Voice]                             [Master Stitching Engine]
 • Zero-shot acoustic cloning                                  • 400ms conversational turn gaps
 • Multi-lingual synthesis (8 languages)                       • Sample-rate normalized MP3
 • Biometric safety consent verification                       • Synchronized timeline subtitles
```

---

## Key Feature Capabilities

### 1. Zero-Shot Instant Custom Voice Cloning
- **Google Cloud Chirp 3 Integration:** Clones target speaker acoustics directly from a brief reference recording (**<= 10 seconds**).
- **Multilingual Custom Voice Synthesis:** Preserves the cloned vocal identity across **8 languages**:
  - English (US / India)
  - Hindi (हिन्दी)
  - Korean (한국어)
  - Spanish (Español)
  - French (Français)
  - German (Deutsch)
  - Japanese (日本語)
  - Portuguese (Português)
- **Automated Voice Profile Management:** Edit voice names directly; the system automatically resolves authentic regional personas and gender roles.

### 2. Multi-Speaker Dynamic Dialogue Generation
- **Gemini 3.8 Flash Integration:** Synthesizes realistic 5–7 turn customer support interactions from scenario prompts (e.g., banking alerts, airline rebooking, telecom outages).
- **Interactive Turn Editor:** Add, remove, or modify speaker turns, dialogue text, and speaker roles before synthesis.
- **Nationality & Persona Adaptation:** Automatically maps character names to match voice nationalities (e.g., Priya/Rahul for Indian personas, Ji-woo/Min-jun for Korean personas).

### 3. Conversational Mastering & Synchronized Subtitles
- **Natural Turn Pacing:** Inserts natural conversational silences (400ms) between agent and customer turns.
- **Dual-Language Subtitle Timeline:** Displays synchronized cards with start/end timestamps and original vs. spoken translations.

### 4. Permanent Google Cloud Storage Persistence
- **GCS Cloud Persistence:** Manifests (`projects/{project_id}.json`) and audio artifacts (`projects/{project_id}.mp3`) are persisted directly to Google Cloud Storage.
- **Session Restoration:** Saved projects persist across container launches and redeployments, allowing instant retrieval via the sidebar.

---

## 🎙️ Mandatory Biometric Consent Statement

To comply with Google Cloud AI safety guidelines and biometric voice cloning requirements, reference audio recordings must contain this exact verbatim statement:

> **"I am the owner of this voice and I consent to Google using this voice to create a synthetic voice model."**

*Recording Requirements:*
- **Duration:** Less than or equal to **10 seconds**.
- **Format:** `.mp3` or `.wav`.
- **Quality:** Clean audio with clear pronunciation and minimal background noise.

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- Python 3.10 or higher
- Google Cloud SDK (`gcloud`) CLI installed
- System `ffmpeg` installed for audio stitching:
  - macOS: `brew install ffmpeg`
  - Debian/Ubuntu: `sudo apt-get install -y ffmpeg`
- Google Cloud project allowlisted for Chirp 3 Instant Custom Voice.

### 2. Authentication
Authenticate your local environment with Application Default Credentials:
```bash
gcloud auth application-default login --scopes="https://www.googleapis.com/auth/cloud-platform"
gcloud config set project YOUR_PROJECT_ID
```

### 3. Installation
```bash
# Clone the repository
git clone https://github.com/LUJ20/Instant-Custom-Voices-for-Customer-Service.git
cd Instant-Custom-Voices-for-Customer-Service

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Run the Streamlit Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## ☁️ Google Cloud Run Deployment

Deploy the application directly to Google Cloud Run as a serverless container:

```bash
# Make deployment script executable
chmod +x deploy.sh

# Deploy to Cloud Run
./deploy.sh YOUR_PROJECT_ID us-central1 YOUR_GCS_BUCKET_NAME YOUR_GCP_ACCOUNT
```

### Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `GOOGLE_CLOUD_PROJECT` | GCP Project ID | `auto-detected` |
| `GOOGLE_CLOUD_LOCATION` | Cloud Run and API region | `us-central1` |
| `GCS_BUCKET_NAME` | Cloud Storage bucket for project persistence | `${PROJECT_ID}-cust-service-voice` |
| `PORT` | Container HTTP port | `8080` |

---

## 📂 Repository Structure

```
├── app.py                     # Streamlit frontend & interactive orchestration
├── voice_service.py           # Chirp 3 Instant Custom Voice synthesis & key creation
├── voice_gallery.py           # Gallery manager for custom audio reference samples
├── script_generator.py        # Gemini 3.8 Flash dynamic dialogue generation
├── project_manager.py         # GCS & local project persistence (save/load/list/delete)
├── gcs_service.py             # Google Cloud Storage REST API service wrapper
├── scenarios.py               # Customer service scenarios & nationality name mapping
├── assets/                    # Reference audio files, gallery metadata, and logos
│   ├── gallery_metadata.json
│   ├── layo_voice.mp3
│   └── rahul_voice.mp3
├── deploy.sh                  # One-click Cloud Run deployment script
├── Dockerfile                 # Container definition with Python 3.11 & FFmpeg
├── requirements.txt           # Pinned production dependencies
└── README.md                  # Comprehensive technical documentation
```

---

## 📚 Technical References

- [Google Cloud Text-to-Speech Instant Custom Voice Documentation](https://docs.cloud.google.com/text-to-speech/docs/chirp3-instant-custom-voice)
- [Google Cloud Vertex AI Gemini Models](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)
- [Google Cloud Run Serverless Architecture](https://cloud.google.com/run/docs)
- [Google Cloud Storage REST API](https://cloud.google.com/storage/docs/json_api)

---

## 📄 License

Copyright 2026 Google LLC. Licensed under the Apache License, Version 2.0.
