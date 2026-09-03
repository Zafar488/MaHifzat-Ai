"""Risk assessment result schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


class ClinicalRiskResult(BaseModel):
    maternal_risk_level: RiskLevel
    maternal_confidence: float = Field(ge=0, le=1)
    maternal_probabilities: Dict[str, float] = {}
    complication_risk_level: Optional[RiskLevel] = None
    complication_probabilities: Optional[Dict[str, float]] = None
    who_red_flags_triggered: List[str] = []
    risk_summary_text: str = ""
    is_emergency: bool = False
    triage_level: str = "GREEN"
    clinical_rationale: List[str] = []
    recommended_actions: List[str] = []


class FetalMonitoringResult(BaseModel):
    fetal_status: str  # normal, suspicious, pathological
    fetal_confidence: float = Field(ge=0, le=1)
    fetal_probabilities: Dict[str, float] = {}
    preterm_risk: Optional[str] = None
    preterm_probabilities: Optional[Dict[str, float]] = None
    escalate: bool = False


class ANCFollowUpResult(BaseModel):
    missed_visit_risk: float = Field(ge=0, le=1)
    priority_score: float = Field(ge=0, le=1)
    recommended_action: str = ""  # sms, call, home_visit
    next_reminder_date: Optional[str] = None
    risk_factors: List[str] = []
