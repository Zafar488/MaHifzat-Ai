"""Reporting node — generates case summary payload and dashboard/trend data structures."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

from backend.schemas.state import AgentState

logger = logging.getLogger(__name__)


async def reporting(state: AgentState) -> dict:
    """Generate comprehensive case summary payload and trend/dashboard data.

    Aggregates results from all upstream agents into a reporting structure
    suitable for dashboards, trend analysis, and export.
    """
    timestamp = datetime.utcnow().isoformat()
    node_name = "reporting"

    try:
        patient_id: str = state.get("patient_id", "unknown")
        case_id: str = state.get("case_id", "unknown")
        is_emergency: bool = state.get("emergency", False)
        language: str = state.get("language", "en")
        channel: str = state.get("channel", "app")

        vitals: Dict[str, Any] = state.get("vitals") or {}
        symptoms: list = state.get("symptoms") or []
        demographics: Dict[str, Any] = state.get("demographics") or {}

        clinical_risk_result: Dict[str, Any] = state.get("clinical_risk_result") or {}
        fetal_result: Dict[str, Any] = state.get("fetal_result") or {}
        anc_result: Dict[str, Any] = state.get("anc_result") or {}
        referral_result: Dict[str, Any] = state.get("referral_result") or {}
        communication_result: Dict[str, Any] = state.get("communication_result") or {}
        clinician_result: Dict[str, Any] = state.get("clinician_result") or {}
        data_quality_result: Dict[str, Any] = state.get("data_quality_result") or {}
        audit_trail: list = state.get("audit_trail") or []
        errors: list = state.get("errors") or []

        # --- Case summary payload --------------------------------------
        case_summary: Dict[str, Any] = {
            "patient_id": patient_id,
            "case_id": case_id,
            "language": language,
            "channel": channel,
            "emergency": is_emergency,
            "created_at": timestamp,
            "patient_profile": {
                "demographics": demographics,
                "vitals": vitals,
                "symptoms_count": len(symptoms),
                "symptoms": symptoms,
            },
            "risk_assessments": {
                "maternal_risk": {
                    "level": clinical_risk_result.get("maternal_risk", {}).get("risk_level", "unknown"),
                    "confidence": clinical_risk_result.get("maternal_risk", {}).get("confidence", 0),
                    "model_available": clinical_risk_result.get("maternal_risk", {}).get("model_available", False),
                },
                "gestational_risk": {
                    "level": clinical_risk_result.get("gestational_risk", {}).get("risk_level") if clinical_risk_result.get("gestational_risk") else "not_assessed",
                    "confidence": clinical_risk_result.get("gestational_risk", {}).get("confidence", 0) if clinical_risk_result.get("gestational_risk") else 0,
                },
                "fetal_status": {
                    "status": fetal_result.get("fetal_status", "not_assessed"),
                    "confidence": fetal_result.get("fetal_confidence", 0),
                },
                "preterm_risk": {
                    "level": fetal_result.get("preterm_risk", "not_assessed"),
                    "confidence": fetal_result.get("preterm_confidence", 0),
                },
                "anc_missed_risk": {
                    "score": anc_result.get("missed_visit_risk", 0),
                    "priority": anc_result.get("priority", "unknown"),
                },
                "who_triage": clinical_risk_result.get("who_red_flags", {}).get("triage_level", "UNKNOWN"),
            },
            "referral": {
                "urgency": referral_result.get("urgency_level"),
                "selected_facility_name": referral_result.get("selected_facility", {}).get("name") if referral_result.get("selected_facility") else None,
                "travel_time_min": referral_result.get("estimated_travel_time_min"),
            },
            "communication": {
                "messages_sent": communication_result.get("messages_sent", 0),
                "all_delivered": communication_result.get("all_delivered", False),
            },
            "clinician_review": {
                "status": clinician_result.get("status", "not_reviewed"),
                "requires_attention": clinician_result.get("requires_immediate_attention", False),
            },
            "data_quality": {
                "quality_score": data_quality_result.get("quality_score", 0),
                "flags_count": len(data_quality_result.get("flags", [])),
                "warnings_count": len(data_quality_result.get("warnings", [])),
            },
            "errors_count": len(errors),
        }

        # --- Trend / dashboard data structure --------------------------
        dashboard_data: Dict[str, Any] = {
            "case_id": case_id,
            "patient_id": patient_id,
            "timestamp": timestamp,
            "risk_scorecard": {
                "maternal": _risk_to_numeric(clinical_risk_result.get("maternal_risk", {}).get("risk_level", "unknown")),
                "gestational": _risk_to_numeric(
                    clinical_risk_result.get("gestational_risk", {}).get("risk_level") if clinical_risk_result.get("gestational_risk") else "not_assessed"
                ),
                "fetal": _fetal_to_numeric(fetal_result.get("fetal_status", "not_assessed")),
                "preterm": _risk_to_numeric(fetal_result.get("preterm_risk", "not_assessed")),
                "anc_missed": anc_result.get("missed_visit_risk", 0),
                "data_quality": data_quality_result.get("quality_score", 0),
            },
            "vitals_snapshot": vitals,
            "pipeline_health": {
                "agents_executed": len(set(e.get("agent") for e in audit_trail if isinstance(e, dict))),
                "total_audit_entries": len(audit_trail),
                "total_errors": len(errors),
                "emergency_escalated": is_emergency,
            },
        }

        result_summary = (
            f"Report generated | Case: {case_id} | Patient: {patient_id} | "
            f"Emergency: {is_emergency} | Agents: {dashboard_data['pipeline_health']['agents_executed']} | "
            f"Errors: {len(errors)}"
        )

        # --- LLM-generated narrative report (optional) ------------------
        # Falls back to the short template summary if the Groq API fails —
        # the structured reporting payload is always produced.
        narrative = result_summary
        llm_generated = False
        try:
            from backend.services.llm import get_llm_service

            llm = get_llm_service()
            if llm is not None:
                analytics_data = {
                    "case_summary": case_summary,
                    "dashboard_data": dashboard_data,
                }
                # Run the sync Groq call in a worker thread so we don't block the loop.
                narrative = await asyncio.to_thread(llm.generate_report, analytics_data)
                llm_generated = True
        except Exception as exc:
            logger.warning("LLM report generation failed: %s", exc)
            narrative = result_summary
            llm_generated = False

        reporting_result: Dict[str, Any] = {
            "case_summary": case_summary,
            "dashboard_data": dashboard_data,
            "narrative": narrative,
            "llm_generated": llm_generated,
            "generated_at": timestamp,
        }

        audit_entry = {
            "agent": node_name,
            "timestamp": timestamp,
            "action": "reporting_generated",
            "result_summary": f"{result_summary} | LLM narrative: {llm_generated}",
        }

        return {
            "reporting_result": reporting_result,
            "current_step": "reporting_complete",
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
            "action": "reporting_error",
            "result_summary": f"Error generating report: {e}",
        }
        return {
            "errors": [error_entry],
            "audit_trail": [audit_entry],
        }


def _risk_to_numeric(risk_level: str) -> float:
    """Convert risk level string to numeric score for dashboard."""
    mapping = {
        "low": 0.25,
        "medium": 0.5,
        "high": 0.75,
        "high risk": 0.75,
        "emergency": 1.0,
        "unknown": 0.0,
        "not_assessed": -1.0,
    }
    return mapping.get(risk_level.lower(), 0.0) if risk_level else 0.0


def _fetal_to_numeric(fetal_status: str) -> float:
    """Convert fetal status to numeric score for dashboard."""
    mapping = {
        "normal": 0.2,
        "suspicious": 0.6,
        "pathological": 1.0,
        "not_assessed": -1.0,
        "unknown": 0.0,
    }
    return mapping.get(fetal_status.lower(), 0.0) if fetal_status else 0.0
