"""Transparent ANC scheduling and outreach rules, independent of proxy ML."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from backend.config import settings
from backend.schemas.care import FollowupContext

CONTACT_WEEKS = [12, 20, 26, 30, 34, 36, 38, 40]
RULE_VERSION = "anc-outreach-v1"
def local_today():
    return datetime.now(ZoneInfo(settings.FOLLOWUP_TIMEZONE)).date()

def plan_followup(context, vitals=None, urgency="routine", today=None):
    ctx = FollowupContext.model_validate(context or {})
    today = today or local_today()
    weeks = ctx.gestational_age_weeks
    if weeks is None:
        weeks = (vitals or {}).get("gestational_age_weeks")
    if weeks is not None and any(w > weeks for w in ctx.completed_contact_weeks):
        raise ValueError("Future completed ANC milestone")
    remaining = [w for w in CONTACT_WEEKS if w not in ctx.completed_contact_weeks]
    next_week = next(iter(remaining), None)
    due = ctx.next_appointment_date
    basis = "clinician_appointment" if due else "suggested_WHO_contact"
    if due is None and weeks is not None and next_week is not None:
        due = today + timedelta(days=max(0, int(round((next_week - weeks)*7))))
    overdue = max(0, (today - due).days) if due else 0
    missing_due = bool(weeks is not None and next_week is not None and next_week < weeks and ctx.next_appointment_date is None)
    reasons = []
    if urgency != "routine":
        reasons.append("Current maternal/fetal concern requires clinical assessment")
    if overdue or missing_due:
        reasons.append("Appointment or ANC contact is overdue")
    if ctx.missed_visits:
        reasons.append(f"{ctx.missed_visits} reported missed visit(s)")
    if ctx.transport_barrier:
        reasons.append("Transport barrier reported")
    if ctx.phone_access is False:
        reasons.append("No phone access reported")
    if urgency == "emergency":
        priority, action = "immediate", "emergency_assessment"
    elif urgency == "urgent":
        priority, action = "high", "call"
    elif ctx.missed_visits >= 2 or ctx.phone_access is False or (ctx.transport_barrier and (overdue or missing_due or ctx.missed_visits)):
        priority, action = "high", "home_visit"
    elif overdue or missing_due or ctx.missed_visits:
        priority, action = "medium", "call"
    elif due is None:
        priority, action = "needs_schedule", "schedule_contact"
    else:
        priority, action = "routine", "reminder"
    task_due = today if action != "reminder" else max(today, due - timedelta(days=1))
    appointment_weeks = round(weeks + (due - today).days / 7, 2) if weeks is not None and due else None
    return {"next_appointment_gestational_age_weeks": appointment_weeks, "status": "rule_based", "priority": priority, "recommended_action": action,
            "risk_factors": reasons, "missed_risk_score": None, "model_available": False,
            "next_contact_week": next_week, "next_appointment_date": due.isoformat() if due else None,
            "next_reminder_date": task_due.isoformat(), "task_due_date": task_due.isoformat(),
            "overdue_days": overdue, "schedule_basis": basis, "rule_version": RULE_VERSION,
            "contact_schedule_weeks": CONTACT_WEEKS, "completed_contact_weeks": ctx.completed_contact_weeks,
            "reason": "Clinician should individualize this suggested schedule. Outreach priority is an operational rule, not a predicted probability."}
