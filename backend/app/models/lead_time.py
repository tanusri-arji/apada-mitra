"""
Pydantic Models for Operational Lead-Time & Evacuation Window Engine.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class LeadTimeDecisionStatus(str, Enum):
    SAFE = "SAFE"
    TIGHT = "TIGHT"
    INSUFFICIENT = "INSUFFICIENT"
    UNKNOWN = "UNKNOWN"


class LeadTimeDataState(str, Enum):
    REAL_LIVE_INPUT = "REAL_LIVE_INPUT"
    ESTIMATED_FROM_LIVE_DATA = "ESTIMATED_FROM_LIVE_DATA"
    CACHED = "CACHED"
    OFFLINE_DEMO = "OFFLINE_DEMO"
    UNKNOWN = "UNKNOWN"


class VillageLeadTimeDetail(BaseModel):
    village_id: str
    village_name: str
    calculated_at: str = Field(..., description="ISO 8601 UTC timestamp of calculation")
    current_risk_score: float = Field(..., ge=0.0, le=100.0, description="Active multi-hazard flash flood risk score")
    current_risk_level: str = Field(..., description="Active risk level classification (LOW, MODERATE, HIGH, CRITICAL)")
    hazard_escalation_estimate_minutes: Optional[float] = Field(
        default=None,
        description="Estimated minutes until hazard reaches or exceeds the critical action threshold"
    )
    evacuation_time_minutes: float = Field(
        ...,
        ge=0.0,
        description="Estimated road travel time to the safest capacity-available shelter (minutes)"
    )
    preparation_time_minutes: float = Field(
        ...,
        ge=0.0,
        description="Estimated community mobilization and preparation time (minutes)"
    )
    total_required_time_minutes: float = Field(
        ...,
        ge=0.0,
        description="Total evacuation duration required (preparation + travel time in minutes)"
    )
    available_lead_time_minutes: Optional[float] = Field(
        default=None,
        description="Actionable operational time window before critical threshold arrival (minutes)"
    )
    safety_margin_minutes: Optional[float] = Field(
        default=None,
        description="Available lead time minus total required evacuation time (minutes)"
    )
    decision_status: LeadTimeDecisionStatus = Field(
        ...,
        description="Operational evacuation decision status (SAFE, TIGHT, INSUFFICIENT, UNKNOWN)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="System confidence percentage in this lead-time assessment"
    )
    calculation_method: str = Field(
        ...,
        description="Explicit description of the calculation algorithm and forecasting model applied"
    )
    data_state: LeadTimeDataState = Field(
        ...,
        description="Data provenance classification for input signals"
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Explicit list of operational parameters, disclaimers, and routing assumptions"
    )
