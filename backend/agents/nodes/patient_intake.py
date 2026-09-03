"""Patient intake node — collects and validates demographics, vitals, symptoms."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

from backend.schemas.state import AgentState
from backend.integrations.voice_client import VoiceClient

logger = logging.getLogger(__name__)


async def _generate_followup_questions(
    missing_fields: List[str],
    patient_context: Dict[str, Any],
) -> tuple:
    """Generate follow-up questions for missing fields via Groq LLM.

    Returns (questions: List[str], llm_generated: bool).
    Falls back to simple template questions if the LLM is unavailable —
    the intake node must never crash because of an LLM failure.
    """
    fallback_questions = [
        f"Could you please provide the patient's {field.replace('_', ' ')}?"
        for field in missing_fields
    ]

    try:
        from backend.services.llm import get_llm_service

        llm = get_llm_service()
        if llm is None:
            return fallback_questions, False

        # Run the sync Groq call in a worker thread so we don't block the loop.
        text = await asyncio.to_thread(
            llm.generate_followup_questions,
            missing_fields,
            patient_context,
        )

        # Parse the LLM response into individual question lines.
        parsed = [
            line.strip().lstrip("0123456789.-) ").strip()
            for line in text.splitlines()
            if "?" in line
        ]
        parsed = [q for q in parsed if q]
        if parsed:
            return parsed, True
        return fallback_questions, False
    except Exception as exc:
        logger.warning("LLM follow-up question generation failed: %s", exc)
        return fallback_questions, False


async def patient_intake(state: AgentState) -> dict:
    """Collect patient demographics, vitals, and symptoms from state.

    If voice audio is present, transcribe and extract symptoms via VoiceClient.
    Validates that required fields are present before marking intake complete.
    """
    timestamp = datetime.utcnow().isoformat()
    node_name = "patient_intake"

    try:
        # --- Gather raw data from state --------------------------------
        vitals: Dict[str, Any] = state.get("vitals") or {}
        symptoms: list = state.get("symptoms") or []
        demographics: Dict[str, Any] = state.get("demographics") or {}
        language: str = state.get("language", "ur")
        audio_data = state.get("audio_data")  # optional voice input

        # --- Voice processing (if audio present) -----------------------
        voice_transcript = None
        if audio_data:
            voice_client = VoiceClient()
            transcription = await voice_client.transcribe(audio_data, language_hint=language)
            voice_transcript = transcription.get("text", "")
            detected_lang = transcription.get("language", language)

            # Extract symptoms from transcribed text
            extracted = await voice_client.extract_symptoms(voice_transcript, detected_lang)
            symptoms = symptoms + extracted

        # --- Build structured profile ----------------------------------
        profile: Dict[str, Any] = {
            "patient_id": state.get("patient_id"),
            "language": language,
            "channel": state.get("channel", "app"),
            "demographics": demographics,
            "vitals": vitals,
            "symptoms": symptoms,
        }
        if voice_transcript:
            profile["voice_transcript"] = voice_transcript

        # --- Validate completeness ------------------------------------
        required_vital_fields = [
            "systolic_bp", "diastolic_bp", "heart_rate",
            "temperature_celsius", "gestational_age_weeks",
        ]
        missing_fields = [
            f for f in required_vital_fields if f not in vitals or vitals[f] is None
        ]

        intake_complete = len(missing_fields) == 0

        # --- LLM-generated follow-up questions for missing fields ------
        followup_questions: List[str] = []
        llm_generated = False
        if missing_fields:
            patient_context = {
                "patient_id": state.get("patient_id"),
                "language": language,
                "collected_vitals": vitals,
                "symptoms": symptoms,
                "demographics": demographics,
            }
            followup_questions, llm_generated = await _generate_followup_questions(
                missing_fields, patient_context
            )

        result_summary = (
            f"Intake {'complete' if intake_complete else 'incomplete'}: "
            f"{len(vitals)} vitals, {len(symptoms)} symptoms, "
            f"{len(missing_fields)} missing fields"
        )

        audit_entry = {
            "agent": node_name,
            "timestamp": timestamp,
            "action": "patient_data_collection",
            "result_summary": result_summary,
        }

        return {
            "intake_complete": intake_complete,
            "vitals": vitals,
            "symptoms": symptoms,
            "demographics": demographics,
            "current_step": "intake_complete" if intake_complete else "intake_incomplete",
            "audit_trail": [audit_entry],
            "profile": profile,
            "missing_fields": missing_fields,
            "followup_questions": followup_questions,
            "llm_generated": llm_generated,
        }

    except Exception as e:
        error_entry = {
            "agent": node_name,
            "error": str(e),
            "timestamp": timestamp,
        }
        audit_entry = {
            "agent": node_name,
            "timestamp": timestamp,
            "action": "patient_intake_error",
            "result_summary": f"Error during intake: {e}",
        }
        return {
            "intake_complete": False,
            "errors": [error_entry],
            "audit_trail": [audit_entry],
        }
