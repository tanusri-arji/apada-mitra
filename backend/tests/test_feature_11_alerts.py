"""
Feature 11 Test Suite: Real-Time Multi-Hazard Alert Generation & Notification Intelligence.
Validates multi-hazard correlation, severity classification, multilingual generation (EN, HI, TE),
deterministic deduplication, lifecycle escalation, audit trail, simulation delivery status,
and non-regression of Features 1–10.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.alert import (
    AlertSeverity,
    AlertLifecycleState,
    HazardType,
    DeliveryStatus,
    DeliveryMode,
    AlertDataState,
    MultiHazardAlertRecord,
)
from app.engine.alert_engine import (
    alert_engine_instance,
    classify_alert_severity,
    generate_multilingual_messages,
)
from app.adapters.notification_provider import simulation_notification_provider_instance
from app.models.domain import ScenarioType
from app.config import FEATURE_WEIGHTS

client = TestClient(app)


def test_severity_classification_mapping():
    """Validates risk score mapping to alert severity tiers."""
    assert classify_alert_severity(15.0)[0] == AlertSeverity.LOW
    assert classify_alert_severity(45.0)[0] == AlertSeverity.MODERATE
    assert classify_alert_severity(70.0)[0] == AlertSeverity.HIGH
    assert classify_alert_severity(90.0)[0] == AlertSeverity.CRITICAL


def test_low_alert_generation_and_monitoring_action():
    """Scenario A: LOW risk generates monitoring alert with standard recommended action."""
    alert = alert_engine_instance.generate_alert_for_village(
        village_id="VIL-001",
        scenario=ScenarioType.NORMAL,
        force_offline=True,
    )
    assert alert.village_id == "VIL-001"
    assert alert.severity in [AlertSeverity.LOW, AlertSeverity.MODERATE]
    assert "MONITOR" in alert.recommended_action or "PREPARE" in alert.recommended_action
    assert alert.delivery_status == DeliveryStatus.NOT_DELIVERED
    assert alert.delivery_mode == DeliveryMode.SIMULATION


def test_critical_alert_generation_and_immediate_action():
    """Scenario D: CRITICAL risk generates immediate evacuation alert."""
    alert = alert_engine_instance.generate_alert_for_village(
        village_id="VIL-003",
        scenario=ScenarioType.EXTREME_RAIN,
        force_offline=True,
    )
    assert alert.village_id == "VIL-003"
    assert alert.severity == AlertSeverity.CRITICAL
    assert "IMMEDIATE_ACTION_REQUIRED" in alert.recommended_action or "EVACUATE" in alert.recommended_action
    assert alert.evacuation_required is True
    assert alert.associated_incident_id is not None
    assert alert.associated_incident_id.startswith("INC-")


def test_multi_hazard_detection_and_correlation():
    """Scenario C: Multi-hazard scenario correlates both flood and landslide hazards."""
    alert = alert_engine_instance.generate_alert_for_village(
        village_id="VIL-003",
        scenario=ScenarioType.EXTREME_RAIN,
        force_offline=True,
    )
    assert len(alert.hazards_detected) >= 2
    assert HazardType.FLASH_FLOOD in alert.hazards_detected or HazardType.LANDSLIDE in alert.hazards_detected
    assert alert.primary_hazard in [HazardType.FLASH_FLOOD, HazardType.LANDSLIDE, HazardType.HEAVY_RAINFALL]
    assert len(alert.key_contributing_factors) >= 2


def test_evacuation_and_shelter_context_integration():
    """Validates that alert incorporates Features 6, 9, 10 lead-time, roads, and shelters."""
    alert = alert_engine_instance.generate_alert_for_village(
        village_id="VIL-001",
        scenario=ScenarioType.NORMAL,
        force_offline=True,
    )
    assert alert.selected_shelter_id == "SH-01"
    assert "Pipalkoti Central High School" in alert.selected_shelter_name
    assert alert.route_summary is not None
    assert alert.evacuation_context is not None
    assert alert.evacuation_context["route_distance_km"] == 4.5
    assert alert.lead_time is not None
    assert "available_lead_time_minutes" in alert.lead_time


def test_multilingual_message_consistency():
    """Validates structured alert messages in 5 regional languages: English, Hindi, Garhwali, Kumaoni, and Nepali."""
    msgs = generate_multilingual_messages(
        village_name="Pipalkoti",
        severity=AlertSeverity.HIGH,
        primary_hazard=HazardType.FLASH_FLOOD,
        secondary_hazards=[HazardType.LANDSLIDE],
        risk_score=75.0,
        recommended_action="PREPARE_EVACUATION",
        shelter_name="Pipalkoti High School Complex",
        route_distance_km=4.5,
        travel_time_minutes=10.8,
        lead_time_status="SUFFICIENT",
    )
    # 1. English
    assert msgs.en and len(msgs.en) > 0
    assert "APADA MITRA HIGH WARNING — Pipalkoti" in msgs.en
    assert "Flash Flood" in msgs.en
    assert "Distance: 4.5 km" in msgs.en
    assert "PREPARE_EVACUATION" in msgs.en

    # 2. Hindi (हिन्दी)
    assert msgs.hi and len(msgs.hi) > 0
    assert "आपदा मित्र HIGH चेतावनी — Pipalkoti" in msgs.hi or "आपदा मित्र HIGH चेतावनी" in msgs.hi
    assert "आकस्मिक बाढ़" in msgs.hi
    assert "निकासी" in msgs.hi

    # 3. Garhwali (गढ़वाली)
    assert msgs.garhwali and len(msgs.garhwali) > 0
    assert "आपदा मित्र HIGH चेतावनी — Pipalkoti" in msgs.garhwali or "आपदा मित्र HIGH चेतावनी" in msgs.garhwali
    assert "बाढ़" in msgs.garhwali or "प्वार" in msgs.garhwali
    assert "सुरक्षित ठौर" in msgs.garhwali
    assert "बाटो" in msgs.garhwali or "दूरी" in msgs.garhwali

    # 4. Kumaoni (कुमाऊँनी)
    assert msgs.kumaoni and len(msgs.kumaoni) > 0
    assert "आपदा मित्र HIGH चेतावनी — Pipalkoti" in msgs.kumaoni or "आपदा मित्र HIGH चेतावनी" in msgs.kumaoni
    assert "बाढ़" in msgs.kumaoni or "गधेर" in msgs.kumaoni
    assert "सुरक्षित थान" in msgs.kumaoni
    assert "बाट" in msgs.kumaoni or "दूरी" in msgs.kumaoni

    # 5. Nepali (नेपाली)
    assert msgs.nepali and len(msgs.nepali) > 0
    assert "आपदा मित्र HIGH चेतावनी — Pipalkoti" in msgs.nepali or "आपदा मित्र HIGH चेतावनी" in msgs.nepali
    assert "आकस्मिक बाढी" in msgs.nepali or "पहिरो" in msgs.nepali
    assert "सुरक्षित आश्रयस्थल" in msgs.nepali
    assert "सडक" in msgs.nepali or "बाटो" in msgs.nepali or "दूरी" in msgs.nepali

    # 6. Telugu removal verification
    msg_dict = msgs.model_dump()
    assert "te" not in msg_dict
    assert "telugu" not in msg_dict


def test_alert_deduplication():
    """Scenario F: Identical alert generated twice without change is deduplicated."""
    a1 = alert_engine_instance.generate_alert_for_village("VIL-005", ScenarioType.NORMAL, force_offline=True)
    a2 = alert_engine_instance.generate_alert_for_village("VIL-005", ScenarioType.NORMAL, force_offline=True)
    assert a1.alert_id == a2.alert_id
    assert a1.fingerprint == a2.fingerprint


def test_alert_escalation_lifecycle():
    """Scenario G: Risk escalation from NORMAL to EXTREME_RAIN creates new escalated alert."""
    a_low = alert_engine_instance.generate_alert_for_village("VIL-003", ScenarioType.NORMAL, force_offline=True)
    a_crit = alert_engine_instance.generate_alert_for_village("VIL-003", ScenarioType.EXTREME_RAIN, force_offline=True)

    assert a_crit.severity == AlertSeverity.CRITICAL
    assert a_crit.alert_id != a_low.alert_id

    # Check audit trail records escalation
    audit = alert_engine_instance.get_audit_trail()
    escalation_records = [r for r in audit if r.village_id == "VIL-003" and r.action == "ESCALATED"]
    assert len(escalation_records) >= 1


def test_alert_acknowledgement_and_resolution():
    """Validates state transitions: ACKNOWLEDGE and RESOLVE with audit trail logging."""
    alert = alert_engine_instance.generate_alert_for_village("VIL-009", ScenarioType.NORMAL, force_offline=True)

    # 1. Acknowledge
    ack = alert_engine_instance.acknowledge_alert(alert.alert_id, notes="Verified by Chamoli DEOC", actor="OPERATOR_01")
    assert ack.lifecycle_state == AlertLifecycleState.ACKNOWLEDGED

    # 2. Resolve
    res = alert_engine_instance.resolve_alert(alert.alert_id, resolution_notes="Threat passed", actor="OPERATOR_01")
    assert res.lifecycle_state == AlertLifecycleState.RESOLVED


def test_notification_provider_simulation_honesty():
    """Validates that simulation provider strictly exposes NOT_DELIVERED external status."""
    alert = alert_engine_instance.generate_alert_for_village("VIL-001", ScenarioType.NORMAL, force_offline=True)
    status_resp = simulation_notification_provider_instance.get_delivery_status(alert)

    assert status_resp.delivery_status == DeliveryStatus.NOT_DELIVERED
    assert status_resp.delivery_mode == DeliveryMode.SIMULATION
    assert "SIMULATION_ONLY" in status_resp.channels["sms_gateway"]
    assert "UNAVAILABLE" in status_resp.channels["whatsapp_gateway"]
    assert "UNCONFIGURED" in status_resp.channels["government_cap_broadcast"]


def test_api_alerts_endpoints():
    """Validates all Feature 11 REST API endpoints and 5 regional languages."""
    # 1. GET /api/alerts/status
    r_stat = client.get("/api/alerts/status")
    assert r_stat.status_code == 200
    assert r_stat.json()["delivery_mode"] == "SIMULATION"
    langs = r_stat.json()["supported_languages"]
    assert len(langs) == 5
    assert "English" in langs
    assert "Hindi" in langs
    assert "Garhwali" in langs
    assert "Kumaoni" in langs
    assert "Nepali" in langs
    assert "Telugu" not in langs

    # 2. POST /api/alerts/generate/VIL-001
    r_gen = client.post("/api/alerts/generate/VIL-001")
    assert r_gen.status_code == 200
    a_data = r_gen.json()
    alert_id = a_data["alert_id"]
    assert a_data["village_id"] == "VIL-001"

    # 3. GET /api/alerts/{alert_id}
    r_det = client.get(f"/api/alerts/{alert_id}")
    assert r_det.status_code == 200
    assert r_det.json()["alert_id"] == alert_id
    msgs_data = r_det.json()["messages"]
    assert "en" in msgs_data
    assert "hi" in msgs_data
    assert "garhwali" in msgs_data
    assert "kumaoni" in msgs_data
    assert "nepali" in msgs_data
    assert "te" not in msgs_data

    # 4. GET /api/alerts/villages/VIL-001
    r_vil = client.get("/api/alerts/villages/VIL-001")
    assert r_vil.status_code == 200
    assert len(r_vil.json()) >= 1

    # 5. POST /api/alerts/{alert_id}/acknowledge
    r_ack = client.post(f"/api/alerts/{alert_id}/acknowledge", params={"notes": "EOC ack"})
    assert r_ack.status_code == 200
    assert r_ack.json()["lifecycle_state"] == "ACKNOWLEDGED"

    # 6. GET /api/alerts/{alert_id}/message
    r_msg = client.get(f"/api/alerts/{alert_id}/message")
    assert r_msg.status_code == 200
    m_body = r_msg.json()
    assert "en" in m_body
    assert "hi" in m_body
    assert "garhwali" in m_body
    assert "kumaoni" in m_body
    assert "nepali" in m_body
    assert "te" not in m_body
    assert "telugu" not in m_body

    # 7. GET /api/alerts/{alert_id}/delivery-status
    r_del = client.get(f"/api/alerts/{alert_id}/delivery-status")
    assert r_del.status_code == 200
    assert r_del.json()["delivery_status"] == "NOT_DELIVERED"
    assert r_del.json()["delivery_mode"] == "SIMULATION"



def test_features_1_to_10_integrity_preserved():
    """Ensures that Feature 1–10 formulas, weights, and modules remain frozen and unaffected."""
    assert FEATURE_WEIGHTS["current_rainfall"] == 0.25
    assert FEATURE_WEIGHTS["forecast_rainfall"] == 0.20
    assert FEATURE_WEIGHTS["soil_saturation"] == 0.15
    assert FEATURE_WEIGHTS["river_water_level"] == 0.15
    assert FEATURE_WEIGHTS["flow_accumulation"] == 0.15
    assert FEATURE_WEIGHTS["slope"] == 0.10
    assert sum(FEATURE_WEIGHTS.values()) == 1.0
