"""
Feature 10: Real Shelter / Relief-Center Data & Suitability Models for APADA MITRA.
Defines schemas for shelter registry, verification states, dynamic hazard exposures,
capacity constraints, suitability evaluations, and rejection provenance.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ShelterDataState(str, Enum):
    REAL_OFFICIAL = "REAL_OFFICIAL"
    REAL_STATIC_GOVERNMENT = "REAL_STATIC_GOVERNMENT"
    CACHED_VERIFIED = "CACHED_VERIFIED"
    DERIVED_FROM_REAL_SOURCE = "DERIVED_FROM_REAL_SOURCE"
    UNVERIFIED = "UNVERIFIED"
    OFFLINE_DEMO = "OFFLINE_DEMO"
    UNAVAILABLE = "UNAVAILABLE"


class ShelterValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID_COORDINATES = "INVALID_COORDINATES"
    DUPLICATE_ID = "DUPLICATE_ID"
    MALFORMED = "MALFORMED"
    UNVERIFIED = "UNVERIFIED"


class ShelterHazardLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CapacityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    NEAR_CAPACITY = "NEAR_CAPACITY"
    FULL = "FULL"
    UNKNOWN = "UNKNOWN"


class ShelterType(str, Enum):
    SCHOOL_RELIEF_COMPLEX = "SCHOOL_RELIEF_COMPLEX"
    STADIUM_HALL = "STADIUM_HALL"
    ARMY_BASE_CAMP = "ARMY_BASE_CAMP"
    HIGH_PLATEAU_SHELTER = "HIGH_PLATEAU_SHELTER"
    VALLEY_BASE_CAMP = "VALLEY_BASE_CAMP"
    COMMUNITY_CENTER = "COMMUNITY_CENTER"


class ShelterRecord(BaseModel):
    """
    Standardized Shelter Record with full geometric and provenance attributes.
    Supports both `shelter_id` and `id` for backwards compatibility.
    """
    shelter_id: str = Field(..., description="Unique shelter identifier, e.g. SH-01")
    id: Optional[str] = Field(None, description="Backwards compatible identifier")
    name: str = Field(..., description="Designated shelter facility name (Configured shelter baseline)")
    shelter_name: Optional[str] = Field(None, description="Alias for name")
    latitude: float = Field(..., ge=8.0, le=36.0, description="WGS84 Latitude")
    longitude: float = Field(..., ge=72.0, le=97.0, description="WGS84 Longitude")
    village_or_area: str = Field(..., description="Nearby village or administrative area")
    district: str = Field("Chamoli", description="Administrative district")
    block: Optional[str] = Field(None, description="Administrative block / tehsil")
    elevation: float = Field(..., ge=0.0, description="Elevation above mean sea level in meters")
    total_capacity: Optional[int] = Field(None, description="Total bed/person capacity (None if unknown)")
    current_occupancy: Optional[int] = Field(None, description="Current occupied beds")
    available_capacity: Optional[int] = Field(None, description="Remaining available capacity")
    capacity_status: CapacityStatus = Field(CapacityStatus.AVAILABLE, description="Operational capacity classification")
    shelter_type: ShelterType = Field(ShelterType.COMMUNITY_CENTER, description="Facility structural category")
    facilities: List[str] = Field(default_factory=list, description="Available emergency facilities")
    accessibility_score: float = Field(75.0, ge=0.0, le=100.0, description="Road access connectivity index")
    
    # Derived Hazard Profile
    flood_hazard_score: float = Field(0.0, ge=0.0, le=100.0, description="Derived flood hazard exposure")
    landslide_hazard_score: float = Field(0.0, ge=0.0, le=100.0, description="Derived landslide hazard exposure")
    combined_hazard_score: float = Field(0.0, ge=0.0, le=100.0, description="Composite shelter hazard score")
    hazard_exposure_score: Optional[float] = Field(None, description="Backwards compatible hazard score")
    hazard_level: ShelterHazardLevel = Field(ShelterHazardLevel.LOW, description="Categorical hazard level")
    
    # Geometric & Proximity Attributes
    primary_nearby_village_id: Optional[str] = Field(None, description="ID of nearest monitored village")
    nearby_village_ids: List[str] = Field(default_factory=list, description="IDs of villages within search radius")
    straight_line_distance_km: Optional[float] = Field(None, description="Haversine straight-line distance in km")

    # Provenance and Data Integrity
    source: str = Field("Uttarakhand Disaster Management Plan / Fallback Registry", description="Data source reference (Source provenance not live-connected)")
    source_url: str = Field("https://usdma.uk.gov.in/", description="Source URL or reference portal")
    verified_at: Optional[str] = Field(None, description="ISO timestamp of verification")
    data_state: ShelterDataState = Field(ShelterDataState.OFFLINE_DEMO, description="Data provenance state")
    freshness: str = Field("STATIC_REGISTRY", description="Data freshness indicator")
    verification_status: ShelterValidationStatus = Field(ShelterValidationStatus.VALID, description="Schema validation result")

    def __init__(self, **data: Any):
        if "id" in data and "shelter_id" not in data:
            data["shelter_id"] = data["id"]
        elif "shelter_id" in data and "id" not in data:
            data["id"] = data["shelter_id"]
        if "name" in data and "shelter_name" not in data:
            data["shelter_name"] = data["name"]
        elif "shelter_name" in data and "name" not in data:
            data["name"] = data["shelter_name"]
        if "hazard_exposure_score" in data and "combined_hazard_score" not in data:
            data["combined_hazard_score"] = data["hazard_exposure_score"]
        elif "combined_hazard_score" in data and "hazard_exposure_score" not in data:
            data["hazard_exposure_score"] = data["combined_hazard_score"]
        super().__init__(**data)


class CandidateShelterEvaluation(BaseModel):
    """
    Suitability evaluation breakdown for a candidate shelter.
    """
    shelter_id: str
    shelter_name: str
    latitude: float
    longitude: float
    elevation: float
    is_accessible: bool
    rejection_reason: Optional[str] = None
    straight_line_distance_km: Optional[float] = None
    route_distance_km: Optional[float] = None
    travel_time_minutes: Optional[float] = None
    route_safety_score: Optional[float] = None
    shelter_hazard_score: float
    shelter_hazard_level: ShelterHazardLevel
    suitability_score: Optional[float] = None
    total_capacity: Optional[int] = None
    available_capacity: Optional[int] = None
    capacity_status: CapacityStatus
    data_state: ShelterDataState
    source: str


class VillageShelterRecommendation(BaseModel):
    """
    Complete output of the Shelter Recommendation Engine for a specific village.
    """
    village_id: str
    village_name: str
    status: str = Field("SAFE_SHELTER_FOUND", description="'SAFE_SHELTER_FOUND' or 'NO_SAFE_SHELTER'")
    selected_shelter_id: Optional[str] = None
    selected_shelter_name: Optional[str] = None
    suitability_score: Optional[float] = None
    route_distance_km: Optional[float] = None
    travel_time_minutes: Optional[float] = None
    route_safety_score: Optional[float] = None
    shelter_hazard_score: Optional[float] = None
    shelter_hazard_level: Optional[ShelterHazardLevel] = None
    capacity: Optional[int] = None
    available_capacity: Optional[int] = None
    capacity_status: Optional[CapacityStatus] = None
    road_status: Optional[str] = None
    blocked_segments: List[str] = Field(default_factory=list)
    degraded_segments: List[str] = Field(default_factory=list)
    data_state: ShelterDataState
    source: str
    source_url: str
    calculation_method: str = "HAZARD_WEIGHTED_SUITABILITY_INDEX"
    suitability_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "route_safety": 0.45,
            "inverse_distance": 0.25,
            "inverse_shelter_hazard": 0.30,
        }
    )
    alternatives: List[CandidateShelterEvaluation] = Field(default_factory=list, description="Ranked alternative candidate relief shelters")
    coverage_status: str = Field("GOOD", description="Coverage status: GOOD, LIMITED, NO_SAFE_SHELTER, UNKNOWN")
    nearest_verified_shelter_distance: Optional[float] = Field(None, description="Distance to nearest verified shelter in km")
    nearest_candidate_distance: Optional[float] = Field(None, description="Distance to nearest shelter candidate in km")
    number_of_candidates: int = Field(0, description="Total candidate shelters evaluated for village")
    number_of_verified_shelters: int = Field(0, description="Number of official government verified candidate shelters")
    number_of_route_accessible_shelters: int = Field(0, description="Number of shelters accessible via open roads")
    rejected_candidates: List[CandidateShelterEvaluation] = Field(default_factory=list)
    all_candidates_evaluated: List[CandidateShelterEvaluation] = Field(default_factory=list)
    selection_reason: str


class ShelterCoverageItem(BaseModel):
    """
    Geographic shelter coverage metrics for a single monitored village.
    """
    village_id: str
    village_name: str
    district: str
    state: str
    nearest_verified_shelter_distance: Optional[float] = None
    nearest_candidate_distance: Optional[float] = None
    number_of_candidates: int = 0
    number_of_verified_shelters: int = 0
    number_of_route_accessible_shelters: int = 0
    recommended_shelter_id: Optional[str] = None
    recommended_shelter_name: Optional[str] = None
    coverage_status: str = Field("GOOD", description="GOOD, LIMITED, NO_SAFE_SHELTER, UNKNOWN")


class ShelterCoverageSummaryResponse(BaseModel):
    """
    Regional shelter coverage breakdown across all monitored villages.
    """
    total_monitored_villages: int
    total_shelter_candidates: int
    villages_with_good_coverage: int
    villages_with_limited_coverage: int
    villages_with_no_safe_shelter: int
    coverage_details: List[ShelterCoverageItem]


class ShelterSystemStatusResponse(BaseModel):
    """
    Overview of the Shelter / Relief-Center Subsystem.
    """
    total_registered_shelters: int
    valid_shelters_count: int
    verified_official_count: int
    unverified_demo_count: int
    data_state: ShelterDataState
    official_authority: str
    official_source_url: str
    suitability_formula: str
    suitability_weights: Dict[str, float]
    disclaimer: str

