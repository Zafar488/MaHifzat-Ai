"""Verified directory or explicitly simulated facilities; no inferred capabilities."""
import json
import math
from datetime import datetime, timezone
from backend.config import settings
from backend.schemas.care import Facility

def haversine_km(origin, destination):
    lat1, lon1, lat2, lon2 = map(math.radians, (*origin, *destination))
    a = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 6371.0088 * 2 * math.asin(min(1, math.sqrt(a)))

class FacilityLocatorClient:
    def __init__(self, directory_path=None):
        self.directory_path = directory_path or settings.FACILITY_DIRECTORY_PATH
        self.status = "unavailable"

    def _directory(self, demo=False):
        if demo and settings.DEMO_MODE:
            path = settings.PROJECT_ROOT / "config" / "demo_facilities.json"
        else:
            path = self.directory_path
        if path is None:
            self.status = "unavailable"
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            rows = [Facility.model_validate(row) for row in raw["facilities"]]
            if len({r.facility_id for r in rows}) != len(rows):
                raise ValueError("Duplicate facility IDs")
            self.status = "simulated" if demo else "directory"
            return [r for r in rows if r.simulated == demo]
        except (OSError, ValueError, KeyError, TypeError):
            self.status = "invalid_directory"
            return []

    async def find_nearby_facilities(self, latitude, longitude, radius_km=100, facility_type="hospital", demo=False):
        now = datetime.now(timezone.utc)
        result = []
        for facility in self._directory(demo):
            verified = facility.verified_at is not None and 0 <= (now.date() - facility.verified_at).days <= settings.FACILITY_VERIFICATION_MAX_DAYS
            if not demo and not verified:
                continue
            row = facility.model_dump(mode="json")
            row["capabilities_verified"] = verified and not demo
            checked = facility.availability_checked_at
            if checked is not None:
                checked = checked.replace(tzinfo=timezone.utc) if checked.tzinfo is None else checked
            age_seconds = (now - checked).total_seconds() if checked else None
            live = age_seconds is not None and 0 <= age_seconds <= 86400 and not demo
            row["availability_verified"] = live
            if not live:
                row["availability"] = "unknown"
            row["distance_km"] = round(haversine_km((latitude, longitude), (facility.latitude, facility.longitude)), 2)
            row["distance_kind"] = "straight_line"
            if row["distance_km"] <= radius_km:
                result.append(row)
        return sorted(result, key=lambda r: (r["distance_km"], r["facility_id"]))

    async def get_facility_details(self, facility_id):
        return next((r.model_dump(mode="json") for r in self._directory() if r.facility_id == facility_id), None)
