"""
Pydantic Domain Models for APADA MITRA backend.
"""
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ScenarioType(str, Enum):
    NORMAL = "NORMAL"
    HEAVY_RAIN = "HEAVY_RAIN"
    EXTREME_RAIN = "EXTREME_RAIN"


class DataQualityStatus(str, Enum):
    OK = "OK"
    DEGRADED = "DEGRADED"
    MISSING = "MISSING"


class DataSourceState(str, Enum):
    LIVE_IOT_SENSOR = "LIVE_IOT_SENSOR"
    LIVE_EXTERNAL_API = "LIVE_EXTERNAL_API"
    LIVE = "LIVE"
    CACHED = "CACHED"
    OFFLINE_DEMO = "OFFLINE_DEMO"
    UNAVAILABLE = "UNAVAILABLE"


class DataQualityLevel(str, Enum):
    GOOD = "GOOD"
    WARNING = "WARNING"
    DEGRADED = "DEGRADED"
    CRITICAL_MISSING = "CRITICAL_MISSING"


class NormalizedEnvironmentObservation(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    observation_timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    current_rainfall_mm_hr: Optional[float] = Field(None, description="Hourly rainfall rate in mm/h")
    forecast_rainfall_24h_mm: Optional[float] = Field(None, description="24h forecast cumulative rainfall in mm")
    soil_saturation_pct: Optional[float] = Field(None, description="Soil saturation percentage (0-100%)")
    river_water_level_m: Optional[float] = Field(None, description="River stage depth in meters or factor multiplier")
    discharge_cumecs: Optional[float] = Field(None, description="River discharge rate in cumecs (m3/s) if available")
    rainfall_source: Optional[str] = Field(None, description="Source classification for rainfall (LIVE_IOT_SENSOR, LIVE_EXTERNAL_API, etc.)")
    soil_source: Optional[str] = Field(None, description="Source classification for soil moisture")
    water_level_source: Optional[str] = Field(None, description="Source classification for water level")
    source_name: str = Field(..., description="Name of external or local provider")
    source_type: str = Field(..., description="Source classification type")
    source_timestamp: str = Field(..., description="Raw provider timestamp")
    data_state: DataSourceState = Field(default=DataSourceState.OFFLINE_DEMO)
    quality_status: DataQualityLevel = Field(default=DataQualityLevel.GOOD)
    freshness_seconds: float = Field(default=0.0, description="Age of observation in seconds")
    missing_fields: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)


class SourceQualityReport(BaseModel):
    source_name: str
    source_type: str
    state: DataSourceState
    quality: DataQualityLevel
    timestamp: str
    age_minutes: float
    missing_fields: List[str]
    validation_warnings: List[str]


class OverallDataQualityResponse(BaseModel):
    overall_state: DataSourceState
    active_source: str
    data_mode: str
    total_sources: int
    sources: List[SourceQualityReport]
    last_validated: str



class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DecisionStatus(str, Enum):
    MONITOR = "MONITOR"
    PREPARE = "PREPARE"
    EVACUATION_READINESS = "EVACUATION_READINESS"


class InfrastructureExposure(BaseModel):
    schools: int = Field(..., ge=0, description="Number of exposed primary/secondary schools")
    health_facilities: int = Field(..., ge=0, description="Number of hospitals/clinics exposed")
    bridges_and_roads: int = Field(..., ge=0, description="Number of critical bridges/road segments exposed")
    critical_structures_count: int = Field(..., ge=0, description="Total count of critical assets")


