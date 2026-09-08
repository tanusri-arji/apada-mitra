"""
In-Memory IoT Sensor Storage Registry & Validation Engine for APADA MITRA.
"""
import math
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from app.data.dataset import DEMO_VILLAGES
from app.models.iot import IoTSensorRecord, IoTFreshnessStatus, IoTSensorType

logger = logging.getLogger(__name__)

# Configurable Freshness Thresholds (in seconds)
IOT_FRESHNESS_LIVE_SECONDS: float = 600.0   # <= 10 minutes -> LIVE
IOT_FRESHNESS_STALE_SECONDS: float = 1800.0  # > 10 min and <= 30 min -> STALE
                                            # > 30 min -> OFFLINE

VALID_SENSOR_TYPES = {IoTSensorType.RAINFALL.value, IoTSensorType.SOIL_MOISTURE.value, IoTSensorType.WATER_LEVEL.value}
VALID_UNITS_BY_TYPE = {
    IoTSensorType.RAINFALL.value: {"mm/h", "mm"},
    IoTSensorType.SOIL_MOISTURE.value: {"m3/m3", "%"},
    IoTSensorType.WATER_LEVEL.value: {"m"},
}


class IoTSensorStore:
    """
    In-memory registry maintaining the latest validated IoT observations.
    """

    def __init__(self):
        self._sensors: Dict[str, IoTSensorRecord] = {}

    def _get_valid_village_ids(self) -> set:
        return {v["id"] for v in DEMO_VILLAGES}

    def compute_freshness(self, observation_timestamp_str: str) -> tuple[IoTFreshnessStatus, float]:
        """Calculates freshness status and age in seconds relative to UTC now."""
        now = datetime.now(timezone.utc)
        try:
            cleaned_ts = observation_timestamp_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned_ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_secs = max(0.0, (now - dt).total_seconds())
        except Exception:
            return IoTFreshnessStatus.OFFLINE, 999999.0

        if age_secs <= IOT_FRESHNESS_LIVE_SECONDS:
            return IoTFreshnessStatus.LIVE, round(age_secs, 1)
        elif age_secs <= IOT_FRESHNESS_STALE_SECONDS:
            return IoTFreshnessStatus.STALE, round(age_secs, 1)
        else:
            return IoTFreshnessStatus.OFFLINE, round(age_secs, 1)

    def validate_payload(self, raw_data: Dict[str, Any]) -> None:
        """
        Strict validation for IoT sensor ingestion payloads.
        Raises ValueError with descriptive detail if invalid.
        """
        required_fields = ["sensor_id", "sensor_type", "village_id", "value", "unit", "timestamp"]
        for field in required_fields:
            if field not in raw_data or raw_data[field] is None:
                raise ValueError(f"Missing required field: '{field}'")
            if isinstance(raw_data[field], str) and not raw_data[field].strip():
                raise ValueError(f"Field '{field}' cannot be empty")

        sensor_id = str(raw_data["sensor_id"]).strip()
        sensor_type = str(raw_data["sensor_type"]).strip().lower()
        village_id = str(raw_data["village_id"]).strip()
        value = raw_data["value"]
        unit = str(raw_data["unit"]).strip()
        timestamp = str(raw_data["timestamp"]).strip()

        # 1. Village ID check
        valid_villages = self._get_valid_village_ids()
        if village_id not in valid_villages:
            raise ValueError(f"Unknown village ID '{village_id}'. Must be a registered APADA MITRA watershed village.")

        # 2. Sensor Type check
        if sensor_type not in VALID_SENSOR_TYPES:
            raise ValueError(f"Unsupported sensor_type '{sensor_type}'. Must be one of {sorted(list(VALID_SENSOR_TYPES))}.")

        # 3. Numeric Value check
        try:
            numeric_val = float(value)
            if math.isnan(numeric_val) or math.isinf(numeric_val):
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError(f"Invalid numeric value '{value}' for sensor '{sensor_id}'.")

        # 4. Non-negative check
        if numeric_val < 0:
            raise ValueError(f"Invalid negative sensor reading {numeric_val} for sensor '{sensor_id}'.")

        # 5. Unit check
        valid_units = VALID_UNITS_BY_TYPE.get(sensor_type, set())
        if unit not in valid_units:
            raise ValueError(f"Invalid unit '{unit}' for sensor_type '{sensor_type}'. Allowed units: {sorted(list(valid_units))}.")

        # 6. Timestamp check
        try:
            cleaned_ts = timestamp.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned_ts)
        except Exception:
            raise ValueError(f"Invalid ISO 8601 timestamp format '{timestamp}'. Example: '2026-09-04T16:30:00Z'.")

    def ingest(self, raw_data: Dict[str, Any]) -> IoTSensorRecord:
        """
        Validates raw payload, computes metadata, and updates in-memory registry.
        """
        self.validate_payload(raw_data)

        sensor_id = str(raw_data["sensor_id"]).strip()
        sensor_type = str(raw_data["sensor_type"]).strip().lower()
        village_id = str(raw_data["village_id"]).strip()
        value = float(raw_data["value"])
        unit = str(raw_data["unit"]).strip()
        timestamp = str(raw_data["timestamp"]).strip()

        now_iso = datetime.now(timezone.utc).isoformat()
        status, age_secs = self.compute_freshness(timestamp)

        record = IoTSensorRecord(
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            village_id=village_id,
            value=value,
            unit=unit,
            timestamp=timestamp,
            received_at=now_iso,
            source="IOT_SENSOR",
            status=status,
            freshness_seconds=age_secs,
            validation_status="VALID",
        )

        self._sensors[sensor_id] = record
        return record

    def get_all_sensors(self) -> List[IoTSensorRecord]:
        """Returns all registered sensor records with updated freshness status."""
        records = []
        for record in self._sensors.values():
            status, age_secs = self.compute_freshness(record.timestamp)
            record.status = status
            record.freshness_seconds = age_secs
            records.append(record)
        return records

    def get_sensor_by_id(self, sensor_id: str) -> Optional[IoTSensorRecord]:
        """Returns latest record for a given sensor_id or None."""
        record = self._sensors.get(sensor_id)
        if record:
            status, age_secs = self.compute_freshness(record.timestamp)
            record.status = status
            record.freshness_seconds = age_secs
        return record

    def get_village_sensors(self, village_id: str) -> List[IoTSensorRecord]:
        """Returns all latest sensor records associated with a village."""
        records = []
        for record in self._sensors.values():
            if record.village_id == village_id:
                status, age_secs = self.compute_freshness(record.timestamp)
                record.status = status
                record.freshness_seconds = age_secs
                records.append(record)
        return records

    def clear(self):
        """Clears all in-memory sensor records (for testing)."""
        self._sensors.clear()


# Global Singleton Store Instance
iot_store_instance = IoTSensorStore()
