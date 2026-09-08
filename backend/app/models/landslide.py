"""
Pydantic Models for Real Historical Landslide Inventory Intelligence.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class LandslideDataState(str, Enum):
    REAL_GIS = "REAL_GIS"
    CACHED_GIS = "CACHED_GIS"
    OFFLINE_DEMO = "OFFLINE_DEMO"
    UNAVAILABLE = "UNAVAILABLE"


class HistoricalLandslideEvent(BaseModel):
    event_id: str
    location_name: str
    district: str
    state: str = "Uttarakhand"
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    date: Optional[str] = Field(default=None, description="ISO 8601 or YYYY-MM-DD date")
    landslide_type: str = Field(..., description="Geomorphological landslide classification")
    trigger: Optional[str] = Field(default=None, description="Reported trigger mechanism")
    severity: str = Field(default="MODERATE", description="Severity / Magnitude ranking")
    source: str = Field(..., description="Authoritative inventory source name")
    source_url: str = Field(..., description="URL / scientific publication provenance")
    confidence: str = Field(default="CONFIRMED_FIELD_SURVEY", description="Survey confidence level")


class VillageHistoricalLandslideSummary(BaseModel):
    village_id: str
    village_name: str
    latitude: float
    longitude: float
    total_events_in_region: int
    events_within_5km: int
    events_within_15km: int
    nearest_event_id: Optional[str] = None
    nearest_event_distance_km: Optional[float] = None
    nearest_event_location: Optional[str] = None
    nearest_event_date: Optional[str] = None
    nearest_event_type: Optional[str] = None
    recent_events_count_post_2015: int = 0
    historical_susceptibility_evidence: str = Field(
        ...,
        description="Categorical historical activity evidence (HIGH_HISTORICAL_ACTIVITY, MODERATE_HISTORICAL_ACTIVITY, LOW_HISTORICAL_RECORDS)"
    )
    data_state: LandslideDataState = Field(default=LandslideDataState.CACHED_GIS)
    source_name: str = Field(default="ISRO NRSC Landslide Atlas of India / GSI National Landslide Inventory")
    source_type: str = Field(default="AUTHORITATIVE_GOVERNMENT_INVENTORY")
    source_url: str = Field(default="https://www.nrsc.gov.in/Landslide_Atlas_of_India")
    retrieved_at: str = Field(..., description="ISO 8601 UTC timestamp")
    limitations: str = Field(
        default="Covers documented high-impact landslides in Chamoli and Rudraprayag districts from ISRO NRSC & GSI records.",
        description="Known spatial/temporal boundaries"
    )


class HistoricalLandslideInventoryResponse(BaseModel):
    total_records: int
    data_state: LandslideDataState
    source_name: str
    source_type: str
    source_url: str
    geographic_coverage: str
    retrieved_at: str
    events: List[HistoricalLandslideEvent]
    limitations: str
