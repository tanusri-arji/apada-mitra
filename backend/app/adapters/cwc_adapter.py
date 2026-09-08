"""
Central Water Commission (CWC) / WIMS Hydrological Data Source Adapter for APADA MITRA.

Design & Provenance Note:
Official CWC (Central Water Commission) and India-WIMS river gauge telemetry data requires authorized
API credentials / government network clearance. This adapter defines the formal interface for real-time
river stage level (m) and discharge (cumecs) telemetry from authorized CWC telemetry stations.

When no official credentials are configured, fetch() returns None, cleanly signaling to the Data Quality Engine
that real-time river telemetry is unavailable and that hydrological inputs are derived from modelled / demo baselines.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.adapters.base import DataSourceAdapter
from app.models.domain import NormalizedEnvironmentObservation, DataSourceState, DataQualityLevel


class CWCHydrologicalAdapter(DataSourceAdapter):
    """
    Pluggable Adapter for CWC (Central Water Commission) / WIMS River Telemetry.
    Prepared for official government API endpoints once API authorization keys are provisioned.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self._api_key = api_key
        self._base_url = base_url

    @property
    def name(self) -> str:
        return "CWC River Telemetry (WIMS)"

    @property
    def source_type(self) -> str:
        return "HYDROLOGICAL_TELEMETRY"

    def fetch(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Fetches live river water level and discharge rate from authorized CWC gauge stations.
        Returns None when credentials or endpoint are unconfigured (graceful fallback).
        """
        if not self._api_key or not self._base_url:
            # Honest status: No unauthorized/fake API call attempted
            return None

        # Implementation skeleton for authorized CWC / WIMS REST API endpoint integration
        # Example: GET {self._base_url}/stations/nearest?lat={latitude}&lon={longitude}
        return None

    def normalize(self, raw_payload: Dict[str, Any], latitude: float, longitude: float) -> NormalizedEnvironmentObservation:
        """
        Normalizes CWC payload into canonical NormalizedEnvironmentObservation.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        if not raw_payload:
            return NormalizedEnvironmentObservation(
                latitude=latitude,
                longitude=longitude,
                observation_timestamp=now_iso,
                current_rainfall_mm_hr=None,
                forecast_rainfall_24h_mm=None,
                soil_saturation_pct=None,
                river_water_level_m=None,
                discharge_cumecs=None,
                source_name=self.name,
                source_type=self.source_type,
                source_timestamp=now_iso,
                data_state=DataSourceState.UNAVAILABLE,
                quality_status=DataQualityLevel.CRITICAL_MISSING,
                freshness_seconds=0.0,
                missing_fields=["river_water_level_m", "discharge_cumecs"],
                validation_warnings=["CWC telemetry endpoint unconfigured or unauthorized. Using modelled hydrological baseline."],
            )

        stage_m = raw_payload.get("water_level_m")
        discharge = raw_payload.get("discharge_cumecs")
        timestamp = raw_payload.get("timestamp", now_iso)

        return NormalizedEnvironmentObservation(
            latitude=latitude,
            longitude=longitude,
            observation_timestamp=now_iso,
            current_rainfall_mm_hr=None,
            forecast_rainfall_24h_mm=None,
            soil_saturation_pct=None,
            river_water_level_m=float(stage_m) if stage_m is not None else None,
            discharge_cumecs=float(discharge) if discharge is not None else None,
            source_name=self.name,
            source_type=self.source_type,
            source_timestamp=str(timestamp),
            data_state=DataSourceState.LIVE,
            quality_status=DataQualityLevel.GOOD,
            freshness_seconds=0.0,
            missing_fields=[],
            validation_warnings=[],
        )
