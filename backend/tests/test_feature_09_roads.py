"""
Feature 9 Test Suite: Real Road Network & Dynamic Road Hazard Intelligence for APADA MITRA.
Validates OpenStreetMap (OSM) geometry, dynamic hazard status derivation, Dijkstra routing exclusions,
explicit NO_SAFE_ROUTE failure handling, provenance tracking, and non-regression of Features 1–8.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.road import (
    RoadDataState,
    RoadOperationalStatus,
    RoadSegmentDetail,
    EvacuationRouteDetail,
    RoadNetworkStatusResponse,
)
from app.engine.road_hazard_engine import (
    road_hazard_engine_instance,
    ROAD_OPEN_MAX_HAZARD,
    ROAD_BLOCKED_MIN_HAZARD,
)
from app.adapters.osm_road_adapter import CACHED_OSM_ROADS
from app.models.domain import ScenarioType
from app.config import FEATURE_WEIGHTS

client = TestClient(app)


def test_road_network_status_endpoint():
    """Verifies road network status summary and OSM attribution."""
    resp = client.get("/api/roads/status")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_segments_count"] == len(CACHED_OSM_ROADS)
    assert data["open_segments_count"] + data["degraded_segments_count"] + data["blocked_segments_count"] == data["total_segments_count"]
    assert "OpenStreetMap" in data["source_authority"]
    assert "https://www.openstreetmap.org/" in data["source_url"]
    assert "ODbL" in data["osm_licensing_note"]
    assert data["data_state"] in [RoadDataState.REAL_LIVE_OSM.value, RoadDataState.CACHED_OSM.value]


def test_road_segments_geometry_and_provenance():
    """Validates that road segments preserve real multi-point geometric traces and metadata."""
    resp = client.get("/api/roads")
    assert resp.status_code == 200
    roads = resp.json()
    assert len(roads) == len(CACHED_OSM_ROADS)

    for r in roads:
        assert r["road_id"].startswith("ROAD-")
        assert len(r["name"]) > 0
        assert r["distance_km"] > 0
        assert len(r["coordinates"]) >= 2, f"Road {r['road_id']} must have at least 2 coordinate pairs"
        for pt in r["coordinates"]:
            assert len(pt) == 2
            assert 8.0 <= pt[0] <= 36.0  # Latitude bounds for disaster monitoring regions
            assert 72.0 <= pt[1] <= 97.0  # Longitude bounds for disaster monitoring regions
        assert r["data_state"] in [RoadDataState.REAL_LIVE_OSM.value, RoadDataState.CACHED_OSM.value]
        assert r["status"] in ["OPEN", "DEGRADED", "BLOCKED", "UNKNOWN"]
        assert 0.0 <= r["flood_exposure"] <= 100.0
        assert 0.0 <= r["landslide_exposure"] <= 100.0
        assert 0.0 <= r["composite_hazard_score"] <= 100.0


def test_single_road_segment_and_village_roads():
    """Verifies single road detail lookup and village road association."""
    # Lookup ROAD-001
    resp = client.get("/api/roads/ROAD-001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["road_id"] == "ROAD-001"
    assert "NH-07" in data["name"] or "NH-58" in data["name"]

    # Village roads for VIL-001 (Pipalkoti)
    v_resp = client.get("/api/roads/villages/VIL-001")
    assert v_resp.status_code == 200
    v_roads = v_resp.json()
    assert len(v_roads) >= 2
    road_ids = [r["road_id"] for r in v_roads]
    assert "ROAD-001" in road_ids or "ROAD-015" in road_ids


def test_normal_open_roads_produce_safe_evacuation_route():
    """Verifies that under NORMAL conditions, a valid safe evacuation route is produced."""
    route = road_hazard_engine_instance.calculate_safest_evacuation_route(
        origin_village_id="VIL-001",
        scenario=ScenarioType.NORMAL,
        force_offline=True,
    )
    assert route.route_status in ["SAFE_OPEN", "SAFE_DEGRADED"]
    assert len(route.road_ids) > 0
    assert route.total_distance_km > 0
    assert route.estimated_travel_time_minutes > 0
    assert route.route_safety_score >= 50.0
    assert route.destination_id == "SH-01"


def test_degraded_roads_increase_travel_time_and_cost():
    """Verifies that higher hazard degrades roads and increases travel time/penalties."""
    route_normal = road_hazard_engine_instance.calculate_safest_evacuation_route(
        origin_village_id="VIL-003",
        scenario=ScenarioType.NORMAL,
        force_offline=True,
    )
    route_heavy = road_hazard_engine_instance.calculate_safest_evacuation_route(
        origin_village_id="VIL-003",
        scenario=ScenarioType.HEAVY_RAIN,
        force_offline=True,
    )
    assert route_heavy.estimated_travel_time_minutes >= route_normal.estimated_travel_time_minutes
    assert route_heavy.route_safety_score <= route_normal.route_safety_score


def test_blocked_roads_excluded_from_dijkstra_route():
    """Verifies that BLOCKED road segments are strictly excluded from the path traversal."""
    roads_extreme = road_hazard_engine_instance.get_all_road_segments(
        scenario=ScenarioType.EXTREME_RAIN,
        force_offline=True,
    )
    blocked_ids = [r.road_id for r in roads_extreme if r.status == RoadOperationalStatus.BLOCKED]

    if blocked_ids:
        route = road_hazard_engine_instance.calculate_safest_evacuation_route(
            origin_village_id="VIL-001",
            scenario=ScenarioType.EXTREME_RAIN,
            force_offline=True,
        )
        for r_id in route.road_ids:
            assert r_id not in blocked_ids, f"Blocked road {r_id} must not be present in active evacuation route"


def test_no_safe_route_explicit_failure_state():
    """Verifies that when all connecting paths are blocked, NO_SAFE_ROUTE is explicitly returned."""
    # Test with custom impassable destination across blocked mountain passes in EXTREME_RAIN
    route_fail = road_hazard_engine_instance.calculate_safest_evacuation_route(
        origin_village_id="VIL-014",  # High alpine Chopta
        destination_shelter_id="SH-06",  # Badrinath ridge shelter across disconnected mountains
        scenario=ScenarioType.EXTREME_RAIN,
        force_offline=True,
    )
    assert route_fail.route_status == "NO_SAFE_ROUTE"
    assert route_fail.estimated_travel_time_minutes == 9999.0
    assert route_fail.route_safety_score == 0.0
    assert len(route_fail.road_ids) == 0
    assert "CRITICAL" in route_fail.explanation or "No safe" in route_fail.explanation


def test_api_get_evacuation_route():
    """Verifies GET /api/evacuation/route/{village_id} endpoint response schema."""
    resp = client.get("/api/evacuation/route/VIL-001")
    assert resp.status_code == 200
    data = resp.json()

    assert data["origin_id"] == "VIL-001"
    assert "Pipalkoti" in data["origin_name"]
    assert "road_ids" in data
    assert "total_distance_km" in data
    assert "estimated_travel_time_minutes" in data
    assert "route_safety_score" in data
    assert "source_provenance" in data
    assert data["calculation_method"] == "HAZARD_WEIGHTED_DIJKSTRA"


def test_flood_risk_engine_weights_remain_unmodified():
    """Verifies that all core risk engine weights remain strictly untouched."""
    assert FEATURE_WEIGHTS["current_rainfall"] == 0.25
    assert FEATURE_WEIGHTS["forecast_rainfall"] == 0.20
    assert FEATURE_WEIGHTS["soil_saturation"] == 0.15
    assert FEATURE_WEIGHTS["river_water_level"] == 0.15
    assert FEATURE_WEIGHTS["flow_accumulation"] == 0.15
    assert FEATURE_WEIGHTS["slope"] == 0.10


def test_features_1_to_8_integrity_preserved():
    """Verifies non-regression of Features 1 through 8."""
    # Feature 1 & 2: Pipeline Data Quality
    r_dq = client.get("/api/data-quality")
    assert r_dq.status_code == 200

    # Feature 3: IoT Sensors
    r_iot = client.get("/api/iot/sensors")
    assert r_iot.status_code == 200

    # Feature 4: GIS Elevation
    r_gis = client.get("/api/terrain/villages/VIL-001")
    assert r_gis.status_code == 200

    # Feature 5: Historical Landslides
    r_ls = client.get("/api/landslides/historical/VIL-001")
    assert r_ls.status_code == 200

    # Feature 6: Lead-Time Engine
    r_lt = client.get("/api/lead-time/villages/VIL-001")
    assert r_lt.status_code == 200

    # Feature 7: Population Exposure
    r_pop = client.get("/api/exposure/villages/VIL-001")
    assert r_pop.status_code == 200

    # Feature 8: Hydrology Telemetry
    r_hyd = client.get("/api/hydrology/villages/VIL-001")
    assert r_hyd.status_code == 200
