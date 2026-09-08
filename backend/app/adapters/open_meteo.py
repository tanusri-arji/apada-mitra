"""
Real Open-Meteo Meteorological Data Adapter.
Fetches real public weather API observations for Himalayan coordinates.
"""
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.adapters.base import DataSourceAdapter
from app.models.domain import NormalizedEnvironmentObservation, DataSourceState, DataQualityLevel

logger = logging.getLogger(__name__)


class OpenMeteoRainfallAdapter(DataSourceAdapter):
    """
    Adapter for Open-Meteo public weather forecast REST API.
    Provides real-time precipitation, 24h forecast, and soil moisture for Himalayan watershed coordinates.
    """

    @property
    def name(self) -> str:
        return "Open-Meteo Weather API"

    @property
    def source_type(self) -> str:
        return "METEOROLOGICAL_API"

    def fetch(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Fetches live observation data from Open-Meteo.
        Returns raw JSON dictionary or None if network is offline / API is unreachable.
        """
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={latitude:.4f}&longitude={longitude:.4f}&"
            f"current=precipitation,rain,showers&"
            f"hourly=precipitation,soil_moisture_0_to_7cm&"
            f"forecast_days=1"
        )
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "APADA-MITRA-Disaster-Intelligence/1.0"}
        )

        try:
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    data["_fetch_timestamp"] = datetime.now(timezone.utc).isoformat()
                    return data
        except Exception as e:
            logger.info(f"Open-Meteo live API fetch skipped or unreachable: {e}")
            return None

        return None

    def normalize(
        self, raw_payload: Dict[str, Any], latitude: float, longitude: float
    ) -> NormalizedEnvironmentObservation:
        """
        Normalizes raw Open-Meteo JSON into canonical NormalizedEnvironmentObservation model.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        
        current_data = raw_payload.get("current", {})
        hourly_data = raw_payload.get("hourly", {})
        
        current_precip = current_data.get("precipitation")
        if current_precip is None:
            current_precip = current_data.get("rain", 0.0)

        # 24h forecast cumulative rainfall sum
        hourly_precip = hourly_data.get("precipitation", [])
        forecast_24h = sum(hourly_precip) if hourly_precip else 0.0

        # Soil moisture (m³/m³ converted to percentage 0-100%)
        soil_moisture_list = hourly_data.get("soil_moisture_0_to_7cm", [])
        soil_sat_pct = None
        if soil_moisture_list:
            avg_moisture = sum(soil_moisture_list) / len(soil_moisture_list)
            # Open-Meteo soil moisture is volumetric water content (0.0 - 0.5+ m3/m3)
            # Cap at 1.0 m3/m3 and scale to percentage (e.g. 0.45 m3/m3 = 90% saturation)
            soil_sat_pct = round(min(100.0, max(0.0, (avg_moisture / 0.50) * 100.0)), 1)

        raw_ts = current_data.get("time", raw_payload.get("_fetch_timestamp", now_iso))

        return NormalizedEnvironmentObservation(
            latitude=latitude,
            longitude=longitude,
            observation_timestamp=now_iso,
            current_rainfall_mm_hr=float(current_precip) if current_precip is not None else None,
            forecast_rainfall_24h_mm=round(float(forecast_24h), 1),
            soil_saturation_pct=soil_sat_pct,
            river_water_level_m=None,  # Not provided by weather API; handled by hydrological models
            discharge_cumecs=None,
            source_name=self.name,
            source_type=self.source_type,
            source_timestamp=str(raw_ts),
            data_state=DataSourceState.LIVE,
            quality_status=DataQualityLevel.GOOD,
            freshness_seconds=0.0,
            missing_fields=["river_water_level_m", "discharge_cumecs"],
            validation_warnings=[],
        )
