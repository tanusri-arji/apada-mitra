"""
Feature 8 Test Suite: Real River-Level & Hydrological Telemetry Layer for APADA MITRA.
Validates CWC gauging station registry, 4-tier source priority, IoT water-level sensor integration,
freshness classification, provenance tracking, risk engine feeding, and non-regression of Features 1–7.
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.models.hydrology import (
    HydrologyDataState,
    HydrologyFreshnessStatus,
    HydrologicalStationRecord,
    HydrologicalObservation,
    HydrologySystemStatus,
)
from app.engine.hydrology_engine import (
    hydrology_engine_instance,
    CWC_STATIONS_REGISTRY,
)
from app.engine.iot_store import iot_store_instance, IoTSensorType
from app.config import FEATURE_WEIGHTS
from app.models.domain import ScenarioType

client = TestClient(app)


def test_hydrology_system_status_reports_honest_official_state():
    """
    Verifies that the system status explicitly reports LIVE_OFFICIAL_SOURCE_UNAVAILABLE
    when official credentials/gateways are unconfigured, adhering to critical honesty rules.
    """
    resp = client.get("/api/hydrology/status")
    assert resp.status_code == 200
    data = resp.json()

    assert data["official_live_status"] == "LIVE_OFFICIAL_SOURCE_UNAVAILABLE"
    assert "Central Water Commission" in data["official_authority"]
    assert "https://india-wris.gov.in/" in data["official_api_url"]
    assert data["registered_stations_count"] == len(CWC_STATIONS_REGISTRY)
    assert len(data["source_priority_order"]) == 4
    assert "honesty" in data["disclaimer"].lower() or "credentials" in data["disclaimer"].lower()


def test_cwc_stations_registry_and_endpoint():
    """Validates that CWC stations are correctly registered and retrievable via API."""
    resp = client.get("/api/hydrology/stations")
    assert resp.status_code == 200
    stations = resp.json()
    assert len(stations) >= 7

    station_ids = [st["station_id"] for st in stations]
    assert "CWC-001" in station_ids  # Joshimath
    assert "CWC-002" in station_ids  # Pipalkoti
    assert "CWC-003" in station_ids  # Govindghat
    assert "CWC-005" in station_ids  # Rudraprayag Sangam

    for st in stations:
        assert st["station_id"].startswith("CWC-")
        assert len(st["station_name"]) > 0
        assert len(st["river_name"]) > 0
        assert st["warning_level_m"] > 0
        assert st["danger_level_m"] > st["warning_level_m"]
        assert len(st["upstream_downstream_relationship"]) > 0


def test_cwc_single_station_endpoint():
    """Verifies retrieval of specific station observation and 404 handling."""
    # Valid station
    resp = client.get("/api/hydrology/stations/CWC-002")
    assert resp.status_code == 200
    data = resp.json()
    assert data["station_id"] == "CWC-002"
    assert "Pipalkoti" in data["station_name"]
    assert "Alaknanda" in data["river_name"]

    # Invalid station
    resp_404 = client.get("/api/hydrology/stations/CWC-999")
    assert resp_404.status_code == 404
    assert "not found" in resp_404.json()["detail"].lower()


def test_village_hydrology_observation_vil_001_pipalkoti():
    """Verifies hydrological observation for VIL-001 Pipalkoti."""
    resp = client.get("/api/hydrology/villages/VIL-001")
    assert resp.status_code == 200
    data = resp.json()

    assert data["village_id"] == "VIL-001"
    assert data["village_name"] == "Pipalkoti"
    assert data["river_name"] == "Alaknanda River"
    assert data["water_level_m"] is not None
    assert data["data_state"] in [
        HydrologyDataState.REAL_LIVE_IOT,
        HydrologyDataState.OFFLINE_DEMO,
    ]
    assert data["risk_contribution_pts"] >= 0.0
    assert len(data["assumptions"]) > 0


def test_village_hydrology_observation_vil_003_govindghat():
    """Verifies hydrological observation for VIL-003 Govindghat."""
    resp = client.get("/api/hydrology/villages/VIL-003")
    assert resp.status_code == 200
    data = resp.json()

    assert data["village_id"] == "VIL-003"
    assert data["village_name"] == "Govindghat"
    assert "Lakshman Ganga" in data["river_name"] or "Alaknanda" in data["river_name"]
    assert data["water_level_m"] is not None


def test_iot_water_level_sensor_promotes_to_real_live_iot():
    """
    Verifies 4-tier source priority:
    When a fresh IoT water-level sensor is ingested, the hydrology layer promotes
    the observation to REAL_LIVE_IOT.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    # Ingest a live water level IoT sensor for VIL-001
    payload = {
        "sensor_id": "IOT-WL-TEST-001",
        "sensor_type": IoTSensorType.WATER_LEVEL.value,
        "village_id": "VIL-001",
        "value": 2.45,
        "unit": "m",
        "timestamp": now_iso,
    }
    ingest_resp = client.post("/api/iot/sensors/ingest", json=payload)
    assert ingest_resp.status_code == 200

    # Query village hydrology observation
    hydro_resp = client.get("/api/hydrology/villages/VIL-001")
    assert hydro_resp.status_code == 200
    data = hydro_resp.json()

    assert data["data_state"] == HydrologyDataState.REAL_LIVE_IOT.value
    assert data["water_level_m"] == 2.45
    assert data["source"] == "IoT Water-Level Sensor (IOT-WL-TEST-001)"
    assert data["freshness"] == HydrologyFreshnessStatus.LIVE.value
    assert data["risk_contribution_pts"] > 0.0


