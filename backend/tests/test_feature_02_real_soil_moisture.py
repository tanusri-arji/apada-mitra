"""
Feature 2 — Real Soil Moisture Data Flow Regression & Edge Mode Tests.
Verifies end-to-end preservation of real Open-Meteo soil moisture from adapter to snapshot,
risk engine, and XAI factor contributions without synthetic demo blending.
"""
import pytest
from app.adapters.open_meteo import OpenMeteoRainfallAdapter
from app.data_pipeline import DataIngestionPipeline
from app.data.dataset import DEMO_VILLAGES, get_village_feature_snapshot
from app.engine.risk_engine import calculate_flash_flood_risk
from app.engine.explainability import calculate_explainability_factors
from app.models.domain import (
    NormalizedEnvironmentObservation,
    DataSourceState,
    DataQualityLevel,
    ScenarioType,
)

PIPALKOTI = DEMO_VILLAGES[0]


def make_mock_observation(soil_sat_pct: float | None, data_state: DataSourceState = DataSourceState.LIVE) -> NormalizedEnvironmentObservation:
    """Helper to construct a controlled NormalizedEnvironmentObservation."""
    return NormalizedEnvironmentObservation(
        latitude=PIPALKOTI["latitude"],
        longitude=PIPALKOTI["longitude"],
        observation_timestamp="2026-09-04T12:00:00Z",
        current_rainfall_mm_hr=0.5,
        forecast_rainfall_24h_mm=10.0,
        soil_saturation_pct=soil_sat_pct,
        river_water_level_m=None,
        discharge_cumecs=None,
        source_name="Open-Meteo Weather API",
        source_type="METEOROLOGICAL_API",
        source_timestamp="2026-09-04T12:00:00Z",
        data_state=data_state,
        quality_status=DataQualityLevel.GOOD,
        freshness_seconds=0.0,
    )


def test_open_meteo_adapter_normalizes_soil_moisture():
    """Verifies Open-Meteo soil_moisture_0_to_7cm volumetric list converts to saturation percentage."""
    adapter = OpenMeteoRainfallAdapter()
    raw_payload = {
        "current": {"precipitation": 0.0, "time": "2026-09-04T12:00:00Z"},
        "hourly": {
            "precipitation": [0.0] * 24,
            "soil_moisture_0_to_7cm": [0.235] * 24  # 0.235 m3/m3 -> (0.235/0.50)*100 = 47.0%
        },
        "_fetch_timestamp": "2026-09-04T12:00:00Z"
    }

    norm = adapter.normalize(raw_payload, PIPALKOTI["latitude"], PIPALKOTI["longitude"])
    assert norm.soil_saturation_pct == 47.0
    assert norm.data_state == DataSourceState.LIVE


def test_snapshot_preserves_low_soil_moisture():
    """Verifies low soil moisture (15.0%) passes through without demo max blending under HEAVY_RAIN."""
    pipeline = DataIngestionPipeline()
    obs = make_mock_observation(soil_sat_pct=15.0)

    snapshot = pipeline.convert_to_risk_feature_snapshot(obs, PIPALKOTI, scenario=ScenarioType.HEAVY_RAIN)
    assert snapshot["soil_saturation"] == 15.0

    demo_snap = get_village_feature_snapshot("VIL-001", ScenarioType.HEAVY_RAIN)
    assert snapshot["soil_saturation"] != demo_snap["soil_saturation"]


def test_snapshot_preserves_high_soil_moisture():
    """Verifies high soil moisture (92.0%) passes through without demo blending under HEAVY_RAIN."""
    pipeline = DataIngestionPipeline()
    obs = make_mock_observation(soil_sat_pct=92.0)

    snapshot = pipeline.convert_to_risk_feature_snapshot(obs, PIPALKOTI, scenario=ScenarioType.HEAVY_RAIN)
    assert snapshot["soil_saturation"] == 92.0


def test_snapshot_preserves_live_soil_moisture_across_all_scenarios():
    """Verifies live soil moisture (25.0%) is preserved under NORMAL, HEAVY_RAIN, and EXTREME_RAIN."""
    pipeline = DataIngestionPipeline()
    obs = make_mock_observation(soil_sat_pct=25.0)

    for scenario in [ScenarioType.NORMAL, ScenarioType.HEAVY_RAIN, ScenarioType.EXTREME_RAIN]:
        snapshot = pipeline.convert_to_risk_feature_snapshot(obs, PIPALKOTI, scenario=scenario)
        assert snapshot["soil_saturation"] == 25.0, f"Failed for scenario {scenario}"


def test_risk_engine_and_xai_use_same_live_soil_moisture():
    """Verifies end-to-end flow from snapshot to risk engine raw_features and XAI factor raw_value."""
    pipeline = DataIngestionPipeline()
    obs = make_mock_observation(soil_sat_pct=40.0)

    snapshot = pipeline.convert_to_risk_feature_snapshot(obs, PIPALKOTI, scenario=ScenarioType.HEAVY_RAIN)
    risk_res = calculate_flash_flood_risk(snapshot)

    assert risk_res["raw_features"]["soil_saturation"] == 40.0

    factors = calculate_explainability_factors(
        raw_features=risk_res["raw_features"],
        normalized_features=risk_res["normalized_features"],
        total_risk_score=risk_res["flash_flood_risk_score"],
    )

    soil_factor = next(f for f in factors if f.feature_key == "soil_saturation")
    assert soil_factor.raw_value == 40.0
    assert soil_factor.normalized_value == 0.40  # 40.0 / 100.0
    assert soil_factor.contribution_points == 6.0  # 0.40 * 0.15 * 100 = 6.0 pts


def test_missing_field_in_successful_live_observation_stays_missing():
    """Verifies missing live soil moisture (None) falls back to deterministic demo snapshot."""
    pipeline = DataIngestionPipeline()
    obs = make_mock_observation(soil_sat_pct=None)

    snapshot = pipeline.convert_to_risk_feature_snapshot(obs, PIPALKOTI, scenario=ScenarioType.HEAVY_RAIN)
    # Successful live source + missing soil field must not import synthetic scenario data.
    assert snapshot["soil_saturation"] is None
