"""
Unit Tests for Real Data Adapters, Data Quality Engine, and Ingestion Pipeline.
"""
from datetime import datetime, timezone, timedelta
from app.models.domain import (
    NormalizedEnvironmentObservation,
    DataSourceState,
    DataQualityLevel,
    ScenarioType,
)
from app.adapters.open_meteo import OpenMeteoRainfallAdapter
from app.adapters.offline_demo import OfflineDemoAdapter
from app.engine.data_quality import DataQualityEngine
from app.data_pipeline import DataIngestionPipeline


def test_offline_demo_adapter_normalization():
    adapter = OfflineDemoAdapter(scenario=ScenarioType.HEAVY_RAIN)
    raw = adapter.fetch(30.4300, 79.4300)
    assert raw is not None
    obs = adapter.normalize(raw, 30.4300, 79.4300)
    assert obs.data_state == DataSourceState.OFFLINE_DEMO
    assert obs.current_rainfall_mm_hr is not None
    assert obs.source_name == "APADA MITRA Himalayan Demo Dataset"


def test_open_meteo_adapter_structure():
    adapter = OpenMeteoRainfallAdapter()
    raw = {
        "current": {"precipitation": 12.5, "time": "2026-09-04T12:00:00Z"},
        "hourly": {
            "precipitation": [2.0] * 24,
            "soil_moisture_0_to_7cm": [0.40] * 24,
        },
        "_fetch_timestamp": "2026-09-04T12:00:00Z",
    }
    obs = adapter.normalize(raw, 30.4300, 79.4300)
    assert obs.data_state == DataSourceState.LIVE
    assert obs.current_rainfall_mm_hr == 12.5
    assert obs.forecast_rainfall_24h_mm == 48.0
    assert obs.soil_saturation_pct == 80.0  # 0.40 / 0.50 * 100%


def test_data_quality_negative_values_rejected():
    now_iso = datetime.now(timezone.utc).isoformat()
    obs = NormalizedEnvironmentObservation(
        latitude=30.43,
        longitude=79.43,
        observation_timestamp=now_iso,
        current_rainfall_mm_hr=-15.0,  # Invalid negative
        forecast_rainfall_24h_mm=50.0,
        soil_saturation_pct=-10.0,    # Invalid negative
        river_water_level_m=1.2,
        source_name="Test Source",
        source_type="TEST",
        source_timestamp=now_iso,
    )
    val_obs = DataQualityEngine.validate_observation(obs)
    assert val_obs.current_rainfall_mm_hr is None
    assert val_obs.soil_saturation_pct is None
    assert "current_rainfall_mm_hr" in val_obs.missing_fields
    assert len(val_obs.validation_warnings) >= 2


def test_data_quality_overflow_capped():
    now_iso = datetime.now(timezone.utc).isoformat()
    obs = NormalizedEnvironmentObservation(
        latitude=30.43,
        longitude=79.43,
        observation_timestamp=now_iso,
        current_rainfall_mm_hr=450.0,  # Exceeds max physical bound (300.0)
        forecast_rainfall_24h_mm=1200.0, # Exceeds max 1000.0
        soil_saturation_pct=150.0,    # Exceeds max 100.0%
        river_water_level_m=20.0,     # Exceeds max 15.0m
        source_name="Test Source",
        source_type="TEST",
        source_timestamp=now_iso,
    )
    val_obs = DataQualityEngine.validate_observation(obs)
    assert val_obs.current_rainfall_mm_hr == 300.0
    assert val_obs.forecast_rainfall_24h_mm == 1000.0
    assert val_obs.soil_saturation_pct == 100.0
    assert val_obs.river_water_level_m == 15.0
    assert len(val_obs.validation_warnings) >= 4


def test_data_quality_staleness_detection():
    old_time = (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat()
    obs = NormalizedEnvironmentObservation(
        latitude=30.43,
        longitude=79.43,
        observation_timestamp=old_time,
        current_rainfall_mm_hr=10.0,
        forecast_rainfall_24h_mm=30.0,
        soil_saturation_pct=50.0,
        river_water_level_m=1.2,
        source_name="Test Source",
        source_type="TEST",
        source_timestamp=old_time,
        freshness_seconds=14400.0,  # 4 hours old
        data_state=DataSourceState.LIVE,
    )
    val_obs = DataQualityEngine.validate_observation(obs)
    assert val_obs.data_state == DataSourceState.CACHED
    assert val_obs.quality_status == DataQualityLevel.DEGRADED
    assert any("stale" in w for w in val_obs.validation_warnings)


def test_pipeline_cached_state():
    pipeline = DataIngestionPipeline()
    now_iso = datetime.now(timezone.utc).isoformat()
    
    cached_obs = NormalizedEnvironmentObservation(
        latitude=30.43,
        longitude=79.43,
        observation_timestamp=now_iso,
        current_rainfall_mm_hr=25.0,
        forecast_rainfall_24h_mm=80.0,
        soil_saturation_pct=70.0,
        river_water_level_m=1.5,
        source_name="Live API Provider",
        source_type="METEOROLOGICAL_API",
        source_timestamp=now_iso,
        data_state=DataSourceState.LIVE,
    )
    pipeline.observation_cache["VIL-001"] = cached_obs

    # Force offline fetch so pipeline falls back to cache
    res = pipeline.get_normalized_observation(
        30.43, 79.43, "VIL-001", scenario=ScenarioType.HEAVY_RAIN, force_offline=False
    )
    assert res is not None
    assert res.current_rainfall_mm_hr is not None


def test_pipeline_risk_snapshot_translation():
    pipeline = DataIngestionPipeline()
    now_iso = datetime.now(timezone.utc).isoformat()
    obs = NormalizedEnvironmentObservation(
        latitude=30.43,
        longitude=79.43,
        observation_timestamp=now_iso,
        current_rainfall_mm_hr=65.0,
        forecast_rainfall_24h_mm=120.0,
        soil_saturation_pct=85.0,
        river_water_level_m=1.8,
        source_name="Open-Meteo",
        source_type="METEOROLOGICAL_API",
        source_timestamp=now_iso,
        data_state=DataSourceState.LIVE,
    )
    village_static = {
        "id": "VIL-001",
        "name": "Pipalkoti",
        "elevation": 1260.0,
        "slope": 28.5,
        "flow_accumulation": 4.2,
        "drainage_proximity_m": 85.0,
    }

    snapshot = pipeline.convert_to_risk_feature_snapshot(obs, village_static, ScenarioType.HEAVY_RAIN)
    assert snapshot["current_rainfall"] == 65.0
    assert snapshot["forecast_rainfall"] == 120.0
    assert snapshot["soil_saturation"] == 85.0
    assert snapshot["river_water_level"] == 1.8
    assert snapshot["slope"] > 0.0
    assert snapshot["feature_statuses"]["current_rainfall"] == "OK"



from fastapi.testclient import TestClient
from app.main import app

def test_data_quality_endpoint():
    client = TestClient(app)
    res = client.get("/api/data-quality")
    assert res.status_code == 200
    data = res.json()
    assert "overall_state" in data
    assert "active_source" in data
    assert "data_mode" in data
    assert "sources" in data
    assert len(data["sources"]) >= 2

