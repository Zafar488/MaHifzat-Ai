"""Real OpenStreetMap hospital discovery; map tags are not clinical verification."""
import asyncio
import math
import time
from collections import OrderedDict
from datetime import datetime, timezone
from urllib.parse import urlencode
import httpx
from backend.config import settings
from backend.schemas.care import PatientLocation
from backend.integrations.facility_locator import haversine_km

_CACHE = OrderedDict()
_GATE = asyncio.Semaphore(1)

def reported_services(tags):
    specialties=set(tags.get("healthcare:speciality","").lower().replace(",",";").split(";"))
    def flag(key):
        value=tags.get(key,"").lower()
        return True if value in ("yes","true","1") else False if value in ("no","false","0") else None
    maternity=flag("healthcare:maternity")
    if maternity is None and specialties & {"gynaecology","gynecology","obstetrics","obstetrics_and_gynaecology"}:
        maternity=True
    nicu=flag("healthcare:nicu")
    # Neonatology alone does not prove an intensive-care unit.
    return {"has_emergency":flag("emergency"),"has_maternity":maternity,"has_nicu":nicu}

async def bounded_map_fallback(client, point, requested_radius):
    """One small map request, never tile/bulk download the editing API."""
    radius=min(2.0,requested_radius)
    latitude_delta=radius/111.32
    longitude_delta=latitude_delta/max(0.1,math.cos(math.radians(point.latitude)))
    bbox=(max(-180,point.longitude-longitude_delta),max(-90,point.latitude-latitude_delta),
          min(180,point.longitude+longitude_delta),min(90,point.latitude+latitude_delta))
    response=await client.get(settings.OSM_MAP_FALLBACK_URL,params={"bbox":",".join(map(str,bbox))},
                              headers={"User-Agent":"MaaHifazat/2.1 (bounded hospital lookup)"},timeout=18)
    response.raise_for_status()
    raw=response.json()
    if not isinstance(raw.get("elements"),list) or any("error" in e for e in raw["elements"]):
        raise ValueError("Incomplete map response")
    nodes={e["id"]:(e["lat"],e["lon"]) for e in raw["elements"] if e.get("type")=="node" and "lat" in e and "lon" in e}
    centers={}
    for e in raw["elements"]:
        if e.get("type")=="way":
            coords=[nodes[n] for n in e.get("nodes",[]) if n in nodes]
            if coords:centers[e["id"]]={"lat":sum(c[0] for c in coords)/len(coords),"lon":sum(c[1] for c in coords)/len(coords)}
    hospitals=[]
    for e in raw["elements"]:
        tags=e.get("tags") or {}
        if tags.get("amenity")!="hospital" and tags.get("healthcare")!="hospital":continue
        row=dict(e)
        if e["type"]=="way":row["center"]=centers.get(e["id"],{})
        elif e["type"]=="relation":
            coords=[nodes[m["ref"]] for m in e.get("members",[]) if m.get("type")=="node" and m.get("ref") in nodes]
            coords += [(centers[m["ref"]]["lat"],centers[m["ref"]]["lon"]) for m in e.get("members",[]) if m.get("type")=="way" and m.get("ref") in centers]
            if coords:row["center"]={"lat":sum(c[0] for c in coords)/len(coords),"lon":sum(c[1] for c in coords)/len(coords)}
        hospitals.append(row)
    return {"elements":hospitals},radius

