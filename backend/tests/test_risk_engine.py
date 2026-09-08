"""
Unit and integration tests for APADA MITRA Risk Engine & Scenarios.
Performs verification of bounds, monotonicity, missing feature handling, and confidence.
"""
import pytest
from app.engine.risk_engine import calculate_flash_flood_risk, classify_risk_level
from app.models.domain import RiskLevel, ScenarioType, DataQualityStatus


def get_base_snapshot():
    return {
        "current_rainfall": 20.0,
        "forecast_rainfall": 50.0,
        "soil_saturation": 50.0,
        "river_water_level": 1.2,
        "slope": 20.0,
        "flow_accumulation": 3.0,
        "feature_statuses": {},
    }


def test_risk_score_and_probability_bounds():
    """Requirement 1, 2, 3: Verify risk score (0-100), probability (0-1), confidence (0-100)."""
    snapshot = get_base_snapshot()
    res = calculate_flash_flood_risk(snapshot)

    assert 0.0 <= res["flash_flood_risk_score"] <= 100.0
    assert 0.0 <= res["risk_probability"] <= 1.0
    assert 0.0 <= res["confidence"] <= 100.0


def test_higher_rainfall_increases_risk():
    """Requirement 4: Higher rainfall must not reduce risk when other variables are constant."""
    base = get_base_snapshot()
    base["current_rainfall"] = 10.0
    res_low = calculate_flash_flood_risk(base)

    high = get_base_snapshot()
    high["current_rainfall"] = 80.0
    res_high = calculate_flash_flood_risk(high)

    assert res_high["flash_flood_risk_score"] >= res_low["flash_flood_risk_score"]
    assert res_high["risk_probability"] >= res_low["risk_probability"]


def test_higher_soil_saturation_increases_risk():
    """Requirement 5: Higher soil saturation must not reduce risk."""
    base = get_base_snapshot()
    base["soil_saturation"] = 30.0
    res_low = calculate_flash_flood_risk(base)

    high = get_base_snapshot()
    high["soil_saturation"] = 95.0
    res_high = calculate_flash_flood_risk(high)

    assert res_high["flash_flood_risk_score"] >= res_low["flash_flood_risk_score"]


def test_higher_flow_accumulation_increases_risk():
    """Requirement 6: Higher flow accumulation must increase risk."""
    base = get_base_snapshot()
    base["flow_accumulation"] = 1.5
    res_low = calculate_flash_flood_risk(base)

    high = get_base_snapshot()
    high["flow_accumulation"] = 4.8
    res_high = calculate_flash_flood_risk(high)

    assert res_high["flash_flood_risk_score"] > res_low["flash_flood_risk_score"]


def test_missing_feature_handling_and_confidence_drop():
    """Requirement 7 & 8: Missing feature does not crash and reduces confidence."""
    snapshot = get_base_snapshot()
    res_full = calculate_flash_flood_risk(snapshot)

    # Missing soil_saturation
    snapshot_missing = get_base_snapshot()
    snapshot_missing["soil_saturation"] = None
    snapshot_missing["feature_statuses"] = {"soil_saturation": DataQualityStatus.MISSING}
    res_missing = calculate_flash_flood_risk(snapshot_missing)

    assert "soil_saturation" in res_missing["missing_features"]
    assert res_missing["confidence"] < res_full["confidence"]
    assert 0.0 <= res_missing["flash_flood_risk_score"] <= 100.0


def test_risk_level_classification_thresholds():
    """Requirement 9: Risk level classification correctness."""
    assert classify_risk_level(10.0) == RiskLevel.LOW
    assert classify_risk_level(35.0) == RiskLevel.MODERATE
    assert classify_risk_level(60.0) == RiskLevel.HIGH
    assert classify_risk_level(85.0) == RiskLevel.CRITICAL
