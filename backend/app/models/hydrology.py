"""
Hydrological Telemetry and River-Level Data Models for APADA MITRA (Feature 8).
Defines schemas for Central Water Commission (CWC) gauging stations, IoT water-level telemetry,
data provenance, freshness classifications, and system status.
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class HydrologyDataState(str, Enum):
    """Explicit data provenance states for hydrological observations."""
    REAL_LIVE_OFFICIAL = "REAL_LIVE_OFFICIAL"
    REAL_LIVE_IOT = "REAL_LIVE_IOT"
    CACHED_OFFICIAL = "CACHED_OFFICIAL"
    ESTIMATED_FROM_REAL_SOURCE = "ESTIMATED_FROM_REAL_SOURCE"
    OFFLINE_DEMO = "OFFLINE_DEMO"
    UNAVAILABLE = "UNAVAILABLE"


class HydrologyFreshnessStatus(str, Enum):
    """Freshness classification based on observation elapsed time."""
    LIVE = "LIVE"              # <= 15 minutes
    FRESH = "FRESH"            # <= 1 hour
    STALE = "STALE"            # > 1 hour and <= 6 hours
    OFFLINE = "OFFLINE"        # > 6 hours
    UNAVAILABLE = "UNAVAILABLE"


class HydrologicalStationRecord(BaseModel):
    """Authoritative River Gauging Station Metadata."""
    station_id: str = Field(..., description="Unique station identifier (e.g. CWC-001)")
    station_name: str = Field(..., description="Official station name")
    river_name: str = Field(..., description="River / stream name (e.g. Alaknanda, Mandakini)")
    basin_name: str = Field(..., description="River basin name (e.g. Ganga Basin - Alaknanda Sub-basin)")
    latitude: float = Field(..., description="Station latitude")
    longitude: float = Field(..., description="Station longitude")
    warning_level_m: Optional[float] = Field(None, description="Official Warning Level in meters (MSL)")
    danger_level_m: Optional[float] = Field(None, description="Official Danger Level in meters (MSL)")
    hfl_m: Optional[float] = Field(None, description="Highest Flood Level recorded in meters (MSL)")
    upstream_downstream_relationship: str = Field(..., description="Hydrological connectivity context")
    associated_village_ids: List[str] = Field(default_factory=list, description="Monitored villages in station hydraulic reach")
    official_authority: str = Field(default="Central Water Commission (CWC) / Uttarakhand Irrigation Dept")


class HydrologicalObservation(BaseModel):
    """Comprehensive Hydrological Observation with explicit provenance and freshness."""
    station_id: Optional[str] = Field(None, description="Nearest / associated gauging station ID")
    station_name: Optional[str] = Field(None, description="Station name")
    village_id: Optional[str] = Field(None, description="Village identifier if queried for village")
    village_name: Optional[str] = Field(None, description="Village name")
    river_name: str = Field(..., description="River / stream name")
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")
    water_level_m: Optional[float] = Field(None, description="Observed river stage or gauge water level in meters")
    river_stage_ratio: Optional[float] = Field(None, description="Normalized stage ratio (1.0 = baseflow, 2.0 = moderate swelling, 3.0 = high flood)")
    discharge_cumecs: Optional[float] = Field(None, description="River volumetric discharge rate in cumecs (m3/s)")
    observation_time: Optional[str] = Field(None, description="ISO timestamp of telemetry observation")
    fetched_at: str = Field(..., description="ISO timestamp when telemetry was processed")
    source: str = Field(..., description="Telemetry source name")
    source_url: str = Field(..., description="Reference official portal or IoT endpoint URL")
    data_state: HydrologyDataState = Field(..., description="Explicit provenance state")
    freshness: HydrologyFreshnessStatus = Field(..., description="Observation freshness status")
    freshness_seconds: float = Field(..., ge=0.0, description="Elapsed seconds since observation")
    upstream_downstream_relationship: Optional[str] = Field(None, description="Hydraulic reach connectivity")
    quality_status: str = Field(..., description="Data quality rating (GOOD, DEGRADED, MISSING, DEMO)")
    warning_status: str = Field(default="NORMAL", description="Hydrological warning level: NORMAL, WARNING, DANGER, UNKNOWN")
    risk_contribution_pts: float = Field(default=0.0, description="Direct point contribution to flood risk score (0-10 pts)")
    assumptions: List[str] = Field(default_factory=list, description="Hydrological and operational assumptions")


class HydrologySystemStatus(BaseModel):
    """Overall Hydrological Subsystem Telemetry Status."""
    official_live_status: str = Field(..., description="LIVE_OFFICIAL_SOURCE_UNAVAILABLE or CONNECTED")
    official_authority: str = Field(default="Central Water Commission (CWC), Ministry of Jal Shakti, GoI")
    official_api_url: str = Field(default="https://india-wris.gov.in/ / https://nwdp.nwic.gov.in/")
    registered_stations_count: int = Field(..., description="Total official gauging stations in basin registry")
    active_iot_water_sensors_count: int = Field(..., description="Total active IoT river-level sensors")
    source_priority_order: List[str] = Field(..., description="Ordered 4-tier source priority list")
    last_checked_at: str = Field(..., description="ISO timestamp of last adapter check")
    disclaimer: str = Field(..., description="Operational disclaimer regarding official credentials")
