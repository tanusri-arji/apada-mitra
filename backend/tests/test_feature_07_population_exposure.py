"""
Feature 7 Test Suite: Real Population & Hazard Exposure Engine for APADA MITRA.
Validates Census 2011 demographic provenance, exposure calculations, API responses,
confidence scoring, and non-regression of Features 1–6.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.population import (
    VillagePopulationRecord,
    VillageExposureDetail,
    PopulationDataState,
    ExposureCalculationMethod,
)
from app.data.census_population_data import (
    get_village_census_population,
    get_all_census_population_records,
    CENSUS_VILLAGE_POPULATION_DATA,
)
from app.engine.exposure_engine import (
    calculate_village_exposure_detail,
    calculate_all_villages_exposure_detail,
    calculate_village_exposure,
)
from app.models.domain import RiskLevel

client = TestClient(app)


def test_census_source_provenance_metadata():
    """Validates that all Census 2011 population records contain authoritative source metadata."""
    records = get_all_census_population_records()
    assert len(records) == 15, "Expected 15 monitored villages in census demographic store."

    for rec in records:
        assert rec.village_id.startswith("VIL-"), f"Invalid village_id format: {rec.village_id}"
        assert rec.population > 0, f"Population must be positive for {rec.village_id}"
        assert rec.source is not None and len(rec.source) > 0, f"Missing source for {rec.village_id}"
        assert rec.source_url.startswith("https://"), f"Invalid source URL for {rec.village_id}"
        assert rec.source_year == 2011, f"Expected 2011 census year, got {rec.source_year}"
        assert rec.data_state in [
            PopulationDataState.REAL_STATIC,
            PopulationDataState.ESTIMATED_FROM_REAL_SOURCE,
        ], f"Unexpected data_state: {rec.data_state}"
        assert rec.confidence >= 80.0, f"Confidence too low for verified record: {rec.confidence}"
        assert len(rec.assumptions) > 0, f"Assumptions must be documented for {rec.village_id}"


def test_village_001_pipalkoti_census_demographics():
    """Verifies VIL-001 Pipalkoti exact Census 2011 values."""
    rec = get_village_census_population("VIL-001")
    assert rec is not None
    assert rec.village_name == "Pipalkoti"
    assert rec.census_2011_code == "042235"
    assert rec.district == "Chamoli"
    assert rec.sub_district_or_block == "Dasholi"
    assert rec.population == 2411
    assert rec.households == 568
    assert rec.vulnerable_population == 432
    assert rec.data_state == PopulationDataState.REAL_STATIC
    assert rec.geographic_level == "VILLAGE_CENSUS_PCA"


def test_village_003_govindghat_census_demographics():
    """Verifies VIL-003 Govindghat exact Census 2011 values."""
    rec = get_village_census_population("VIL-003")
    assert rec is not None
    assert rec.village_name == "Govindghat"
    assert rec.census_2011_code == "042031"
    assert rec.district == "Chamoli"
    assert rec.sub_district_or_block == "Joshi Math"
    assert rec.population == 1237
    assert rec.households == 274
    assert rec.vulnerable_population == 215
    assert rec.data_state == PopulationDataState.REAL_STATIC


def test_exposure_calculation_separation_and_bounds():
    """
    Verifies that population DATA is strictly separated from hazard EXPOSURE calculation,
    and exposure headcounts and percentages respect mathematical bounds (0 <= exposed <= total).
    """
    for village_id in [f"VIL-{i:03d}" for i in range(1, 16)]:
        detail = calculate_village_exposure_detail(village_id)
        assert detail is not None, f"Failed exposure calculation for {village_id}"

        # Non-negative and bounded properties
        assert detail.total_population > 0
        assert 0 <= detail.exposed_population <= detail.total_population
        assert 0.0 <= detail.exposure_percentage <= 100.0
        assert 0 <= detail.vulnerable_exposed <= detail.vulnerable_population
        assert 0.0 <= detail.composite_exposure_score <= 100.0

        # Flood hazard breakdown
        assert 0 <= detail.flood_exposure.exposed_population <= detail.total_population
        assert 0.0 <= detail.flood_exposure.exposure_fraction <= 1.0
        assert 0.0 <= detail.flood_exposure.risk_score <= 100.0

        # Landslide hazard breakdown
        assert 0 <= detail.landslide_exposure.exposed_population <= detail.total_population
        assert 0.0 <= detail.landslide_exposure.exposure_fraction <= 1.0
        assert 0.0 <= detail.landslide_exposure.risk_score <= 100.0

        # Exposure percentage arithmetic
        expected_pct = round((detail.exposed_population / detail.total_population) * 100.0, 2)
        assert detail.exposure_percentage == expected_pct


def test_exposure_not_blindly_100_percent():
    """Verifies that high or moderate risk does NOT blindly claim 100% of the village is exposed."""
    detail = calculate_village_exposure_detail("VIL-001")
    assert detail is not None
    # Pipalkoti in normal/baseline should not have 100% exposed
    assert detail.exposure_percentage < 100.0, "Exposure percentage should be bounded and realistic, not 100%."
    assert detail.exposed_population < detail.total_population


def test_estimated_data_state_properly_labelled():
    """Verifies that aggregated/ward sector estimates are explicitly labelled ESTIMATED_FROM_REAL_SOURCE."""
    # Badrinath (VIL-004) and Karnaprayag (VIL-005) are ward/sector reaches
    badri = calculate_village_exposure_detail("VIL-004")
    assert badri is not None
    assert badri.data_state == PopulationDataState.ESTIMATED_FROM_REAL_SOURCE
    assert badri.source_provenance["data_state"] == "ESTIMATED_FROM_REAL_SOURCE"

    karna = calculate_village_exposure_detail("VIL-005")
    assert karna is not None
    assert karna.data_state == PopulationDataState.ESTIMATED_FROM_REAL_SOURCE


def test_api_get_village_exposure_single():
    """Verifies GET /api/exposure/villages/{village_id} returns valid schema."""
    resp = client.get("/api/exposure/villages/VIL-001")
    assert resp.status_code == 200
    data = resp.json()

    assert data["village_id"] == "VIL-001"
    assert data["village_name"] == "Pipalkoti"
    assert data["total_population"] == 2411
    assert data["households"] == 568
    assert data["vulnerable_population"] == 432
    assert "flood_exposure" in data
    assert "landslide_exposure" in data
    assert "source_provenance" in data
    assert data["source_provenance"]["source_year"] == 2011
    assert data["data_state"] == "REAL_STATIC"
    assert len(data["assumptions"]) > 0


def test_api_get_village_exposure_all():
    """Verifies GET /api/exposure/villages returns all 15 monitored settlements."""
    resp = client.get("/api/exposure/villages")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 15
    ids = [v["village_id"] for v in data]
    for i in range(1, 16):
        assert f"VIL-{i:03d}" in ids


def test_api_invalid_village_exposure_404():
    """Verifies 404 response for invalid village ID."""
    resp = client.get("/api/exposure/villages/VIL-999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_legacy_calculate_village_exposure_unmodified():
    """Ensures backwards compatibility of legacy calculate_village_exposure function."""
    exp = calculate_village_exposure(
        population=2000,
        infra_dict={"schools": 2, "health_facilities": 1, "bridges_and_roads": 1, "critical_structures_count": 4},
        risk_level=RiskLevel.HIGH,
        risk_probability=0.7,
    )
    assert exp.population_exposed > 0
    assert exp.exposure_score > 0
    assert exp.infrastructure.critical_structures_count == 4


def test_features_1_to_6_integrity_preserved():
    """Verifies that Features 1-6 remain functional and untouched."""
    # Pipeline & Data Quality
    r_dq = client.get("/api/data-quality")
    assert r_dq.status_code == 200

    # Feature 3: IoT Sensor ingestion
    r_iot = client.get("/api/iot/sensors")
    assert r_iot.status_code == 200

    # Feature 4: Real GIS terrain intelligence
    r_terrain = client.get("/api/terrain/villages/VIL-001")
    assert r_terrain.status_code == 200

    # Feature 5: Historical landslide inventory
    r_ls = client.get("/api/landslides/historical/VIL-001")
    assert r_ls.status_code == 200

    # Feature 6: Real lead-time engine
    r_lt = client.get("/api/lead-time/villages/VIL-001")
    assert r_lt.status_code == 200
    assert r_lt.json()["decision_status"] in ["SAFE", "TIGHT", "INSUFFICIENT", "UNKNOWN"]
