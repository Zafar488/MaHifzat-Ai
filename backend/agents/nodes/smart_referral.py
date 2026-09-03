"""Smart referral node — facility lookup, ranking, route planning, referral creation."""

from datetime import datetime
from typing import Any, Dict, List

from backend.schemas.state import AgentState
from backend.integrations.facility_locator import FacilityLocatorClient
from backend.integrations.routing_client import RoutingClient


async def smart_referral(state: AgentState) -> dict:
    """Find and rank nearby healthcare facilities, plan route, create referral record.

    Ranks facilities by capability match (emergency/maternity/NICU) + distance.
    Determines urgency from state emergency flag and clinical risk results.
    """
    timestamp = datetime.utcnow().isoformat()
    node_name = "smart_referral"

    try:
        is_emergency: bool = state.get("emergency", False)
        demographics: Dict[str, Any] = state.get("demographics") or {}
        clinical_risk_result: Dict[str, Any] = state.get("clinical_risk_result") or {}
        fetal_result: Dict[str, Any] = state.get("fetal_result") or {}

        # Default location (Peshawar region) if not provided
        patient_lat = float(demographics.get("latitude", 34.0080))
        patient_lon = float(demographics.get("longitude", 71.5785))

        # Determine required capabilities based on risk
        need_emergency = is_emergency
        need_nicu = (
            fetal_result.get("fetal_status", "").lower() in ("pathological", "suspicious")
            or fetal_result.get("preterm_risk", "").lower() in ("high", "high risk")
        )

        # --- Find nearby facilities ------------------------------------
        locator = FacilityLocatorClient()
        facilities = await locator.find_nearby_facilities(
            latitude=patient_lat,
            longitude=patient_lon,
            radius_km=50.0 if is_emergency else 20.0,
            facility_type="hospital",
        )

        # --- Rank facilities by capability match + distance ------------
        def _score_facility(fac: Dict[str, Any]) -> float:
            score = 0.0
            if need_emergency and fac.get("has_emergency"):
                score += 10.0
            if need_nicu and fac.get("has_nicu"):
                score += 10.0
            if fac.get("has_maternity"):
                score += 5.0
            # Lower distance = higher score
            distance = fac.get("distance_km", 100)
            score += max(0, 20.0 - distance)
            # Penalize high-load facilities
            if fac.get("current_load") == "high":
                score -= 3.0
            return score

        ranked = sorted(facilities, key=_score_facility, reverse=True)

        # --- Route planning for top facility ---------------------------
        route_info = None
        selected_facility = ranked[0] if ranked else None
        if selected_facility:
            routing = RoutingClient()
            origin = (patient_lat, patient_lon)
            destination = (selected_facility["latitude"], selected_facility["longitude"])
            route_info = await routing.get_route(origin, destination)

        # --- Determine urgency level -----------------------------------
        if is_emergency:
            urgency = "emergency"
        else:
            maternal_risk = clinical_risk_result.get("maternal_risk", {}).get("risk_level", "unknown")
            if maternal_risk.lower() in ("high", "high risk"):
                urgency = "urgent"
            else:
                urgency = "routine"

        # --- Build referral result -------------------------------------
        referral_result: Dict[str, Any] = {
            "referral_case_id": state.get("case_id", "unknown"),
            "urgency_level": urgency,
            "ranked_facilities": ranked,
            "selected_facility": selected_facility,
            "route_info": route_info,
            "estimated_travel_time_min": route_info.get("travel_time_minutes") if route_info else None,
            "capabilities_needed": {
                "emergency": need_emergency,
                "nicu": need_nicu,
                "maternity": True,
            },
            "timestamp": timestamp,
        }

        result_summary = (
            f"Referral: {urgency} | "
            f"Top facility: {selected_facility.get('name', 'N/A') if selected_facility else 'N/A'} | "
            f"Travel: {route_info.get('travel_time_minutes', 'N/A') if route_info else 'N/A'} min | "
            f"{len(ranked)} facilities found"
        )

        audit_entry = {
            "agent": node_name,
            "timestamp": timestamp,
            "action": "smart_referral_created",
            "result_summary": result_summary,
        }

        return {
            "referral_result": referral_result,
            "current_step": "referral_complete",
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
            "action": "smart_referral_error",
            "result_summary": f"Error during referral: {e}",
        }
        return {
            "errors": [error_entry],
            "audit_trail": [audit_entry],
        }
