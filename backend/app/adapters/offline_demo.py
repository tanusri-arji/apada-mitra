"""
Offline Deterministic Scenario Data Adapter.
Wraps existing SIH Himalayan demo dataset as OFFLINE_DEMO provider.
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.adapters.base import DataSourceAdapter
from app.data.dataset import get_village_feature_snapshot, DEMO_VILLAGES
from app.models.domain import ScenarioType, NormalizedEnvironmentObservation, DataSourceState, DataQualityLevel


class OfflineDemoAdapter(DataSourceAdapter):
    """
    Adapter for deterministic SIH Himalayan scenario dataset.
    Used for offline demonstration, reproducible judging, and network failure fallback.
    """

    def __init__(self, scenario: ScenarioType = ScenarioType.HEAVY_RAIN):
        self.scenario = scenario

    @property
    def name(self) -> str:
        return "APADA MITRA Himalayan Demo Dataset"

    @property
    def source_type(self) -> str:
        return "OFFLINE_DEMO"

    def fetch(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Retrieves village feature snapshot from deterministic dataset matching coordinates or nearest village.
        """
        # Find village nearest to requested lat/lon
        nearest_village = min(
            DEMO_VILLAGES,
            key=lambda v: (v["latitude"] - latitude) ** 2 + (v["longitude"] - longitude) ** 2
        )
        snapshot = get_village_feature_snapshot(nearest_village["id"], self.scenario)
        snapshot["latitude"] = nearest_village["latitude"]
        snapshot["longitude"] = nearest_village["longitude"]
        return snapshot

    def normalize(
        self, raw_payload: Dict[str, Any], latitude: float, longitude: float
    ) -> NormalizedEnvironmentObservation:
        """
        Normalizes dataset snapshot into canonical NormalizedEnvironmentObservation model.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        
        missing_fields = []
        if raw_payload.get("soil_saturation") is None:
            missing_fields.append("soil_saturation_pct")

        return NormalizedEnvironmentObservation(
            latitude=raw_payload.get("latitude", latitude),
            longitude=raw_payload.get("longitude", longitude),
            observation_timestamp=raw_payload.get("timestamp", now_iso),
            current_rainfall_mm_hr=raw_payload.get("current_rainfall"),
            forecast_rainfall_24h_mm=raw_payload.get("forecast_rainfall"),
            soil_saturation_pct=raw_payload.get("soil_saturation"),
            river_water_level_m=raw_payload.get("river_water_level"),
            discharge_cumecs=None,
            source_name=self.name,
            source_type=self.source_type,
            source_timestamp=raw_payload.get("timestamp", now_iso),
            data_state=DataSourceState.OFFLINE_DEMO,
            quality_status=DataQualityLevel.GOOD if not missing_fields else DataQualityLevel.WARNING,
            freshness_seconds=0.0,
            missing_fields=missing_fields,
            validation_warnings=["SIH Deterministic Demo Dataset active"] if not missing_fields else ["Missing soil saturation in stress scenario"],
        )
