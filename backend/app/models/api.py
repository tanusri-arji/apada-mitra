"""
Pydantic API Request/Response schemas for APADA MITRA backend.
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from app.models.domain import ScenarioType, VillageRiskDetail, DataQualityStatus, RiskLevel


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    service: str = "APADA MITRA Disaster Intelligence Backend"
    data_mode: str = "DEMO MODE — SYNTHETIC LOCAL DATA"


class ReadinessResponse(BaseModel):
    status: str = "SYSTEM READY"
    ready: bool = True
    checks: Dict[str, bool] = Field(..., description="System component health checks")
    data_mode: str = "DEMO MODE — SYNTHETIC LOCAL DATA"
    version: str = "1.0.0"


class ScenarioStateResponse(BaseModel):
    scenario: ScenarioType
    description: str
    data_quality_status: DataQualityStatus
    active_villages_count: int
    last_updated: str


class ScenarioUpdateRequest(BaseModel):
    scenario: ScenarioType = Field(..., description="Target scenario: NORMAL, HEAVY_RAIN, EXTREME_RAIN")


class ImpactSummaryResponse(BaseModel):
    scenario: ScenarioType
    total_villages: int
    critical_villages_count: int
    high_villages_count: int
    moderate_villages_count: int
    low_villages_count: int
    total_population_exposed: int
    average_risk_score: float
    average_confidence: float
    data_quality_summary: str
    last_updated: str


class RiskOverviewResponse(BaseModel):
    scenario: ScenarioType
    impact_summary: ImpactSummaryResponse
    villages_risk: List[VillageRiskDetail]


class RouteCalculationRequest(BaseModel):
    origin_village_id: str = Field(..., description="Origin village ID (e.g. VIL-001)")
    destination_shelter_id: str = Field(..., description="Destination shelter ID (e.g. SH-01)")

