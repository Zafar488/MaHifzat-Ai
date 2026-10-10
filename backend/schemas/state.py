"""LangGraph AgentState definition — shared state for all agent nodes."""
from typing import TypedDict, Optional, Any
from typing_extensions import Annotated
import operator


class AgentState(TypedDict, total=False):
    # Case identification
    patient_id: str
    case_id: str
    language: str  # en, ur, ps, sk (Saraiki)
    channel: str   # app, web, voice, sms, offline

    # Patient data
    vitals: dict           # BP, HR, temp, etc.
    symptoms: list         # Structured symptom list
    location: Optional[dict]
    followup: dict
    provenance: str
    allow_llm_processing: bool
    demographics: dict     # Age, gestational_age, parity, etc.
    encounter: dict
    patient_context: dict  # Local report identity; never sent to the language provider.
    ctg_data: Optional[dict]  # CTG features if available
    profile: Optional[dict]       # Structured intake profile (patient_intake)
    missing_fields: list         # Required vitals still missing (patient_intake)
    followup_questions: list     # LLM/template follow-up questions (patient_intake)
    llm_generated: bool          # True if intake follow-ups were LLM-generated

    # Flow control
    intake_complete: bool
    emergency: bool
    current_step: str

    # Agent outputs (each agent writes to its namespace)
    clinical_risk_result: Optional[dict]
    fetal_result: Optional[dict]
    anc_result: Optional[dict]
    referral_result: Optional[dict]
    communication_result: Optional[dict]
    clinician_result: Optional[dict]
    data_quality_result: Optional[dict]
    reporting_result: Optional[dict]
    research_results: Optional[dict]

    # Cross-cutting concerns
    audit_trail: Annotated[list, operator.add]  # Append-only log
    errors: Annotated[list, operator.add]       # Error accumulator
    messages: Annotated[list, operator.add]     # Messages to send
