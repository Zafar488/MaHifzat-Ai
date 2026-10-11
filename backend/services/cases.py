"""Durable case reservation and consistent assessment persistence."""
import hashlib
import json
import uuid
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from backend.config import settings
from backend.db.models import CaseRecord, ClinicalRecord, AuditLog, Alert
from backend.schemas.assessment import AssessmentInput


def normalized_input(request):
    value = request.model_dump(mode="json")
    value.pop("case_id", None)
    # Workflow transport fields do not alter the clinical encounter.
    for field in ("language", "channel", "demographics"):
        value.pop(field, None)
    ctg_data = value.pop("ctg_data", None)
    if ctg_data is not None:
        if value["ctg_features"] is not None and value["ctg_features"] != ctg_data:
            raise HTTPException(422, "Conflicting CTG locations")
        value["ctg_features"] = ctg_data
    if value["provenance"] == "demo":
        if not settings.DEMO_MODE:
            raise HTTPException(422, "Demo assessments require explicit development DEMO_MODE")
    location = value.get("location")
    if location and location["source"] == "demo" and value["provenance"] != "demo":
        raise HTTPException(422, "Demo coordinates cannot be assigned to a real assessment")
    if value["ctg_features"] is not None:
        if value["ctg_source"] not in ("uci_measured", "demo"):
            raise HTTPException(422, "CTG provenance required; raw-signal extraction is not validated for UCI serving")
        if value["ctg_source"] == "demo" and value["provenance"] != "demo":
            raise HTTPException(422, "Demo CTG cannot be assigned to a real assessment")
    return value


async def reserve_case(db, request, user):
    value = normalized_input(request)
    digest = hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()
    case_id = request.case_id or str(uuid.uuid4())
    existing = await db.get(CaseRecord, case_id)
    if existing:
        if existing.patient_id != request.patient_id or existing.request_hash != digest:
            raise HTTPException(409, "Case identifier already used with different clinical inputs")
        return existing, False
    case = CaseRecord(id=case_id, patient_id=request.patient_id, created_by=user.sub, request_hash=digest, status="running", state_data={"input": value})
    try:
        async with db.begin_nested():
            db.add(case)
            await db.flush()
    except IntegrityError:
        raise HTTPException(409, "Case is being created; retry the same request")
    return case, True


async def persist_assessment(db, case, response, user):
    record = await db.scalar(select(ClinicalRecord).where(ClinicalRecord.case_id == case.id).limit(1))
    if record is None:
        record = ClinicalRecord(patient_id=case.patient_id, case_id=case.id)
        db.add(record)
    intake = case.state_data["input"]
    record.vitals = intake["vitals"]
    record.symptoms = intake["symptoms"]
    record.maternal_risk_level = (response.get("maternal_risk") or {}).get("risk_level", "unknown")
    record.fetal_status = (response.get("fetal_health") or {}).get("fetal_status", "not_assessed")
    record.triage_level = response["safety_triage"]["triage_level"]
    record.who_red_flags = response["safety_triage"]
    record.is_emergency = response["is_emergency"]
    record.model_outputs = response
    db.add(AuditLog(case_id=case.id, agent_name="assessment", action="assessment_saved", input_summary={"actor_id": user.sub}, output_summary={"status": response["status"], "rule_version": response["safety_triage"]["rule_version"]}))
    if response["is_emergency"]:
        existing = await db.scalar(select(Alert.id).where(Alert.case_id == case.id, Alert.kind == "danger_sign"))
        if not existing:
            db.add(Alert(case_id=case.id, patient_id=case.patient_id, kind="danger_sign", message="Danger signs detected. Seek immediate maternity assessment.", provider_status="not_sent"))
    await db.flush()


def assess(intake, case_id, registry, safety):
    triage = safety.check_who_red_flags(intake["vitals"], intake["symptoms"])
    maternal = registry.predict_maternal_risk(intake["vitals"])
    fetal = registry.predict_fetal_health(intake["ctg_features"]) if intake["ctg_features"] else None
    if intake["ctg_features"] and fetal is not None and fetal["status"] in ("unavailable", "insufficient_data", "error"):
        fetal_incomplete = True
    else:
        fetal_incomplete = False
    incomplete = bool(triage["missing_fields"]) or maternal["status"] in ("unavailable", "insufficient_data", "error") or fetal_incomplete
    from backend.services.referral_planner import effective_urgency
    from backend.services.followup import plan_followup
    urgency = effective_urgency(triage, maternal, fetal)
    anc = plan_followup(intake.get("followup"), intake["vitals"], urgency)
    carereach_ml = registry.predict_anc_followup_risk(intake["vitals"])
    if carereach_ml.get("model_available"):
        anc["carereach_ml"] = carereach_ml

    return {"case_id": case_id, "patient_id": intake["patient_id"],
            "status": "incomplete" if incomplete else "pending_review",
            "provenance": intake["provenance"], "maternal_risk": maternal, "fetal_health": fetal,
            "preterm_risk": registry.predict_preterm_risk(intake.get("ctg_features") or {}),
            "gestational_complication": registry.predict_gestational_complication(intake["vitals"]),
            "anc_followup": anc, "urgency_level": urgency, "fetal_concern": bool(fetal and fetal.get("fetal_status") in ("suspect", "pathological")),
            "safety_triage": triage, "is_emergency": urgency == "emergency"}
