"""Clinical risk assessment node — maternal risk + gestational complications + WHO safety rules."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

from backend.schemas.state import AgentState
from backend.services.inference import ModelRegistry
from backend.services.safety import SafetyService

logger = logging.getLogger(__name__)


async def clinical_risk(state: AgentState) -> dict:
    """Run maternal risk prediction, gestational complication prediction, and WHO red-flag check.

    SafetyService.check_who_red_flags is ALWAYS called — it is mandatory and cannot be skipped.
    If WHO rules return RED triage, emergency is set to True.
    """
    timestamp = datetime.utcnow().isoformat()
    node_name = "clinical_risk"

    try:
        vitals: Dict[str, Any] = state.get("vitals") or {}
        demographics: Dict[str, Any] = state.get("demographics") or {}
        registry = ModelRegistry()

        # --- MaternalGuard prediction ----------------------------------
        maternal_pred = registry.predict_maternal_risk(vitals)

        # --- GestationInsight prediction (if clinical features available) ---
        gestational_pred = None
        clinical_features = {**demographics, **vitals}
        gestation_keys = {"Glucose", "BloodPressure", "BMI", "Insulin", "SkinThickness", "Pregnancies"}
        if any(k in clinical_features for k in gestation_keys):
            gestational_pred = registry.predict_gestational_complication(clinical_features)

        # --- WHO Safety Rules (MANDATORY — never skip) -----------------
        safety_service = SafetyService()
        who_result = safety_service.check_who_red_flags(vitals)

        triage_level = who_result.get("triage_level", "GREEN")
        is_emergency = triage_level == "HIGH_RISK_EMERGENCY"

        # --- Build result dict -----------------------------------------
        clinical_risk_result: Dict[str, Any] = {
            "maternal_risk": maternal_pred,
            "gestational_risk": gestational_pred,
            "who_red_flags": {
                "triage_level": triage_level,
                "triggered_rules": who_result.get("triggered_rules", []),
                "clinical_rationale": who_result.get("clinical_rationale", ""),
                "recommended_actions": who_result.get("recommended_actions", []),
            },
            "is_emergency": is_emergency,
            "timestamp": timestamp,
        }

        # Risk summary text (short template version, used as LLM fallback)
        risk_parts = [f"Maternal: {maternal_pred.get('risk_level', 'unknown')}"]
        if gestational_pred:
            risk_parts.append(f"Gestational: {gestational_pred.get('risk_level', 'unknown')}")
        risk_parts.append(f"WHO Triage: {triage_level}")
        short_summary = " | ".join(risk_parts)

        # --- LLM-generated human-readable risk summary (optional) -------
        # Falls back to the short template summary if the Groq API fails —
        # the risk assessment itself must never depend on the LLM.
        risk_summary = short_summary
        llm_generated = False
        try:
            from backend.services.llm import get_llm_service

            llm = get_llm_service()
            if llm is not None:
                risk_data = {
                    "patient_id": state.get("patient_id"),
                    "vitals": vitals,
                    "demographics": demographics,
                    "maternal_risk": maternal_pred,
                    "gestational_risk": gestational_pred,
                    "who_red_flags": clinical_risk_result["who_red_flags"],
                    "is_emergency": is_emergency,
                }
                # Run the sync Groq call in a worker thread so we don't block the loop.
                risk_summary = await asyncio.to_thread(llm.generate_risk_summary, risk_data)
                llm_generated = True
        except Exception as exc:
            logger.warning("LLM risk summary generation failed: %s", exc)
            risk_summary = short_summary
            llm_generated = False

        clinical_risk_result["risk_summary"] = risk_summary
        clinical_risk_result["llm_generated"] = llm_generated

        audit_entry = {
            "agent": node_name,
            "timestamp": timestamp,
            "action": "clinical_risk_assessment",
            "result_summary": f"{short_summary} | LLM summary: {llm_generated}",
        }

        return {
            "clinical_risk_result": clinical_risk_result,
            "emergency": is_emergency,
            "current_step": "clinical_risk_complete",
            "audit_trail": [audit_entry],
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
            "action": "clinical_risk_error",
            "result_summary": f"Error during clinical risk assessment: {e}",
        }
        return {
            "errors": [error_entry],
            "audit_trail": [audit_entry],
        }
