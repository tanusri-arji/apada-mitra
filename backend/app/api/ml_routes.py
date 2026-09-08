"""
FastAPI Route Handlers for Deep Learning Hydrograph Prediction (Feature 12).
Provides 6-hour forward flood stage forecasting, wave crest timing, and model benchmark transparency.
"""
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Path

from app.models.ml_models import (
    HydrographPredictionResponse,
    WhatIfHydrographRequest,
    ModelBenchmarkInfoResponse,
)
from app.models.domain import ScenarioType
from app.engine.hydro_lstm_engine import hydro_lstm_engine_instance
from app.data.dataset import DEMO_VILLAGES


router = APIRouter(prefix="/ml", tags=["Deep Learning Hydrology"])


@router.get(
    "/hydrograph/{village_id}",
    response_model=HydrographPredictionResponse,
    summary="Get 6-hour forward hydrograph prediction for a specific village reach",
)
def get_village_hydrograph_prediction(
    village_id: str = Path(..., description="Target village ID (e.g. VIL-001)"),
    scenario: ScenarioType = Query(
        ScenarioType.HEAVY_RAIN,
        description="Hydro-meteorological scenario (NORMAL, HEAVY_RAIN, EXTREME_RAIN)",
    ),
):
    """
    Computes 6-hour forward river stage height, discharge rate, and flood crest lead time
    using the 2-Layer Recurrent LSTM trained on 10 monsoon seasons of Himalayan hydrographs.
    """
    village = next((v for v in DEMO_VILLAGES if v["id"] == village_id), None)
    if not village:
        raise HTTPException(status_code=404, detail=f"Village with ID '{village_id}' not found.")

    try:
        prediction = hydro_lstm_engine_instance.predict_village_hydrograph(
            village_id=village_id,
            scenario=scenario,
        )
        return prediction
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Hydrograph prediction calculation failed: {str(e)}",
        )


@router.post(
    "/predict-hydrograph",
    response_model=HydrographPredictionResponse,
    summary="Run what-if scenario simulation with custom rainfall and soil moisture",
)
def simulate_custom_hydrograph(request: WhatIfHydrographRequest):
    """
    Simulates custom cloudburst or heavy rainfall scenarios to test flood wave cresting,
    danger threshold exceedance, and evacuation lead times.
    """
    v_id = request.village_id or "VIL-001"
    village = next((v for v in DEMO_VILLAGES if v["id"] == v_id), None)
    if not village:
        v_id = "VIL-001"

    try:
        prediction = hydro_lstm_engine_instance.predict_village_hydrograph(
            village_id=v_id,
            scenario=ScenarioType.HEAVY_RAIN,
            custom_rainfall_mm_h=request.rainfall_intensity_mm_h,
            custom_soil_saturation_pct=request.soil_saturation_pct,
            upstream_stage_offset_m=request.upstream_stage_offset_m or 0.0,
        )
        return prediction
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"What-if hydrograph simulation failed: {str(e)}",
        )


@router.get(
    "/model-info",
    response_model=ModelBenchmarkInfoResponse,
    summary="Get model architecture, dataset provenance, and validation benchmarks",
)
def get_model_benchmark_info():
    """
    Returns complete transparent AI/ML evaluation metrics:
    Nash-Sutcliffe Efficiency (NSE >= 0.88), R², RMSE, and 10-year training provenance.
    """
    return hydro_lstm_engine_instance.get_benchmark_info()


@router.get(
    "/health",
    summary="Check status of HydroLSTM inference engine",
)
def check_ml_health():
    """Returns runtime latency and model loading status."""
    t0 = time.perf_counter()
    # Execute dummy forward pass
    _ = hydro_lstm_engine_instance.predict_stages(
        precip_mm_h=10.0,
        cum_24h_precip_mm=40.0,
        soil_saturation_pct=60.0,
        upstream_stage_m=2.0,
    )
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 3)

    return {
        "status": "READY",
        "engine": "HydroLSTM-v1",
        "weights_loaded": hydro_lstm_engine_instance._weights is not None,
        "inference_latency_ms": latency_ms,
        "runtime": "Vectorized NumPy Recurrent Forward Pass",
        "device": "CPU-Edge-Ready",
    }
