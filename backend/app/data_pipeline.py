"""
Data Ingestion & Quality Pipeline for APADA MITRA.
Coordinates real-time data adapters, validation, caching, and existing risk engine feature mapping.
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from app.adapters.open_meteo import OpenMeteoRainfallAdapter
from app.adapters.offline_demo import OfflineDemoAdapter
from app.engine.data_quality import DataQualityEngine
from app.engine.iot_store import iot_store_instance, IoTFreshnessStatus, IoTSensorType
from app.data.dataset import get_village_feature_snapshot
from app.models.domain import (
    NormalizedEnvironmentObservation,
    DataSourceState,
    DataQualityLevel,
    DataQualityStatus,
    SourceQualityReport,
    OverallDataQualityResponse,
    ScenarioType,
)


def safe_val(val1: Optional[float], val2: Optional[float], mode: str = "max") -> Optional[float]:
    if val1 is None:
        return val2
    if val2 is None:
        return val1
    return max(val1, val2) if mode == "max" else min(val1, val2)


class DataIngestionPipeline:
    """
    Central environmental data management pipeline.
    Manages live IoT sensor ingestion, live API retrieval, cached observation store,
    fallback to offline demo dataset, and translation to risk engine feature snapshots.
    """

    def __init__(self):
        self.live_adapter = OpenMeteoRainfallAdapter()
        self.offline_adapter = OfflineDemoAdapter()
        self.observation_cache: Dict[str, NormalizedEnvironmentObservation] = {}
        self.last_fetch_attempt: Optional[datetime] = None
        self._live_api_cooldown_until: Optional[datetime] = None
        self._live_api_cooldown_seconds: float = 30.0
        self.last_live_success: Optional[datetime] = None
        self.cache_ttl_seconds: float = 10800.0  # 3 hours

    def clear_cache(self):
        """Clears in-memory observation cache."""
        self.observation_cache.clear()

    def _apply_iot_source_priority(
        self, base_obs: NormalizedEnvironmentObservation, location_key: str
    ) -> NormalizedEnvironmentObservation:
        """
        Applies explicit IoT source priority over external API and demo data.
        If a valid, fresh (LIVE) IoT sensor exists for a given location and feature,
        its value is used directly without max/min/average blending.
        """
        iot_sensors = iot_store_instance.get_village_sensors(location_key)
        live_iot_sensors = [s for s in iot_sensors if s.status == IoTFreshnessStatus.LIVE]

        if not live_iot_sensors:
            # Set default source labels if no IoT sensors active
            if base_obs.data_state in [DataSourceState.LIVE, DataSourceState.LIVE_EXTERNAL_API]:
                base_obs.rainfall_source = base_obs.rainfall_source or "LIVE_EXTERNAL_API"
                base_obs.soil_source = base_obs.soil_source or "LIVE_EXTERNAL_API"
            elif base_obs.data_state == DataSourceState.CACHED:
                base_obs.rainfall_source = base_obs.rainfall_source or "CACHED"
                base_obs.soil_source = base_obs.soil_source or "CACHED"
            else:
                base_obs.rainfall_source = base_obs.rainfall_source or "OFFLINE_DEMO"
                base_obs.soil_source = base_obs.soil_source or "OFFLINE_DEMO"
            base_obs.water_level_source = base_obs.water_level_source or "OFFLINE_DEMO"
            return base_obs

        active_iot_ids = []

        # 1. Rainfall IoT Priority
        rain_sensor = next((s for s in live_iot_sensors if s.sensor_type == IoTSensorType.RAINFALL.value), None)
        if rain_sensor is not None:
            base_obs.current_rainfall_mm_hr = float(rain_sensor.value)
            base_obs.rainfall_source = "LIVE_IOT_SENSOR"
            active_iot_ids.append(rain_sensor.sensor_id)
        else:
            base_obs.rainfall_source = "LIVE_EXTERNAL_API" if base_obs.data_state == DataSourceState.LIVE else "OFFLINE_DEMO"

        # 2. Soil Moisture IoT Priority
        soil_sensor = next((s for s in live_iot_sensors if s.sensor_type == IoTSensorType.SOIL_MOISTURE.value), None)
        if soil_sensor is not None:
            val = float(soil_sensor.value)
            if soil_sensor.unit == "m3/m3":
                # Explicit conversion: (m3/m3 / 0.50) * 100 clamped to 0-100%
                sat_pct = round(min(100.0, max(0.0, (val / 0.50) * 100.0)), 1)
            else:
                sat_pct = round(min(100.0, max(0.0, val)), 1)
            base_obs.soil_saturation_pct = sat_pct
            base_obs.soil_source = "LIVE_IOT_SENSOR"
            active_iot_ids.append(soil_sensor.sensor_id)
        else:
            base_obs.soil_source = "LIVE_EXTERNAL_API" if base_obs.data_state == DataSourceState.LIVE else "OFFLINE_DEMO"

        # 3. Water Level IoT Priority
        water_sensor = next((s for s in live_iot_sensors if s.sensor_type == IoTSensorType.WATER_LEVEL.value), None)
        if water_sensor is not None:
            base_obs.river_water_level_m = float(water_sensor.value)
            base_obs.water_level_source = "LIVE_IOT_SENSOR"
            active_iot_ids.append(water_sensor.sensor_id)
        else:
            base_obs.water_level_source = "OFFLINE_DEMO"

        if active_iot_ids:
            base_obs.data_state = DataSourceState.LIVE_IOT_SENSOR
            base_obs.source_name = f"LIVE IoT Sensor ({', '.join(active_iot_ids)}) / {base_obs.source_name}"
            base_obs.source_type = "IOT_SENSOR_REST_API"

        return base_obs

    def get_normalized_observation(
        self,
        latitude: float,
        longitude: float,
        location_key: str,
        scenario: ScenarioType = ScenarioType.HEAVY_RAIN,
        force_offline: bool = False,
    ) -> NormalizedEnvironmentObservation:
        """
        Retrieves a validated, normalized environmental observation for given coordinates.
        Priority:
        1. Live IoT Sensor observation (if fresh and valid)
        2. Cached observation (if fresh and valid)
        3. Live API fetch (if available and not forced offline)
        4. Deterministic SIH Offline Demo Dataset (fallback)
        """
        now = datetime.now(timezone.utc)
        self.last_fetch_attempt = now

        base_obs = None

        # For non-NORMAL scenarios (HEAVY_RAIN, EXTREME_RAIN) the user is running a
        # disaster simulation. The scenario dataset values will always override live API
        # values in convert_to_risk_feature_snapshot(), so there is zero benefit in
        # making 15 network round-trips to Open-Meteo/wttr.in (each with a 5s timeout).
        # Skipping them reduces scenario-switch latency from ~75s → <1s.
        # NORMAL scenario still fetches real live weather as the true baseline.
        scenario_forces_offline = (scenario != ScenarioType.NORMAL)

        # 1a. For NORMAL: check exact-location cache FIRST before any live API call.
        # This means only the FIRST village triggers a network fetch; the remaining
        # 14 reuse the cached observation — reducing 15 API calls to 1.
        if not force_offline and not scenario_forces_offline:
            cached = self.observation_cache.get(location_key)
            if cached is not None:
                try:
                    cache_time = datetime.fromisoformat(cached.observation_timestamp)
                    age_secs = max(0.0, (now - cache_time).total_seconds())
                except Exception:
                    age_secs = float("inf")
                if age_secs < self.cache_ttl_seconds:
                    cached.freshness_seconds = age_secs
                    base_obs = DataQualityEngine.validate_observation(cached)

            # 1b. Regional cache (villages with same rounded lat/lon share a fetch).
            if base_obs is None:
                region_key = f"{round(latitude, 1)},{round(longitude, 1)}"
                cached_region = self.observation_cache.get(region_key)
                if cached_region is not None:
                    try:
                        cache_time = datetime.fromisoformat(cached_region.observation_timestamp)
                        age_secs = max(0.0, (now - cache_time).total_seconds())
                    except Exception:
                        age_secs = float("inf")
                    if age_secs < self.cache_ttl_seconds:
                        cached_region.freshness_seconds = age_secs
                        base_obs = DataQualityEngine.validate_observation(cached_region)

        # 2. Live API fetch for NORMAL (only if cache missed).
        # Skipped entirely while the circuit breaker is cooling down after a recent failure.
        breaker_open = (
            self._live_api_cooldown_until is not None
            and now < self._live_api_cooldown_until
        )
        if base_obs is None and not force_offline and not scenario_forces_offline and not breaker_open:
            try:
                raw_payload = self.live_adapter.fetch(latitude, longitude)
                if raw_payload is not None:
                    norm_obs = self.live_adapter.normalize(raw_payload, latitude, longitude)
                    validated_obs = DataQualityEngine.validate_observation(norm_obs)
                    region_key = f"{round(latitude, 1)},{round(longitude, 1)}"
                    self.observation_cache[location_key] = validated_obs
                    self.observation_cache[region_key] = validated_obs
                    self.last_live_success = now
                    self._live_api_cooldown_until = None
                    base_obs = validated_obs
                else:
                    self._live_api_cooldown_until = now + timedelta(
                        seconds=self._live_api_cooldown_seconds
                    )
            except Exception:
                self._live_api_cooldown_until = now + timedelta(
                    seconds=self._live_api_cooldown_seconds
                )

        # 3. Offline Demo Dataset (final fallback for all scenarios).
        if base_obs is None:
            demo_adapter = OfflineDemoAdapter(scenario=scenario)
            raw_demo = demo_adapter.fetch(latitude, longitude)
            norm_demo = demo_adapter.normalize(raw_demo, latitude, longitude)
            base_obs = DataQualityEngine.validate_observation(norm_demo)

        # Apply IoT Source Priority Layer (Overwrites base_obs fields ONLY if fresh IoT sensors exist)
        return self._apply_iot_source_priority(base_obs, location_key)

    def convert_to_risk_feature_snapshot(
        self,
        obs: NormalizedEnvironmentObservation,
        village_static_data: Dict[str, Any],
        scenario: ScenarioType = ScenarioType.HEAVY_RAIN,
    ) -> Dict[str, Any]:
        """
        Converts NormalizedEnvironmentObservation into the feature_snapshot dict
        expected by calculate_flash_flood_risk().

        Scenario Override Logic:
        - NORMAL: Uses real live API weather (actual current conditions).
        - HEAVY_RAIN / EXTREME_RAIN: Always uses scenario dataset values for rainfall,
          soil saturation, and river level — this is the user's explicit simulation intent.
          Real terrain/geography from live API is still preserved.
        """
        demo_snapshot = get_village_feature_snapshot(village_static_data["id"], scenario)

        # For non-NORMAL scenarios the user is explicitly simulating a disaster event.
        # Scenario dataset values MUST drive the hydro-meteorological inputs regardless
        # of whether the live API returned data. Real weather (e.g. 0mm/h clear sky) would
        # otherwise make HEAVY_RAIN and EXTREME_RAIN look identical to NORMAL.
        if scenario != ScenarioType.NORMAL:
            curr_rf = demo_snapshot["current_rainfall"]
            fc_rf = demo_snapshot["forecast_rainfall"]
            soil_sat = demo_snapshot["soil_saturation"]
            river_lvl = demo_snapshot["river_water_level"]
        elif obs.data_state in [DataSourceState.LIVE, DataSourceState.LIVE_IOT_SENSOR, DataSourceState.LIVE_EXTERNAL_API, DataSourceState.CACHED]:
            # NORMAL scenario: use real current weather from live API
            curr_rf = obs.current_rainfall_mm_hr
            fc_rf = obs.forecast_rainfall_24h_mm
            soil_sat = obs.soil_saturation_pct
            # River level is not provided by weather APIs; use demo baseline for NORMAL
            river_lvl = obs.river_water_level_m if obs.river_water_level_m is not None else demo_snapshot["river_water_level"]
        else:
            # NORMAL scenario, all sources unavailable: fall back to demo dataset
            curr_rf = obs.current_rainfall_mm_hr if obs.current_rainfall_mm_hr is not None else demo_snapshot["current_rainfall"]
            fc_rf = obs.forecast_rainfall_24h_mm if obs.forecast_rainfall_24h_mm is not None else demo_snapshot["forecast_rainfall"]
            soil_sat = obs.soil_saturation_pct if obs.soil_saturation_pct is not None else demo_snapshot["soil_saturation"]
            river_lvl = obs.river_water_level_m if obs.river_water_level_m is not None else demo_snapshot["river_water_level"]

        from app.engine.terrain_engine import terrain_engine_instance
        terrain_detail = terrain_engine_instance.get_village_terrain(village_static_data)

        feature_statuses: Dict[str, DataQualityStatus] = {
            "current_rainfall": DataQualityStatus.OK if curr_rf is not None else DataQualityStatus.MISSING,
            "forecast_rainfall": DataQualityStatus.OK if fc_rf is not None else DataQualityStatus.MISSING,
            "soil_saturation": DataQualityStatus.OK if soil_sat is not None else DataQualityStatus.MISSING,
            "river_water_level": DataQualityStatus.OK if river_lvl is not None else DataQualityStatus.MISSING,
            "slope": DataQualityStatus.OK,
            "flow_accumulation": DataQualityStatus.OK,
        }

        return {
            "village_id": village_static_data.get("id"),
            "village_name": village_static_data.get("name"),
            "elevation": terrain_detail.elevation_m,
            "slope": terrain_detail.slope_deg,
            "flow_accumulation": terrain_detail.flow_accumulation,
            "drainage_proximity_m": village_static_data.get("drainage_proximity_m"),
            "current_rainfall": curr_rf,
            "forecast_rainfall": fc_rf,
            "soil_saturation": soil_sat,
            "river_water_level": river_lvl,
            "rainfall_source": obs.rainfall_source or "OFFLINE_DEMO",
            "soil_source": obs.soil_source or "OFFLINE_DEMO",
            "water_level_source": obs.water_level_source or "OFFLINE_DEMO",
            "terrain_status": terrain_detail.terrain_status,
            "elevation_source": terrain_detail.elevation_source,
            "slope_source": terrain_detail.slope_source,
            "flow_accumulation_source": terrain_detail.flow_accumulation_source,
            "feature_statuses": feature_statuses,
            "timestamp": obs.observation_timestamp,
            "data_state": obs.data_state,
            "source_name": obs.source_name,
        }




    def get_data_quality_report(
        self, current_scenario: ScenarioType = ScenarioType.HEAVY_RAIN
    ) -> OverallDataQualityResponse:
        """
        Generates overall structured data quality health report across input adapters.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # Test default central Himalayan watershed coordinates (Pipalkoti / Rudraprayag reach)
        test_obs = self.get_normalized_observation(
            latitude=30.4300,
            longitude=79.4300,
            location_key="VIL-001",
            scenario=current_scenario,
            force_offline=False,
        )

        overall_state = test_obs.data_state
        data_mode_label = (
            "LIVE API METEOROLOGICAL INGESTION ACTIVE"
            if overall_state == DataSourceState.LIVE
            else "CACHED OBSERVATIONS ACTIVE"
            if overall_state == DataSourceState.CACHED
            else "OFFLINE DEMONSTRATION MODE — SIH DATASET"
        )

        sources_report = [
            SourceQualityReport(
                source_name=self.live_adapter.name,
                source_type=self.live_adapter.source_type,
                state=overall_state if overall_state == DataSourceState.LIVE else DataSourceState.UNAVAILABLE,
                quality=test_obs.quality_status if overall_state == DataSourceState.LIVE else DataQualityLevel.DEGRADED,
                timestamp=test_obs.source_timestamp,
                age_minutes=round(test_obs.freshness_seconds / 60.0, 1),
                missing_fields=test_obs.missing_fields if overall_state == DataSourceState.LIVE else ["network_access"],
                validation_warnings=test_obs.validation_warnings if overall_state == DataSourceState.LIVE else ["Live API endpoint unreachable or using demo mode"],
            ),
            SourceQualityReport(
                source_name=self.offline_adapter.name,
                source_type=self.offline_adapter.source_type,
                state=DataSourceState.OFFLINE_DEMO,
                quality=DataQualityLevel.GOOD,
                timestamp=now_iso,
                age_minutes=0.0,
                missing_fields=[],
                validation_warnings=["SIH Deterministic Scenario Dataset Active"],
            )
        ]

        return OverallDataQualityResponse(
            overall_state=overall_state,
            active_source=test_obs.source_name,
            data_mode=data_mode_label,
            total_sources=len(sources_report),
            sources=sources_report,
            last_validated=now_iso,
        )


# Global Singleton Pipeline Instance
pipeline_instance = DataIngestionPipeline()
