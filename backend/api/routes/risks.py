"""Quick risk assessment routes (inference + safety, without full workflow)."""
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.api.deps import get_db, get_model_registry, get_safety_service
from backend.db.repositories import ClinicalRepo
from backend.schemas.auth import TokenPayload
from backend.services.inference import ModelRegistry
from backend.services.safety import SafetyService

router = APIRouter(prefix="/risks", tags=["risks"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class RiskAssessmentRequest(BaseModel):
    patient_id: str
    case_id: Optional[str] = None
    vitals: Dict[str, Any] = Field(
        default_factory=dict,
        description="Vitals for MaternalGuard (Age, SystolicBP, DiastolicBP, BS, BodyTemp, HeartRate)",
    )
    ctg_features: Optional[Dict[str, float]] = Field(
        None,
        description="21 CTG features for FetalWatch + PretermGuard",
    )
    clinical_features: Optional[Dict[str, float]] = Field(
        None,
        description="Clinical features for GestationInsight",
    )
    anc_features: Optional[Dict[str, Any]] = Field(
        None,
        description="Patient features for CareReach ANC follow-up",
    )


class RiskAssessmentResponse(BaseModel):
    case_id: str
    maternal_risk: Optional[Dict[str, Any]] = None
    fetal_health: Optional[Dict[str, Any]] = None
    preterm_risk: Optional[Dict[str, Any]] = None
    gestational_complication: Optional[Dict[str, Any]] = None
    anc_followup: Optional[Dict[str, Any]] = None
    safety_triage: Optional[Dict[str, Any]] = None
    is_emergency: bool = False


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/assess", response_model=RiskAssessmentResponse)
async def assess_risk(
    request: RiskAssessmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
    registry: ModelRegistry = Depends(get_model_registry),
    safety: SafetyService = Depends(get_safety_service),
):
    """
    Quick risk assessment — calls inference models + safety rules directly
    without running the full agent workflow.
    """
    case_id = request.case_id or str(uuid.uuid4())
    response = RiskAssessmentResponse(case_id=case_id)

    # --- MaternalGuard (maternal risk) ---
    if request.vitals:
        response.maternal_risk = registry.predict_maternal_risk(request.vitals)

    # --- Safety triage (WHO red flags) ---
    if request.vitals:
        response.safety_triage = safety.check_who_red_flags(request.vitals)
        response.is_emergency = safety.is_emergency(request.vitals)

    # --- FetalWatch + PretermGuard (CTG-based) ---
    if request.ctg_features:
        response.fetal_health = registry.predict_fetal_health(request.ctg_features)
        response.preterm_risk = registry.predict_preterm_risk(request.ctg_features)

    # --- GestationInsight ---
    if request.clinical_features:
        response.gestational_complication = registry.predict_gestational_complication(
            request.clinical_features
        )

    # --- CareReach (ANC follow-up) ---
    if request.anc_features:
        response.anc_followup = registry.predict_anc_followup_risk(request.anc_features)

    # Persist to clinical_records
    clinical_repo = ClinicalRepo(db)
    await clinical_repo.create(
        {
            "patient_id": request.patient_id,
            "case_id": case_id,
            "vitals": request.vitals,
            "maternal_risk_level": (response.maternal_risk or {}).get("risk_level"),
            "fetal_status": (response.fetal_health or {}).get("fetal_status"),
            "complication_risk": (response.gestational_complication or {}).get("risk_level"),
            "triage_level": (response.safety_triage or {}).get("triage_level"),
            "who_red_flags": response.safety_triage,
            "is_emergency": response.is_emergency,
            "model_outputs": {
                "maternal_risk": response.maternal_risk,
                "fetal_health": response.fetal_health,
                "preterm_risk": response.preterm_risk,
                "gestational_complication": response.gestational_complication,
                "anc_followup": response.anc_followup,
            },
        }
    )

    return response


@router.get("/{case_id}")
async def get_risk_assessment(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Retrieve a previously stored risk assessment by case_id."""
    repo = ClinicalRepo(db)
    record = await repo.get_by_case_id(case_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk assessment not found")
    return {
        "case_id": record.case_id,
        "patient_id": record.patient_id,
        "maternal_risk_level": record.maternal_risk_level,
        "fetal_status": record.fetal_status,
        "complication_risk": record.complication_risk,
        "triage_level": record.triage_level,
        "who_red_flags": record.who_red_flags,
        "is_emergency": record.is_emergency,
        "model_outputs": record.model_outputs,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }
