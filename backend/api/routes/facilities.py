"""Authenticated facility capability matching with explicit location consent."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from backend.config import settings
from backend.api.auth import get_current_user
from backend.api.access import accessible_patient
from backend.api.deps import get_db
from backend.schemas.care import PatientLocation
from backend.services.referral_planner import plan_referral

router = APIRouter(prefix="/facilities", tags=["facilities"])
class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patient_id: str
    location: PatientLocation
    urgency: Literal["routine", "urgent", "emergency"] = "routine"
    newborn_care: bool = False
    demo: bool = False

@router.post("/search")
async def search(request: SearchRequest, db=Depends(get_db), user=Depends(get_current_user)):
    await accessible_patient(db, user, request.patient_id)
    if request.demo and not settings.DEMO_MODE:
        raise HTTPException(422, "Demo mode disabled")
    return await plan_referral(request.location.model_dump(mode="json"), request.urgency,
           {"fetal_status": "suspect"} if request.newborn_care else None, request.demo)

class NearbyRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    location:PatientLocation
    radius_km:float=Field(25,ge=1,le=100)

@router.post("/nearby")
async def nearby(request:NearbyRequest,user=Depends(get_current_user)):
    from backend.services.hospital_search import discover_hospitals
    return await discover_hospitals(request.location.model_dump(mode="json"),request.radius_km)

@router.get("/integrations")
async def integrations(user=Depends(get_current_user)):
    return {"hospital_search":{"provider":"OpenStreetMap Overpass","available_without_key":True},
      "road_routing":{"provider":"openrouteservice","configured":bool(settings.OPENROUTESERVICE_API_KEY)},
      "llm":{"provider":"Groq","configured":bool(settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("your_")),
             "enabled":settings.ENABLE_LLM,"model":settings.GROQ_MODEL},
      "verified_directory_configured":bool(settings.FACILITY_DIRECTORY_PATH),
      "messaging":{"configured":False,"status":"provider required"}}
