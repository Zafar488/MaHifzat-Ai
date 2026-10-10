"""Seed synthetic demo identities, patients, cases, and follow-up tasks."""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select
from backend.config import settings
from backend.db.engine import init_db, AsyncSessionLocal, engine
from backend.db.models import User, Patient, PatientAccess, CaseRecord, FollowupTask
from backend.api.auth import _hash_password

DEMO_PASSWORD = "MaaHifazat-Demo-2026!"
STANDARD_PASSWORD = "clinician"

async def seed():
    await init_db()
    async with AsyncSessionLocal() as db:
        # 1. Seed Default Accounts
        users_to_seed = [
            ("admin", "admin", "System Admin", STANDARD_PASSWORD),
            ("clinician", "clinician", "Dr. Aisha Ahmed", STANDARD_PASSWORD),
            ("lhw", "lhw", "Zainab Bibi (LHW)", STANDARD_PASSWORD),
            ("patient", "patient", "Fatima Bibi", STANDARD_PASSWORD),
            ("demo-admin", "admin", "Demo Administrator", DEMO_PASSWORD),
            ("demo-clinician", "clinician", "Demo Clinician", DEMO_PASSWORD),
            ("demo-lhw", "lhw", "Demo Health Worker", DEMO_PASSWORD),
        ]

        for username, role, full_name, pwd in users_to_seed:
            user_obj = await db.scalar(select(User).where(User.username == username))
            if not user_obj:
                user_obj = User(
                    id="usr-" + username,
                    username=username,
                    full_name=full_name,
                    role=role,
                    hashed_password=_hash_password(pwd),
                )
                db.add(user_obj)
        await db.commit()

        # 2. Seed Sample Patient Profiles
        sample_patients = [
            {
                "id": "pat-demo-01",
                "name": "Fatima Bibi",
                "age": 28,
                "phone": "+923001234567",
                "location": "Peshawar Rural Clinic",
                "gestational_age_weeks": 32.0,
                "parity": 2,
            },
            {
                "id": "pat-demo-02",
                "name": "Zainab Khan",
                "age": 22,
                "phone": "+923009876543",
                "location": "Swat Rural Health Center",
                "gestational_age_weeks": 24.5,
                "parity": 1,
            },
        ]

        for p_data in sample_patients:
            pat = await db.scalar(select(Patient).where(Patient.id == p_data["id"]))
            if not pat:
                pat = Patient(**p_data)
                db.add(pat)
                # Assign access to staff users
                for u_id in ["usr-admin", "usr-clinician", "usr-lhw", "usr-demo-admin", "usr-demo-clinician", "usr-demo-lhw"]:
                    db.add(PatientAccess(patient_id=p_data["id"], user_id=u_id, is_owner=(u_id == "usr-admin")))
        await db.commit()

        # 3. Seed Sample Case Records
        sample_cases = [
            {
                "id": "case-demo-01",
                "patient_id": "pat-demo-01",
                "created_by": "usr-clinician",
                "request_hash": "demo-hash-01",
                "status": "completed",
                "state_data": {"status": "completed", "urgency_level": "urgent", "triage_level": "URGENT"},
                "review_status": "approved",
                "review_notes": "Initial baseline assessment reviewed.",
            },
            {
                "id": "case-demo-02",
                "patient_id": "pat-demo-02",
                "created_by": "usr-clinician",
                "request_hash": "demo-hash-02",
                "status": "completed",
                "state_data": {"status": "completed", "urgency_level": "routine", "triage_level": "LOW_RISK"},
                "review_status": "pending",
            },
            {
                "id": "case-demo-03",
                "patient_id": "pat-demo-01",
                "created_by": "usr-lhw",
                "request_hash": "demo-hash-03",
                "status": "completed",
                "state_data": {"status": "completed", "urgency_level": "routine", "triage_level": "LOW_RISK"},
                "review_status": "approved",
            },
        ]

        for c_data in sample_cases:
            case_obj = await db.scalar(select(CaseRecord).where(CaseRecord.id == c_data["id"]))
            if not case_obj:
                db.add(CaseRecord(**c_data))
        await db.commit()

        # 4. Seed Sample Follow-up Tasks
        tasks_to_seed = [
            {
                "id": "task-demo-01",
                "patient_id": "pat-demo-01",
                "case_id": "case-demo-01",
                "action": "home_visit",
                "priority": "high",
                "due_date": (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"),
                "status": "pending",
                "details": {"reason": "Elevated BP follow-up home checkup required"},
            },
            {
                "id": "task-demo-02",
                "patient_id": "pat-demo-02",
                "case_id": "case-demo-02",
                "action": "schedule_contact",
                "priority": "medium",
                "due_date": (datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%d"),
                "status": "pending",
                "details": {"reason": "Routine ANC 24-week follow-up call"},
            },
            {
                "id": "task-demo-03",
                "patient_id": "pat-demo-01",
                "case_id": "case-demo-03",
                "action": "reminder",
                "priority": "low",
                "due_date": (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "status": "completed",
                "details": {"reason": "Iron supplement reminder sent"},
                "notes": "LHW confirmed patient received supplements.",
            },
        ]

        for task_data in tasks_to_seed:
            existing_task = await db.scalar(select(FollowupTask).where(FollowupTask.id == task_data["id"]))
            if not existing_task:
                db.add(FollowupTask(**task_data))

        await db.commit()

    await engine.dispose()
    print("Demo accounts (admin, clinician, lhw, patient), sample patients & follow-up tasks successfully seeded.")

if __name__ == "__main__":
    asyncio.run(seed())