class VillageBase(BaseModel):
    id: str = Field(..., description="Unique village identifier")
    name: str = Field(..., description="Village name")
    district: str = Field(..., description="District name")
    block: str = Field(..., description="Sub-district / Block name")
    latitude: float = Field(..., ge=-90, le=90, description="WGS84 Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="WGS84 Longitude")
    population: int = Field(..., ge=0, description="Total resident population")
    elevation: float = Field(..., description="Elevation above sea level in meters")
    slope: float = Field(..., ge=0, description="Average terrain slope angle in degrees")
    flow_accumulation: float = Field(..., ge=0, description="Hydrological flow accumulation log index")
    drainage_proximity_m: float = Field(..., ge=0, description="Distance to major river channel in meters")
    road_accessibility_score: float = Field(..., ge=0, le=100, description="Road access connectivity index")
    infrastructure: InfrastructureExposure


class MultiSourceFeatureData(BaseModel):
    current_rainfall: Optional[float] = Field(None, description="Hourly rainfall rate in mm/h")
    forecast_rainfall: Optional[float] = Field(None, description="24-hour forecast rainfall in mm")
    soil_saturation: Optional[float] = Field(None, description="Soil moisture saturation percentage (0-100%)")
    river_water_level: Optional[float] = Field(None, description="River depth factor multiplier (1.0 - 3.0)")
    slope: Optional[float] = Field(None, description="Terrain slope angle in degrees")
    flow_accumulation: Optional[float] = Field(None, description="Flow accumulation index")
    feature_statuses: Dict[str, DataQualityStatus] = Field(
        default_factory=dict, description="Per-feature data quality status"
    )
    timestamp: str = Field(..., description="ISO timestamp of feature data snapshot")


class FactorContribution(BaseModel):
    feature_key: str = Field(..., description="Feature identifier (e.g. current_rainfall)")
    feature_label: str = Field(..., description="Human readable label")
    raw_value: float = Field(..., description="Un-normalized raw value")
    unit: str = Field(..., description="Measurement unit")
    normalized_value: float = Field(..., ge=0.0, le=1.0, description="Normalized 0.0 - 1.0 value")
    weight: float = Field(..., ge=0.0, le=1.0, description="Configured weight")
    contribution_points: float = Field(..., ge=0.0, le=100.0, description="Risk points contributed (out of 100)")
    contribution_percent: float = Field(..., ge=0.0, le=100.0, description="Percentage of total risk score")


class ExposureMetrics(BaseModel):
    population_exposed: int = Field(..., ge=0, description="Estimated population directly exposed to flood risk")
    exposure_score: float = Field(..., ge=0.0, le=100.0, description="0-100 overall exposure index")
    infrastructure: InfrastructureExposure


class VillageRiskDetail(BaseModel):
    village_id: str
    village_name: str
    latitude: float
    longitude: float
    population: int
    elevation: float
    scenario: ScenarioType
    flash_flood_risk_score: float = Field(..., ge=0.0, le=100.0, description="Flash flood risk score (0-100)")
    risk_probability: float = Field(..., ge=0.0, le=1.0, description="Normalized probability (0.0-1.0)")
    confidence: float = Field(..., ge=0.0, le=100.0, description="Calculation confidence score (0-100%)")
    risk_level: RiskLevel
    decision_status: DecisionStatus
    exposure: ExposureMetrics
    factors: List[FactorContribution]
    missing_features: List[str] = Field(default_factory=list)
    last_updated: str
    state: Optional[str] = Field(None, description="Administrative state / territory")
    district: Optional[str] = Field(None, description="Administrative district")
    slope: Optional[float] = Field(None, description="Average terrain slope angle in degrees")
    landslide_risk_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Landslide risk score (0-100)")
    landslide_risk_level: Optional[RiskLevel] = Field(None, description="Categorical landslide risk level")


class LandslideRiskDetail(BaseModel):
    village_id: str
    village_name: str
    landslide_risk_score: float = Field(..., ge=0.0, le=100.0, description="Landslide risk score (0-100)")
    risk_level: RiskLevel
    confidence: float = Field(..., ge=0.0, le=100.0)
    contributing_factors: List[FactorContribution]
    historical_landslide_evidence: Optional[str] = Field(default=None, description="Qualitative historical landslide proximity evidence")
    historical_landslides_within_15km: Optional[int] = Field(default=None, description="Count of historical landslides within 15km")
    nearest_historical_landslide_km: Optional[float] = Field(default=None, description="Distance in km to nearest historical event")


class EvacuationPriority(BaseModel):
    village_id: str
    village_name: str
    evacuation_priority_score: float = Field(..., ge=0.0, le=100.0, description="Evacuation priority index (0-100)")
    priority_level: RiskLevel
    rank: int = Field(..., ge=1, description="Numerical urgency rank (1 = highest urgency)")
    flash_flood_risk_score: float
    landslide_risk_score: float
    population_exposed: int
    critical_infrastructure_count: int
    flood_contribution_pts: float
    landslide_contribution_pts: float
    population_contribution_pts: float
    infrastructure_contribution_pts: float
    factor_breakdown_summary: str
    primary_urgency_reason: str


class RoadStatus(str, Enum):
    OPEN = "OPEN"
    DEGRADED = "DEGRADED"
    BLOCKED = "BLOCKED"


class RoadSegment(BaseModel):
    id: str = Field(..., description="Unique road segment ID")
    name: str = Field(..., description="Road / Highway name")
    source_id: str = Field(..., description="Source node ID (village or shelter)")
    target_id: str = Field(..., description="Target node ID")
    distance_km: float = Field(..., ge=0.0)
    flood_exposure: float = Field(..., ge=0.0, le=100.0)
    landslide_exposure: float = Field(..., ge=0.0, le=100.0)
    status: RoadStatus
    coordinates: List[List[float]] = Field(default_factory=list, description="[[lat, lon], ...] polyline")


class Shelter(BaseModel):
    id: str = Field(..., description="Unique shelter ID")
    name: str = Field(..., description="Shelter name")
    latitude: float
    longitude: float
    total_capacity: Optional[int] = Field(None, ge=0)
    current_occupancy: Optional[int] = Field(None, ge=0)
    available_capacity: Optional[int] = Field(None, ge=0)
    elevation: float
    accessibility_score: float = Field(..., ge=0.0, le=100.0)
    hazard_exposure_score: float = Field(..., ge=0.0, le=100.0)


class EvacuationRouteResult(BaseModel):
    origin_village_id: str
    origin_village_name: str
    destination_shelter_id: str
    destination_shelter_name: str
    path_village_and_shelter_ids: List[str]
    road_segment_ids: List[str]
    total_distance_km: float
    estimated_travel_time_mins: int
    route_safety_score: float = Field(..., ge=0.0, le=100.0)
    path_coordinates: List[List[float]] = Field(default_factory=list)
    hazards_encountered: List[str] = Field(default_factory=list)
    rejected_dangerous_alternatives: List[str] = Field(default_factory=list)


class ShelterRecommendationResult(BaseModel):
    village_id: str
    village_name: str
    recommended_shelter: Shelter
    route: EvacuationRouteResult
    recommendation_reason: str


class WhatIfSimulationInput(BaseModel):
    current_rainfall_mm_hr: float = Field(..., ge=0.0, le=200.0, description="Rainfall intensity in mm/hr")
    forecast_rainfall_24h_mm: float = Field(..., ge=0.0, le=500.0, description="24h forecast rainfall in mm")
    soil_saturation_pct: float = Field(..., ge=0.0, le=100.0, description="Soil saturation percentage")
    river_level_m: float = Field(..., ge=0.0, le=15.0, description="River stream stage level in meters")
    selected_village_id: Optional[str] = Field(default="VIL-011", description="Village to evaluate evacuation routing")


class ComparisonMetric(BaseModel):
    name: str
    current_val: float
    simulated_val: float
    delta: float
    unit: str
    direction: str  # "INCREASE", "DECREASE", "NEUTRAL"


class SimulationComparisonSummary(BaseModel):
    avg_flood_risk: ComparisonMetric
    avg_landslide_risk: ComparisonMetric
    critical_villages_count: ComparisonMetric
    total_population_exposed: ComparisonMetric
    blocked_roads_count: ComparisonMetric
    shelter_shortfall_count: ComparisonMetric


class MultilingualAlert(BaseModel):
    english: str
    hindi: str
    garhwali: str
    kumaoni: str
    nepali: str


class EmergencyOperatorAlert(BaseModel):
    village_id: str
    village_name: str
    risk_level: RiskLevel
    risk_score: float
    primary_drivers: List[str]
    recommended_action: str
    shelter_name: str
    safe_route_summary: str
    roads_to_avoid: List[str]
    translations: MultilingualAlert


class WhatIfSimulationResponse(BaseModel):
    input: WhatIfSimulationInput
    preset_used: Optional[str] = None
    comparison_summary: SimulationComparisonSummary
    simulated_villages_flood: List[VillageRiskDetail]
    simulated_landslide_overview: List[LandslideRiskDetail]
    simulated_evacuation_priorities: List[EvacuationPriority]
    simulated_roads: List[RoadSegment]
    simulated_shelters: List[Shelter]
    simulated_route: Optional[EvacuationRouteResult] = None
    simulated_shelter_recommendation: Optional[ShelterRecommendationResult] = None
    shelter_shortfall_count: int = 0
    shelter_shortfall_warning: Optional[str] = None
    operator_alert: Optional[EmergencyOperatorAlert] = None


class IncidentActionEnum(str, Enum):
    ACKNOWLEDGE = "ACKNOWLEDGE"
    ESCALATE = "ESCALATE"
    MARK_EVACUATION_ACTIVE = "MARK_EVACUATION_ACTIVE"
    PREPARE_ALERT = "PREPARE_ALERT"


class IncidentStatusEnum(str, Enum):
    PENDING = "PENDING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ESCALATED = "ESCALATED"
    EVACUATION_ACTIVE = "EVACUATION_ACTIVE"
    ALERT_PREPARED = "ALERT_PREPARED"


class OperationalIncident(BaseModel):
    incident_id: str
    village_id: str
    village_name: str
    created_time: str
    hazard: str = Field(default="MULTI_HAZARD")
    flash_flood_risk: float
    landslide_risk: float
    confidence: float
    exposed_population: int
    evacuation_priority_score: float
    evacuation_rank: int
    recommended_route: str
    recommended_shelter: str
    blocked_unsafe_roads: List[str]
    recommended_action: str = Field(..., description="Recommended operator action")
    disclaimer: str = Field(
        default="FINAL EVACUATION / PUBLIC WARNING DECISION REMAINS WITH AUTHORIZED DISASTER MANAGEMENT AUTHORITIES.",
        description="Legal and operational decision-support disclaimer"
    )
    alert_status: IncidentStatusEnum = Field(default=IncidentStatusEnum.PENDING)
    last_updated: str


class IncidentActionRequest(BaseModel):
    incident_id: str
    action: IncidentActionEnum
    notes: Optional[str] = None


class AuditTrailEntry(BaseModel):
    timestamp: str
    event: str
    village_name: str
    risk_state: str
    operator_action: str



