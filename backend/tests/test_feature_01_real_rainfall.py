"""
Feature 1 regression tests: live rainfall must reach the risk engine unchanged.
"""
from datetime import datetime, timezone

from app.adapters.open_meteo import OpenMeteoRainfallAdapter
from app.data_pipeline import DataIngestionPipeline
from app.engine.explainability import calculate_explainability_factors
from app.engine.risk_engine import calculate_flash_flood_risk
from app.models.domain import DataSourceState, NormalizedEnvironmentObservation, ScenarioType


VILLAGE_STATIC = {
    "id": "VIL-001",
    "name": "Pipalkoti",
    "elevation": 1260.0,
    "slope": 28.5,
    "flow_accumulation": 4.2,
    "drainage_proximity_m": 85.0,
}


def _live_obs(current_rainfall_mm_hr: float, forecast_rainfall_24h_mm: float = 11.2) -> NormalizedEnvironmentObservation:
    now_iso = datetime.now(timezone.utc).isoformat()
    return NormalizedEnvironmentObservation(
        latitude=30.43,
        longitude=79.43,
        observation_timestamp=now_iso,
        current_rainfall_mm_hr=current_rainfall_mm_hr,
        forecast_rainfall_24h_mm=forecast_rainfall_24h_mm,
        soil_saturation_pct=82.4,
        river_water_level_m=None,
        source_name="Open-Meteo Weather API",
        source_type="METEOROLOGICAL_API",
        source_timestamp=now_iso,
        data_state=DataSourceState.LIVE,
    )


def test_open_meteo_normalize_preserves_raw_precipitation_half_mm():
    adapter = OpenMeteoRainfallAdapter()
    raw = {
        "current": {"precipitation": 0.5, "time": "2026-09-04T11:30"},
        "hourly": {
            "precipitation": [0.5] + [0.0] * 23,
            "soil_moisture_0_to_7cm": [0.412] * 24,
        },
    }
    obs = adapter.normalize(raw, 30.4300, 79.4300)
    assert obs.current_rainfall_mm_hr == 0.5
    assert obs.forecast_rainfall_24h_mm == 0.5


def test_snapshot_preserves_live_current_rainfall_0_5_under_heavy_rain():
    pipeline = DataIngestionPipeline()
    snapshot = pipeline.convert_to_risk_feature_snapshot(
        _live_obs(0.5), VILLAGE_STATIC, ScenarioType.HEAVY_RAIN
    )
    assert snapshot["current_rainfall"] == 0.5
    assert snapshot["current_rainfall"] != 56.0


def test_snapshot_preserves_live_current_rainfall_10_no_hardcoded_conversion():
    pipeline = DataIngestionPipeline()
    snapshot = pipeline.convert_to_risk_feature_snapshot(
        _live_obs(10.0), VILLAGE_STATIC, ScenarioType.HEAVY_RAIN
    )
    assert snapshot["current_rainfall"] == 10.0


def test_snapshot_preserves_live_rainfall_across_all_scenarios():
    pipeline = DataIngestionPipeline()
    for scenario in (ScenarioType.NORMAL, ScenarioType.HEAVY_RAIN, ScenarioType.EXTREME_RAIN):
        snapshot = pipeline.convert_to_risk_feature_snapshot(
            _live_obs(0.5), VILLAGE_STATIC, scenario
        )
        assert snapshot["current_rainfall"] == 0.5, f"scenario {scenario} mutated rainfall"


def test_risk_engine_and_xai_use_same_live_rainfall():
    pipeline = DataIngestionPipeline()
    snapshot = pipeline.convert_to_risk_feature_snapshot(
        _live_obs(0.5), VILLAGE_STATIC, ScenarioType.HEAVY_RAIN
    )
    risk_res = calculate_flash_flood_risk(snapshot)

    assert risk_res["raw_features"]["current_rainfall"] == 0.5

    factors = calculate_explainability_factors(
        raw_features=risk_res["raw_features"],
        normalized_features=risk_res["normalized_features"],
        total_risk_score=risk_res["flash_flood_risk_score"],
    )
    rain_factor = next(f for f in factors if f.feature_key == "current_rainfall")
    assert rain_factor.raw_value == 0.5
    assert rain_factor.raw_value == snapshot["current_rainfall"]
    assert rain_factor.raw_value == risk_res["raw_features"]["current_rainfall"]
    # 0.5 mm/h / FEATURE_BOUNDS 100 mm/h → 0.005; * weight 0.25 * 100 = 0.125 → 0.12
    assert rain_factor.normalized_value == 0.005
    assert rain_factor.contribution_points == 0.12


def test_missing_field_in_successful_live_observation_stays_missing():
    pipeline = DataIngestionPipeline()
    now_iso = datetime.now(timezone.utc).isoformat()
    obs = NormalizedEnvironmentObservation(
        latitude=30.43,
        longitude=79.43,
        observation_timestamp=now_iso,
        current_rainfall_mm_hr=None,
        forecast_rainfall_24h_mm=None,
        soil_saturation_pct=82.4,
        river_water_level_m=None,
        source_name="Open-Meteo Weather API",
        source_type="METEOROLOGICAL_API",
        source_timestamp=now_iso,
        data_state=DataSourceState.LIVE,
        missing_fields=["current_rainfall_mm_hr", "forecast_rainfall_24h_mm"],
    )
    snapshot = pipeline.convert_to_risk_feature_snapshot(obs, VILLAGE_STATIC, ScenarioType.HEAVY_RAIN)
    # A successful live observation with missing fields must not silently import
    # synthetic scenario values. The risk engine handles missing inputs explicitly.
    assert snapshot["current_rainfall"] is None
    assert snapshot["forecast_rainfall"] is None
