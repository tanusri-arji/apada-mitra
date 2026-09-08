"""
Pytest test suite for Day 2 engines:
Landslide risk, Evacuation Priority, Mountain Road Graph, Hazard-Aware Dijkstra Router, and Shelter Allocation.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.domain import ScenarioType, RoadStatus
from app.engine.landslide_engine import calculate_landslide_risk
from app.engine.priority_engine import calculate_evacuation_priorities
from app.engine.routing_engine import calculate_safest_route
from app.engine.shelter_engine import recommend_safest_shelter
from app.data.dataset import get_village_feature_snapshot, DEMO_VILLAGES
from app.data.road_network import get_active_road_segments
from app.data.shelters import get_shelters_list

client = TestClient(app)


def test_landslide_risk_bounds_and_structure():
    """Requirement 1: Landslide score remains within 0-100."""
    snapshot = get_village_feature_snapshot("VIL-001", ScenarioType.HEAVY_RAIN)
    ls = calculate_landslide_risk("VIL-001", "Pipalkoti", snapshot)

    assert 0.0 <= ls.landslide_risk_score <= 100.0
    assert 0.0 <= ls.confidence <= 100.0
    assert len(ls.contributing_factors) > 0


def test_evacuation_priority_bounds_and_ranking():
    """Requirement 2: Evacuation priority score remains within 0-100 and ranks all 15 villages transparently."""
    # Test API endpoint
    res = client.get("/api/evacuation/priorities")
    assert res.status_code == 200
    priorities = res.json()
    assert len(priorities) == 15

    ranks_found = [p["rank"] for p in priorities]
    assert sorted(ranks_found) == list(range(1, 16))

    for idx, p in enumerate(priorities):
        assert 0.0 <= p["evacuation_priority_score"] <= 100.0
        assert p["population_exposed"] > 0
        assert p["critical_infrastructure_count"] >= 0
        assert p["flood_contribution_pts"] >= 0.0
        assert p["landslide_contribution_pts"] >= 0.0
        assert p["population_contribution_pts"] >= 0.0
        assert p["infrastructure_contribution_pts"] >= 0.0
        assert len(p["factor_breakdown_summary"]) > 0
        assert len(p["primary_urgency_reason"]) > 0
        
        # Verify monotonically ordered by priority score
        if idx > 0:
            assert priorities[idx - 1]["evacuation_priority_score"] >= p["evacuation_priority_score"]


def test_road_network_blocked_segments_in_extreme_rain():
    """Requirement 3: EXTREME_RAIN blocks highly exposed mountain roads."""
    roads_normal = get_active_road_segments(ScenarioType.NORMAL)
    roads_extreme = get_active_road_segments(ScenarioType.EXTREME_RAIN)

    blocked_extreme = [r for r in roads_extreme if r.status == RoadStatus.BLOCKED]
    assert len(blocked_extreme) > 0
    assert any(r.id == "ROAD-010" for r in blocked_extreme)


def test_dijkstra_router_rejects_blocked_roads_and_prefers_safer_route():
    """Requirement 4: Router rejects dangerous/blocked roads and prefers safer route."""
    # In EXTREME_RAIN, ROAD-010 (Phata to Sonprayag) is BLOCKED
    route = calculate_safest_route("VIL-011", "SH-04", ScenarioType.EXTREME_RAIN)
    assert route.route_safety_score > 0
    assert "ROAD-010" not in route.road_segment_ids
    assert len(route.rejected_dangerous_alternatives) > 0


def test_shelter_capacity_constraint_enforcement():
    """Requirement 5: Over-capacity / full shelters are never recommended."""
    rec = recommend_safest_shelter("VIL-001", ScenarioType.HEAVY_RAIN)
    assert rec.recommended_shelter.available_capacity > 0
    assert rec.recommended_shelter.id != "SH-05"  # SH-05 near full capacity


def test_scenario_change_alters_route_and_priorities():
    """Requirement 6: Scenario change updates evacuation priorities and route calculations."""
    # Normal vs Extreme rain priority check
    client.post("/api/scenario", json={"scenario": "NORMAL"})
    p_norm = client.get("/api/evacuation/priorities").json()

    client.post("/api/scenario", json={"scenario": "EXTREME_RAIN"})
    p_ext = client.get("/api/evacuation/priorities").json()

    # Verify scores shifted significantly under extreme rain
    assert p_ext[0]["evacuation_priority_score"] > p_norm[0]["evacuation_priority_score"]


def test_day2_endpoints():
    """Requirement 7 & 8: Verify all Day 2 API endpoints return valid JSON."""
    client.post("/api/scenario", json={"scenario": "HEAVY_RAIN"})

    assert client.get("/api/landslide").status_code == 200
    assert client.get("/api/roads").status_code == 200
    assert client.get("/api/shelters").status_code == 200

    rec_res = client.get("/api/evacuation/shelter-recommendation/VIL-001")
    assert rec_res.status_code == 200
    data = rec_res.json()
    assert "recommended_shelter" in data
    assert "route" in data
