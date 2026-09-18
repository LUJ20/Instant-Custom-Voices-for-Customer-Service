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
import re
import json
import logging
from typing import List, Dict, Any, Optional
import google.auth
from google.auth.transport.requests import AuthorizedSession

logger = logging.getLogger("script_generator")

CANDIDATE_GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.1-pro-preview",
    "gemini-2.5-flash",
    "gemini-2.5-pro"
]


class ScriptGenerator:
    """Generates 5-7 turn customer service dialogues using Gemini 3.8 Flash."""

    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1"):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "consumer-genai-experiments")
        self.location = location or os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.session = None
        self._init_session()

    def _init_session(self):
        try:
            credentials, default_project = google.auth.default()
            self.session = AuthorizedSession(credentials)
            self.project_id = (
                os.getenv("GOOGLE_CLOUD_PROJECT")
                or getattr(credentials, "quota_project_id", None)
                or default_project
                or "consumer-genai-experiments"
            )
        except Exception as e:
            logger.warning("Auth session initialization for ScriptGenerator: %s", e)
            self.session = None

    def generate_dialogue(
        self,
        user_scenario_prompt: str,
        agent_name: str = "Priya",
        customer_name: str = "Rahul",
        agent_gender: str = "Female",
        customer_gender: str = "Male"
    ) -> List[Dict[str, Any]]:
        """Generates 5-7 turn dialogue between Agent and Customer based on prompt and character profiles."""
        if not user_scenario_prompt.strip():
            user_scenario_prompt = "A customer calling support regarding an unexpected charge on their bill."

        system_instruction = (
            "You are an expert customer service scriptwriter. Generate a realistic, empathetic, "
            "and professional multi-turn dialogue between a Customer Care Specialist and a Customer.\n"
            f"Characters & Identity:\n"
            f"- Customer Care Specialist: {agent_gender}, named '{agent_name}'. The Specialist must introduce themselves in turn 1 as '{agent_name}'.\n"
            f"- Customer: {customer_gender}, named '{customer_name}'. The Specialist addresses the Customer as '{customer_name}', and the Customer addresses the Specialist as '{agent_name}'.\n"
            "Requirements:\n"
            "- Strictly match these exact names and genders with zero mismatches (e.g., female characters must have female names and pronouns; male characters must have male names and pronouns).\n"
            "- Exactly 5 to 7 dialogue turns total.\n"
            "- Strictly alternating speakers (Agent starts first with a polite greeting, Customer responds, Agent troubleshoots/resolves, Customer confirms, Agent closes).\n"
            "- Return ONLY a valid JSON array of objects with keys: 'speaker' ('agent' or 'customer'), "
            f"'speaker_name' (e.g. 'Customer Care Specialist ({agent_name})' or 'Customer ({customer_name})'), and 'text' (concise spoken line).\n"
            "- No markdown code blocks, backticks, or explanations. Only pure JSON."
        )

        user_content = f"Scenario: {user_scenario_prompt}\nGenerate the 5-7 turn customer service dialogue JSON:"

        if self.session:
            for model_name in CANDIDATE_GEMINI_MODELS:
                try:
                    url = (
                        f"https://{self.location}-aiplatform.googleapis.com/v1/"
                        f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/{model_name}:generateContent"
                    )
                    payload = {
                        "contents": [
                            {"role": "user", "parts": [{"text": f"{system_instruction}\n\n{user_content}"}]}
                        ],
                        "generationConfig": {
                            "temperature": 0.3,
                            "topP": 0.95,
                            "maxOutputTokens": 2048,
                            "responseMimeType": "application/json"
                        }
                    }
                    resp = self.session.post(url, json=payload, timeout=30)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                raw_text = parts[0].get("text", "").strip()
                                dialogue = self._parse_json(raw_text)
                                if dialogue and len(dialogue) >= 3:
                                    logger.info("Successfully generated dialogue using %s (%d turns)", model_name, len(dialogue))
                                    return dialogue
                except Exception as e:
                    logger.warning("Gemini model %s call failed: %s", model_name, e)

        # Fallback dialogue generator
        return self._generate_rule_based_fallback(user_scenario_prompt, agent_name, customer_name)

    def generate_script(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """Alias for generate_dialogue."""
        return self.generate_dialogue(*args, **kwargs)

    def _parse_json(self, raw_text: str) -> Optional[List[Dict[str, Any]]]:
        try:
            # Strip markdown fences if present
            cleaned = re.sub(r"^```json\s*", "", raw_text.strip(), flags=re.IGNORECASE)
            cleaned = re.sub(r"^```\s*", "", cleaned.strip())
            cleaned = re.sub(r"\s*```$", "", cleaned.strip())
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict) and "dialogue" in parsed:
                return parsed["dialogue"]
        except Exception as e:
            logger.warning("JSON parsing error: %s on text: %s", e, raw_text[:100])
        return None

    def _generate_rule_based_fallback(self, prompt: str, agent_name: str = "Priya", customer_name: str = "Rahul") -> List[Dict[str, Any]]:
        """Fallback dialogue in case of connectivity limitation."""
        return [
            {
                "speaker": "agent",
                "speaker_name": f"Customer Care Specialist ({agent_name})",
                "text": f"Thank you for contacting Premier Customer Care. My name is {agent_name}. How can I assist you with your request regarding {prompt[:40]} today?"
            },
            {
                "speaker": "customer",
                "speaker_name": f"Customer ({customer_name})",
                "text": f"Hi {agent_name}, I need some help resolving an issue. Specifically, {prompt}."
            },
            {
                "speaker": "agent",
                "speaker_name": f"Customer Care Specialist ({agent_name})",
                "text": f"I completely understand, {customer_name}, and I would be delighted to help resolve this for you right away. Let me look into your account details."
            },
            {
                "speaker": "customer",
                "speaker_name": f"Customer ({customer_name})",
                "text": f"Thank you, {agent_name}, I really appreciate your swift assistance with this."
            },
            {
                "speaker": "agent",
                "speaker_name": f"Customer Care Specialist ({agent_name})",
                "text": "I have processed your request successfully and updated your confirmation in our system. You should see the changes reflected immediately."
            },
            {
                "speaker": "customer",
                "speaker_name": f"Customer ({customer_name})",
                "text": f"That was very quick and seamless. Thank you so much, {agent_name}!"
            },
            {
                "speaker": "agent",
                "speaker_name": f"Customer Care Specialist ({agent_name})",
                "text": f"You are very welcome, {customer_name}! Thank you for choosing us and have a wonderful day."
            }
        ]
