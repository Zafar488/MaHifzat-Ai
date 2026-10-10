"""Voice transcription is unavailable; no fabricated text or confidence."""
from backend.config import settings


class VoiceClient:
    def __init__(self, *args, **kwargs):
        pass

    async def transcribe(self, audio_data, language_hint="ur"):
        return {"status": "simulated" if settings.DEMO_MODE else "unavailable", "simulated": settings.DEMO_MODE, "text": "", "language": None, "confidence": None, "symptoms_extracted": []}

    async def detect_language(self, text):
        return {"status": "unavailable", "language": None, "confidence": None}

    async def extract_symptoms(self, text, language="ur"):
        return []
