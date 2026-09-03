"""Clinician review node — aggregates upstream results into case summary for human review."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

from backend.schemas.state import AgentState

logger = logging.getLogger(__name__)


async def clinician_review(state: AgentState) -> dict:
    """Aggregate all upstream agent results into a structured case summary.

    Marks the case as pending_review for human-in-the-loop approval.
    Does NOT make clinical decisions — only presents data for clinician review.
    """
    timestamp = datetime.utcnow().isoformat()
    node_name = "clinician_review"

    try:
        patient_id: str = state.get("patient_id", "unknown")
        case_id: str = state.get("case_id", "unknown")
        is_emergency: bool = state.get("emergency", False)
        vitals: Dict[str, Any] = state.get("vitals") or {}
        symptoms: list = state.get("symptoms") or []
        demographics: Dict[str, Any] = state.get("demographics") or {}

        clinical_risk_result: Dict[str, Any] = state.get("clinical_risk_result") or {}
        fetal_result: Dict[str, Any] = state.get("fetal_result") or {}
        anc_result: Dict[str, Any] = state.get("anc_result") or {}
        referral_result: Dict[str, Any] = state.get("referral_result") or {}
        communication_result: Dict[str, Any] = state.get("communication_result") or {}

        # --- Build case summary ----------------------------------------
        case_summary: Dict[str, Any] = {
            "patient_id": patient_id,
            "case_id": case_id,
            "emergency": is_emergency,
            "patient_info": {
                "demographics": demographics,
                "vitals": vitals,
                "symptoms": symptoms,
            },
            "clinical_assessment": {
                "maternal_risk": clinical_risk_result.get("maternal_risk"),
                "gestational_risk": clinical_risk_result.get("gestational_risk"),
                "who_triage": clinical_risk_result.get("who_red_flags"),
            },
            "fetal_assessment": {
                "fetal_status": fetal_result.get("fetal_status"),
                "preterm_risk": fetal_result.get("preterm_risk"),
                "escalate": fetal_result.get("escalate", False),
            },
            "anc_followup": {
                "missed_visit_risk": anc_result.get("missed_visit_risk"),
                "priority": anc_result.get("priority"),
                "recommended_action": anc_result.get("recommended_action"),
            },
            "referral": {
                "urgency": referral_result.get("urgency_level"),
                "selected_facility": referral_result.get("selected_facility"),
                "estimated_travel_time_min": referral_result.get("estimated_travel_time_min"),
            },
            "communication_log": {
                "messages_sent": communication_result.get("messages_sent", 0),
                "all_delivered": communication_result.get("all_delivered", False),
            },
            "review_timestamp": timestamp,
        }

        # --- Generate quick-risk indicators for clinician ---------------
        risk_indicators: List[str] = []
        if is_emergency:
            risk_indicators.append("EMERGENCY FLAGGED")
        maternal_risk = clinical_risk_result.get("maternal_risk", {}).get("risk_level", "")
        if maternal_risk.lower() in ("high", "high risk"):
            risk_indicators.append(f"High maternal risk: {maternal_risk}")
        fetal_status = fetal_result.get("fetal_status", "")
        if fetal_status.lower() in ("pathological", "suspicious"):
            risk_indicators.append(f"Fetal concern: {fetal_status}")
        who_triage = clinical_risk_result.get("who_red_flags", {}).get("triage_level", "")
        if who_triage not in ("GREEN", "UNKNOWN", ""):
            risk_indicators.append(f"WHO triage: {who_triage}")

        case_summary["risk_indicators"] = risk_indicators

        # --- LLM-generated narrative case summary (optional) ----------
        # Falls back to a short template summary if the Groq API fails —
        # the review payload itself is always produced from structured data.
        fallback_text = (
            f"Case {case_id} (patient {patient_id}). "
            f"Emergency: {is_emergency}. "
            + (
                f"Risk indicators: {'; '.join(risk_indicators)}. "
                if risk_indicators
                else "No specific risk indicators. "
            )
            + "Awaiting clinician review."
        )

        case_summary_text = fallback_text
        llm_generated = False
        try:
            from backend.services.llm import get_llm_service

            llm = get_llm_service()
            if llm is not None:
                # Run the sync Groq call in a worker thread so we don't block the loop.
                case_summary_text = await asyncio.to_thread(
                    llm.generate_case_summary, case_summary
                )
                llm_generated = True
        except Exception as exc:
            logger.warning("LLM case summary generation failed: %s", exc)
            case_summary_text = fallback_text
            llm_generated = False

        clinician_result: Dict[str, Any] = {
            "status": "pending_review",
            "case_summary": case_summary,
            "case_summary_text": case_summary_text,
            "risk_indicators": risk_indicators,
            "llm_generated": llm_generated,
            "requires_immediate_attention": is_emergency or len(risk_indicators) >= 2,
            "timestamp": timestamp,
        }

        result_summary = (
            f"Case summary ready for review | Patient: {patient_id} | "
            f"Emergency: {is_emergency} | Risk indicators: {len(risk_indicators)} | "
            f"Status: pending_review"
        )

        audit_entry = {
            "agent": node_name,
            "timestamp": timestamp,
            "action": "clinician_review_prepared",
            "result_summary": result_summary,
        }

        return {
            "clinician_result": clinician_result,
            "current_step": "pending_clinician_review",
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
            "action": "clinician_review_error",
            "result_summary": f"Error preparing clinician review: {e}",
        }
        return {
            "errors": [error_entry],
            "audit_trail": [audit_entry],
        }
