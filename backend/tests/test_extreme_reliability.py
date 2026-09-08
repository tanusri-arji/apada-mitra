"""
Extreme Failure Testing Suite for APADA MITRA Backend.
Verifies all 20 edge-case and extreme failure conditions for high reliability.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.domain import ScenarioType, RiskLevel, RoadStatus
from app.engine.risk_engine import calculate_flash_flood_risk, classify_risk_level
from app.engine.landslide_engine import calculate_landslide_risk
from app.engine.routing_engine import calculate_safest_route
from app.engine.shelter_engine import recommend_safest_shelter
import app.api.routes as routes

client = TestClient(app)


def test_extreme_01_rainfall_zero():
    """Case 1: Rainfall = 0 mm/hr does not crash and produces valid low risk."""
    snapshot = {
        "current_rainfall": 0.0,
        "forecast_rainfall": 0.0,
        "soil_saturation": 10.0,
        "river_water_level": 1.0,
        "slope": 5.0,
        "flow_accumulation": 1.0,
        "feature_statuses": {},
    }
    res = calculate_flash_flood_risk(snapshot)
    assert 0.0 <= res["flash_flood_risk_score"] <= 100.0
    assert res["risk_level"] == RiskLevel.LOW


def test_extreme_02_rainfall_max():
    """Case 2: Rainfall at maximum allowed value (200 mm/hr) stays within [0, 100]."""
    payload = {
        "current_rainfall_mm_hr": 200.0,
        "forecast_rainfall_24h_mm": 500.0,
        "soil_saturation_pct": 100.0,
        "river_level_m": 15.0,
        "selected_village_id": "VIL-001",
    }
    res = client.post("/api/simulation/what-if", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["simulated_villages_flood"][0]["flash_flood_risk_score"] <= 100.0


def test_extreme_03_forecast_zero():
    """Case 3: Forecast = 0 mm produces valid calculation."""
    snapshot = {
        "current_rainfall": 5.0,
        "forecast_rainfall": 0.0,
        "soil_saturation": 20.0,
        "river_water_level": 1.0,
        "slope": 10.0,
        "flow_accumulation": 2.0,
        "feature_statuses": {},
    }
    res = calculate_flash_flood_risk(snapshot)
    assert 0.0 <= res["flash_flood_risk_score"] <= 100.0


def test_extreme_04_forecast_max():
    """Case 4: Forecast = 500 mm produces valid high score."""
    snapshot = {
        "current_rainfall": 50.0,
        "forecast_rainfall": 500.0,
        "soil_saturation": 80.0,
        "river_water_level": 2.5,
        "slope": 25.0,
        "flow_accumulation": 4.0,
        "feature_statuses": {},
    }
    res = calculate_flash_flood_risk(snapshot)
    assert 0.0 <= res["flash_flood_risk_score"] <= 100.0


def test_extreme_05_soil_saturation_zero():
    """Case 5: Soil saturation = 0% does not crash."""
    snapshot = {
        "current_rainfall": 10.0,
        "forecast_rainfall": 20.0,
        "soil_saturation": 0.0,
        "river_water_level": 1.0,
        "slope": 15.0,
        "flow_accumulation": 2.0,
        "feature_statuses": {},
    }
    res = calculate_flash_flood_risk(snapshot)
    assert 0.0 <= res["flash_flood_risk_score"] <= 100.0


def test_extreme_06_soil_saturation_max():
    """Case 6: Soil saturation = 100% calculates properly."""
    snapshot = {
        "current_rainfall": 40.0,
        "forecast_rainfall": 100.0,
        "soil_saturation": 100.0,
        "river_water_level": 2.0,
        "slope": 30.0,
        "flow_accumulation": 4.0,
        "feature_statuses": {},
    }
    res = calculate_flash_flood_risk(snapshot)
    assert 0.0 <= res["flash_flood_risk_score"] <= 100.0


def test_extreme_07_river_stage_zero():
    """Case 7: River stage = 0 factor handles bounds gracefully."""
    snapshot = {
        "current_rainfall": 5.0,
        "forecast_rainfall": 10.0,
        "soil_saturation": 20.0,
        "river_water_level": 0.0,
        "slope": 10.0,
        "flow_accumulation": 1.0,
        "feature_statuses": {},
    }
    res = calculate_flash_flood_risk(snapshot)
    assert 0.0 <= res["flash_flood_risk_score"] <= 100.0


def test_extreme_08_river_stage_max():
    """Case 8: River stage = 15m handles bounds properly."""
    payload = {
        "current_rainfall_mm_hr": 50.0,
        "forecast_rainfall_24h_mm": 100.0,
        "soil_saturation_pct": 80.0,
        "river_level_m": 15.0,
        "selected_village_id": "VIL-001",
    }
    res = client.post("/api/simulation/what-if", json=payload)
    assert res.status_code == 200


def test_extreme_09_multiple_missing_data():
    """Case 9: Multiple missing features degrade confidence without crashing."""
    snapshot = {
        "current_rainfall": None,
        "forecast_rainfall": None,
        "soil_saturation": 50.0,
        "river_water_level": 1.2,
        "slope": 20.0,
        "flow_accumulation": 3.0,
        "feature_statuses": {
            "current_rainfall": "MISSING",
            "forecast_rainfall": "MISSING",
        },
    }
    res = calculate_flash_flood_risk(snapshot)
    assert len(res["missing_features"]) == 2
    assert res["confidence"] < 100.0
    assert 0.0 <= res["flash_flood_risk_score"] <= 100.0


def test_extreme_10_invalid_scenario():
    """Case 10: Invalid scenario payload returns 422 Unprocessable Entity."""
    res = client.post("/api/scenario", json={"scenario": "INVALID_SCENARIO_NAME"})
    assert res.status_code == 422


def test_extreme_11_invalid_village_id():
    """Case 11: Invalid village ID returns HTTP 404 Not Found."""
    res = client.get("/api/villages/NON_EXISTENT_VILLAGE_ID")
    assert res.status_code == 404


def test_extreme_12_invalid_shelter_recommendation_id():
    """Case 12: Invalid village ID for shelter recommendation returns 400 Bad Request."""
    res = client.get("/api/evacuation/shelter-recommendation/INVALID_ID")
    assert res.status_code == 400


def test_extreme_13_invalid_route_request():
    """Case 13: Invalid origin or destination in route calculation returns 400."""
    res = client.post(
        "/api/evacuation/route",
        json={"origin_village_id": "INVALID", "destination_shelter_id": "INVALID"},
    )
    assert res.status_code == 400


def test_extreme_14_full_shelter_rejection():
    """Case 14: Capacity constraint ensures over-capacity shelters are never recommended."""
    rec = recommend_safest_shelter("VIL-001", ScenarioType.NORMAL)
    assert rec.recommended_shelter.available_capacity > 0


def test_extreme_15_extreme_road_blockages_handling():
    """Case 15: Dijkstra router handles blocked routes by finding alternative paths or raising ValueError."""
    # Under EXTREME_RAIN, ROAD-010 is BLOCKED
    route = calculate_safest_route("VIL-011", "SH-04", ScenarioType.EXTREME_RAIN)
    assert "ROAD-010" not in route.road_segment_ids


def test_extreme_16_extreme_rainfall_what_if():
    """Case 16: Extreme rainfall (cloudburst) computes valid response."""
    payload = {
        "current_rainfall_mm_hr": 200.0,
        "forecast_rainfall_24h_mm": 500.0,
        "soil_saturation_pct": 100.0,
        "river_level_m": 15.0,
    }
    res = client.post("/api/simulation/what-if", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["preset_used"] == "EXTREME CLOUDBURST"


def test_extreme_17_repeated_scenario_switching():
    """Case 17: Repeated scenario toggles remain deterministic."""
    for _ in range(3):
        client.post("/api/scenario", json={"scenario": "NORMAL"})
        v1 = client.get("/api/villages/VIL-001").json()["flash_flood_risk_score"]
        client.post("/api/scenario", json={"scenario": "EXTREME_RAIN"})
        v2 = client.get("/api/villages/VIL-001").json()["flash_flood_risk_score"]
        assert v2 > v1


def test_extreme_18_what_if_followed_by_normal_scenario():
    """Case 18: Running What-If simulation leaves normal scenario intact."""
    client.post("/api/scenario", json={"scenario": "NORMAL"})
    client.post(
        "/api/simulation/what-if",
        json={
            "current_rainfall_mm_hr": 150.0,
            "forecast_rainfall_24h_mm": 350.0,
            "soil_saturation_pct": 95.0,
            "river_level_m": 10.0,
        },
    )
    sc = client.get("/api/scenario").json()
    assert sc["scenario"] == "NORMAL"


def test_extreme_19_what_if_state_immutability():
    """Case 19: Global active scenario variable is unchanged during What-If."""
    initial = routes.CURRENT_SCENARIO
    client.post(
        "/api/simulation/what-if",
        json={
            "current_rainfall_mm_hr": 180.0,
            "forecast_rainfall_24h_mm": 400.0,
            "soil_saturation_pct": 90.0,
            "river_level_m": 12.0,
        },
    )
    assert routes.CURRENT_SCENARIO == initial


def test_extreme_20_non_existent_endpoint():
    """Case 20: Non-existent endpoint returns 404 cleanly."""
    res = client.get("/api/non_existent_route")
    assert res.status_code == 404
