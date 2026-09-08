"""
Feature 3 — Real IoT Sensor API Ingestion Layer & Priority Pipeline Tests.
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.engine.iot_store import iot_store_instance, IoTFreshnessStatus
from app.data_pipeline import DataIngestionPipeline
from app.data.dataset import DEMO_VILLAGES, get_village_feature_snapshot
from app.models.domain import DataSourceState, ScenarioType

client = TestClient(app)
VIL_003 = "VIL-003"


@pytest.fixture(autouse=True)
def reset_iot_store():
    """Resets in-memory IoT store before each test."""
    iot_store_instance.clear()
    yield
    iot_store_instance.clear()


def test_valid_rainfall_ingestion():
    """Verifies successful ingestion of valid rainfall IoT sensor payload."""
    now_iso = datetime.now(timezone.utc).isoformat()
    payload = {
        "sensor_id": "RAIN-001",
        "sensor_type": "rainfall",
        "village_id": VIL_003,
        "value": 12.5,
        "unit": "mm/h",
        "timestamp": now_iso,
    }
    response = client.post("/api/iot/sensors/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sensor_id"] == "RAIN-001"
    assert data["value"] == 12.5
    assert data["status"] == "LIVE"
    assert data["source"] == "IOT_SENSOR"


def test_valid_soil_moisture_ingestion():
    """Verifies successful ingestion of valid soil moisture IoT sensor payload in m3/m3."""
    now_iso = datetime.now(timezone.utc).isoformat()
    payload = {
        "sensor_id": "SOIL-001",
        "sensor_type": "soil_moisture",
        "village_id": VIL_003,
        "value": 0.42,
        "unit": "m3/m3",
        "timestamp": now_iso,
    }
    response = client.post("/api/iot/sensors/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sensor_id"] == "SOIL-001"
    assert data["value"] == 0.42
    assert data["unit"] == "m3/m3"


def test_valid_water_level_ingestion():
    """Verifies successful ingestion of valid water level IoT sensor payload."""
    now_iso = datetime.now(timezone.utc).isoformat()
    payload = {
        "sensor_id": "WATER-001",
        "sensor_type": "water_level",
        "village_id": VIL_003,
        "value": 2.4,
        "unit": "m",
        "timestamp": now_iso,
    }
    response = client.post("/api/iot/sensors/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sensor_id"] == "WATER-001"
    assert data["value"] == 2.4


def test_rejection_invalid_sensor_type():
    """Verifies rejection of unsupported sensor type with HTTP 400."""
    now_iso = datetime.now(timezone.utc).isoformat()
    payload = {
        "sensor_id": "TEMP-001",
        "sensor_type": "temperature",
        "village_id": VIL_003,
        "value": 25.0,
        "unit": "C",
        "timestamp": now_iso,
    }
    response = client.post("/api/iot/sensors/ingest", json=payload)
    assert response.status_code == 400
    assert "Unsupported sensor_type" in response.json()["detail"]


def test_rejection_unknown_village():
    """Verifies rejection of unknown village ID with HTTP 404."""
    now_iso = datetime.now(timezone.utc).isoformat()
    payload = {
        "sensor_id": "RAIN-001",
        "sensor_type": "rainfall",
        "village_id": "VIL-999",
        "value": 10.0,
        "unit": "mm/h",
        "timestamp": now_iso,
    }
    response = client.post("/api/iot/sensors/ingest", json=payload)
    assert response.status_code == 404
    assert "Unknown village ID" in response.json()["detail"]


def test_rejection_missing_fields():
    """Verifies rejection when required fields are missing with HTTP 400."""
    payload = {
        "sensor_id": "RAIN-001",
        "sensor_type": "rainfall",
        "village_id": VIL_003,
        # missing value, unit, timestamp
    }
    response = client.post("/api/iot/sensors/ingest", json=payload)
    assert response.status_code == 400
    assert "Missing required field" in response.json()["detail"]


def test_rejection_invalid_unit():
    """Verifies rejection of invalid units for sensor type with HTTP 400."""
    now_iso = datetime.now(timezone.utc).isoformat()
    payload = {
        "sensor_id": "RAIN-001",
        "sensor_type": "rainfall",
        "village_id": VIL_003,
        "value": 10.0,
        "unit": "psi",  # Invalid unit for rainfall
        "timestamp": now_iso,
    }
    response = client.post("/api/iot/sensors/ingest", json=payload)
    assert response.status_code == 400
    assert "Invalid unit" in response.json()["detail"]


def test_rejection_negative_value():
    """Verifies rejection of impossible negative values with HTTP 400."""
    now_iso = datetime.now(timezone.utc).isoformat()
    payload = {
        "sensor_id": "RAIN-001",
        "sensor_type": "rainfall",
        "village_id": VIL_003,
        "value": -5.0,
        "unit": "mm/h",
        "timestamp": now_iso,
    }
    response = client.post("/api/iot/sensors/ingest", json=payload)
    assert response.status_code == 400
    assert "negative" in response.json()["detail"]


def test_freshness_states_stale_and_offline():
    """Verifies freshness calculation for LIVE, STALE (>10m), and OFFLINE (>30m)."""
    now = datetime.now(timezone.utc)

    # 1. Live (5 mins ago)
    ts_live = (now - timedelta(minutes=5)).isoformat()
    # 2. Stale (15 mins ago)
    ts_stale = (now - timedelta(minutes=15)).isoformat()
    # 3. Offline (45 mins ago)
    ts_offline = (now - timedelta(minutes=45)).isoformat()

    client.post("/api/iot/sensors/ingest", json={"sensor_id": "S1", "sensor_type": "rainfall", "village_id": VIL_003, "value": 5.0, "unit": "mm/h", "timestamp": ts_live})
    client.post("/api/iot/sensors/ingest", json={"sensor_id": "S2", "sensor_type": "soil_moisture", "village_id": VIL_003, "value": 40.0, "unit": "%", "timestamp": ts_stale})
    client.post("/api/iot/sensors/ingest", json={"sensor_id": "S3", "sensor_type": "water_level", "village_id": VIL_003, "value": 1.5, "unit": "m", "timestamp": ts_offline})

    r1 = client.get("/api/iot/sensors/S1").json()
    r2 = client.get("/api/iot/sensors/S2").json()
    r3 = client.get("/api/iot/sensors/S3").json()

    assert r1["status"] == "LIVE"
    assert r2["status"] == "STALE"
    assert r3["status"] == "OFFLINE"


def test_multiple_sensors_and_lookups():
    """Verifies listing all sensors and village-specific sensor lookup endpoints."""
    now_iso = datetime.now(timezone.utc).isoformat()

    client.post("/api/iot/sensors/ingest", json={"sensor_id": "R-1", "sensor_type": "rainfall", "village_id": VIL_003, "value": 8.0, "unit": "mm/h", "timestamp": now_iso})
    client.post("/api/iot/sensors/ingest", json={"sensor_id": "S-1", "sensor_type": "soil_moisture", "village_id": VIL_003, "value": 0.35, "unit": "m3/m3", "timestamp": now_iso})
    client.post("/api/iot/sensors/ingest", json={"sensor_id": "R-2", "sensor_type": "rainfall", "village_id": "VIL-001", "value": 2.0, "unit": "mm/h", "timestamp": now_iso})

    # List all
    all_sensors = client.get("/api/iot/sensors").json()
    assert len(all_sensors) == 3

    # Village lookup
    v3_sensors = client.get("/api/iot/villages/VIL-003/sensors").json()
    assert len(v3_sensors) == 2
    assert {s["sensor_id"] for s in v3_sensors} == {"R-1", "S-1"}


def test_iot_rainfall_source_priority():
    """Verifies that a fresh IoT rainfall sensor overrides Open-Meteo and demo sources without blending."""
    now_iso = datetime.now(timezone.utc).isoformat()

    # Ingest fresh IoT rainfall sensor (18.5 mm/h)
    client.post("/api/iot/sensors/ingest", json={
        "sensor_id": "RAIN-VIP",
        "sensor_type": "rainfall",
        "village_id": VIL_003,
        "value": 18.5,
        "unit": "mm/h",
        "timestamp": now_iso
    })

    pipe = DataIngestionPipeline()
    village_data = next(v for v in DEMO_VILLAGES if v["id"] == VIL_003)

    obs = pipe.get_normalized_observation(village_data["latitude"], village_data["longitude"], VIL_003, scenario=ScenarioType.HEAVY_RAIN, force_offline=False)

    assert obs.current_rainfall_mm_hr == 18.5
    assert obs.rainfall_source == "LIVE_IOT_SENSOR"
    assert obs.data_state == DataSourceState.LIVE_IOT_SENSOR

    snapshot = pipe.convert_to_risk_feature_snapshot(obs, village_data, scenario=ScenarioType.HEAVY_RAIN)
    assert snapshot["current_rainfall"] == 18.5
    assert snapshot["rainfall_source"] == "LIVE_IOT_SENSOR"


def test_iot_soil_m3_per_m3_conversion():
    """Verifies explicit (m3/m3 / 0.50) * 100 conversion for IoT soil moisture."""
    now_iso = datetime.now(timezone.utc).isoformat()

    # Ingest 0.42 m3/m3 -> (0.42 / 0.50) * 100 = 84.0%
    client.post("/api/iot/sensors/ingest", json={
        "sensor_id": "SOIL-M3",
        "sensor_type": "soil_moisture",
        "village_id": VIL_003,
        "value": 0.42,
        "unit": "m3/m3",
        "timestamp": now_iso
    })

    pipe = DataIngestionPipeline()
    village_data = next(v for v in DEMO_VILLAGES if v["id"] == VIL_003)
    obs = pipe.get_normalized_observation(village_data["latitude"], village_data["longitude"], VIL_003, scenario=ScenarioType.HEAVY_RAIN, force_offline=False)

    assert obs.soil_saturation_pct == 84.0
    assert obs.soil_source == "LIVE_IOT_SENSOR"


def test_open_meteo_fallback_when_no_fresh_iot_sensor():
    """Verifies fallback to Open-Meteo / demo when no fresh IoT sensor exists."""
    pipe = DataIngestionPipeline()
    village_data = next(v for v in DEMO_VILLAGES if v["id"] == VIL_003)

    # No IoT sensors ingested
    obs = pipe.get_normalized_observation(village_data["latitude"], village_data["longitude"], VIL_003, scenario=ScenarioType.HEAVY_RAIN, force_offline=False)

    assert obs.data_state != DataSourceState.LIVE_IOT_SENSOR
    assert obs.rainfall_source != "LIVE_IOT_SENSOR"


def test_invalid_sensor_data_does_not_corrupt_valid_sensor():
    """Verifies that failed ingestion attempts do not corrupt previously stored valid sensors."""
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Ingest valid sensor
    res1 = client.post("/api/iot/sensors/ingest", json={"sensor_id": "VALID-1", "sensor_type": "rainfall", "village_id": VIL_003, "value": 14.0, "unit": "mm/h", "timestamp": now_iso})
    assert res1.status_code == 200

    # 2. Ingest invalid payload with same ID (e.g. negative reading)
    res2 = client.post("/api/iot/sensors/ingest", json={"sensor_id": "VALID-1", "sensor_type": "rainfall", "village_id": VIL_003, "value": -99.0, "unit": "mm/h", "timestamp": now_iso})
    assert res2.status_code == 400

    # 3. Check that stored sensor remains valid and unchanged
    stored = client.get("/api/iot/sensors/VALID-1").json()
    assert stored["value"] == 14.0
