"""
Pydantic Models for IoT Sensor API Ingestion Layer.
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class IoTSensorType(str, Enum):
    RAINFALL = "rainfall"
    SOIL_MOISTURE = "soil_moisture"
    WATER_LEVEL = "water_level"


class IoTFreshnessStatus(str, Enum):
    LIVE = "LIVE"
    STALE = "STALE"
    OFFLINE = "OFFLINE"


class IoTIngestionPayload(BaseModel):
    sensor_id: str = Field(..., description="Unique sensor identifier (e.g. RAIN-001)")
    sensor_type: str = Field(..., description="Sensor type: rainfall, soil_moisture, or water_level")
    village_id: str = Field(..., description="Target village identifier (e.g. VIL-003)")
    value: float = Field(..., description="Observed numeric sensor reading")
    unit: str = Field(..., description="Unit of measurement (mm/h, mm, m3/m3, %, m)")
    timestamp: str = Field(..., description="ISO 8601 observation timestamp")


class IoTSensorRecord(BaseModel):
    sensor_id: str
    sensor_type: str
    village_id: str
    value: float
    unit: str
    timestamp: str
    received_at: str
    source: str = Field(default="IOT_SENSOR")
    status: IoTFreshnessStatus
    freshness_seconds: float
    validation_status: str = Field(default="VALID")
