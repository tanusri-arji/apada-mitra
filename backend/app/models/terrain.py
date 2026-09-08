"""
Pydantic Models for Real GIS Terrain Intelligence.
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TerrainQualityStatus(str, Enum):
    REAL_GIS = "REAL_GIS"
    CACHED_GIS = "CACHED_GIS"
    OFFLINE_DEMO = "OFFLINE_DEMO"
    UNAVAILABLE = "UNAVAILABLE"


class VillageTerrainDetail(BaseModel):
    village_id: str
    village_name: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    elevation_m: float = Field(..., description="DEM Elevation in meters above sea level")
    elevation_source: str = Field(default="OFFLINE_DEMO", description="Provenance of elevation data")
    slope_deg: float = Field(..., ge=0.0, le=90.0, description="Derived slope steepness in degrees")
    slope_source: str = Field(default="OFFLINE_DEMO", description="Derivation method for slope")
    flow_accumulation: float = Field(..., ge=0.0, description="Derived D8 hydrological flow accumulation log index")
    flow_accumulation_source: str = Field(default="OFFLINE_DEMO", description="Derivation method for flow accumulation")
    flow_accumulation_cells: Optional[float] = Field(default=None, description="Raw D8 accumulated upstream cell count")
    terrain_status: TerrainQualityStatus = Field(default=TerrainQualityStatus.OFFLINE_DEMO)
    terrain_source: str = Field(default="SIH Synthetic Scenario Dataset")
    dem_resolution: Optional[str] = Field(default="90m (Copernicus DEM GLO-90)")
    dem_window_size: Optional[str] = Field(default="9x9 grid (~1km x 1km raster window)")
    processing_method: Optional[str] = Field(
        default="D8_HYDROLOGICAL_ROUTING_WITH_DEPRESSION_HANDLING",
        description="Algorithm applied to DEM raster"
    )
    retrieved_at: str = Field(..., description="ISO 8601 UTC timestamp")

