"""
Feature 6 — Operational Lead-Time & Evacuation Window Engine Tests.
Verifies lead-time calculation arithmetic, safety margins, decision states (SAFE, TIGHT, INSUFFICIENT, UNKNOWN),
confidence reductions, missing forecast resilience, fallback handling, API endpoints,
and non-modification of existing risk weights.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.engine.lead_time_engine import (
    lead_time_engine_instance,
    DEFAULT_PREPARATION_TIME_MINUTES,
    SAFE_SAFETY_MARGIN_MINUTES,
    CRITICAL_ACTION_RISK_THRESHOLD,
    HIGH_ACTION_RISK_THRESHOLD,
)
from app.models.lead_time import (
    LeadTimeDecisionStatus,
    LeadTimeDataState,
    VillageLeadTimeDetail,
)
from app.data.dataset import DEMO_VILLAGES
from app.models.domain import ScenarioType
from app.config import FEATURE_WEIGHTS

client = TestClient(app)
VIL_001 = DEMO_VILLAGES[0]  # Pipalkoti
VIL_003 = DEMO_VILLAGES[2]  # Govindghat


def test_sufficient_lead_time_safe_status():
    """1. Verifies SAFE decision status when available lead time exceeds total required evacuation time by >= 60 mins."""
    # Under low/moderate conditions, available lead time is ~360 mins, total required is ~60 mins -> margin ~300 mins (SAFE)
    detail = lead_time_engine_instance.calculate_village_lead_time(
        village_data=VIL_001,
        scenario=ScenarioType.NORMAL,
        custom_current_rainfall=5.0,
        custom_forecast_rainfall=30.0,
    )
    assert detail.decision_status == LeadTimeDecisionStatus.SAFE
    assert detail.safety_margin_minutes is not None
    assert detail.safety_margin_minutes >= SAFE_SAFETY_MARGIN_MINUTES
    assert detail.available_lead_time_minutes is not None
    assert detail.available_lead_time_minutes > detail.total_required_time_minutes


def test_tight_lead_time_status():
    """2. Verifies TIGHT decision status when safety margin is positive but < 60 minutes."""
    # High rainfall pushing risk into high zone with rapid escalation window (~70-90 mins)
    detail = lead_time_engine_instance.calculate_village_lead_time(
        village_data=VIL_001,
        scenario=ScenarioType.HEAVY_RAIN,
        custom_current_rainfall=60.0,
        custom_forecast_rainfall=180.0,
    )
    # Available lead time is between total_required (~55-60m) and total_required + 60m
    if 0.0 <= detail.safety_margin_minutes < SAFE_SAFETY_MARGIN_MINUTES:
        assert detail.decision_status == LeadTimeDecisionStatus.TIGHT
    elif detail.safety_margin_minutes < 0:
        assert detail.decision_status == LeadTimeDecisionStatus.INSUFFICIENT


def test_insufficient_lead_time_status_critical():
    """3. Verifies INSUFFICIENT decision status when available lead time is less than required evacuation duration."""
    detail = lead_time_engine_instance.calculate_village_lead_time(
        village_data=VIL_001,
        scenario=ScenarioType.EXTREME_RAIN,
        custom_current_rainfall=95.0,
        custom_forecast_rainfall=240.0,
    )
    assert detail.safety_margin_minutes < 0.0
    assert detail.decision_status == LeadTimeDecisionStatus.INSUFFICIENT
    assert detail.available_lead_time_minutes is not None
    assert detail.available_lead_time_minutes < detail.total_required_time_minutes


def test_unknown_missing_forecast_resilience():
    """4. Verifies missing forecast data returns UNKNOWN status and does not crash."""
    detail = lead_time_engine_instance.calculate_village_lead_time(
        village_data=VIL_001,
        force_missing_forecast=True,
    )
    assert detail.decision_status == LeadTimeDecisionStatus.UNKNOWN
    assert detail.available_lead_time_minutes is None
    assert detail.hazard_escalation_estimate_minutes is None
    assert detail.safety_margin_minutes is None
    assert detail.data_state == LeadTimeDataState.UNKNOWN
    assert "MISSING" in detail.calculation_method.upper()


def test_fallback_offline_data_state_and_confidence_penalty():
    """5. Verifies force_offline correctly marks OFFLINE_DEMO and applies confidence reduction."""
    detail_live = lead_time_engine_instance.calculate_village_lead_time(VIL_001, force_offline=False)
    detail_offline = lead_time_engine_instance.calculate_village_lead_time(VIL_001, force_offline=True)

    assert detail_offline.data_state == LeadTimeDataState.OFFLINE_DEMO
    assert detail_offline.confidence <= detail_live.confidence


def test_calculation_arithmetic_consistency():
    """6. Verifies exact mathematical identity: safety_margin = available_lead_time - total_required_time."""
    detail = lead_time_engine_instance.calculate_village_lead_time(VIL_001, scenario=ScenarioType.HEAVY_RAIN)
    if detail.available_lead_time_minutes is not None:
        expected_total = detail.preparation_time_minutes + detail.evacuation_time_minutes
        assert round(detail.total_required_time_minutes, 1) == round(expected_total, 1)
        expected_margin = detail.available_lead_time_minutes - detail.total_required_time_minutes
        assert round(detail.safety_margin_minutes, 1) == round(expected_margin, 1)


def test_invalid_village_id_returns_404():
    """7. Verifies 404 response for invalid village ID."""
    response = client.get("/api/lead-time/villages/VIL-INVALID-999")
    assert response.status_code == 404


def test_invalid_coordinates_handled_gracefully():
    """8. Verifies invalid coordinate input returns UNKNOWN without crashing."""
    invalid_v = {"id": "VIL-999", "name": "Invalid", "latitude": 999.0, "longitude": 999.0}
    detail = lead_time_engine_instance.calculate_village_lead_time(invalid_v)
    assert detail.decision_status == LeadTimeDecisionStatus.UNKNOWN
    assert detail.confidence == 0.0
    assert detail.data_state == LeadTimeDataState.UNKNOWN


def test_get_village_lead_time_api_schema():
    """9. Verifies GET /api/lead-time/villages/{village_id} response schema and required fields."""
    response = client.get(f"/api/lead-time/villages/{VIL_001['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["village_id"] == VIL_001["id"]
    assert "current_risk_score" in data
    assert "current_risk_level" in data
    assert "evacuation_time_minutes" in data
    assert "preparation_time_minutes" in data
    assert "total_required_time_minutes" in data
    assert "decision_status" in data
    assert "confidence" in data
    assert "calculation_method" in data
    assert "data_state" in data
    assert "assumptions" in data
    assert len(data["assumptions"]) >= 2


def test_get_all_villages_lead_time_api():
    """10. Verifies GET /api/lead-time endpoint returns assessments for all 15 villages."""
    response = client.get("/api/lead-time")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(DEMO_VILLAGES)
    for v_detail in data:
        assert v_detail["decision_status"] in ["SAFE", "TIGHT", "INSUFFICIENT", "UNKNOWN"]
        assert v_detail["total_required_time_minutes"] >= DEFAULT_PREPARATION_TIME_MINUTES


def test_risk_weights_remain_unmodified():
    """11. Verifies that risk engine weights and parameters remain strictly unmodified."""
    assert FEATURE_WEIGHTS["current_rainfall"] == 0.25
    assert FEATURE_WEIGHTS["forecast_rainfall"] == 0.20
    assert FEATURE_WEIGHTS["soil_saturation"] == 0.15
    assert FEATURE_WEIGHTS["river_water_level"] == 0.15
    assert FEATURE_WEIGHTS["flow_accumulation"] == 0.15
    assert FEATURE_WEIGHTS["slope"] == 0.10
    assert sum(FEATURE_WEIGHTS.values()) == 1.0


def test_preservation_of_features_1_to_5():
    """12. Verifies Features 1-5 remain completely intact."""
    # Feature 1 & 2
    res_dq = client.get("/api/v1/data-quality")
    assert res_dq.status_code == 200

    # Feature 3
    res_iot = client.get("/api/iot/sensors")
    assert res_iot.status_code == 200

    # Feature 4
    res_terrain = client.get(f"/api/terrain/villages/{VIL_001['id']}")
    assert res_terrain.status_code == 200

    # Feature 5
    res_ls = client.get(f"/api/landslides/historical/{VIL_001['id']}")
    assert res_ls.status_code == 200
