"""
Real Road Network & Dynamic Road Hazard Intelligence Models for APADA MITRA (Feature 9).
Defines schemas for OpenStreetMap (OSM) road geometry, dynamic hazard exposure,
operational road status, and hazard-aware evacuation routes.
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class RoadDataState(str, Enum):
    """Explicit data provenance states for road network data."""
    REAL_LIVE_OSM = "REAL_LIVE_OSM"
    CACHED_OSM = "CACHED_OSM"
    REAL_STATIC_GIS = "REAL_STATIC_GIS"
    DERIVED_FROM_REAL_GIS = "DERIVED_FROM_REAL_GIS"
    OFFLINE_DEMO = "OFFLINE_DEMO"
    UNAVAILABLE = "UNAVAILABLE"


class RoadOperationalStatus(str, Enum):
    """Operational passability status of a road segment."""
    OPEN = "OPEN"            # Low hazard exposure (H < 40.0)
    DEGRADED = "DEGRADED"    # Meaningful hazard exposure (40.0 <= H < 75.0)
    BLOCKED = "BLOCKED"      # Severe hazard exposure (H >= 75.0)
    UNKNOWN = "UNKNOWN"      # Insufficient data


class RoadSegmentDetail(BaseModel):
    """Detailed road segment with real geometry, attributes, and dynamic hazard ratings."""
    road_id: str = Field(..., description="Unique road segment identifier (e.g. ROAD-001)")
    id: Optional[str] = Field(None, description="Backwards-compatible identifier matching road_id")
    name: str = Field(..., description="Official highway or local road name")
    source_id: str = Field(..., description="Origin node (Village or Junction ID)")
    target_id: str = Field(..., description="Destination node (Village, Junction, or Shelter ID)")
    road_type: str = Field(..., description="OSM highway classification: trunk, primary, secondary, tertiary, unclassified")
    ref: Optional[str] = Field(None, description="Official road reference number (e.g. NH-07, NH-107)")
    coordinates: List[List[float]] = Field(..., description="Ordered [[lat, lon], ...] geometric trace coordinates")
    distance_km: float = Field(..., ge=0.0, description="Total road centerline distance in kilometers")
    max_speed_kmh: Optional[float] = Field(None, ge=0.0, description="Design or legal speed limit in km/h")
    surface: Optional[str] = Field(None, description="Pavement surface type (e.g. asphalt, paved, unpaved)")
    source: str = Field(default="OpenStreetMap (OSM) via Overpass API / Cached GeoJSON", description="Authoritative map data source")
    source_url: str = Field(default="https://www.openstreetmap.org/", description="Source attribution URL")
    fetched_at: str = Field(..., description="ISO timestamp when road data was fetched / synchronized")
    data_state: RoadDataState = Field(..., description="Provenance state of the road geometry")
    freshness: str = Field(..., description="Freshness status of road network geometry")
    status: RoadOperationalStatus = Field(..., description="Dynamic operational passability status")
    flood_exposure: float = Field(..., ge=0.0, le=100.0, description="Flash flood inundation hazard score (0-100%)")
    landslide_exposure: float = Field(..., ge=0.0, le=100.0, description="Landslide slope instability hazard score (0-100%)")
    composite_hazard_score: float = Field(..., ge=0.0, le=100.0, description="Dominant hazard exposure score (0-100%)")
    status_reason: str = Field(..., description="Explanation for current operational status")
    assumptions: List[str] = Field(default_factory=list, description="Hydraulic and geotechnical assumptions")


class EvacuationRouteDetail(BaseModel):
    """Hazard-aware evacuation route with geometry, travel time, and safety ratings."""
    origin_id: str = Field(..., description="Origin village ID")
    origin_name: str = Field(..., description="Origin village name")
    destination_id: str = Field(..., description="Target shelter ID")
    destination_name: str = Field(..., description="Target shelter name")
    road_ids: List[str] = Field(..., description="Sequence of traversed road segment IDs")
    road_names: List[str] = Field(..., description="Sequence of traversed road names")
    total_distance_km: float = Field(..., ge=0.0, description="Total route distance in kilometers")
    estimated_travel_time_minutes: float = Field(..., ge=0.0, description="Estimated evacuation travel time in minutes")
    route_safety_score: float = Field(..., ge=0.0, le=100.0, description="Route safety score (0-100%, 100=highest safety)")
    route_status: str = Field(..., description="SAFE_OPEN, SAFE_DEGRADED, HIGH_HAZARD_REROUTED, or NO_SAFE_ROUTE")
    blocked_segments: List[str] = Field(default_factory=list, description="Blocked road segments avoided during routing")
    degraded_segments: List[str] = Field(default_factory=list, description="Degraded road segments traversed with speed penalty")
    path_nodes: List[str] = Field(..., description="Sequence of visited graph nodes")
    data_state: RoadDataState = Field(..., description="Provenance state of underlying road network")
    source_provenance: Dict[str, Any] = Field(..., description="Authoritative map and attribution metadata")
    calculation_method: str = Field(default="HAZARD_WEIGHTED_DIJKSTRA", description="Routing algorithm used")
    explanation: str = Field(..., description="Operational routing explanation")
    assumptions: List[str] = Field(default_factory=list, description="Evacuation route operational assumptions")


class RoadNetworkStatusResponse(BaseModel):
    """Overall Road Network Subsystem Status."""
    total_segments_count: int
    open_segments_count: int
    degraded_segments_count: int
    blocked_segments_count: int
    data_state: RoadDataState
    source_authority: str
    source_url: str
    osm_licensing_note: str
    last_updated: str
    disclaimer: str
