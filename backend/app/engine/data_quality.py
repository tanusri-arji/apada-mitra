"""
Data Quality & Validation Engine for APADA MITRA.
Performs data quality checks, anomaly detection, physical bounds verification, and quality status assignment.
"""
from typing import List
from app.models.domain import (
    NormalizedEnvironmentObservation,
    DataQualityLevel,
    DataSourceState,
)


class DataQualityEngine:
    """
    Validation layer for environmental observations before ingestion into risk calculation engines.
    """

    MAX_HOURLY_RAINFALL = 300.0     # mm/hr extreme physical limit
    MAX_FORECAST_RAINFALL = 1000.0  # mm 24h cumulative upper limit
    MAX_SOIL_SATURATION = 100.0     # % percentage upper limit
    MAX_RIVER_STAGE = 15.0          # meters upper limit
    STALE_THRESHOLD_SECONDS = 10800 # 3 hours

    @classmethod
    def validate_observation(
        cls, obs: NormalizedEnvironmentObservation
    ) -> NormalizedEnvironmentObservation:
        """
        Validates raw normalized observation against domain physical bounds and quality criteria.
        Returns updated observation with populated validation_warnings, missing_fields, and quality_status.
        """
        warnings: List[str] = list(obs.validation_warnings)
        missing: List[str] = list(obs.missing_fields)

        # 1. Hourly Rainfall Validation
        if obs.current_rainfall_mm_hr is not None:
            if obs.current_rainfall_mm_hr < 0.0:
                warnings.append(
                    f"Invalid negative rainfall intensity ({obs.current_rainfall_mm_hr} mm/hr) rejected."
                )
                obs.current_rainfall_mm_hr = None
                if "current_rainfall_mm_hr" not in missing:
                    missing.append("current_rainfall_mm_hr")
            elif obs.current_rainfall_mm_hr > cls.MAX_HOURLY_RAINFALL:
                warnings.append(
                    f"Rainfall intensity ({obs.current_rainfall_mm_hr} mm/hr) exceeded physical limit; capped at {cls.MAX_HOURLY_RAINFALL} mm/hr."
                )
                obs.current_rainfall_mm_hr = cls.MAX_HOURLY_RAINFALL

        # 2. 24h Forecast Rainfall Validation
        if obs.forecast_rainfall_24h_mm is not None:
            if obs.forecast_rainfall_24h_mm < 0.0:
                warnings.append(
                    f"Invalid negative forecast rainfall ({obs.forecast_rainfall_24h_mm} mm) rejected."
                )
                obs.forecast_rainfall_24h_mm = None
                if "forecast_rainfall_24h_mm" not in missing:
                    missing.append("forecast_rainfall_24h_mm")
            elif obs.forecast_rainfall_24h_mm > cls.MAX_FORECAST_RAINFALL:
                warnings.append(
                    f"Forecast rainfall ({obs.forecast_rainfall_24h_mm} mm) capped at upper limit {cls.MAX_FORECAST_RAINFALL} mm."
                )
                obs.forecast_rainfall_24h_mm = cls.MAX_FORECAST_RAINFALL

        # 3. Soil Saturation Validation
        if obs.soil_saturation_pct is not None:
            if obs.soil_saturation_pct < 0.0:
                warnings.append(
                    f"Invalid negative soil saturation ({obs.soil_saturation_pct}%) rejected."
                )
                obs.soil_saturation_pct = None
                if "soil_saturation_pct" not in missing:
                    missing.append("soil_saturation_pct")
            elif obs.soil_saturation_pct > cls.MAX_SOIL_SATURATION:
                warnings.append(
                    f"Soil saturation ({obs.soil_saturation_pct}%) capped at maximum 100.0%."
                )
                obs.soil_saturation_pct = cls.MAX_SOIL_SATURATION

        # 4. River Stage Water Level Validation
        if obs.river_water_level_m is not None:
            if obs.river_water_level_m < 0.0:
                warnings.append(
                    f"Invalid negative river water level ({obs.river_water_level_m} m) rejected."
                )
                obs.river_water_level_m = None
                if "river_water_level_m" not in missing:
                    missing.append("river_water_level_m")
            elif obs.river_water_level_m > cls.MAX_RIVER_STAGE:
                warnings.append(
                    f"River water level ({obs.river_water_level_m} m) capped at limit {cls.MAX_RIVER_STAGE} m."
                )
                obs.river_water_level_m = cls.MAX_RIVER_STAGE

        # Check for missing primary fields
        if obs.current_rainfall_mm_hr is None and "current_rainfall_mm_hr" not in missing:
            missing.append("current_rainfall_mm_hr")
        if obs.forecast_rainfall_24h_mm is None and "forecast_rainfall_24h_mm" not in missing:
            missing.append("forecast_rainfall_24h_mm")

        # 5. Staleness Verification
        if obs.freshness_seconds > cls.STALE_THRESHOLD_SECONDS:
            warnings.append(
                f"Observation data stale ({round(obs.freshness_seconds / 60, 1)} minutes old)."
            )
            if obs.data_state == DataSourceState.LIVE:
                obs.data_state = DataSourceState.CACHED

        # 6. Overall Quality Level Classification
        if len(missing) >= 3:
            quality = DataQualityLevel.CRITICAL_MISSING
        elif len(missing) >= 1 or obs.freshness_seconds > cls.STALE_THRESHOLD_SECONDS:
            quality = DataQualityLevel.DEGRADED
        elif len(warnings) > 0:
            quality = DataQualityLevel.WARNING
        else:
            quality = DataQualityLevel.GOOD

        obs.validation_warnings = list(dict.fromkeys(warnings))
        obs.missing_fields = list(dict.fromkeys(missing))
        obs.quality_status = quality

        return obs
