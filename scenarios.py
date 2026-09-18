"""
Copyright 2026 Google LLC

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

# Pre-configured Customer Service Scenarios

SCENARIOS = {
    "Banking & Financial Services (Fraud Alert & Card Replacement)": {
        "description": "Customer calling bank fraud prevention to verify unrecognized charge and order expedited replacement card.",
        "prompt": "A customer calling their bank support team after receiving an SMS alert regarding a suspicious international charge.",
        "dialogue": [
            {
                "speaker": "agent",
                "speaker_name": "Fraud Protection Specialist (Marcus)",
                "text": "Thank you for calling Apex Premier Bank Security. My name is Marcus. I understand you received a fraud alert today?"
            },
            {
                "speaker": "customer",
                "speaker_name": "Customer (Sophia)",
                "text": "Yes Marcus, I just received a text about a 450 dollar transaction in London, but I am currently home in Chicago!"
            },
            {
                "speaker": "agent",
                "speaker_name": "Fraud Protection Specialist (Marcus)",
                "text": "Thank you for confirming, Sophia. I have immediately blocked that charge and secured your account so no further unauthorized transactions can occur."
            },
            {
                "speaker": "customer",
                "speaker_name": "Customer (Sophia)",
                "text": "Thank you! How soon can I get a replacement debit card?"
            },
            {
                "speaker": "agent",
                "speaker_name": "Fraud Protection Specialist (Marcus)",
                "text": "I have ordered a priority contactless card with free overnight shipping. In the meantime, I have issued a digital card to your Apple and Google Wallet for immediate use."
            },
            {
                "speaker": "customer",
                "speaker_name": "Customer (Sophia)",
                "text": "That is incredible! The digital card is already showing up on my phone. Thank you so much, Marcus."
            },
            {
                "speaker": "agent",
                "speaker_name": "Fraud Protection Specialist (Marcus)",
                "text": "You are very welcome, Sophia. We are always here 24/7 to keep your account secure. Have a wonderful day!"
            }
        ]
    },
    "Healthcare & Hospital (Patient Scheduling & Prescription)": {
        "description": "Patient calling hospital care desk to reschedule specialist consultation and request medication refill.",
        "prompt": "A patient calling their medical clinic to reschedule an upcoming cardiology checkup and confirm their blood pressure prescription renewal.",
        "dialogue": [
            {
                "speaker": "agent",
                "speaker_name": "Clinic Care Coordinator (Elena)",
                "text": "Thank you for calling St. Jude Health Center. My name is Elena. How may I assist with your care today?"
            },
            {
                "speaker": "customer",
                "speaker_name": "Patient (Robert)",
                "text": "Hello Elena, I need to reschedule my cardiology follow-up scheduled for this Friday, and also verify if my blood pressure refill went through."
            },
            {
                "speaker": "agent",
                "speaker_name": "Clinic Care Coordinator (Elena)",
                "text": "I can assist you with both right now, Robert. I see Dr. Chen has an opening next Tuesday at 10:00 AM. Would that time work for you?"
            },
            {
                "speaker": "customer",
                "speaker_name": "Patient (Robert)",
                "text": "Tuesday morning at 10:00 AM is perfect. And what about the prescription refill?"
            },
            {
                "speaker": "agent",
                "speaker_name": "Clinic Care Coordinator (Elena)",
                "text": "Dr. Chen approved your 90-day refill this morning. It has been transmitted electronically to your neighborhood pharmacy and is ready for pickup."
            },
            {
                "speaker": "customer",
                "speaker_name": "Patient (Robert)",
                "text": "That is such a relief! Thank you so much for your thorough and compassionate help, Elena."
            },
            {
                "speaker": "agent",
                "speaker_name": "Clinic Care Coordinator (Elena)",
                "text": "You are very welcome, Robert. Take good care and we will see you next Tuesday!"
            }
        ]
    },
    "Airline Flight Rebooking & Support": {
        "description": "Customer calling airline support to rebook a delayed flight.",
        "prompt": "A customer calling support because their connecting flight was delayed by four hours.",
        "dialogue": [
            {
                "speaker": "agent",
                "speaker_name": "Customer Care Specialist (Sarah)",
                "text": "Thank you for calling SkyWays Premier Support. My name is Sarah. How can I assist you with your travel today?"
            },
            {
                "speaker": "customer",
                "speaker_name": "Customer (David)",
                "text": "Hi Sarah, my connecting flight from Chicago to Seattle just got delayed by four hours. I really need to make an evening dinner meeting."
            },
            {
                "speaker": "agent",
                "speaker_name": "Customer Care Specialist (Sarah)",
                "text": "I completely understand how important that meeting is, David. Let me check the next available direct connection for you right away."
            },
            {
                "speaker": "customer",
                "speaker_name": "Customer (David)",
                "text": "Thank you so much, I really appreciate your quick help!"
            },
            {
                "speaker": "agent",
                "speaker_name": "Customer Care Specialist (Sarah)",
                "text": "Good news! I have confirmed you on the 4:15 PM non-stop flight to Seattle in an aisle seat. Your boarding pass is updated in the mobile app."
            },
            {
                "speaker": "customer",
                "speaker_name": "Customer (David)",
                "text": "That is wonderful news! Thank you for the incredible support, Sarah."
            },
            {
                "speaker": "agent",
                "speaker_name": "Customer Care Specialist (Sarah)",
                "text": "You are very welcome, David! Have a safe and pleasant flight to Seattle."
            }
        ]
    },
    "E-Commerce Order & Return Assistance": {
        "description": "Customer contacting online retail support regarding an item exchange.",
        "prompt": "A customer calling online retail support to exchange an item for a different size and obtain a prepaid shipping label.",
        "dialogue": [
            {
                "speaker": "agent",
                "speaker_name": "Customer Care Specialist (Alex)",
                "text": "Hello, thank you for contacting Apex Retail Customer Care. My name is Alex. How may I help you today?"
            },
            {
                "speaker": "customer",
                "speaker_name": "Customer (Emily)",
                "text": "Hi Alex! I received my winter jacket yesterday, but the size medium is a bit too snug. I'd love to exchange it for a large."
            },
            {
                "speaker": "agent",
                "speaker_name": "Customer Care Specialist (Alex)",
                "text": "I can certainly take care of that exchange for you, Emily. Let me pull up size large in the navy blue colorway."
            },
            {
                "speaker": "customer",
                "speaker_name": "Customer (Emily)",
                "text": "Great! Will I need to pay any return shipping fee?"
            },
            {
                "speaker": "agent",
                "speaker_name": "Customer Care Specialist (Alex)",
                "text": "Not at all. Exchanges are completely free! I have just emailed you a prepaid return shipping label and dispatched your new jacket."
            },
            {
                "speaker": "customer",
                "speaker_name": "Customer (Emily)",
                "text": "That was super fast and easy. Thanks so much, Alex!"
            },
            {
                "speaker": "agent",
                "speaker_name": "Customer Care Specialist (Alex)",
                "text": "It was my pleasure, Emily. Thank you for shopping with Apex Retail and have a great day!"
            }
        ]
    },
    "High-Speed Fiber Technical Support": {
        "description": "Customer contacting ISP support to optimize home WiFi speeds.",
        "prompt": "A customer contacting internet technical support to diagnose slow upstairs wireless speeds.",
        "dialogue": [
            {
                "speaker": "agent",
                "speaker_name": "Technical Support Engineer (Marcus)",
                "text": "Thanks for calling Horizon Fiber Technical Support. My name is Marcus. How can I help resolve your network issue today?"
            },
            {
                "speaker": "customer",
                "speaker_name": "Customer (Jordan)",
                "text": "Hi Marcus, my home internet speed seems much slower in my upstairs home office than downstairs."
            },
            {
                "speaker": "agent",
                "speaker_name": "Technical Support Engineer (Marcus)",
                "text": "I can help with that, Jordan. I just ran a remote diagnostic on your optical router and signal levels to the home are perfect."
            },
            {
                "speaker": "customer",
                "speaker_name": "Customer (Jordan)",
                "text": "Oh, that is good to know. What do you recommend I do to fix the upstairs coverage?"
            },
            {
                "speaker": "agent",
                "speaker_name": "Technical Support Engineer (Marcus)",
                "text": "I just enabled the 5 Gigahertz band steering and pushed an automatic channel optimization to your router. Could you run a quick speed test now?"
            },
            {
                "speaker": "customer",
                "speaker_name": "Customer (Jordan)",
                "text": "Wow, I am now getting 850 Megabits per second upstairs! That completely solved it."
            },
            {
                "speaker": "agent",
                "speaker_name": "Technical Support Engineer (Marcus)",
                "text": "Fantastic! Glad we could get your connection back to peak speed. Enjoy your high-speed fiber!"
            }
        ]
    },
    "Hotel & Hospitality Concierge Services": {
        "description": "Hotel guest calling the front desk concierge for dining recommendations and late check-out arrangements.",
        "prompt": "A hotel guest calling the concierge to book dinner reservations at a downtown bistro and request a 2:00 PM late check-out.",
        "dialogue": [
            {
                "speaker": "agent",
                "speaker_name": "Guest Concierge (Claire)",
                "text": "Good evening, Grand Horizon Hotel Concierge Desk. My name is Claire. How may I assist your stay tonight?"
            },
            {
                "speaker": "customer",
                "speaker_name": "Guest (Liam)",
                "text": "Hi Claire, we are looking for an authentic Italian restaurant nearby with outdoor seating for two around 7:30 PM."
            },
            {
                "speaker": "agent",
                "speaker_name": "Guest Concierge (Claire)",
                "text": "I highly recommend Osteria Del Lago, just two blocks away. I have secured a quiet garden patio table for you at 7:30 PM under your room number."
            },
            {
                "speaker": "customer",
                "speaker_name": "Guest (Liam)",
                "text": "Wonderful! Could we also arrange a late check-out tomorrow at 2:00 PM?"
            },
            {
                "speaker": "agent",
                "speaker_name": "Guest Concierge (Claire)",
                "text": "Certainly, Liam. I have extended your room keys and confirmed your complimentary late check-out until 2:00 PM tomorrow."
            },
            {
                "speaker": "customer",
                "speaker_name": "Guest (Liam)",
                "text": "That is top notch hospitality. Thank you very much, Claire!"
            },
            {
                "speaker": "agent",
                "speaker_name": "Guest Concierge (Claire)",
                "text": "It is our absolute pleasure, Liam. Enjoy your dinner and have a relaxing evening!"
            }
        ]
    }
}


import copy
import re
from typing import Dict, Any, List, Optional


def get_display_name_for_voice(voice_info: Optional[Dict[str, Any]], role: str = "agent") -> str:
    """Resolves a culturally authentic human name matching the voice profile, detected nationality/culture, and gender."""
    if not voice_info:
        return "Priya" if role == "agent" else "Rahul"

    raw_name = voice_info.get("name", "").strip()
    gender = str(voice_info.get("gender", "Female")).capitalize()
    locale = str(voice_info.get("native_locale", "")).lower()

    generic_words = {
        "female", "male", "voice", "profile", "custom", "cloned", "reference", "default",
        "agent", "customer", "support", "care", "service", "sample", "test",
        "indian", "korean", "japanese", "spanish", "french", "german", "american", "british",
        "hindi", "english", "mexican", "asian", "european", "latin"
    }
    name_tokens = re.findall(r"[A-Za-z]+", raw_name.lower())
    is_generic = not name_tokens or any(tok in generic_words for tok in name_tokens) or raw_name.lower().startswith("voice_")

    if not is_generic and len(raw_name) > 1 and "(" not in raw_name:
        return raw_name.strip()

    # Detect nationality/region from name or locale
    text_to_search = (raw_name + " " + locale).lower()

    if "korean" in text_to_search or "ko" in text_to_search:
        if role == "agent":
            return "Ji-woo" if gender == "Female" else "Min-jun"
        else:
            return "Seo-yeon" if gender == "Female" else "Do-hyun"

    elif "japanese" in text_to_search or "ja" in text_to_search:
        if role == "agent":
            return "Sakura" if gender == "Female" else "Kenji"
        else:
            return "Yui" if gender == "Female" else "Hiroshi"

    elif "spanish" in text_to_search or "mexican" in text_to_search or "es" in text_to_search or "latin" in text_to_search:
        if role == "agent":
            return "Sofia" if gender == "Female" else "Carlos"
        else:
            return "Elena" if gender == "Female" else "Diego"

    elif "french" in text_to_search or "fr" in text_to_search:
        if role == "agent":
            return "Camille" if gender == "Female" else "Antoine"
        else:
            return "Juliette" if gender == "Female" else "Lucas"

    elif "german" in text_to_search or "de" in text_to_search:
        if role == "agent":
            return "Emma" if gender == "Female" else "Lukas"
        else:
            return "Hannah" if gender == "Female" else "Felix"

    elif "american" in text_to_search or "us" in text_to_search or "british" in text_to_search or "english" in text_to_search:
        if role == "agent":
            return "Sarah" if gender == "Female" else "Marcus"
        else:
            return "Claire" if gender == "Female" else "David"

    # Default to Indian authentic names aligned with gender
    if role == "agent":
        return "Priya" if gender == "Female" else "Rahul"
    else:
        return "Ananya" if gender == "Female" else "Rohan"


def adapt_dialogue_names_and_genders(
    dialogue: List[Dict[str, Any]],
    agent_voice_info: Optional[Dict[str, Any]] = None,
    customer_voice_info: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Dynamically adapts dialogue lines, introductions, and speaker labels to match voice profile genders and names."""
    if not dialogue:
        return []

    agent_name = get_display_name_for_voice(agent_voice_info, role="agent")
    customer_name = get_display_name_for_voice(customer_voice_info, role="customer")

    known_agent_names = [
        "Marcus", "Elena", "Sarah", "Alex", "Claire", "Priya", "Rahul", "Agent",
        "Ji-woo", "Min-jun", "Sakura", "Kenji", "Sofia", "Carlos", "Camille", "Antoine", "Emma", "Lukas"
    ]
    known_customer_names = [
        "Sophia", "Robert", "David", "Emily", "Jordan", "Liam", "Rohan", "Customer", "Patient", "Guest",
        "Ananya", "Seo-yeon", "Do-hyun", "Yui", "Hiroshi", "Diego", "Juliette", "Lucas", "Hannah", "Felix"
    ]

    adapted = copy.deepcopy(dialogue)
    for turn in adapted:
        speaker = turn.get("speaker", "agent")
        text = turn.get("text", "")

        # 1. Adapt agent text
        if speaker == "agent":
            text = re.sub(r"\bMy name is [A-Za-z\-']+\b", f"My name is {agent_name}", text, flags=re.IGNORECASE)
            text = re.sub(r"\bThis is [A-Za-z\-']+\b", f"This is {agent_name}", text, flags=re.IGNORECASE)

            for old_c in known_customer_names:
                text = re.sub(rf"\b(confirming|thank you|welcome|certainly|hello|hi),\s+{old_c}\b", rf"\1, {customer_name}", text, flags=re.IGNORECASE)
                text = re.sub(rf",\s+{old_c}\b", f", {customer_name}", text, flags=re.IGNORECASE)

            current_label = turn.get("speaker_name", "Customer Care Specialist")
            base_role = re.sub(r"\s*\(.*?\)", "", current_label).strip() or "Customer Care Specialist"
            turn["speaker_name"] = f"{base_role} ({agent_name})"
            turn["text"] = text

        # 2. Adapt customer text
        else:
            for old_a in known_agent_names:
                text = re.sub(rf"\b(yes|hi|hello|thank you|thanks),\s+{old_a}\b", rf"\1 {agent_name}", text, flags=re.IGNORECASE)
                text = re.sub(rf"\b(yes|hi|hello|thank you|thanks)\s+{old_a}\b", rf"\1 {agent_name}", text, flags=re.IGNORECASE)
                text = re.sub(rf",\s+{old_a}\b", f", {agent_name}", text, flags=re.IGNORECASE)

            current_label = turn.get("speaker_name", "Customer")
            base_role = re.sub(r"\s*\(.*?\)", "", current_label).strip() or "Customer"
            turn["speaker_name"] = f"{base_role} ({customer_name})"
            turn["text"] = text

    return adapted

