"""
Feature 11: Real-Time Multi-Hazard Alert Generation & Notification Intelligence Engine.
Couples multi-hazard risk signals (flash flood, landslide, rainfall, river telemetry, road blockages, shelter availability, lead-time),
determines alert severity, generates structured multilingual warning messages (English, Hindi, Garhwali, Kumaoni, Nepali),
enforces deterministic deduplication, maintains an auditable lifecycle, and links with incident command.

"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import hashlib
from app.models.alert import (
    AlertSeverity,
    AlertLifecycleState,
    HazardType,
    DeliveryStatus,
    DeliveryMode,
    AlertDataState,
    MultilingualAlertText,
    AlertAuditRecord,
    MultiHazardAlertRecord,
    AlertStatusResponse,
)
from app.models.domain import ScenarioType, RiskLevel
from app.data.dataset import DEMO_VILLAGES
from app.data_pipeline import pipeline_instance
from app.engine.risk_engine import calculate_flash_flood_risk
from app.engine.landslide_engine import calculate_landslide_risk
from app.engine.lead_time_engine import lead_time_engine_instance
from app.engine.shelter_suitability_engine import shelter_suitability_engine_instance
from app.engine.road_hazard_engine import road_hazard_engine_instance
from app.adapters.notification_provider import simulation_notification_provider_instance


def classify_alert_severity(risk_score: float) -> Tuple[AlertSeverity, str]:
    """Maps composite hazard risk score (0-100) to standard operational alert severity."""
    if risk_score >= 80.0:
        return AlertSeverity.CRITICAL, "CRITICAL"
    elif risk_score >= 60.0:
        return AlertSeverity.HIGH, "HIGH"
    elif risk_score >= 30.0:
        return AlertSeverity.MODERATE, "MODERATE"
    else:
        return AlertSeverity.LOW, "LOW"


def generate_multilingual_messages(
    village_name: str,
    severity: AlertSeverity,
    primary_hazard: HazardType,
    secondary_hazards: List[HazardType],
    risk_score: float,
    recommended_action: str,
    shelter_name: Optional[str],
    route_distance_km: Optional[float],
    travel_time_minutes: Optional[float],
    lead_time_status: Optional[str],
) -> MultilingualAlertText:
    """
    Generates consistent, high-fidelity emergency warning messages in 5 regional languages
    essential for the Himalayan Uttarakhand geography: English, Hindi, Garhwali, Kumaoni, and Nepali.
    """
    # English translation terms
    hazard_en_map = {
        HazardType.FLASH_FLOOD: "Flash Flood",
        HazardType.LANDSLIDE: "Landslide",
        HazardType.RIVER_LEVEL: "High River Surge",
        HazardType.HEAVY_RAINFALL: "Extreme Rainfall / Cloudburst",
        HazardType.ROAD_ACCESS: "Road Blockage / Access Hazard",
        HazardType.SHELTER_SAFETY: "Shelter Hazard",
        HazardType.MULTI_HAZARD: "Combined Flash Flood & Landslide Multi-Hazard",
    }
    
    # Hindi translation terms (हिन्दी)
    hazard_hi_map = {
        HazardType.FLASH_FLOOD: "आकस्मिक बाढ़ (Flash Flood)",
        HazardType.LANDSLIDE: "भूस्खलन (Landslide)",
        HazardType.RIVER_LEVEL: "नदी जलस्तर वृद्धि",
        HazardType.HEAVY_RAINFALL: "अति भारी वर्षा / बादल फटना",
        HazardType.ROAD_ACCESS: "सड़क अवरोध / मार्ग खतरा",
        HazardType.SHELTER_SAFETY: "राहत केंद्र सुरक्षा जोखिम",
        HazardType.MULTI_HAZARD: "बाढ़ एवं भूस्खलन बहु-आपदा",
    }
    
    # Garhwali translation terms (गढ़वाली - Central Pahari)
    hazard_gar_map = {
        HazardType.FLASH_FLOOD: "अचानक ऐणी बाढ़ (Flash Flood)",
        HazardType.LANDSLIDE: "प्वार गिरण / पहाड़ खिसकण (Landslide)",
        HazardType.RIVER_LEVEL: "गाड़-गदेरा / नदी उफान",
        HazardType.HEAVY_RAINFALL: "मूसलाधार बरखा / फाट्यो बादल",
        HazardType.ROAD_ACCESS: "बाटो बंद / रस्ता टूट्युं",
        HazardType.SHELTER_SAFETY: "सुरक्षित ठौर खतरा",
        HazardType.MULTI_HAZARD: "बाढ़ अर भूस्खलन द्वि-आपदा",
    }

    # Kumaoni translation terms (कुमाऊँनी - Central Pahari)
    hazard_kum_map = {
        HazardType.FLASH_FLOOD: "अचानक औणि बाढ़ / गधेर बाढ़ (Flash Flood)",
        HazardType.LANDSLIDE: "पथर/डांग खिसकण (Landslide)",
        HazardType.RIVER_LEVEL: "गाड़-नदी उफान / जलस्तर बढ़ौत",
        HazardType.HEAVY_RAINFALL: "मूसलधार पाणि / बादल फुटण",
        HazardType.ROAD_ACCESS: "बाट बन्न / रस्तो टूटण",
        HazardType.SHELTER_SAFETY: "सुरक्षित थान जोखिम",
        HazardType.MULTI_HAZARD: "बाढ़ और भूस्खलन दु-आपदा",
    }

    # Nepali translation terms (नेपाली)
    hazard_ne_map = {
        HazardType.FLASH_FLOOD: "आकस्मिक बाढी (Flash Flood)",
        HazardType.LANDSLIDE: "पहिरो / भूस्खलन (Landslide)",
        HazardType.RIVER_LEVEL: "नदीको सतह वृद्धि / बाढीको खतरा",
        HazardType.HEAVY_RAINFALL: "अति भारी वर्षा / बादल फुट्ने",
        HazardType.ROAD_ACCESS: "सडक अवरुद्ध / बाटो बन्द",
        HazardType.SHELTER_SAFETY: "आश्रयस्थल सुरक्षा जोखिम",
        HazardType.MULTI_HAZARD: "बाढी तथा पहिरो बहु-प्रकोप",
    }

    p_en = hazard_en_map.get(primary_hazard, "Multi-Hazard")
    p_hi = hazard_hi_map.get(primary_hazard, "बहु-आपदा")
    p_gar = hazard_gar_map.get(primary_hazard, "द्वि-आपदा")
    p_kum = hazard_kum_map.get(primary_hazard, "दु-आपदा")
    p_ne = hazard_ne_map.get(primary_hazard, "बहु-प्रकोप")

    # Shelters
    shelter_en = shelter_name or "NO_SAFE_SHELTER (Seek highest accessible ground immediately)"
    shelter_hi = shelter_name or "कोई सुरक्षित आश्रय उपलब्ध नहीं (तत्काल ऊंचे स्थान पर जाएं)"
    shelter_gar = shelter_name or "कोइ सुरक्षित ठौर नि च (उंचा डांडा मा जावा)"
    shelter_kum = shelter_name or "कोई सुरक्षित थान न्है (उंच थान मा जावा)"
    shelter_ne = shelter_name or "कुनै सुरक्षित आश्रयस्थल छैन (तुरुन्तै उच्च स्थानमा जानुहोस्)"

    # Routes
    route_en = f"Distance: {route_distance_km:.1f} km, Est. Travel Time: {travel_time_minutes:.1f} mins" if route_distance_km else "Route: Impassable / Blocked"
    route_hi = f"दूरी: {route_distance_km:.1f} किमी, अनुमानित समय: {travel_time_minutes:.1f} मिनट" if route_distance_km else "मार्ग: अवरुद्ध / अगम्य"
    route_gar = f"दूरी: {route_distance_km:.1f} किमी, लगण वाळू बखत: {travel_time_minutes:.1f} मिनट" if route_distance_km else "बाटो: बंद / अगम्य"
    route_kum = f"दूरी: {route_distance_km:.1f} किमी, अनुमानित टैम: {travel_time_minutes:.1f} मिनट" if route_distance_km else "बाट: बन्न / खतरनाक"
    route_ne = f"दूरी: {route_distance_km:.1f} किमी, अनुमानित समय: {travel_time_minutes:.1f} मिनेट" if route_distance_km else "बाटो: अवरुद्ध / खतरनाक"

    # Action localization
    action_hi_map = {
        "MONITOR": "निगरानी रखें (MONITOR)। सतर्क रहें।",
        "PREPARE": "तैयारी करें (PREPARE)। जरूरी सामान समेटें।",
        "PREPARE_EVACUATION": "सुरक्षित निकासी की तैयारी करें (PREPARE EVACUATION)।",
        "EVACUATE": "तत्काल सुरक्षित स्थान पर जाएं (EVACUATE)!",
        "IMMEDIATE_ACTION_REQUIRED": "तत्काल कार्रवाई आवश्यक (IMMEDIATE ACTION REQUIRED)!",
    }
    action_gar_map = {
        "MONITOR": "देखरेख रखा (MONITOR)। सतर्क रया।",
        "PREPARE": "तैयरी करा (PREPARE)। जरूरी सामान समेटा।",
        "PREPARE_EVACUATION": "निकासी तैयरी करा (PREPARE EVACUATION)।",
        "EVACUATE": "तुरंत सुरक्षित ठौर जावा (EVACUATE)!",
        "IMMEDIATE_ACTION_REQUIRED": "अबे-कि-अबे सुरक्षित ठौर पुज्जा (IMMEDIATE ACTION REQUIRED)!",
    }
    action_kum_map = {
        "MONITOR": "ध्यान रखा (MONITOR)। सतर्क रौ।",
        "PREPARE": "तयारी करा (PREPARE)। जरूरी सामान जोड़ा।",
        "PREPARE_EVACUATION": "निकासी की तैयारी करा (PREPARE EVACUATION)।",
        "EVACUATE": "तुरंत सुरक्षित थान जावा (EVACUATE)!",
        "IMMEDIATE_ACTION_REQUIRED": "झटपट सुरक्षित थान पुजा (IMMEDIATE ACTION REQUIRED)!",
    }
    action_ne_map = {
        "MONITOR": "निगरानी गर्नुहोस् (MONITOR)। सतर्क रहनुहोस्।",
        "PREPARE": "तयारी अवस्थामा रहनुहोस् (PREPARE)।",
        "PREPARE_EVACUATION": "सुरक्षित ठाउँमा सर्न तयारी गर्नुहोस् (PREPARE EVACUATION)।",
        "EVACUATE": "तत्काल सुरक्षित स्थानमा जानुहोस् (EVACUATE)!",
        "IMMEDIATE_ACTION_REQUIRED": "तुरुन्तै सुरक्षित स्थानमा जानुहोस् (IMMEDIATE ACTION REQUIRED)!",
    }

    act_hi = action_hi_map.get(recommended_action, recommended_action)
    act_gar = action_gar_map.get(recommended_action, recommended_action)
    act_kum = action_kum_map.get(recommended_action, recommended_action)
    act_ne = action_ne_map.get(recommended_action, recommended_action)

    en_msg = (
        f"🚨 APADA MITRA {severity.value} WARNING — {village_name}\n"
        f"Hazard: {p_en} (Risk Score: {risk_score:.1f}/100)\n"
        f"Action: {recommended_action}\n"
        f"Evacuation Target: {shelter_en}\n"
        f"{route_en}\n"
        f"Lead Time Window: {lead_time_status or 'NORMAL'}"
    )

    hi_msg = (
        f"🚨 आपदा मित्र {severity.value} चेतावनी — {village_name}\n"
        f"खतरा: {p_hi} (जोखिम स्कोर: {risk_score:.1f}/100)\n"
        f"कार्रवाई: {act_hi}\n"
        f"निकासी केंद्र: {shelter_hi}\n"
        f"{route_hi}\n"
        f"निकासी समय स्थिति: {lead_time_status or 'सामान्य'}"
    )

    gar_msg = (
        f"🚨 आपदा मित्र {severity.value} चेतावनी — {village_name}\n"
        f"खतरो: {p_gar} (जोखिम स्कोर: {risk_score:.1f}/100)\n"
        f"कार्रवाई: {act_gar}\n"
        f"सुरक्षित ठौर: {shelter_gar}\n"
        f"{route_gar}\n"
        f"निकासी बखत स्थिति: {lead_time_status or 'सामान्य'}"
    )

    kum_msg = (
        f"🚨 आपदा मित्र {severity.value} चेतावनी — {village_name}\n"
        f"खतरो: {p_kum} (जोखिम स्कोर: {risk_score:.1f}/100)\n"
        f"कार्रवाई: {act_kum}\n"
        f"सुरक्षित थान: {shelter_kum}\n"
        f"{route_kum}\n"
        f"निकासी टैम स्थिति: {lead_time_status or 'सामान्य'}"
    )

    ne_msg = (
        f"🚨 आपदा मित्र {severity.value} चेतावनी — {village_name}\n"
        f"खतरा: {p_ne} (जोखिम स्कोर: {risk_score:.1f}/100)\n"
        f"कार्रवाई: {act_ne}\n"
        f"सुरक्षित आश्रयस्थल: {shelter_ne}\n"
        f"{route_ne}\n"
        f"निकासी समय स्थिति: {lead_time_status or 'सामान्य'}"
    )

    return MultilingualAlertText(
        en=en_msg,
        hi=hi_msg,
        garhwali=gar_msg,
        kumaoni=kum_msg,
        nepali=ne_msg,
        gar=gar_msg,
        kum=kum_msg,
        ne=ne_msg,
    )



class AlertEngine:
    """
    Real-Time Multi-Hazard Alert Generation, Deduplication, and Lifecycle Engine.
    """

    def __init__(self):
        self._alerts_store: Dict[str, MultiHazardAlertRecord] = {}
        self._audit_trail: List[AlertAuditRecord] = []
        self._alert_counter = 1

    def generate_alert_for_village(
        self,
        village_id: str,
        scenario: ScenarioType = ScenarioType.HEAVY_RAIN,
        force_offline: bool = False,
        operator_notes: Optional[str] = None,
    ) -> MultiHazardAlertRecord:
        """
        Synthesizes multi-hazard risk, lead-time, roads, and shelters to generate an auditable alert.
        Enforces deterministic deduplication unless risk escalates.
        """
        village = next((v for v in DEMO_VILLAGES if v["id"] == village_id), None)
        if not village:
            raise ValueError(f"Village ID '{village_id}' not found.")

        v_name = village["name"]

        # 1. Feature 1 & Risk Engine Flood Calculation
        if force_offline:
            from app.data.dataset import get_village_feature_snapshot
            snapshot = get_village_feature_snapshot(village_id, scenario)
        else:
            obs = pipeline_instance.get_normalized_observation(
                village["latitude"], village["longitude"], village_id, scenario
            )
            snapshot = pipeline_instance.convert_to_risk_feature_snapshot(obs, village, scenario)

        risk_res = calculate_flash_flood_risk(snapshot)
        flood_score = risk_res["flash_flood_risk_score"]
        confidence_val = risk_res.get("confidence", 100.0)

        # 2. Feature 5 Landslide Calculation
        ls_detail = calculate_landslide_risk(village_id, v_name, snapshot)
        ls_score = ls_detail.landslide_risk_score

        # 3. Multi-Hazard Correlation & Detection
        hazards_detected: List[HazardType] = []
        rainfall_val = snapshot.get("current_rainfall") or 0.0
        soil_val = snapshot.get("soil_saturation") or 0.0
        river_val = snapshot.get("river_water_level") or 1.0

        if flood_score >= 30.0 or rainfall_val >= 25.0:
            hazards_detected.append(HazardType.FLASH_FLOOD)
        if ls_score >= 30.0 or soil_val >= 70.0:
            hazards_detected.append(HazardType.LANDSLIDE)
        if rainfall_val >= 40.0:
            hazards_detected.append(HazardType.HEAVY_RAINFALL)
        if river_val >= 1.8:
            hazards_detected.append(HazardType.RIVER_LEVEL)

        if not hazards_detected:
            hazards_detected.append(HazardType.FLASH_FLOOD)

        # Primary vs Secondary Hazard
        if flood_score >= ls_score:
            primary_hazard = HazardType.FLASH_FLOOD if flood_score >= 30.0 else HazardType.HEAVY_RAINFALL
            secondary = [h for h in hazards_detected if h != primary_hazard]
        else:
            primary_hazard = HazardType.LANDSLIDE
            secondary = [h for h in hazards_detected if h != primary_hazard]

        composite_risk_score = round(max(flood_score, ls_score), 1)
        severity, severity_str = classify_alert_severity(composite_risk_score)

        # 4. Feature 6 Lead-Time Evaluation
        try:
            lead_time_res = lead_time_engine_instance.calculate_village_lead_time(
                village_data=village,
                scenario=scenario,
                force_offline=force_offline,
            )
            lead_time_dict = {
                "available_lead_time_minutes": lead_time_res.available_lead_time_minutes,
                "total_required_time_minutes": lead_time_res.total_required_time_minutes,
                "decision_status": lead_time_res.decision_status.value,
                "margin_minutes": lead_time_res.safety_margin_minutes,
            }
            lead_time_status = lead_time_res.decision_status.value
            insufficient_time = lead_time_res.decision_status.value in ["INSUFFICIENT_TIME", "CRITICAL_DEFICIT"]
        except Exception:
            lead_time_dict = None
            lead_time_status = "UNKNOWN"
            insufficient_time = False

        # 5. Feature 9 & 10 Shelter & Road Evaluation
        try:
            shelter_rec = shelter_suitability_engine_instance.evaluate_village_shelters(
                village_id=village_id,
                scenario=scenario,
                force_offline=force_offline,
            )
            has_safe_shelter = shelter_rec.status == "SAFE_SHELTER_FOUND"
            selected_shelter_id = shelter_rec.selected_shelter_id if has_safe_shelter else None
            selected_shelter_name = shelter_rec.selected_shelter_name if has_safe_shelter else "NO_SAFE_SHELTER"
            route_dist = shelter_rec.route_distance_km
            travel_time = shelter_rec.travel_time_minutes
            route_safety = shelter_rec.route_safety_score
            blocked_segs = shelter_rec.blocked_segments
            degraded_segs = shelter_rec.degraded_segments
            evac_context = {
                "route_distance_km": route_dist,
                "travel_time_minutes": travel_time,
                "route_safety_score": route_safety,
                "blocked_segments": blocked_segs,
                "degraded_segments": degraded_segs,
                "shelter_status": shelter_rec.status,
            }
            route_summary = f"{route_dist} km to {selected_shelter_name} (Travel Time: {travel_time} mins, Safety: {route_safety}%)" if has_safe_shelter else "NO_SAFE_ROUTE (All routes impassable)"
        except Exception:
            selected_shelter_id = None
            selected_shelter_name = "NO_SAFE_SHELTER"
            route_dist = None
            travel_time = None
            route_safety = None
            blocked_segs = []
            degraded_segs = []
            evac_context = None
            route_summary = "NO_SAFE_SHELTER"

        # 6. Recommended Action Formulation
        evac_required = severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL] or insufficient_time

        if severity == AlertSeverity.LOW:
            action = "MONITOR — Maintain standard hydro-meteorological observation."
        elif severity == AlertSeverity.MODERATE:
            action = "PREPARE — Alert emergency response teams and test communication relays."
        elif severity == AlertSeverity.HIGH:
            if insufficient_time:
                action = "IMMEDIATE_ACTION_REQUIRED: EVACUATE_HIGH_RISK_AREAS — Available evacuation window is narrow."
            else:
                action = "PREPARE_EVACUATION — Stage relief transport and ready community shelters."
        else:  # CRITICAL
            action = "IMMEDIATE_ACTION_REQUIRED: EVACUATE — Execute complete village evacuation to designated safe shelter."

        # Key Contributing Factors
        factors: List[str] = []
        if rainfall_val >= 25.0:
            factors.append(f"High Rainfall Intensity ({rainfall_val:.1f} mm/hr)")
        if soil_val >= 60.0:
            factors.append(f"Elevated Soil Saturation ({soil_val:.1f}%)")
        if river_val >= 1.5:
            factors.append(f"River Stage Surge Multiplier ({river_val:.2f}x)")
        if flood_score >= 50.0:
            factors.append(f"High Flash Flood Risk ({flood_score:.1f} pts)")
        if ls_score >= 50.0:
            factors.append(f"Severe Landslide Risk ({ls_score:.1f} pts)")
        if insufficient_time:
            factors.append(f"Insufficient Evacuation Lead-Time ({lead_time_status})")
        if blocked_segs:
            factors.append(f"Road Network Blockages ({len(blocked_segs)} segments impassable)")
        if not factors:
            factors.append("Environmental parameters within normal seasonal variations")

        # Multilingual Message Generation
        multilingual_msgs = generate_multilingual_messages(
            village_name=v_name,
            severity=severity,
            primary_hazard=primary_hazard,
            secondary_hazards=secondary,
            risk_score=composite_risk_score,
            recommended_action=action,
            shelter_name=selected_shelter_name if selected_shelter_id else None,
            route_distance_km=route_dist,
            travel_time_minutes=travel_time,
            lead_time_status=lead_time_status,
        )

        # 7. Deduplication & Escalation Fingerprint
        fp_raw = f"{village_id}:{severity.value}:{primary_hazard.value}:{int(composite_risk_score // 5)}:{evac_required}:{selected_shelter_id}"
        fingerprint = hashlib.md5(fp_raw.encode("utf-8")).hexdigest()

        # Check existing alerts for this village
        existing_active = [
            a for a in self._alerts_store.values()
            if a.village_id == village_id and a.lifecycle_state in [AlertLifecycleState.NEW, AlertLifecycleState.ACKNOWLEDGED, AlertLifecycleState.ESCALATED]
        ]

        now_iso = datetime.now(timezone.utc).isoformat()

        if existing_active:
            latest = existing_active[-1]
            # If identical fingerprint and no severity escalation, return existing deduplicated alert
            if latest.fingerprint == fingerprint and latest.severity == severity:
                return latest

            # If severity increased (e.g. MODERATE -> HIGH or HIGH -> CRITICAL), escalate previous alert
            if (severity == AlertSeverity.CRITICAL and latest.severity != AlertSeverity.CRITICAL) or \
               (severity == AlertSeverity.HIGH and latest.severity in [AlertSeverity.LOW, AlertSeverity.MODERATE]):
                latest.lifecycle_state = AlertLifecycleState.ESCALATED
                self._audit_trail.append(
                    AlertAuditRecord(
                        timestamp=now_iso,
                        alert_id=latest.alert_id,
                        village_id=village_id,
                        action="ESCALATED",
                        previous_state=latest.severity.value,
                        new_state=severity.value,
                        reason=f"Hazard escalated from {latest.severity.value} to {severity.value} (Risk score: {composite_risk_score})",
                        actor="SYSTEM",
                    )
                )

        # 8. Create New Multi-Hazard Alert Record
        alert_id = f"ALT-{village_id}-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{self._alert_counter:03d}"
        self._alert_counter += 1

        alert_record = MultiHazardAlertRecord(
            alert_id=alert_id,
            village_id=village_id,
            village_name=v_name,
            generated_at=now_iso,
            severity=severity,
            lifecycle_state=AlertLifecycleState.NEW,
            primary_hazard=primary_hazard,
            secondary_hazards=secondary,
            hazards_detected=hazards_detected,
            risk_score=composite_risk_score,
            risk_level=severity_str,
            reason=f"Multi-hazard evaluation triggered by {primary_hazard.value} risk score {composite_risk_score:.1f}.",
            key_contributing_factors=factors,
            recommended_action=action,
            evacuation_required=evac_required,
            selected_shelter_id=selected_shelter_id,
            selected_shelter_name=selected_shelter_name,
            route_summary=route_summary,
            lead_time=lead_time_dict,
            evacuation_context=evac_context,
            confidence=confidence_val,
            data_state=AlertDataState.OFFLINE_DEMO,
            delivery_status=DeliveryStatus.NOT_DELIVERED,
            delivery_mode=DeliveryMode.SIMULATION,
            messages=multilingual_msgs,
            associated_incident_id=f"INC-{village_id}-20260905" if severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL] else None,
            fingerprint=fingerprint,
        )

        self._alerts_store[alert_id] = alert_record

        # Audit Trail for Alert Generation
        self._audit_trail.append(
            AlertAuditRecord(
                timestamp=now_iso,
                alert_id=alert_id,
                village_id=village_id,
                action="ALERT_GENERATED",
                previous_state=None,
                new_state=AlertLifecycleState.NEW.value,
                reason=f"Generated {severity.value} alert for {v_name} with risk score {composite_risk_score}.",
                actor="SYSTEM",
            )
        )

        return alert_record

    def acknowledge_alert(self, alert_id: str, notes: Optional[str] = None, actor: str = "OPERATOR") -> MultiHazardAlertRecord:
        """Transitions alert to ACKNOWLEDGED state and writes to audit trail."""
        alert = self._alerts_store.get(alert_id)
        if not alert:
            raise ValueError(f"Alert ID '{alert_id}' not found.")

        prev_state = alert.lifecycle_state.value
        alert.lifecycle_state = AlertLifecycleState.ACKNOWLEDGED
        now_iso = datetime.now(timezone.utc).isoformat()

        self._audit_trail.append(
            AlertAuditRecord(
                timestamp=now_iso,
                alert_id=alert_id,
                village_id=alert.village_id,
                action="ACKNOWLEDGED",
                previous_state=prev_state,
                new_state=AlertLifecycleState.ACKNOWLEDGED.value,
                reason=notes or "Operator acknowledged alert and initiated situation response.",
                actor=actor,
            )
        )
        return alert

    def escalate_alert(self, alert_id: str, reason: str, actor: str = "OPERATOR") -> MultiHazardAlertRecord:
        """Manually or programmatically escalates an alert and writes to audit trail."""
        alert = self._alerts_store.get(alert_id)
        if not alert:
            raise ValueError(f"Alert ID '{alert_id}' not found.")

        prev_state = alert.lifecycle_state.value
        alert.lifecycle_state = AlertLifecycleState.ESCALATED
        now_iso = datetime.now(timezone.utc).isoformat()

        self._audit_trail.append(
            AlertAuditRecord(
                timestamp=now_iso,
                alert_id=alert_id,
                village_id=alert.village_id,
                action="ESCALATED",
                previous_state=prev_state,
                new_state=AlertLifecycleState.ESCALATED.value,
                reason=reason,
                actor=actor,
            )
        )
        return alert

    def resolve_alert(self, alert_id: str, resolution_notes: Optional[str] = None, actor: str = "OPERATOR") -> MultiHazardAlertRecord:
        """Resolves an alert and writes to audit trail."""
        alert = self._alerts_store.get(alert_id)
        if not alert:
            raise ValueError(f"Alert ID '{alert_id}' not found.")

        prev_state = alert.lifecycle_state.value
        alert.lifecycle_state = AlertLifecycleState.RESOLVED
        now_iso = datetime.now(timezone.utc).isoformat()

        self._audit_trail.append(
            AlertAuditRecord(
                timestamp=now_iso,
                alert_id=alert_id,
                village_id=alert.village_id,
                action="RESOLVED",
                previous_state=prev_state,
                new_state=AlertLifecycleState.RESOLVED.value,
                reason=resolution_notes or "Disaster threat subsided; emergency all-clear issued.",
                actor=actor,
            )
        )
        return alert

    def get_alert_by_id(self, alert_id: str) -> Optional[MultiHazardAlertRecord]:
        return self._alerts_store.get(alert_id)

    def get_alerts_for_village(self, village_id: str) -> List[MultiHazardAlertRecord]:
        return [a for a in self._alerts_store.values() if a.village_id == village_id]

    def get_all_alerts(self) -> List[MultiHazardAlertRecord]:
        return list(self._alerts_store.values())

    def get_audit_trail(self) -> List[AlertAuditRecord]:
        return list(self._audit_trail)

    def get_system_status(self) -> AlertStatusResponse:
        """Returns aggregate alert subsystem status."""
        alerts = list(self._alerts_store.values())
        active = sum(1 for a in alerts if a.lifecycle_state in [AlertLifecycleState.NEW, AlertLifecycleState.ESCALATED])
        ack = sum(1 for a in alerts if a.lifecycle_state == AlertLifecycleState.ACKNOWLEDGED)
        esc = sum(1 for a in alerts if a.lifecycle_state == AlertLifecycleState.ESCALATED)
        res = sum(1 for a in alerts if a.lifecycle_state == AlertLifecycleState.RESOLVED)

        return AlertStatusResponse(
            total_alerts_count=len(alerts),
            active_alerts_count=active,
            acknowledged_count=ack,
            escalated_count=esc,
            resolved_count=res,
            delivery_mode=DeliveryMode.SIMULATION,
            provider_status="LOCAL_SIMULATION_ACTIVE (External gateways unconfigured for zero-cost operation)",
            supported_languages=["English", "Hindi", "Garhwali", "Kumaoni", "Nepali"],
            disclaimer="All generated alerts are prepared locally in memory. External public SMS / WhatsApp broadcasts remain simulated.",
        )


alert_engine_instance = AlertEngine()
