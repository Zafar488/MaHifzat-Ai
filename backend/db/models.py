"""SQLAlchemy ORM models for all 7 data stores."""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
import uuid
from .engine import Base

def gen_uuid():
    return str(uuid.uuid4())

class Patient(Base):
    __tablename__ = "patients"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(String, default="female")
    phone = Column(String)
    location = Column(String)
    gestational_age_weeks = Column(Float)
    parity = Column(Integer)
    language = Column(String, default="ur")
    channel = Column(String, default="app")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    # Relationships
    clinical_records = relationship("ClinicalRecord", back_populates="patient")
    referrals = relationship("Referral", back_populates="patient")

class ClinicalRecord(Base):
    __tablename__ = "clinical_records"
    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    case_id = Column(String, index=True)
    vitals = Column(JSON)  # Full vitals dict
    symptoms = Column(JSON)  # Symptom list
    maternal_risk_level = Column(String)
    fetal_status = Column(String)
    complication_risk = Column(String)
    triage_level = Column(String)
    who_red_flags = Column(JSON)
    is_emergency = Column(Boolean, default=False)
    model_outputs = Column(JSON)  # All model predictions
    clinician_decision = Column(String)
    clinician_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    client_generated_id = Column(String)  # Offline sync
    created_offline_at = Column(DateTime)  # Offline sync
    # Relationships
    patient = relationship("Patient", back_populates="clinical_records")

class Referral(Base):
    __tablename__ = "referrals"
    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    case_id = Column(String, index=True)
    facility_name = Column(String)
    facility_type = Column(String)
    facility_lat = Column(Float)
    facility_lon = Column(Float)
    distance_km = Column(Float)
    travel_time_min = Column(Float)
    urgency_level = Column(String, default="routine")  # routine, urgent, emergency
    status = Column(String, default="pending")  # pending, accepted, in_transit, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    # Relationships
    patient = relationship("Patient", back_populates="referrals")

class AgentStateRecord(Base):
    __tablename__ = "agent_states"
    id = Column(String, primary_key=True, default=gen_uuid)
    case_id = Column(String, index=True, nullable=False)
    thread_id = Column(String, index=True)
    state_data = Column(JSON)  # Full AgentState serialized
    current_step = Column(String)
    is_complete = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String, primary_key=True, default=gen_uuid)
    case_id = Column(String, index=True)
    agent_name = Column(String, nullable=False)
    action = Column(String, nullable=False)
    input_summary = Column(JSON)
    output_summary = Column(JSON)
    confidence = Column(Float)
    duration_ms = Column(Integer)
    error = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(String, primary_key=True, default=gen_uuid)
    model_name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    file_path = Column(String)
    metrics = Column(JSON)  # {macro_f1, auroc, etc.}
    features = Column(JSON)  # Feature list
    is_active = Column(Boolean, default=True)
    trained_at = Column(DateTime)
    registered_at = Column(DateTime, default=datetime.utcnow)

class FileRecord(Base):
    __tablename__ = "files"
    id = Column(String, primary_key=True, default=gen_uuid)
    case_id = Column(String, index=True)
    file_type = Column(String)  # audio, document, qr_code, report
    file_path = Column(String)
    mime_type = Column(String)
    size_bytes = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=gen_uuid)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="patient")
    is_active = Column(Boolean, nullable=False, default=True)
    token_version = Column(Integer, nullable=False, default=0)
    preferences = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class PatientAccess(Base):
    __tablename__ = "patient_access"
    patient_id = Column(String, ForeignKey("patients.id"), primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    is_owner = Column(Boolean, nullable=False, default=False)


class CaseRecord(Base):
    __tablename__ = "cases"
    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    request_hash = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    state_data = Column(JSON, nullable=False, default=dict)
    review_status = Column(String, nullable=False, default="pending")
    reviewed_by = Column(String, ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    review_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    case_id = Column(String, ForeignKey("cases.id"), index=True)
    kind = Column(String, default="clinical")
    message = Column(Text, nullable=False)
    channel = Column(String, default="app")
    provider_status = Column(String, default="not_sent")
    message_id = Column(String)
    acknowledged_by = Column(String, ForeignKey("users.id"))
    acknowledged_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class FollowupTask(Base):
    __tablename__ = "followup_tasks"
    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False, unique=True)
    action = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    due_date = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    details = Column(JSON, nullable=False)
    notes = Column(Text)
    completed_by = Column(String, ForeignKey("users.id"))
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class LoginThrottle(Base):
    __tablename__ = "login_throttles"
    key = Column(String, primary_key=True)
    failures = Column(Integer, default=0, nullable=False)
    window_start = Column(DateTime, default=datetime.utcnow, nullable=False)
