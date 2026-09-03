"""Facility locator client — OpenStreetMap/Overpass API stub."""
import httpx
from typing import Dict, Any, List, Optional
from backend.config import settings


class FacilityLocatorClient:
    """Client for finding nearby healthcare facilities."""

    def __init__(self, base_url: str = None, timeout: float = 3.0):
        self.base_url = base_url or settings.FACILITY_API_URL
        self.timeout = timeout

    async def find_nearby_facilities(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 20.0,
        facility_type: str = "hospital",
    ) -> List[Dict[str, Any]]:
        """Find healthcare facilities within radius. Returns ranked list."""
        # STUB: Return mock facilities near Peshawar, KP
        return [
            {
                "facility_id": "fac_001",
                "name": "Lady Reading Hospital",
                "type": "hospital",
                "latitude": 34.0151,
                "longitude": 71.5249,
                "distance_km": 2.5,
                "has_emergency": True,
                "has_maternity": True,
                "has_nicu": True,
                "current_load": "medium",
            },
            {
                "facility_id": "fac_002",
                "name": "Hayatabad Medical Complex",
                "type": "hospital",
                "latitude": 33.9928,
                "longitude": 71.4502,
                "distance_km": 8.3,
                "has_emergency": True,
                "has_maternity": True,
                "has_nicu": True,
                "current_load": "low",
            },
            {
                "facility_id": "fac_003",
                "name": "BHU Regi Model Town",
                "type": "health_center",
                "latitude": 34.0050,
                "longitude": 71.4800,
                "distance_km": 4.1,
                "has_emergency": False,
                "has_maternity": True,
                "has_nicu": False,
                "current_load": "low",
            },
        ]

    async def get_facility_details(self, facility_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed facility info."""
        facilities = await self.find_nearby_facilities(34.0, 71.5)
        for f in facilities:
            if f["facility_id"] == facility_id:
                return f
        return None
