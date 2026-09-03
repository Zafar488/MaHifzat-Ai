"""Repository classes for CRUD operations on all 7 stores."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from .models import Patient, ClinicalRecord, Referral, AgentStateRecord, AuditLog, ModelVersion, FileRecord
import uuid

class PatientRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, data: Dict[str, Any]) -> Patient:
        patient = Patient(id=str(uuid.uuid4()), **data)
        self.session.add(patient)
        await self.session.flush()
        return patient
    
    async def get_by_id(self, patient_id: str) -> Optional[Patient]:
        result = await self.session.execute(select(Patient).where(Patient.id == patient_id))
        return result.scalar_one_or_none()
    
    async def update(self, patient_id: str, data: Dict[str, Any]) -> Optional[Patient]:
        await self.session.execute(update(Patient).where(Patient.id == patient_id).values(**data))
        return await self.get_by_id(patient_id)
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Patient]:
        result = await self.session.execute(select(Patient).order_by(desc(Patient.created_at)).limit(limit).offset(offset))
        return list(result.scalars().all())

class ClinicalRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, data: Dict[str, Any]) -> ClinicalRecord:
        record = ClinicalRecord(id=str(uuid.uuid4()), **data)
        self.session.add(record)
        await self.session.flush()
        return record
    
    async def get_by_case_id(self, case_id: str) -> Optional[ClinicalRecord]:
        result = await self.session.execute(select(ClinicalRecord).where(ClinicalRecord.case_id == case_id))
        return result.scalar_one_or_none()
    
    async def get_by_patient(self, patient_id: str) -> List[ClinicalRecord]:
        result = await self.session.execute(select(ClinicalRecord).where(ClinicalRecord.patient_id == patient_id).order_by(desc(ClinicalRecord.created_at)))
        return list(result.scalars().all())

class ReferralRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, data: Dict[str, Any]) -> Referral:
        referral = Referral(id=str(uuid.uuid4()), **data)
        self.session.add(referral)
        await self.session.flush()
        return referral
    
    async def get_by_id(self, referral_id: str) -> Optional[Referral]:
        result = await self.session.execute(select(Referral).where(Referral.id == referral_id))
        return result.scalar_one_or_none()
    
    async def update_status(self, referral_id: str, status: str) -> None:
        await self.session.execute(update(Referral).where(Referral.id == referral_id).values(status=status))

class AuditRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log(self, agent_name: str, action: str, case_id: str = None, **kwargs) -> AuditLog:
        entry = AuditLog(id=str(uuid.uuid4()), agent_name=agent_name, action=action, case_id=case_id, **kwargs)
        self.session.add(entry)
        await self.session.flush()
        return entry
    
    async def get_by_case(self, case_id: str) -> List[AuditLog]:
        result = await self.session.execute(select(AuditLog).where(AuditLog.case_id == case_id).order_by(AuditLog.timestamp))
        return list(result.scalars().all())
    
    async def get_recent(self, limit: int = 50) -> List[AuditLog]:
        result = await self.session.execute(select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit))
        return list(result.scalars().all())

class StateRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save_state(self, case_id: str, thread_id: str, state_data: dict, current_step: str) -> AgentStateRecord:
        record = AgentStateRecord(id=str(uuid.uuid4()), case_id=case_id, thread_id=thread_id, state_data=state_data, current_step=current_step)
        self.session.add(record)
        await self.session.flush()
        return record
    
    async def get_latest(self, case_id: str) -> Optional[AgentStateRecord]:
        result = await self.session.execute(select(AgentStateRecord).where(AgentStateRecord.case_id == case_id).order_by(desc(AgentStateRecord.updated_at)))
        return result.scalars().first()

class ModelRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def register(self, data: Dict[str, Any]) -> ModelVersion:
        record = ModelVersion(id=str(uuid.uuid4()), **data)
        self.session.add(record)
        await self.session.flush()
        return record
    
    async def get_active(self, model_name: str) -> Optional[ModelVersion]:
        result = await self.session.execute(select(ModelVersion).where(ModelVersion.model_name == model_name, ModelVersion.is_active == True))
        return result.scalars().first()

class FileRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, data: Dict[str, Any]) -> FileRecord:
        record = FileRecord(id=str(uuid.uuid4()), **data)
        self.session.add(record)
        await self.session.flush()
        return record
    
    async def get_by_case(self, case_id: str) -> List[FileRecord]:
        result = await self.session.execute(select(FileRecord).where(FileRecord.case_id == case_id))
        return list(result.scalars().all())
