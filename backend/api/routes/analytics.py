"""SQL counts. Risk distribution counts assessments, not patients."""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.auth import get_current_user
from backend.api.access import patient_scope
from backend.api.deps import get_db, get_model_registry
from backend.db.models import Patient, ClinicalRecord, Referral

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    scope = select(Patient.id).where(patient_scope(user))
    total = await db.scalar(select(func.count(Patient.id)).where(patient_scope(user)))
    risks = await db.execute(select(ClinicalRecord.maternal_risk_level, func.count()).where(ClinicalRecord.patient_id.in_(scope)).group_by(ClinicalRecord.maternal_risk_level))
    distribution = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
    for label, count in risks:
        normalized = (label or "").lower().strip()
        bucket = {"high": "high", "high risk": "high", "mid risk": "medium", "medium": "medium", "moderate": "medium", "low": "low", "low risk": "low", "emergency": "high"}.get(normalized, "unknown")
        distribution[bucket] += count
    referrals = await db.execute(select(Referral.status, func.count()).where(Referral.patient_id.in_(scope)).group_by(Referral.status))
    by_status = dict(referrals.all())
    assessments = sum(distribution.values())
    return {"total_patients": total, "total_assessments": assessments, "risk_count_unit": "assessments", "risk_distribution": distribution, "referral_stats": {"total": sum(by_status.values()), "by_status": by_status}, "recent_cases": min(assessments, 10)}


@router.get("/models/health")
async def model_health(registry=Depends(get_model_registry), user=Depends(get_current_user)):
    health = registry.health_check()
    return {"models": health, "all_loaded": all(health.values()), "supported_ready": all(health[name] for name in ("maternalguard", "fetalwatch")), "loaded_count": sum(health.values()), "total_count": len(health), "clinical_validation": "not established"}

@router.get("/models/evidence")
async def evidence(user=Depends(get_current_user), registry=Depends(get_model_registry)):
    import json
    from backend.config import settings
    from backend.services.inference import DISABLED
    supported = []
    for name in ("maternalguard", "fetalwatch"):
        try:
            manifest = json.loads((settings.ARTIFACTS_DIR / "serving" / name / "manifest.json").read_text())
            supported.append({"Model": name, "Available": registry.health_check()[name], "Dataset rows": manifest["rows"],
                 "Macro-F1": round(manifest["final_test_macro_f1"], 4), "Accuracy": round(manifest["test_report"]["accuracy"], 4),
                 "Dataset target": manifest["target"], "Split": manifest["split_strategy"],
                 "Version": registry._models.get(name, {}).get("model_version", "unavailable")})
        except (OSError, ValueError, KeyError):
            supported.append({"Model": name, "Available": False, "Version": "Unavailable"})
    return {"supported": supported, "disabled": [{"Model": name, "Reason": reason} for name, reason in DISABLED.items()]}

@router.get("/models/demo-ctg")
async def demo_ctg(user=Depends(get_current_user), registry=Depends(get_model_registry)):
    import json
    import pandas as pd
    from fastapi import HTTPException
    from backend.config import settings
    from backend.services.inference import CTG_FEATURES
    if not settings.DEMO_MODE:
        raise HTTPException(403, "Synthetic scenario requires demo mode")
    bundle = registry._models.get("fetalwatch")
    if bundle is None:
        raise HTTPException(503, "Fetal model unavailable")
    try:
        manifest = json.loads((settings.ARTIFACTS_DIR / "serving/fetalwatch/manifest.json").read_text())
        frame = pd.read_parquet(settings.DATA_DIR / manifest["dataset"])
        holdout = frame.iloc[manifest["test_indices"]]
        rows = holdout[holdout["NSP"] == 3][CTG_FEATURES]
        labels = bundle["pipeline"].predict(rows)
        matches = rows.loc[labels == "pathological"]
        if matches.empty:
            raise ValueError("No correctly classified pathological example")
        return {"features": matches.iloc[0].to_dict(), "source": "labelled UCI held-out example; demo only",
                "selection": "Correctly classified pathological demonstration; full scores are in Model evidence"}
    except (OSError, ValueError, KeyError):
        raise HTTPException(503, "Labelled demo data unavailable")
