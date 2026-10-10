"""Optional road routing. Only coordinates leave the app, after explicit consent."""
import math
import httpx
from backend.config import settings
from backend.integrations.facility_locator import haversine_km

class RoutingClient:
    async def get_travel_time(self, origin, destination, mode="driving", consent=False, demo=False):
        fallback = {"status": "estimate_only", "simulated": demo, "distance_km": round(haversine_km(origin, destination), 2),
                    "distance_kind": "straight_line", "travel_time_minutes": None,
                    "route_summary": "Straight-line distance; road distance and ETA unavailable", "mode": mode, "waypoints": []}
        if not settings.OPENROUTESERVICE_API_KEY or not consent or demo:
            return fallback
        try:
            async with httpx.AsyncClient(timeout=settings.ROUTING_TIMEOUT_SECONDS) as client:
                response = await client.post("https://api.openrouteservice.org/v2/directions/driving-car/geojson",
                    headers={"Authorization": settings.OPENROUTESERVICE_API_KEY},
                    json={"coordinates": [[origin[1], origin[0]], [destination[1], destination[0]]]})
                response.raise_for_status()
                feature = response.json()["features"][0]
                summary = feature["properties"]["summary"]
                meters, seconds = float(summary["distance"]), float(summary["duration"])
                points = feature["geometry"]["coordinates"]
                if not all(math.isfinite(v) and v >= 0 for v in (meters, seconds)):
                    raise ValueError("Invalid route summary")
                return {"status": "routed", "simulated": False, "distance_km": round(meters/1000, 2),
                        "distance_kind": "road", "travel_time_minutes": round(seconds/60, 1),
                        "route_summary": "openrouteservice driving estimate; traffic and access may change",
                        "mode": mode, "waypoints": points}
        except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError):
            return {**fallback, "status": "provider_failed", "route_summary": "Road provider failed; straight-line distance only"}

    async def get_route(self, origin, destination, **kwargs):
        return await self.get_travel_time(origin, destination, **kwargs)
