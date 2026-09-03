"""Routing client — OpenRouteService API stub."""
import httpx
from typing import Dict, Any, Optional, Tuple
from backend.config import settings
import math


class RoutingClient:
    """Client for travel time and route estimation."""

    def __init__(self, base_url: str = None, api_key: str = None, timeout: float = 3.0):
        self.base_url = base_url or settings.ROUTING_API_URL
        self.api_key = api_key
        self.timeout = timeout

    async def get_travel_time(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        mode: str = "driving",
    ) -> Dict[str, Any]:
        """Estimate travel time between two points.

        Args:
            origin: (latitude, longitude)
            destination: (latitude, longitude)
            mode: driving, walking, ambulance
        """
        # STUB: Estimate based on straight-line distance
        distance_km = self._haversine(origin, destination)

        # Average speeds (km/h) by mode in KP road conditions
        speeds = {"driving": 30, "walking": 4, "ambulance": 45}
        speed = speeds.get(mode, 30)

        travel_time_min = (distance_km / speed) * 60

        return {
            "distance_km": round(distance_km, 1),
            "travel_time_minutes": round(travel_time_min, 0),
            "mode": mode,
            "route_summary": f"Via main road ({distance_km:.1f} km)",
            "traffic_condition": "normal",
        }

    async def get_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
    ) -> Dict[str, Any]:
        """Get full route with waypoints."""
        travel = await self.get_travel_time(origin, destination)
        return {
            **travel,
            "waypoints": [
                {"lat": origin[0], "lon": origin[1], "type": "start"},
                {"lat": destination[0], "lon": destination[1], "type": "end"},
            ],
        }

    @staticmethod
    def _haversine(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two lat/lon points in km."""
        R = 6371  # Earth radius in km
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return R * 2 * math.asin(math.sqrt(a))
