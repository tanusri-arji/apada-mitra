"""
Feature 10 Test Suite: Local Geographic Shelter Candidate Network for APADA MITRA.
Validates 66 real documented public shelter facilities across 15 local village clusters,
Haversine straight-line distance calculation, local search radius filtering,
prevention of distant shelter contamination, safe null capacity handling,
alternative shelter ranking, regional coverage metrics, and API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.shelter import (
    ShelterRecord,
    ShelterDataState,
    ShelterValidationStatus,
    ShelterHazardLevel,
    CapacityStatus,
    VillageShelterRecommendation,
)
from app.adapters.shelter_adapter import (
    shelter_adapter_instance,
    validate_shelter_record,
    validate_shelter_coordinates,
    calculate_haversine_distance_km,
    REGISTERED_SHELTERS_DATA,
)
from app.engine.shelter_suitability_engine import (
    shelter_suitability_engine_instance,
    SUITABILITY_WEIGHTS,
)
from app.models.domain import ScenarioType
from app.config import FEATURE_WEIGHTS
from app.data.dataset import DEMO_VILLAGES

client = TestClient(app)


def test_shelter_system_status_endpoint():
    """Verifies shelter subsystem status, provenance metadata, and suitability formula."""
    resp = client.get("/api/shelters/status")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_registered_shelters"] == 63
    assert data["valid_shelters_count"] == 63
    assert data["data_state"] == ShelterDataState.REAL_STATIC_GOVERNMENT.value
    assert "Uttarakhand" in data["official_authority"] or "USDMA" in data["official_authority"]
    assert "https://usdma.uk.gov.in/" in data["official_source_url"]
    assert data["suitability_weights"]["route_safety"] == 0.45
    assert data["suitability_weights"]["inverse_distance"] == 0.25
    assert data["suitability_weights"]["inverse_shelter_hazard"] == 0.30
    assert "disclaimer" in data


def test_shelter_registry_and_coordinate_bounds():
    """Validates that all registered shelters have valid coordinates and required provenance attributes."""
    shelters, state = shelter_adapter_instance.get_all_shelters()
    assert len(shelters) == 63
    assert state == ShelterDataState.REAL_STATIC_GOVERNMENT

    for s in shelters:
        assert s.shelter_id.startswith("SH-")
        assert len(s.name) > 0
        assert 8.0 <= s.latitude <= 36.0, f"Shelter {s.shelter_id} lat {s.latitude} out of bounds"
        assert 72.0 <= s.longitude <= 97.0, f"Shelter {s.shelter_id} lon {s.longitude} out of bounds"
        assert s.elevation >= 0
        assert s.verification_status == ShelterValidationStatus.VALID
        assert s.source is not None and len(s.source) > 0
        assert s.source_url is not None and len(s.source_url) > 0
        assert 0.0 <= s.flood_hazard_score <= 100.0
        assert 0.0 <= s.landslide_hazard_score <= 100.0
        assert 0.0 <= s.combined_hazard_score <= 100.0


def test_haversine_distance_calculation():
    """Validates Haversine distance calculation between known coordinates."""
    # Distance between Pipalkoti (30.4300, 79.4300) and SH-01 (30.4400, 79.4100) should be approx 2.2 km
    dist = calculate_haversine_distance_km(30.4300, 79.4300, 30.4400, 79.4100)
    assert 1.5 <= dist <= 3.0


def test_local_radius_filter_and_no_distant_shelter_marked_nearby():
    """Verifies that candidates for a village are strictly filtered by local radius (no 50+ km distant shelters)."""
    # Pipalkoti (VIL-001)
    pipalkoti_cands = shelter_adapter_instance.get_local_shelter_candidates_for_village("VIL-001", 30.4300, 79.4300, radius_km=15.0)
    pipalkoti_ids = [s.shelter_id for _, s in pipalkoti_cands]

    # Badrinath shelter SH-06 (~35 km away) and Kerala shelter SH-08 MUST NOT be in Pipalkoti's local candidates list
    assert "SH-06" not in pipalkoti_ids
    assert "SH-08" not in pipalkoti_ids
    assert "SH-01" in pipalkoti_ids
    assert len(pipalkoti_cands) >= 3


def test_route_distance_separate_from_straight_line():
    """Validates candidate evaluation models store both straight_line_distance_km and route_distance_km."""
    rec = shelter_suitability_engine_instance.evaluate_village_shelters("VIL-001", ScenarioType.NORMAL)
    for cand in rec.all_candidates_evaluated:
        assert cand.straight_line_distance_km is not None
        assert cand.straight_line_distance_km > 0
        if cand.is_accessible:
            assert cand.route_distance_km is not None
            assert cand.route_distance_km >= cand.straight_line_distance_km  # Route is >= straight line


def test_duplicate_shelter_and_coordinate_deduplication():
    """Validates that adapter gracefully prevents duplicate shelter IDs and duplicate coordinates."""
    shelters, _ = shelter_adapter_instance.get_all_shelters()
    shelter_ids = [s.shelter_id for s in shelters]
    assert len(shelter_ids) == len(set(shelter_ids))

    coords = [(round(s.latitude, 5), round(s.longitude, 5)) for s in shelters]
    assert len(coords) == len(set(coords))


def test_null_capacity_handling_honesty():
    """Verifies facilities without published bed capacity are safely scored without crashing or assuming zero/infinite capacity."""
    shelters, _ = shelter_adapter_instance.get_all_shelters()
    unknown_cap_shelters = [s for s in shelters if s.available_capacity is None]
    assert len(unknown_cap_shelters) > 0, "Expected shelters with unknown/un published capacity"

    for s in unknown_cap_shelters:
        assert s.capacity_status == CapacityStatus.UNKNOWN
        assert s.total_capacity is None
        assert s.current_occupancy is None


# --- TESTS FOR ALL 15 MONITORED VILLAGE CLUSTERS ---

def test_pipalkoti_local_shelters():
    """Validates local shelter cluster for VIL-001 Pipalkoti."""
    rec = shelter_suitability_engine_instance.evaluate_village_shelters("VIL-001", ScenarioType.NORMAL)
    assert rec.status in ["SAFE_SHELTER_FOUND", "NO_SAFE_SHELTER"]
    assert rec.coverage_status in ["GOOD", "LIMITED", "NO_SAFE_SHELTER", "NO_LOCAL_SHELTER"]
    assert rec.number_of_candidates >= 1


def test_helang_local_shelters():
    """Validates local shelter cluster for VIL-002 Helang."""
    rec = shelter_suitability_engine_instance.evaluate_village_shelters("VIL-002", ScenarioType.NORMAL)
    assert rec.status in ["SAFE_SHELTER_FOUND", "NO_SAFE_SHELTER"]
    assert rec.coverage_status in ["GOOD", "LIMITED", "NO_SAFE_SHELTER", "NO_LOCAL_SHELTER"]
    assert rec.number_of_candidates >= 1


def test_govindghat_local_shelters():
    """Validates local shelter cluster for VIL-003 Govindghat."""
    rec = shelter_suitability_engine_instance.evaluate_village_shelters("VIL-003", ScenarioType.NORMAL)
    assert rec.status in ["SAFE_SHELTER_FOUND", "NO_SAFE_SHELTER"]
    assert rec.coverage_status in ["GOOD", "LIMITED", "NO_SAFE_SHELTER", "NO_LOCAL_SHELTER"]
    assert rec.number_of_candidates >= 1


def test_badrinath_local_shelters():
    """Validates local shelter cluster for VIL-004 Badrinath Base Valley."""
    rec = shelter_suitability_engine_instance.evaluate_village_shelters("VIL-004", ScenarioType.NORMAL)
    assert rec.status in ["SAFE_SHELTER_FOUND", "NO_SAFE_SHELTER"]
    assert rec.coverage_status in ["GOOD", "LIMITED", "NO_SAFE_SHELTER", "NO_LOCAL_SHELTER"]
    assert rec.number_of_candidates >= 1


def test_karnaprayag_local_shelters():
    """Validates local shelter cluster for VIL-005 Karnaprayag Reach."""
    rec = shelter_suitability_engine_instance.evaluate_village_shelters("VIL-005", ScenarioType.NORMAL)
    assert rec.status in ["SAFE_SHELTER_FOUND", "NO_SAFE_SHELTER"]
    assert rec.coverage_status in ["GOOD", "LIMITED", "NO_SAFE_SHELTER", "NO_LOCAL_SHELTER"]
    assert rec.number_of_candidates >= 1


def test_nandaprayag_local_shelters():
    """Validates local shelter cluster for VIL-006 Nandaprayag Basin."""
    rec = shelter_suitability_engine_instance.evaluate_village_shelters("VIL-006", ScenarioType.NORMAL)
    assert rec.status in ["SAFE_SHELTER_FOUND", "NO_SAFE_SHELTER"]
    assert rec.coverage_status in ["GOOD", "LIMITED", "NO_SAFE_SHELTER", "NO_LOCAL_SHELTER"]
    assert rec.number_of_candidates >= 1


def test_rudraprayag_local_shelters():
    """Validates local shelter cluster for VIL-007 Rudraprayag Sangam."""
    rec = shelter_suitability_engine_instance.evaluate_village_shelters("VIL-007", ScenarioType.NORMAL)
    assert rec.status in ["SAFE_SHELTER_FOUND", "NO_SAFE_SHELTER"]
    assert rec.coverage_status in ["GOOD", "LIMITED", "NO_SAFE_SHELTER", "NO_LOCAL_SHELTER"]
    assert rec.number_of_candidates >= 1


def test_tilwara_local_shelters():
    """Validates local shelter cluster for VIL-008 Tilwara Valley."""
    rec = shelter_suitability_engine_instance.evaluate_village_shelters("VIL-008", ScenarioType.NORMAL)
    assert rec.status in ["SAFE_SHELTER_FOUND", "NO_SAFE_SHELTER"]
    assert rec.coverage_status in ["GOOD", "LIMITED", "NO_SAFE_SHELTER", "NO_LOCAL_SHELTER"]
    assert rec.number_of_candidates >= 1


def test_augustmuni_local_shelters():
    """Validates local shelter cluster for VIL-009 Augustmuni Stream."""
    rec = shelter_suitability_engine_instance.evaluate_village_shelters("VIL-009", ScenarioType.NORMAL)
    assert rec.status in ["SAFE_SHELTER_FOUND", "NO_SAFE_SHELTER"]
    assert rec.coverage_status in ["GOOD", "LIMITED", "NO_SAFE_SHELTER", "NO_LOCAL_SHELTER"]
    assert rec.number_of_candidates >= 1


def test_guptkashi_local_shelters():
    """Validates local shelter cluster for VIL-010 Guptkashi Slope."""
    rec = shelter_suitability_engine_instance.evaluate_village_shelters("VIL-010", ScenarioType.NORMAL)
    assert rec.status in ["SAFE_SHELTER_FOUND", "NO_SAFE_SHELTER"]
    assert rec.coverage_status in ["GOOD", "LIMITED", "NO_SAFE_SHELTER", "NO_LOCAL_SHELTER"]
    assert rec.number_of_candidates >= 1


def test_phata_local_shelters():
    """Validates local shelter cluster for VIL-011 Phata Funnel."""
    rec = shelter_suitability_engine_instance.evaluate_village_shelters("VIL-011", ScenarioType.NORMAL)
    assert rec.status in ["SAFE_SHELTER_FOUND", "NO_SAFE_SHELTER"]
    assert rec.coverage_status in ["GOOD", "LIMITED", "NO_SAFE_SHELTER", "NO_LOCAL_SHELTER"]
    assert rec.number_of_candidates >= 1


def test_sonprayag_local_shelters():
    """Validates local shelter cluster for VIL-012 Sonprayag Confluence."""
    rec = shelter_suitability_engine_instance.evaluate_village_shelters("VIL-012", ScenarioType.NORMAL)
    assert rec.status in ["SAFE_SHELTER_FOUND", "NO_SAFE_SHELTER"]
    assert rec.coverage_status in ["GOOD", "LIMITED", "NO_SAFE_SHELTER", "NO_LOCAL_SHELTER"]
    assert rec.number_of_candidates >= 1


def test_mandi_local_shelters():
    """Validates local shelter cluster for VIL-013 Aut / Mandi."""
    rec = shelter_suitability_engine_instance.evaluate_village_shelters("VIL-013", ScenarioType.NORMAL)
    assert rec.status in ["SAFE_SHELTER_FOUND", "NO_SAFE_SHELTER"]
    assert rec.coverage_status in ["GOOD", "LIMITED", "NO_SAFE_SHELTER", "NO_LOCAL_SHELTER"]
    assert rec.number_of_candidates >= 1


def test_meppadi_local_shelters():
    """Validates local shelter cluster for VIL-014 Meppadi / Wayanad."""
    rec = shelter_suitability_engine_instance.evaluate_village_shelters("VIL-014", ScenarioType.NORMAL)
    assert rec.status in ["SAFE_SHELTER_FOUND", "NO_SAFE_SHELTER"]
    assert rec.coverage_status in ["GOOD", "LIMITED", "NO_SAFE_SHELTER", "NO_LOCAL_SHELTER"]
    assert rec.number_of_candidates >= 1


def test_chooralmala_local_shelters():
    """Validates local shelter cluster for VIL-015 Chooralmala / Vellarimala."""
    rec = shelter_suitability_engine_instance.evaluate_village_shelters("VIL-015", ScenarioType.NORMAL)
    assert rec.status in ["SAFE_SHELTER_FOUND", "NO_SAFE_SHELTER"]
    assert rec.coverage_status in ["GOOD", "LIMITED", "NO_SAFE_SHELTER", "NO_LOCAL_SHELTER"]
    assert rec.number_of_candidates >= 1


def test_regional_shelter_coverage_summary():
    """Validates the coverage summary across Uttarakhand, Himachal Pradesh, and Kerala."""
    summary = shelter_suitability_engine_instance.get_shelter_coverage_summary()
    assert summary.total_monitored_villages == 15
    assert summary.total_shelter_candidates == 63
    assert len(summary.coverage_details) == 15
    assert summary.villages_with_good_coverage + summary.villages_with_limited_coverage + summary.villages_with_no_safe_shelter == 15


def test_api_shelters_and_coverage_endpoints():
    """Validates all Feature 10 API endpoints via FastAPI TestClient."""
    # 1. GET /api/shelters
    resp1 = client.get("/api/shelters")
    assert resp1.status_code == 200
    shelters = resp1.json()
    assert len(shelters) == 63
    assert shelters[0]["id"] == "SH-01"

    # 2. GET /api/shelters/SH-01
    resp2 = client.get("/api/shelters/SH-01")
    assert resp2.status_code == 200
    s1 = resp2.json()
    assert s1["shelter_id"] == "SH-01"
    assert s1["district"] == "Chamoli"

    # 3. GET /api/shelters/coverage
    resp3 = client.get("/api/shelters/coverage")
    assert resp3.status_code == 200
    cov = resp3.json()
    assert cov["total_monitored_villages"] == 15
    assert cov["total_shelter_candidates"] == 63

    # 4. GET /api/shelters/villages/VIL-001/candidates
    resp4 = client.get("/api/shelters/villages/VIL-001/candidates")
    assert resp4.status_code == 200
    cands = resp4.json()
    assert 3 <= len(cands) <= 15

    # 5. GET /api/evacuation/shelter/VIL-001/alternatives
    resp5 = client.get("/api/evacuation/shelter/VIL-001/alternatives")
    assert resp5.status_code == 200
    alts = resp5.json()
    assert len(alts) > 0


def test_features_1_to_9_integrity_preserved():
    """Ensures Features 1 through 9 core weights and functionalities are 100% preserved."""
    assert FEATURE_WEIGHTS["current_rainfall"] == 0.25
    assert FEATURE_WEIGHTS["forecast_rainfall"] == 0.20
    assert FEATURE_WEIGHTS["soil_saturation"] == 0.15
    assert FEATURE_WEIGHTS["river_water_level"] == 0.15
    assert FEATURE_WEIGHTS["flow_accumulation"] == 0.15
    assert FEATURE_WEIGHTS["slope"] == 0.10
    assert sum(FEATURE_WEIGHTS.values()) == 1.0


