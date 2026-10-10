"""Capability matching before distance ranking; unavailable facilities excluded."""
import asyncio
from urllib.parse import urlencode
from backend.config import settings
from backend.schemas.care import PatientLocation
from backend.integrations.facility_locator import FacilityLocatorClient, haversine_km
from backend.integrations.routing_client import RoutingClient

def effective_urgency(safety, maternal=None, fetal=None):
    if safety.get("is_emergency") or (fetal or {}).get("fetal_status", "").lower() == "pathological":
        return "emergency"
    if safety.get("triage_level") == "URGENT" or (fetal or {}).get("fetal_status", "").lower() in ("suspect", "suspicious") or (maternal or {}).get("risk_level") == "high risk":
        return "urgent"
    return "routine"

async def plan_referral(location, urgency, fetal=None, demo=False):
    capabilities = {"has_maternity": True, "has_emergency": urgency != "routine",
                    "has_nicu": (fetal or {}).get("fetal_status", "").lower() in ("pathological", "suspect", "suspicious")}
    base = {"urgency_level": urgency, "capabilities_needed": capabilities, "selected_facility": None,
            "ranked_facilities": [], "excluded_facilities": [], "estimated_travel_time_min": None, "simulated": demo}
    if not location:
        return {**base, "status": "location_required", "reason": "Record GPS or manually confirmed coordinates. Emergency care must not wait for location capture."}
    point = PatientLocation.model_validate(location)
    if point.source == "demo" and not demo:
        return {**base, "status": "location_required", "reason": "Demo coordinates cannot be used for a real referral"}
    locator = FacilityLocatorClient()
    facilities = await locator.find_nearby_facilities(point.latitude, point.longitude, demo=demo)
    candidates, excluded = [], []
    for fac in facilities:
        missing = [k for k, required in capabilities.items() if required and not fac.get(k)]
        if missing or fac["availability"] == "unavailable":
            excluded.append({"facility_id": fac["facility_id"], "name": fac["name"],
                             "reason": "Missing services: " + ", ".join(missing) if missing else "Recently confirmed unavailable"})
        else:
            candidates.append(fac)
    if not candidates and not demo and point.share_for_discovery:
        from backend.services.hospital_search import tentative_referral
        discovery, tentative = await tentative_referral(point.model_dump(mode="json"),capabilities,urgency)
        if tentative:
            selected=tentative[0]
            return {**base,"status":"unverified_candidate_requires_confirmation","selected_facility":selected,
                "ranked_facilities":tentative,"excluded_facilities":excluded,"directory_status":locator.status,
                "discovery_status":discovery["status"],"coverage_radius_km":discovery.get("coverage_radius_km"),"coverage_limited":discovery.get("coverage_limited",False),"discovery_reason":discovery.get("reason"),"ranking_basis":"reported_service_tags_then_straight_line",
                "estimated_travel_time_min":selected.get("travel_time_minutes"),"source":"OpenStreetMap",
                "reason":"Actual mapped hospital candidate. Required services, availability and acceptance are unverified; call before travelling. Emergency care must not wait."}
        base.update(discovery_status=discovery["status"])
    if not candidates:
        return {**base, "excluded_facilities": excluded, "status": "no_matching_facility",
                "directory_status": locator.status, "reason": "No verified capable facility found within 100 km. Contact maternity/emergency services to arrange care manually."}
    # Bound external calls; route only the five closest capable facilities.
    candidates = candidates[:5]
    routing = RoutingClient()
    routes = await asyncio.gather(*(routing.get_travel_time((point.latitude, point.longitude),
               (fac["latitude"], fac["longitude"]), consent=point.share_for_routing, demo=demo) for fac in candidates))
    ranked = [{**fac, **route} for fac, route in zip(candidates, routes)]
    # Do not mix ETA with straight-line distances if only some routes succeed.
    all_routed = all(f["status"] == "routed" for f in ranked)
    for fac in ranked:
        fac["rank_distance_km"] = fac["distance_km"] if all_routed else round(
            haversine_km(
            (point.latitude, point.longitude), (fac["latitude"], fac["longitude"])), 2)
        fac["requires_availability_confirmation"] = not fac["availability_verified"]
        fac["directions_url"] = None if demo else "https://www.google.com/maps/dir/?" + urlencode(
            {"api": 1, "origin": f"{point.latitude},{point.longitude}", "destination": f"{fac['latitude']},{fac['longitude']}", "travelmode": "driving"})
    ranked.sort(key=lambda f: (not f["availability_verified"], f["travel_time_minutes"] if all_routed else f["rank_distance_km"], f["facility_id"]))
    selected = ranked[0]
    return {**base, "status": "simulated_candidate" if demo else "candidate_requires_confirmation",
            "directory_status": locator.status, "selected_facility": selected,
            "ranked_facilities": ranked, "excluded_facilities": excluded,
            "ranking_basis": "road_eta" if all_routed else "straight_line_distance",
            "estimated_travel_time_min": selected["travel_time_minutes"],
            "reason": "Required services matched first, then availability and travel estimate. Clinician must confirm services, access and acceptance; emergency care must not wait."}
