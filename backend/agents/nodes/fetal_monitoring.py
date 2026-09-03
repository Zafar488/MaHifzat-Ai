"""Fetal monitoring node — FetalWatch + PretermGuard predictions from CTG data."""

from datetime import datetime
from typing import Any, Dict

from backend.schemas.state import AgentState
from backend.services.inference import ModelRegistry


async def fetal_monitoring(state: AgentState) -> dict:
    """Run FetalWatch and PretermGuard models on CTG features.

    If fetal status is pathological or preterm risk is high, sets emergency=True.
    Skips gracefully if no CTG data is available in state.
    """
    timestamp = datetime.utcnow().isoformat()
    node_name = "fetal_monitoring"

    try:
        ctg_data: Dict[str, Any] = state.get("ctg_data") or {}

        if not ctg_data:
            audit_entry = {
                "agent": node_name,
                "timestamp": timestamp,
                "action": "fetal_monitoring_skipped",
                "result_summary": "No CTG data available — skipping fetal assessment",
            }
            return {
                "fetal_result": {
                    "fetal_status": "not_assessed",
                    "preterm_risk": "not_assessed",
                    "reason": "no_ctg_data",
                },
                "current_step": "fetal_monitoring_skipped",
                "audit_trail": [audit_entry],
            }

        registry = ModelRegistry()

        # --- FetalWatch prediction -------------------------------------
        fetal_pred = registry.predict_fetal_health(ctg_data)

        # --- PretermGuard prediction -----------------------------------
        preterm_pred = registry.predict_preterm_risk(ctg_data)

        # --- Determine if emergency ------------------------------------
        fetal_status = fetal_pred.get("fetal_status", "unknown")
        preterm_risk = preterm_pred.get("risk_level", "unknown")

        is_emergency = fetal_status.lower() == "pathological"
        is_high_risk = (
            fetal_status.lower() in ("pathological", "suspicious")
            or preterm_risk.lower() in ("high", "high risk")
        )

        # --- Build result dict -----------------------------------------
        fetal_result: Dict[str, Any] = {
            "fetal_status": fetal_status,
            "fetal_probabilities": fetal_pred.get("probabilities", {}),
            "fetal_confidence": fetal_pred.get("confidence", 0.0),
            "fetal_model_available": fetal_pred.get("model_available", False),
            "preterm_risk": preterm_risk,
            "preterm_probabilities": preterm_pred.get("probabilities", {}),
            "preterm_confidence": preterm_pred.get("confidence", 0.0),
            "preterm_model_available": preterm_pred.get("model_available", False),
            "escalate": is_high_risk,
            "timestamp": timestamp,
        }

        result_summary = (
            f"Fetal: {fetal_status} (conf {fetal_pred.get('confidence', 0):.2f}) | "
            f"Preterm: {preterm_risk} (conf {preterm_pred.get('confidence', 0):.2f}) | "
            f"Emergency: {is_emergency}"
        )

        audit_entry = {
            "agent": node_name,
            "timestamp": timestamp,
            "action": "fetal_monitoring_assessment",
            "result_summary": result_summary,
        }

        updates: Dict[str, Any] = {
            "fetal_result": fetal_result,
            "current_step": "fetal_monitoring_complete",
            "audit_trail": [audit_entry],
        }

        if is_emergency:
            updates["emergency"] = True

        return updates

    except Exception as e:
        error_entry = {
            "agent": node_name,
            "error": str(e),
            "timestamp": timestamp,
        }
        audit_entry = {
            "agent": node_name,
            "timestamp": timestamp,
            "action": "fetal_monitoring_error",
            "result_summary": f"Error during fetal monitoring: {e}",
        }
        return {
            "errors": [error_entry],
            "audit_trail": [audit_entry],
        }
