"""LLM service — Groq API integration for real-time natural language generation.

Provides GroqLLMService, a thin wrapper around Groq's chat completions API
used by agent nodes to generate clinical risk narratives, intake follow-up
questions, patient/staff communication messages, clinician case summaries
and analytics reports.

IMPORTANT: all agent nodes must treat LLM generation as OPTIONAL. If the
Groq API is unavailable (package missing, network failure, invalid key),
callers should fall back to their template text and set llm_generated=False.
"""

import logging
from typing import Optional

from backend.config import Settings

logger = logging.getLogger(__name__)

# Guarded import so the rest of the backend keeps working without groq installed.
try:
    from groq import Groq

    GROQ_AVAILABLE = True
except ImportError:  # pragma: no cover - depends on environment
    Groq = None
    GROQ_AVAILABLE = False
    logger.warning("groq package not installed — LLM text generation disabled")


class GroqLLMService:
    """LLM service using Groq API for real-time text generation."""

    # Groq reasoning models that accept the reasoning_effort parameter.
    # Keeping it at "low" gives fast, concise outputs that fit the small
    # max_tokens budgets used for messages and questions.
    _REASONING_MODEL_PREFIXES = ("openai/gpt-oss", "qwen/", "groq/compound")

    def __init__(self):
        if not GROQ_AVAILABLE:
            raise RuntimeError(
                "The 'groq' package is not installed. Install it with: pip install groq"
            )
        settings = Settings()
        self.client = Groq(api_key=settings.GROQ_API_KEY, timeout=30.0)
        self.model = settings.GROQ_MODEL

    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        """Generate text completion using Groq."""
        request_kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
        if self.model.startswith(self._REASONING_MODEL_PREFIXES):
            request_kwargs["reasoning_effort"] = "low"
        response = self.client.chat.completions.create(**request_kwargs)
        content = response.choices[0].message.content
        if not content or not content.strip():
            raise ValueError("Groq returned an empty completion")
        return content

    def generate_risk_summary(self, risk_data: dict) -> str:
        """Generate a clinical risk summary in plain language."""
        system = (
            "You are a maternal health AI assistant. Generate clear, professional "
            "clinical risk summaries. Be concise but thorough. Include key risk "
            "factors and recommended actions. Respond in both English and Urdu "
            "(Roman Urdu)."
        )
        user = f"Generate a clinical risk summary for this patient data:\n{risk_data}"
        return self.generate(system, user)

    def generate_followup_questions(self, missing_fields: list, patient_context: dict) -> str:
        """Generate follow-up questions for missing patient info."""
        system = (
            "You are a maternal health intake assistant. Generate gentle, "
            "culturally-sensitive follow-up questions in Roman Urdu and English "
            "to collect missing patient information."
        )
        user = (
            f"Missing fields: {missing_fields}\nPatient context: {patient_context}\n"
            "Generate 2-3 follow-up questions."
        )
        return self.generate(system, user, max_tokens=512)

    def generate_communication_message(self, message_type: str, context: dict) -> str:
        """Generate patient/staff communication messages."""
        system = (
            "You are a healthcare communication assistant. Generate clear, "
            "empathetic messages for patients and health workers. Use simple "
            "language. Include both English and Roman Urdu versions."
        )
        user = f"Generate a {message_type} message with this context:\n{context}"
        return self.generate(system, user, max_tokens=512)

    def generate_case_summary(self, case_data: dict) -> str:
        """Generate comprehensive case summary for clinician review."""
        system = (
            "You are a clinical decision support system. Generate a structured "
            "case summary for clinician review. Include: patient overview, risk "
            "assessment, model outputs, recommended actions, and any red flags. "
            "Be precise and medical-professional."
        )
        user = f"Generate a clinician review case summary:\n{case_data}"
        return self.generate(system, user, max_tokens=1500)

    def generate_report(self, analytics_data: dict) -> str:
        """Generate analytics/reporting text."""
        system = (
            "You are a healthcare analytics assistant. Generate concise dashboard "
            "summaries and trend analysis."
        )
        user = f"Generate a brief analytics report:\n{analytics_data}"
        return self.generate(system, user, max_tokens=800)


# ---------------------------------------------------------------------------
# Shared accessor (mirrors the get_model_registry singleton pattern)
# ---------------------------------------------------------------------------

_llm_service: Optional["GroqLLMService"] = None


def get_llm_service() -> Optional["GroqLLMService"]:
    """Return a shared GroqLLMService instance, or None if unavailable.

    Never raises — callers treat None as "LLM unavailable" and fall back
    to template text.
    """
    global _llm_service
    if _llm_service is None:
        try:
            _llm_service = GroqLLMService()
            logger.info("GroqLLMService initialised (model=%s)", _llm_service.model)
        except Exception as exc:
            logger.warning("GroqLLMService unavailable: %s", exc)
            return None
    return _llm_service
