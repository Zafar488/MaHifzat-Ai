"""Analytics routes — dashboard summary stats and model health checks."""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.api.deps import get_db, get_model_registry
from backend.db.repositories import PatientRepo, ClinicalRepo, ReferralRepo
from backend.services.inference import ModelRegistry
from backend.schemas.auth import TokenPayload

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/dashboard")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    Return summary statistics for the operational dashboard.

    Includes:
        - total_patients
        - risk_distribution (high / medium / low counts from clinical records)
        - referral_stats (total, by status)
        - recent_cases count (last 10 records)
    """
    try:
        patient_repo = PatientRepo(db)
        clinical_repo = ClinicalRepo(db)
        referral_repo = ReferralRepo(db)

        patients = await patient_repo.list_all(limit=10_000, offset=0)
        total_patients = len(patients)

        # Build recent_cases from latest few patients (proxy metric)
        recent_cases = min(total_patients, 10)

        # Risk distribution — aggregate from clinical records of all patients
        risk_distribution: Dict[str, int] = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
        for patient in patients[:200]:  # cap at 200 to avoid N+1 query slowdown in MVP
            records = await clinical_repo.get_by_patient(patient.id)
            for rec in records:
                level = getattr(rec, "risk_level", None) or "unknown"
                bucket = level.lower() if level.lower() in risk_distribution else "unknown"
                risk_distribution[bucket] += 1

        # Referral stats — retrieve recent batch
        referral_stats: Dict[str, Any] = {"total": 0, "by_status": {}}
        try:
            from sqlalchemy import select, func
            from backend.db.models import Referral
            result = await db.execute(select(Referral.status, func.count(Referral.id)).group_by(Referral.status))
            rows = result.all()
            referral_stats["by_status"] = {row[0]: row[1] for row in rows}
            referral_stats["total"] = sum(referral_stats["by_status"].values())
        except Exception:
            pass  # Gracefully degrade if table is empty

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute dashboard stats: {str(exc)}",
        )

    return {
        "total_patients": total_patients,
        "risk_distribution": risk_distribution,
        "referral_stats": referral_stats,
        "recent_cases": recent_cases,
    }


@router.get("/models/health")
async def get_model_health(
    registry: ModelRegistry = Depends(get_model_registry),
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    Return model health check — shows which ML models are loaded.
    """
    try:
        health = registry.health_check()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model health check failed: {str(exc)}",
        )
    return {
        "models": health,
        "all_loaded": all(health.values()),
        "loaded_count": sum(1 for v in health.values() if v),
        "total_count": len(health),
    }
