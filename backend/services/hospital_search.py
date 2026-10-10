"""Discover actual hospitals and enrich only the nearest results with consented routes."""
import asyncio
from backend.integrations.osm_discovery import OSMDiscoveryClient
from backend.integrations.routing_client import RoutingClient
from backend.schemas.care import PatientLocation

async def discover_hospitals(location,radius_km=25):
    point=PatientLocation.model_validate(location)
    result=await OSMDiscoveryClient().search(point.model_dump(mode="json"),radius_km)
    if not result["facilities"]: return result
    facilities=[dict(f) for f in result["facilities"][:10]]
    routing=RoutingClient()
    routes=await asyncio.gather(*(routing.get_route((point.latitude,point.longitude),(f["latitude"],f["longitude"]),
           consent=point.share_for_routing) for f in facilities[:5]))
    for facility,route in zip(facilities,routes):
        facility.update(route)
        facility["distance_m"]=round(facility["distance_km"]*1000)
    return {**result,"facilities":facilities}

async def tentative_referral(location,capabilities,urgency):
    from backend.integrations.facility_locator import haversine_km
    point=PatientLocation.model_validate(location)
    result=await OSMDiscoveryClient().search(point.model_dump(mode="json"),100)
    candidates=[]
    for fac in result["facilities"]:
        reported=fac["reported_services"]
        missing=[k for k,needed in capabilities.items() if needed and reported.get(k) is False]
        if missing:continue
        hints=sum(reported.get(k) is True for k,needed in capabilities.items() if needed)
        fac={**fac,"reported_required_services":hints,"requires_service_confirmation":True,
             "rank_distance_km":haversine_km((location["latitude"],location["longitude"]),(fac["latitude"],fac["longitude"]))}
        candidates.append(fac)
    candidates.sort(key=lambda f:(-f["reported_required_services"],f["rank_distance_km"],f["facility_id"]))
    candidates=candidates[:5]
    routes=await asyncio.gather(*(RoutingClient().get_route((point.latitude,point.longitude),(f["latitude"],f["longitude"]),consent=point.share_for_routing) for f in candidates))
    for fac,route in zip(candidates,routes):
        fac.update(route)
        fac["distance_m"]=round(fac["distance_km"]*1000)
    return result,candidates