def test_offline_demo_never_labeled_as_real():
    """Verifies that offline fallback observations are never labeled as REAL_LIVE_OFFICIAL."""
    # Force offline for VIL-002
    obs = hydrology_engine_instance.get_village_hydrology("VIL-002", force_offline=True)
    assert obs is not None
    assert obs.data_state == HydrologyDataState.OFFLINE_DEMO
    assert obs.data_state != HydrologyDataState.REAL_LIVE_OFFICIAL
    assert "OFFLINE_DEMO" in obs.assumptions[-1] or "DEMO" in obs.quality_status


def test_invalid_village_hydrology_404():
    """Verifies 404 response for invalid village ID."""
    resp = client.get("/api/hydrology/villages/VIL-INVALID")
    assert resp.status_code == 404


def test_flood_risk_engine_weights_strictly_unmodified():
    """Verifies that existing flood risk weights remain strictly immutable."""
    assert FEATURE_WEIGHTS["current_rainfall"] == 0.25
    assert FEATURE_WEIGHTS["forecast_rainfall"] == 0.20
    assert FEATURE_WEIGHTS["soil_saturation"] == 0.15
    assert FEATURE_WEIGHTS["river_water_level"] == 0.15
    assert FEATURE_WEIGHTS["flow_accumulation"] == 0.15
    assert FEATURE_WEIGHTS["slope"] == 0.10


def test_features_1_to_7_integrity_preserved():
    """Verifies that Features 1-7 remain intact and functioning seamlessly."""
    # Feature 1: Weather & Forecast
    r1 = client.get("/api/data-quality")
    assert r1.status_code == 200

    # Feature 3: IoT Sensors
    r3 = client.get("/api/iot/sensors")
    assert r3.status_code == 200

    # Feature 4: GIS Terrain Elevation
    r4 = client.get("/api/terrain/villages/VIL-001")
    assert r4.status_code == 200

    # Feature 5: Historical Landslides
    r5 = client.get("/api/landslides/historical/VIL-001")
    assert r5.status_code == 200

    # Feature 6: Real Lead-Time Engine
    r6 = client.get("/api/lead-time/villages/VIL-001")
    assert r6.status_code == 200

    # Feature 7: Census Population & Exposure
    r7 = client.get("/api/exposure/villages/VIL-001")
    assert r7.status_code == 200
    assert r7.json()["total_population"] == 2411
