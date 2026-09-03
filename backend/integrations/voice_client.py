"""Voice/Text API client — Qwen Voice integration stub."""
import httpx
from typing import Dict, Any, Optional
from backend.config import settings


class VoiceClient:
    """Client for speech-to-text and language detection."""

    def __init__(self, base_url: str = None, timeout: float = 3.0):
        self.base_url = base_url or settings.VOICE_API_URL
        self.timeout = timeout

    async def transcribe(self, audio_data: bytes, language_hint: str = "ur") -> Dict[str, Any]:
        """Convert audio to text. Returns {text, language, confidence}."""
        # STUB: Return mock transcription
        return {
            "text": "Mujhe sar mein dard hai aur blood pressure zyada hai",
            "language": language_hint,
            "confidence": 0.92,
            "symptoms_extracted": ["headache", "high_blood_pressure"],
        }

    async def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect language of input text."""
        return {
            "language": "ur",
            "confidence": 0.95,
            "script": "roman_urdu",
        }

    async def extract_symptoms(self, text: str, language: str = "ur") -> list:
        """Extract structured symptoms from free text."""
        # STUB: Basic keyword matching
        symptom_keywords = {
            "headache": ["sar dard", "headache", "sir mein dard"],
            "bleeding": ["bleeding", "khoon", "blood"],
            "fever": ["bukhar", "fever", "tap"],
            "pain": ["dard", "pain", "takleef"],
            "nausea": ["ulti", "nausea", "ji machlana"],
        }
        found = []
        text_lower = text.lower()
        for symptom, keywords in symptom_keywords.items():
            if any(kw in text_lower for kw in keywords):
                found.append({"name": symptom, "severity": "moderate", "source": "voice"})
        return found if found else [{"name": "general_discomfort", "severity": "mild", "source": "voice"}]
