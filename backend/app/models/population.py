"""
Population and Hazard Exposure Data Models for APADA MITRA (Feature 7).
Defines schemas for Census-provenanced population datasets and transparent hazard exposure calculations.
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class PopulationDataState(str, Enum):
    """Data provenance state for population records."""
    REAL_STATIC = "REAL_STATIC"
    CACHED = "CACHED"
    ESTIMATED_FROM_REAL_SOURCE = "ESTIMATED_FROM_REAL_SOURCE"
    OFFLINE_DEMO = "OFFLINE_DEMO"
    UNAVAILABLE = "UNAVAILABLE"


class ExposureCalculationMethod(str, Enum):
    """Methodology applied for calculating exposed population and vulnerability."""
    MULTI_HAZARD_SPATIAL_INTERSECTION = "MULTI_HAZARD_SPATIAL_INTERSECTION"
    TERRAIN_SLOPE_FLOOD_PROXIMITY_ENVELOPE = "TERRAIN_SLOPE_FLOOD_PROXIMITY_ENVELOPE"
    OFFLINE_FALLBACK_ESTIMATE = "OFFLINE_FALLBACK_ESTIMATE"
    UNAVAILABLE = "UNAVAILABLE"


class VillagePopulationRecord(BaseModel):
    """Authoritative population record with full provenance tracking."""
    village_id: str = Field(..., description="Unique village identifier (e.g. VIL-001)")
    village_name: str = Field(..., description="Official revenue village or municipal town name")
    district: str = Field(..., description="Administrative District (e.g. Chamoli, Rudraprayag)")
    sub_district_or_block: str = Field(..., description="Sub-district / Tehsil or Development Block")
    census_2011_code: Optional[str] = Field(None, description="Official Census of India 2011 Village/Town Code")
    population: int = Field(..., ge=0, description="Total resident population from census record or sector estimate")
    households: Optional[int] = Field(None, ge=0, description="Total occupied residential households")
    vulnerable_population: Optional[int] = Field(None, ge=0, description="Vulnerable demographic count (Children 0-6, elderly 60+, and high-risk groups)")
    geographic_level: str = Field(..., description="Resolution level: VILLAGE_CENSUS_PCA, TOWN_WARD_PCA, or WARD_SECTOR_PCA")
    source: str = Field(..., description="Authoritative dataset name")
    source_url: str = Field(..., description="Publicly accessible URL to census / official government publication")
    source_year: int = Field(..., description="Reference census or publication year")
    data_state: PopulationDataState = Field(..., description="Provenance state of the population record")
    confidence: float = Field(..., ge=0.0, le=100.0, description="Confidence score (0-100%)")
    assumptions: List[str] = Field(default_factory=list, description="Documented demographic assumptions and geographic scope")


class HazardExposureBreakdown(BaseModel):
    """Hazard-specific exposure breakdown."""
    hazard_type: str = Field(..., description="Hazard category: FLASH_FLOOD or LANDSLIDE")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Computed risk score (0-100)")
    risk_level: str = Field(..., description="LOW, MODERATE, HIGH, or CRITICAL")
    exposed_population: int = Field(..., ge=0, description="Estimated headcount exposed directly to this hazard")
    exposure_fraction: float = Field(..., ge=0.0, le=1.0, description="Fraction of population exposed (0.0 - 1.0)")
    vulnerable_exposed: int = Field(..., ge=0, description="Vulnerable demographic headcount exposed to this hazard")


class VillageExposureDetail(BaseModel):
    """Detailed multi-hazard exposure assessment with population provenance."""
    village_id: str = Field(..., description="Unique village identifier")
    village_name: str = Field(..., description="Village / Town name")
    district: str = Field(..., description="District")
    sub_district_or_block: str = Field(..., description="Tehsil / Block")
    total_population: int = Field(..., ge=0, description="Total resident population")
    households: Optional[int] = Field(None, ge=0, description="Total residential households")
    vulnerable_population: int = Field(..., ge=0, description="Total vulnerable demographic headcount")
    exposed_population: int = Field(..., ge=0, description="Total non-overlapping population exposed to hazards")
    vulnerable_exposed: int = Field(..., ge=0, description="Vulnerable demographic headcount in exposure zone")
    exposure_percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of village population exposed (0-100%)")
    overall_hazard_level: str = Field(..., description="Dominant composite hazard level")
    overall_hazard_score: float = Field(..., ge=0.0, le=100.0, description="Composite risk score (0-100)")
    flood_exposure: HazardExposureBreakdown = Field(..., description="Flash flood specific exposure")
    landslide_exposure: HazardExposureBreakdown = Field(..., description="Landslide specific exposure")
    infrastructure_exposed: Dict[str, int] = Field(..., description="Exposed critical infrastructure counts")
    composite_exposure_score: float = Field(..., ge=0.0, le=100.0, description="Composite exposure index (0-100)")
    calculation_method: ExposureCalculationMethod = Field(..., description="Methodology applied")
    data_state: PopulationDataState = Field(..., description="Provenance state")
    confidence: float = Field(..., ge=0.0, le=100.0, description="Confidence score (0-100%)")
    source_provenance: Dict[str, Any] = Field(..., description="Source metadata and reference links")
    assumptions: List[str] = Field(default_factory=list, description="Methodological and spatial assumptions")
