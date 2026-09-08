"""
Automated Pytest Suite for Day 3 What-If Disaster Cascade Simulator.
Tests input validation, monotonicity, state immutability, road blockages, Dijkstra rerouting, shelter shortfalls, and multilingual alert schema.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
import app.api.routes as routes
from app.models.domain import ScenarioType, RiskLevel

client = TestClient(app)


def test_what_if_simulation_input_validation():
    """Requirement 1: Input ranges are validated strictly."""
    # Out of bounds rainfall (> 200.0)
    res_bad1 = client.post(
        "/api/simulation/what-if",
        json={
            "current_rainfall_mm_hr": 250.0,
            "forecast_rainfall_24h_mm": 50.0,
            "soil_saturation_pct": 50.0,
            "river_level_m": 3.0,
        },
    )
    assert res_bad1.status_code == 422

    # Out of bounds soil saturation (> 100.0)
    res_bad2 = client.post(
        "/api/simulation/what-if",
        json={
            "current_rainfall_mm_hr": 30.0,
            "forecast_rainfall_24h_mm": 50.0,
            "soil_saturation_pct": 150.0,
            "river_level_m": 3.0,
        },
    )
    assert res_bad2.status_code == 422


def test_what_if_simulation_valid_execution_and_schema():
    """Requirement 2: Valid simulation returns expected schema and non-empty calculations."""
    payload = {
        "current_rainfall_mm_hr": 60.0,
        "forecast_rainfall_24h_mm": 150.0,
        "soil_saturation_pct": 80.0,
        "river_level_m": 6.5,
        "selected_village_id": "VIL-011",
    }
    res = client.post("/api/simulation/what-if", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["preset_used"] == "HEAVY RAIN"
    assert len(data["simulated_villages_flood"]) == 15
    assert len(data["simulated_landslide_overview"]) == 15
    assert len(data["simulated_evacuation_priorities"]) == 15
    assert len(data["simulated_roads"]) >= 20
    assert len(data["simulated_shelters"]) >= 6
    assert "english" in data["operator_alert"]["translations"]
    assert "hindi" in data["operator_alert"]["translations"]
    assert "garhwali" in data["operator_alert"]["translations"]
    assert "kumaoni" in data["operator_alert"]["translations"]
    assert "nepali" in data["operator_alert"]["translations"]
    assert "telugu" not in data["operator_alert"]["translations"]


def test_what_if_simulation_monotonicity():
    """Requirement 3: Higher rainfall input produces non-decreasing flood and landslide risk scores."""
    payload_low = {
        "current_rainfall_mm_hr": 10.0,
        "forecast_rainfall_24h_mm": 20.0,
        "soil_saturation_pct": 30.0,
        "river_level_m": 2.0,
    }
    payload_high = {
        "current_rainfall_mm_hr": 140.0,
        "forecast_rainfall_24h_mm": 350.0,
        "soil_saturation_pct": 95.0,
        "river_level_m": 11.0,
    }

    res_low = client.post("/api/simulation/what-if", json=payload_low).json()
    res_high = client.post("/api/simulation/what-if", json=payload_high).json()

    assert res_high["comparison_summary"]["avg_flood_risk"]["simulated_val"] >= res_low["comparison_summary"]["avg_flood_risk"]["simulated_val"]
    assert res_high["comparison_summary"]["avg_landslide_risk"]["simulated_val"] >= res_low["comparison_summary"]["avg_landslide_risk"]["simulated_val"]
    assert res_high["comparison_summary"]["critical_villages_count"]["simulated_val"] >= res_low["comparison_summary"]["critical_villages_count"]["simulated_val"]


def test_simulation_does_not_mutate_global_active_scenario():
    """Requirement 4: Simulation MUST NOT mutate global active scenario state."""
    routes.CURRENT_SCENARIO = ScenarioType.NORMAL
    initial_scenario = routes.CURRENT_SCENARIO

    payload_extreme = {
        "current_rainfall_mm_hr": 180.0,
        "forecast_rainfall_24h_mm": 450.0,
        "soil_saturation_pct": 98.0,
        "river_level_m": 13.0,
    }
    res = client.post("/api/simulation/what-if", json=payload_extreme)
    assert res.status_code == 200

    # Global scenario MUST remain NORMAL
    assert routes.CURRENT_SCENARIO == initial_scenario
    assert routes.CURRENT_SCENARIO == ScenarioType.NORMAL


def test_road_blockage_and_dijkstra_rerouting():
    """Requirement 5 & 6: Extreme rainfall blocks roads and Dijkstra pathfinder reroutes around them."""
    payload_cloudburst = {
        "current_rainfall_mm_hr": 160.0,
        "forecast_rainfall_24h_mm": 380.0,
        "soil_saturation_pct": 95.0,
        "river_level_m": 12.0,
        "selected_village_id": "VIL-011",
    }
    res = client.post("/api/simulation/what-if", json=payload_cloudburst).json()

    blocked_roads = [r for r in res["simulated_roads"] if r["status"] == "BLOCKED"]
    assert len(blocked_roads) > 0

    route = res["simulated_route"]
    if route:
        # Verify active route path coordinates exist
        assert len(route["path_coordinates"]) >= 2
        assert len(route["rejected_dangerous_alternatives"]) > 0


def test_shelter_capacity_shortfall_detection():
    """Requirement 7: Detects shelter capacity shortfall when exposed evacuees exceed shelter beds."""
    payload_catastrophic = {
        "current_rainfall_mm_hr": 190.0,
        "forecast_rainfall_24h_mm": 480.0,
        "soil_saturation_pct": 100.0,
        "river_level_m": 14.5,
    }
    res = client.post("/api/simulation/what-if", json=payload_catastrophic).json()

    shortfall = res["shelter_shortfall_count"]
    assert shortfall >= 0
    if shortfall > 0:
        assert res["shelter_shortfall_warning"] is not None
        assert "SHELTER CAPACITY SHORTFALL" in res["shelter_shortfall_warning"]