class OSMDiscoveryClient:
    async def search(self,location,radius_km=25):
        point=PatientLocation.model_validate(location)
        empty={"facilities":[],"source":"OpenStreetMap contributors","attribution":"© OpenStreetMap contributors",
               "capabilities_verified":False,"fetched_at":None}
        if not point.share_for_discovery:
            return {**empty,"status":"consent_required","reason":"Allow coordinate sharing with the hospital-search provider first."}
        if point.source=="demo":
            return {**empty,"status":"invalid_location","reason":"Fictional coordinates cannot be used for live discovery."}
        radius_km=max(1,min(100,float(radius_km)))
        key=(round(point.latitude,4),round(point.longitude,4),radius_km)
        cached=_CACHE.get(key)
        if cached and time.monotonic()-cached[0]<300:
            _CACHE.move_to_end(key)
            return {**cached[1],"cached":True}
        radius=int(radius_km*1000)
        query=f'[out:json][timeout:20];(nwr["amenity"="hospital"](around:{radius},{point.latitude},{point.longitude});nwr["healthcare"="hospital"](around:{radius},{point.latitude},{point.longitude}););out center;'
        coverage_radius=radius_km
        provider="overpass"
        try:
            async with _GATE:
                async with httpx.AsyncClient(timeout=settings.HOSPITAL_SEARCH_TIMEOUT_SECONDS) as client:
                    try:
                        response=await client.post(settings.OVERPASS_URL,data={"data":query},
                              headers={"User-Agent":"MaaHifazat/2.1 (hospital discovery)"})
                        response.raise_for_status()
                        payload=response.json()
                        if payload.get("remark") or not isinstance(payload.get("elements"),list):
                            raise ValueError("Incomplete provider response")
                    except (httpx.HTTPError,ValueError):
                        payload,coverage_radius=await bounded_map_fallback(client,point,radius_km)
                        provider="osm_bounded_map"
            if payload.get("remark") or not isinstance(payload.get("elements"),list):
                raise ValueError("Incomplete provider response")
            facilities=[]
            seen=set()
            for element in payload["elements"][:1000]:
                try:
                    kind=element["type"]
                    identity=f"osm-{kind}-{int(element['id'])}"
                    tags=element.get("tags") or {}
                    center=element if kind=="node" else element.get("center",{})
                    lat,lon=float(center["lat"]),float(center["lon"])
                    if not math.isfinite(lat+lon) or not -90<=lat<=90 or not -180<=lon<=180: continue
                    if identity in seen: continue
                    seen.add(identity)
                    km=haversine_km((point.latitude,point.longitude),(lat,lon))
                    if km>coverage_radius: continue
                    phone=(tags.get("phone") or tags.get("contact:phone") or "")[:100] or None
                    facilities.append({"facility_id":identity,"name":(tags.get("name:en") or tags.get("name") or "Unnamed mapped hospital")[:200],
                         "latitude":lat,"longitude":lon,"phone":phone,"type":"hospital","source":"OpenStreetMap",
                         "source_url":f"https://www.openstreetmap.org/{kind}/{element['id']}",
                         "reported_services":reported_services(tags),"has_maternity":False,"has_emergency":False,"has_nicu":False,
                         "capabilities_verified":False,"availability_verified":False,"availability":"unknown",
                         "verified_at":None,"simulated":False,"distance_km":round(km,3),"distance_m":round(km*1000),
                         "distance_kind":"straight_line","travel_time_minutes":None,"requires_availability_confirmation":True,
                         "directions_url":"https://www.google.com/maps/dir/?"+urlencode({"api":1,"origin":f"{point.latitude},{point.longitude}","destination":f"{lat},{lon}","travelmode":"driving"})})
                except (KeyError,TypeError,ValueError):
                    continue
            result={**empty,"facilities":sorted(facilities,key=lambda f:(f["distance_km"],f["facility_id"]))[:100],
                    "status":"ok" if facilities else "no_results","cached":False,
                    "provider":provider,"coverage_radius_km":coverage_radius,"coverage_limited":coverage_radius<radius_km,
                    "fetched_at":datetime.now(timezone.utc).isoformat(),
                    "reason":("Overpass unavailable: bounded map search covers only the nearest "+str(coverage_radius)+" km, not the full requested radius. " if provider=="osm_bounded_map" else "")+"Actual mapped hospitals. Service tags and bed availability require direct confirmation."}
            _CACHE[key]=(time.monotonic(),result)
            while len(_CACHE)>128: _CACHE.popitem(last=False)
            return result
        except (httpx.HTTPError,ValueError,KeyError,TypeError):
            return {**empty,"status":"provider_unavailable","reason":"Hospital search is unavailable. Retry or use a verified local directory; emergency care must not wait."}
