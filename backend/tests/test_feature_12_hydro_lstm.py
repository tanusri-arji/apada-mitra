"""
Unit and Integration Tests for Feature 12: Deep Learning Hydrograph Prediction Pipeline.
Validates synthetic catchment time series, LSTM recurrence, hydrological metrics (NSE/R2/RMSE),
peak crest wave dynamics, and FastAPI API routes.
"""
import pytest
import numpy as np
from fastapi.testclient import TestClient
from app.main import app
from app.data.hydro_training_data import (
    generate_catchment_hydrograph_series,
    calculate_nash_sutcliffe,
    calculate_rmse,
    calculate_r2,
)
from app.engine.hydro_lstm_engine import hydro_lstm_engine_instance
from app.models.domain import ScenarioType


client = TestClient(app)


def test_catchment_dataset_generation():
    """Verifies that the synthetic 10-year catchment dataset generates physically valid features and targets."""
    df = generate_catchment_hydrograph_series(num_hours=2000, seed=123)
    assert len(df) == 2000
    assert "precip_mm_h" in df.columns
    assert "soil_saturation_pct" in df.columns
    assert "upstream_stage_m" in df.columns
    assert "stage_t1" in df.columns
    assert "stage_t6" in df.columns

    # Verify physical bounds
    assert (df["precip_mm_h"] >= 0.0).all()
    assert (df["soil_saturation_pct"] >= 15.0).all()
    assert (df["soil_saturation_pct"] <= 100.0).all()
    assert (df["upstream_stage_m"] >= 1.0).all()


def test_hydrological_metrics():
    """Verifies that NSE, RMSE, and R² calculate correctly on standard benchmarks."""
    obs = np.array([2.0, 2.5, 3.0, 4.0, 5.0, 3.5])
    pred_perfect = np.array([2.0, 2.5, 3.0, 4.0, 5.0, 3.5])
    pred_imperfect = np.array([2.1, 2.4, 3.1, 3.9, 4.8, 3.6])

    # Perfect prediction
    assert calculate_nash_sutcliffe(obs, pred_perfect) == 1.0
    assert calculate_rmse(obs, pred_perfect) == 0.0
    assert calculate_r2(obs, pred_perfect) == 1.0

    # Imperfect prediction
    nse = calculate_nash_sutcliffe(obs, pred_imperfect)
    assert nse > 0.95
    rmse = calculate_rmse(obs, pred_imperfect)
    assert rmse < 0.20


def test_hydro_lstm_engine_initialization():
    """Verifies that weights are loaded into the inference engine with expected dimensions."""
    assert hydro_lstm_engine_instance._weights is not None
    assert hydro_lstm_engine_instance.w_ih_l1.shape == (128, 6)
    assert hydro_lstm_engine_instance.w_hh_l1.shape == (128, 32)
    assert hydro_lstm_engine_instance.fc_w.shape == (6, 32)
    assert hydro_lstm_engine_instance.fc_b.shape == (6,)


def test_hydro_lstm_prediction_output_structure():
    """Verifies that 6-hour forward predictions return continuous stages, discharges, and peak metrics."""
    res = hydro_lstm_engine_instance.predict_village_hydrograph("VIL-001", scenario=ScenarioType.NORMAL)

    assert res.village_id == "VIL-001"
    assert res.river_name == "Alaknanda River"
    assert len(res.series) == 6
    assert res.peak_lead_hour in [1, 2, 3, 4, 5, 6]
    assert res.peak_stage_m >= res.initial_stage_m
    assert res.confidence_score >= 0.80

    for idx, pt in enumerate(res.series, start=1):
        assert pt.lead_hour == idx
        assert pt.stage_m > 0.0
        assert pt.discharge_cumec > 0.0
        assert pt.status in ["NORMAL", "ALERT", "WARNING", "DANGER"]


def test_dynamic_rainfall_response():
    """Verifies that heavy cloudburst rain drives significantly higher stages and crests than light rain."""
    res_light = hydro_lstm_engine_instance.predict_village_hydrograph(
        "VIL-001",
        custom_rainfall_mm_h=5.0,
        custom_soil_saturation_pct=30.0,
    )
    res_heavy = hydro_lstm_engine_instance.predict_village_hydrograph(
        "VIL-001",
        custom_rainfall_mm_h=75.0,
        custom_soil_saturation_pct=88.0,
    )

    assert res_heavy.peak_stage_m > res_light.peak_stage_m
    assert res_heavy.danger_exceeded is True
    assert res_light.danger_exceeded is False


def test_api_get_village_hydrograph():
    """Verifies the GET /api/ml/hydrograph/{village_id} endpoint."""
    response = client.get("/api/ml/hydrograph/VIL-001")
    assert response.status_code == 200
    data = response.json()
    assert data["village_id"] == "VIL-001"
    assert len(data["series"]) == 6
    assert "nash_sutcliffe_efficiency" in data["validation_metrics"]
    assert data["validation_metrics"]["nash_sutcliffe_efficiency"] >= 0.86


def test_api_get_village_hydrograph_not_found():
    """Verifies that requesting an invalid village ID returns 404."""
    response = client.get("/api/ml/hydrograph/VIL-INVALID-999")
    assert response.status_code == 404


def test_api_post_simulate_custom_hydrograph():
    """Verifies the POST /api/ml/predict-hydrograph endpoint with custom what-if inputs."""
    payload = {
        "village_id": "VIL-002",
        "rainfall_intensity_mm_h": 65.0,
        "soil_saturation_pct": 82.0,
        "upstream_stage_offset_m": 1.0,
    }
    response = client.post("/api/ml/predict-hydrograph", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["village_id"] == "VIL-002"
    assert data["danger_exceeded"] is True
    assert data["peak_lead_hour"] in [1, 2, 3, 4, 5, 6]
    assert len(data["series"]) == 6


def test_api_model_info_and_health():
    """Verifies transparency metadata and sub-second health check for SIH jury inspection."""
    info_resp = client.get("/api/ml/model-info")
    assert info_resp.status_code == 200
    info = info_resp.json()
    assert info["model_name"] == "APADA-HydroLSTM-v1"
    assert info["benchmarks"]["nash_sutcliffe_efficiency_nse"] >= 0.86
    assert len(info["catchments_covered"]) >= 2

    health_resp = client.get("/api/ml/health")
    assert health_resp.status_code == 200
    health = health_resp.json()
    assert health["status"] == "READY"
    assert health["weights_loaded"] is True
    assert health["inference_latency_ms"] < 20.0  # Ultra-fast <20ms
