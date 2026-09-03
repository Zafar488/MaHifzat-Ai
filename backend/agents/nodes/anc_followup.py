"""ANC follow-up node — CareReach missed-visit risk prediction and action recommendation."""

from datetime import datetime
from typing import Any, Dict

from backend.schemas.state import AgentState
from backend.services.inference import ModelRegistry


async def anc_followup(state: AgentState) -> dict:
    """Predict ANC missed-visit risk and recommend follow-up action.

    Action is based on priority: high -> home_visit, medium -> call, low -> sms.
    """
    timestamp = datetime.utcnow().isoformat()
    node_name = "anc_followup"

    try:
        demographics: Dict[str, Any] = state.get("demographics") or {}
        vitals: Dict[str, Any] = state.get("vitals") or {}

        # Build patient features for CareReach model
        patient_features: Dict[str, Any] = {**demographics}
        # Merge relevant vitals if not already present
        for key, value in vitals.items():
            if key not in patient_features:
                patient_features[key] = value

        registry = ModelRegistry()
        prediction = registry.predict_anc_followup_risk(patient_features)

        missed_risk_score = prediction.get("missed_risk_score", 0.0)
        priority = prediction.get("priority", "unknown")
        confidence = prediction.get("confidence", 0.0)

        # Determine recommended action based on priority
        action_map = {
            "high": "home_visit",
            "medium": "call",
            "low": "sms",
            "unknown": "sms",
        }
        recommended_action = action_map.get(priority, "sms")

        # Build risk factors list
        risk_factors = []
        if demographics.get("age", 0) < 18:
            risk_factors.append("adolescent_pregnancy")
        if demographics.get("age", 0) > 35:
            risk_factors.append("advanced_maternal_age")
        if demographics.get("parity", 0) > 4:
            risk_factors.append("high_parity")
        if demographics.get("Scholarship", 0) == 0:
            risk_factors.append("no_financial_support")
        if vitals.get("SystolicBP", 0) > 140:
            risk_factors.append("elevated_blood_pressure")

        anc_result: Dict[str, Any] = {
            "missed_visit_risk": missed_risk_score,
            "priority": priority,
            "priority_score": round(missed_risk_score, 4),
            "recommended_action": recommended_action,
            "confidence": confidence,
            "model_available": prediction.get("model_available", False),
            "risk_factors": risk_factors,
            "timestamp": timestamp,
        }

        result_summary = (
            f"ANC Risk: {missed_risk_score:.3f} | Priority: {priority} | "
            f"Action: {recommended_action} | Factors: {len(risk_factors)}"
        )

        audit_entry = {
            "agent": node_name,
            "timestamp": timestamp,
            "action": "anc_followup_assessment",
            "result_summary": result_summary,
        }

        return {
            "anc_result": anc_result,
            "current_step": "anc_followup_complete",
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
            "action": "anc_followup_error",
            "result_summary": f"Error during ANC follow-up: {e}",
        }
        return {
            "errors": [error_entry],
            "audit_trail": [audit_entry],
        }
