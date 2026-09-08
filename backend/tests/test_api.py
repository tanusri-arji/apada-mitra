"""
API Integration tests using FastAPI TestClient.
Tests endpoints, schemas, and scenario switching behavior.
"""
from fastapi.testclient import TestClient
from app.main import app
from app.models.domain import ScenarioType

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert ("LIVE" in data["data_mode"] or "DEMO" in data["data_mode"])



def test_scenario_get_and_post():
    # Set scenario to NORMAL
    res = client.post("/api/scenario", json={"scenario": "NORMAL"})
    assert res.status_code == 200
    assert res.json()["scenario"] == "NORMAL"

    get_res = client.get("/api/scenario")
    assert get_res.status_code == 200
    assert get_res.json()["scenario"] == "NORMAL"


def test_list_villages():
    """Requirement 10: Village API returns valid data."""
    res = client.get("/api/villages")
    assert res.status_code == 200
    villages = res.json()
    assert len(villages) == 15
    assert villages[0]["id"] == "VIL-001"
    assert "latitude" in villages[0]
    assert "longitude" in villages[0]


def test_village_detail_and_scenario_change_effect():
    """Requirement 11: Scenario change produces different risk values."""
    # 1. Fetch under NORMAL scenario
    client.post("/api/scenario", json={"scenario": "NORMAL"})
    res_normal = client.get("/api/villages/VIL-001")
    assert res_normal.status_code == 200
    risk_normal = res_normal.json()["flash_flood_risk_score"]

    # 2. Switch to EXTREME_RAIN scenario
    client.post("/api/scenario", json={"scenario": "EXTREME_RAIN"})
    res_extreme = client.get("/api/villages/VIL-001")
    assert res_extreme.status_code == 200
    risk_extreme = res_extreme.json()["flash_flood_risk_score"]

    # Verify risk score changed significantly
    assert risk_extreme > risk_normal


def test_risk_overview_and_impact_summary():
    res = client.get("/api/risk")
    assert res.status_code == 200
    data = res.json()
    assert "impact_summary" in data
    assert len(data["villages_risk"]) == 15

    imp_res = client.get("/api/impact")
    assert imp_res.status_code == 200
    imp = imp_res.json()
    assert imp["total_villages"] == 15
    assert imp["total_population_exposed"] > 0
