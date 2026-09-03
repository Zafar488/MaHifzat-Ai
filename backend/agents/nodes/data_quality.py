"""Data quality node — validates vitals ranges, flags anomalies, checks model confidence."""

from datetime import datetime
from typing import Any, Dict, List

from backend.schemas.state import AgentState


# Valid physiological ranges for vitals
VITALS_RANGES: Dict[str, Dict[str, Any]] = {
    "systolic_bp": {"min": 60, "max": 250, "unit": "mmHg", "label": "Systolic BP"},
    "diastolic_bp": {"min": 30, "max": 150, "unit": "mmHg", "label": "Diastolic BP"},
    "heart_rate": {"min": 40, "max": 200, "unit": "bpm", "label": "Heart Rate"},
    "temperature_celsius": {"min": 35, "max": 42, "unit": "°C", "label": "Temperature"},
    "SpO2": {"min": 70, "max": 100, "unit": "%", "label": "SpO2"},
    "fetal_hr": {"min": 60, "max": 220, "unit": "bpm", "label": "Fetal Heart Rate"},
    "respiratory_rate": {"min": 8, "max": 60, "unit": "breaths/min", "label": "Respiratory Rate"},
    "gestational_age_weeks": {"min": 0, "max": 45, "unit": "weeks", "label": "Gestational Age"},
}

# Minimum acceptable model confidence
MIN_CONFIDENCE_THRESHOLD = 0.5


async def data_quality(state: AgentState) -> dict:
    """Validate vitals ranges, flag anomalies, and check model confidence scores.

    Returns data_quality_result with:
    - flags: list of out-of-range or impossible values
    - warnings: list of soft warnings (borderline values, low confidence)
    - model_confidence_checks: per-model confidence assessment
    - quality_score: overall data quality score (0-1)
    """
    timestamp = datetime.utcnow().isoformat()
    node_name = "data_quality"

    try:
        vitals: Dict[str, Any] = state.get("vitals") or {}
        clinical_risk_result: Dict[str, Any] = state.get("clinical_risk_result") or {}
        fetal_result: Dict[str, Any] = state.get("fetal_result") or {}
        anc_result: Dict[str, Any] = state.get("anc_result") or {}

        flags: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []

        # --- Vitals range validation -----------------------------------
        for vital_key, ranges in VITALS_RANGES.items():
            value = vitals.get(vital_key)
            if value is None:
                continue

            try:
                val = float(value)
            except (TypeError, ValueError):
                flags.append({
                    "field": vital_key,
                    "value": value,
                    "issue": "non_numeric_value",
                    "severity": "critical",
                    "label": ranges["label"],
                })
                continue

            if val < ranges["min"] or val > ranges["max"]:
                flags.append({
                    "field": vital_key,
                    "value": val,
                    "expected_range": f"{ranges['min']}-{ranges['max']} {ranges['unit']}",
                    "issue": "out_of_range",
                    "severity": "critical",
                    "label": ranges["label"],
                })

            # Soft warnings for borderline values
            margin = (ranges["max"] - ranges["min"]) * 0.05
            if val < ranges["min"] + margin or val > ranges["max"] - margin:
                warnings.append({
                    "field": vital_key,
                    "value": val,
                    "issue": "borderline_value",
                    "label": ranges["label"],
                })

        # --- Impossible value checks -----------------------------------
        sbp = vitals.get("systolic_bp")
        dbp = vitals.get("diastolic_bp")
        if sbp is not None and dbp is not None:
            try:
                if float(dbp) >= float(sbp):
                    flags.append({
                        "field": "blood_pressure",
                        "issue": "diastolic_gte_systolic",
                        "value": f"{sbp}/{dbp}",
                        "severity": "critical",
                        "label": "Blood Pressure",
                    })
            except (TypeError, ValueError):
                pass

        # --- Model confidence checks -----------------------------------
        model_checks: List[Dict[str, Any]] = []

        maternal_conf = clinical_risk_result.get("maternal_risk", {}).get("confidence", 0)
        model_checks.append({
            "model": "MaternalGuard",
            "confidence": maternal_conf,
            "below_threshold": maternal_conf < MIN_CONFIDENCE_THRESHOLD,
        })

        gestational_conf = clinical_risk_result.get("gestational_risk", {}).get("confidence", 0) if clinical_risk_result.get("gestational_risk") else None
        if gestational_conf is not None:
            model_checks.append({
                "model": "GestationInsight",
                "confidence": gestational_conf,
                "below_threshold": gestational_conf < MIN_CONFIDENCE_THRESHOLD,
            })

        fetal_conf = fetal_result.get("fetal_confidence", 0)
        if fetal_result.get("fetal_status") != "not_assessed":
            model_checks.append({
                "model": "FetalWatch",
                "confidence": fetal_conf,
                "below_threshold": fetal_conf < MIN_CONFIDENCE_THRESHOLD,
            })

        preterm_conf = fetal_result.get("preterm_confidence", 0)
        if fetal_result.get("preterm_risk") != "not_assessed":
            model_checks.append({
                "model": "PretermGuard",
                "confidence": preterm_conf,
                "below_threshold": preterm_conf < MIN_CONFIDENCE_THRESHOLD,
            })

        anc_conf = anc_result.get("confidence", 0)
        if anc_result:
            model_checks.append({
                "model": "CareReach",
                "confidence": anc_conf,
                "below_threshold": anc_conf < MIN_CONFIDENCE_THRESHOLD,
            })

        # Low confidence warnings
        for check in model_checks:
            if check["below_threshold"]:
                warnings.append({
                    "field": check["model"],
                    "issue": "low_model_confidence",
                    "value": check["confidence"],
                    "threshold": MIN_CONFIDENCE_THRESHOLD,
                })

        # --- Overall quality score -------------------------------------
        total_checks = len(VITALS_RANGES) + len(model_checks)
        issues = len(flags) + sum(1 for mc in model_checks if mc["below_threshold"])
        quality_score = round(max(0, 1.0 - (issues / max(total_checks, 1))), 4)

        data_quality_result: Dict[str, Any] = {
            "quality_score": quality_score,
            "flags": flags,
            "warnings": warnings,
            "model_confidence_checks": model_checks,
            "vitals_checked": len([k for k in VITALS_RANGES if k in vitals]),
            "timestamp": timestamp,
        }

        result_summary = (
            f"Data quality: {quality_score:.2f} | "
            f"Flags: {len(flags)} | Warnings: {len(warnings)} | "
            f"Models checked: {len(model_checks)}"
        )

        audit_entry = {
            "agent": node_name,
            "timestamp": timestamp,
            "action": "data_quality_validation",
            "result_summary": result_summary,
        }

        return {
            "data_quality_result": data_quality_result,
            "current_step": "data_quality_complete",
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
            "action": "data_quality_error",
            "result_summary": f"Error during data quality check: {e}",
        }
        return {
            "errors": [error_entry],
            "audit_trail": [audit_entry],
        }
