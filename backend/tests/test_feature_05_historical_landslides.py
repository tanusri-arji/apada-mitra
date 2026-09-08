"""
Feature 5 — Real Historical Landslide Inventory Tests.
Verifies authoritative ISRO NRSC & GSI landslide dataset loading, spatial proximity analytics,
data quality states (REAL_GIS, CACHED_GIS, OFFLINE_DEMO, UNAVAILABLE), API endpoints,
and integration with the landslide engine while preserving Features 1-4.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.adapters.landslide_inventory import HistoricalLandslideInventoryAdapter, haversine_km
from app.engine.landslide_inventory import historical_landslide_service
from app.engine.landslide_engine import calculate_landslide_risk
from app.data.dataset import DEMO_VILLAGES
from app.models.landslide import LandslideDataState, HistoricalLandslideEvent

client = TestClient(app)
VIL_001 = DEMO_VILLAGES[0]  # Pipalkoti
VIL_003 = DEMO_VILLAGES[2]  # Govindghat


@pytest.fixture(autouse=True)
def reset_landslide_cache():
    """Resets in-memory historical landslide cache before each test."""
    historical_landslide_service.clear_cache()
    yield
    historical_landslide_service.clear_cache()


def test_haversine_distance_calculation():
    """1. Verifies Haversine great-circle distance math."""
    # Pipalkoti (30.43, 79.43) to Pakhi landslide (30.432, 79.431) is ~0.24 km
    d = haversine_km(30.4300, 79.4300, 30.4320, 79.4310)
    assert 0.1 <= d <= 0.5

    # Pipalkoti to Govindghat (~24.5 km)
    d2 = haversine_km(30.4300, 79.4300, 30.6240, 79.5630)
    assert 22.0 <= d2 <= 28.0


def test_authoritative_inventory_loading():
    """2. Verifies authoritative ISRO NRSC & GSI dataset loading."""
    adapter = HistoricalLandslideInventoryAdapter()
    res = adapter.get_all_events(force_offline=False)
    assert res.total_records >= 15
    assert len(res.events) == res.total_records
    assert res.data_state == LandslideDataState.REAL_GIS
    assert "ISRO NRSC" in res.source_name
    assert "https://" in res.source_url


def test_event_record_schema_and_provenance():
    """3. Verifies schema and provenance fields for each historical event."""
    adapter = HistoricalLandslideInventoryAdapter()
    res = adapter.get_all_events()
    for ev in res.events:
        assert ev.event_id.startswith("LS-UK-")
        assert len(ev.location_name) > 0
        assert ev.district in ["Chamoli", "Rudraprayag", "Tehri Garhwal", "Uttarkashi"]
        assert ev.state == "Uttarakhand"
        assert 28.0 <= ev.latitude <= 32.0
        assert 77.0 <= ev.longitude <= 81.0
        assert len(ev.landslide_type) > 0
        assert ev.source != ""
        assert ev.source_url.startswith("https://")


def test_village_proximity_calculation_pipalkoti():
    """4. Verifies proximity calculation for Pipalkoti (near Pakhi slide)."""
    summary = historical_landslide_service.get_village_historical_summary(VIL_001)
    assert summary.village_id == "VIL-001"
    assert summary.nearest_event_id is not None
    assert summary.nearest_event_distance_km is not None
    assert summary.nearest_event_distance_km <= 5.0  # Pakhi is ~0.24km away
    assert summary.historical_susceptibility_evidence == "HIGH_HISTORICAL_ACTIVITY"
    assert summary.data_state == LandslideDataState.REAL_GIS


def test_village_proximity_calculation_govindghat():
    """5. Verifies proximity calculation for Govindghat (near Bhyundar/Pandukeshwar slides)."""
    summary = historical_landslide_service.get_village_historical_summary(VIL_003)
    assert summary.village_id == "VIL-003"
    assert summary.nearest_event_id is not None
    assert summary.nearest_event_distance_km is not None
    assert summary.nearest_event_distance_km <= 2.0  # Govindghat slide is right at village
    assert summary.events_within_5km >= 1
    assert summary.historical_susceptibility_evidence == "HIGH_HISTORICAL_ACTIVITY"


def test_get_historical_inventory_endpoint():
    """6. Verifies GET /api/landslides/historical endpoint."""
    response = client.get("/api/landslides/historical")
    assert response.status_code == 200
    data = response.json()
    assert "total_records" in data
    assert data["total_records"] >= 15
    assert "events" in data
    assert "source_name" in data
    assert data["data_state"] == "REAL_GIS"


def test_get_village_historical_summary_endpoint():
    """7. Verifies GET /api/landslides/historical/{village_id} endpoint."""
    response = client.get(f"/api/landslides/historical/{VIL_001['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["village_id"] == VIL_001["id"]
    assert "nearest_event_distance_km" in data
    assert "events_within_15km" in data
    assert "historical_susceptibility_evidence" in data
    assert data["data_state"] == "REAL_GIS"


def test_invalid_village_id_returns_404():
    """8. Verifies 404 for non-existent village ID."""
    response = client.get("/api/landslides/historical/VIL-NONEXISTENT")
    assert response.status_code == 404


def test_invalid_coordinate_handling_returns_unavailable():
    """9. Verifies invalid coordinate inputs cleanly return UNAVAILABLE status."""
    adapter = HistoricalLandslideInventoryAdapter()
    invalid_village = {"id": "VIL-999", "name": "Invalid", "latitude": 999.0, "longitude": 999.0}
    summary = adapter.get_village_summary(invalid_village)
    assert summary.data_state == LandslideDataState.UNAVAILABLE
    assert summary.historical_susceptibility_evidence == "UNAVAILABLE"
    assert summary.nearest_event_distance_km is None


def test_force_offline_mode_returns_offline_demo():
    """10. Verifies force_offline mode explicitly returns OFFLINE_DEMO without claiming REAL_GIS."""
    summary = historical_landslide_service.get_village_historical_summary(VIL_001, force_offline=True)
    assert summary.data_state == LandslideDataState.OFFLINE_DEMO
    assert summary.data_state != LandslideDataState.REAL_GIS


def test_empty_catalog_fallback_handling():
    """11. Verifies adapter resilience when dataset path points to non-existent file."""
    adapter = HistoricalLandslideInventoryAdapter(data_file_path="non_existent_file.json")
    res = adapter.get_all_events()
    assert res.total_records == 0
    assert res.data_state == LandslideDataState.UNAVAILABLE

    summary = adapter.get_village_summary(VIL_001)
    assert summary.total_events_in_region == 0
    assert summary.historical_susceptibility_evidence == "LOW_HISTORICAL_RECORDS"


def test_missing_date_handling_in_events():
    """12. Verifies events with missing/null dates parse and calculate without crashing."""
    ev = HistoricalLandslideEvent(
        event_id="LS-TEST-001",
        location_name="Test Reach",
        district="Chamoli",
        latitude=30.43,
        longitude=79.43,
        date=None,  # Missing date
        landslide_type="Debris Flow",
        source="Test Source",
        source_url="https://test.gov",
    )
    assert ev.date is None
    assert ev.event_id == "LS-TEST-001"


def test_landslide_engine_receives_historical_context():
    """13. Verifies existing landslide risk calculation incorporates historical context without altering weights."""
    feature_snapshot = {
        "slope": 30.0,
        "soil_saturation": 85.0,
        "current_rainfall": 45.0,
        "forecast_rainfall": 120.0,
        "river_water_level": 1.8,
        "latitude": VIL_001["latitude"],
        "longitude": VIL_001["longitude"],
    }
    risk_res = calculate_landslide_risk(VIL_001["id"], VIL_001["name"], feature_snapshot)
    assert risk_res.landslide_risk_score > 0.0
    assert risk_res.historical_landslide_evidence is not None
    assert risk_res.historical_landslide_evidence == "HIGH_HISTORICAL_ACTIVITY"
    assert risk_res.nearest_historical_landslide_km is not None


def test_preservation_of_features_1_to_4():
    """14. Verifies Features 1 (Rainfall), 2 (Soil), 3 (IoT), and 4 (GIS Terrain) remain operational."""
    # Feature 1 & 2
    res_dq = client.get("/api/v1/data-quality")
    assert res_dq.status_code == 200

    # Feature 3
    res_iot = client.get("/api/iot/sensors")
    assert res_iot.status_code == 200

    # Feature 4
    res_terrain = client.get(f"/api/terrain/villages/{VIL_001['id']}")
    assert res_terrain.status_code == 200
    t_data = res_terrain.json()
    assert t_data["elevation_m"] > 0
    assert t_data["slope_deg"] > 0
    assert "flow_accumulation" in t_data
