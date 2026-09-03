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
