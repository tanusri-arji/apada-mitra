# APADA MITRA — FEATURE 11 VERIFICATION REPORT
**Real-Time Multi-Hazard Alert Generation + Notification Intelligence**
**Project:** APADA MITRA (SIH 26192)  
**Status:** PASS  
**Languages Supported:** English, Hindi, Garhwali, Kumaoni, Nepali (Telugu Removed)  
**Timestamp:** 2026-09-05T07:06:00+05:30  

---

## 1. Executive Summary & Architecture Overview

Feature 11 establishes a deterministic, auditable, and regional multilingual **Multi-Hazard Alert Generation & Notification Intelligence Layer** on top of the frozen Features 1–10 pipeline.

```
LIVE HAZARD STATE (Features 1–5, 8)
              ↓
RISK CHANGE DETECTION (Feature 11 Alert Engine)
              ↓
MULTI-HAZARD CORRELATION & SEVERITY CLASSIFICATION
              ↓
RECOMMENDED OPERATIONAL ACTION (Lead-Time Aware)
              ↓
EVACUATION & SHELTER CONTEXT (Features 6, 9, 10)
              ↓
STRUCTURED 5-LANGUAGE MESSAGE GENERATION (EN, HI, GARHWALI, KUMAONI, NEPALI)
              ↓
DEDUPLICATION & LIFECYCLE STATE MACHINE (NEW, ACK, ESCALATED, RESOLVED)
              ↓
AUDIT TRAIL LOGGING (Zero-Tamper Record)
              ↓
SIMULATION NOTIFICATION ADAPTER (Zero-Cost / Honest Delivery Boundary)
```

---

## 2. Target Region & 5-Language Selection Rationale

The alert system supports exactly **5 languages** tailored specifically for the mountainous terrain, administrative structure, and local communities of Uttarakhand:

1. **English (`en`):** State and national disaster management authorities (NDMA, SDMA), emergency responders, technical engineers, and domestic/international pilgrims and tourists.
2. **Hindi (`hi`):** Broad official and inter-district emergency communication across North India and Uttarakhand.
3. **Garhwali (`garhwali` / `gar`):** Primary indigenous Central Pahari language spoken across the Garhwal Himalayas (Chamoli, Rudraprayag, Uttarkashi, Pauri, Tehri).
4. **Kumaoni (`kumaoni` / `kum`):** Primary indigenous Central Pahari language spoken across Kumaon region (Pithoragarh, Bageshwar, Almora, Nainital, Champawat).
5. **Nepali (`nepali` / `ne`):** Spoken widely by Nepali-speaking resident communities, migrant workers, porters, and border populations along the Himalayan corridor.

> [!NOTE]
> **Telugu Removal:** Telugu was removed because the operational deployment area is the Himalayan watershed of Uttarakhand, where Garhwali, Kumaoni, and Nepali represent the genuine local linguistic requirements.

---

## 3. Multi-Hazard Input & Correlation Logic

The alert engine synthesizes multiple simultaneous hazard dimensions across monitored Himalayan villages without creating a competing risk engine or altering existing formulas:
- **Flash Flood Risk** (Feature 1 rainfall, Feature 2 soil moisture, Feature 4 flow accumulation, Feature 8 river levels)
- **Landslide Risk** (Feature 1/2 moisture, Feature 4 slope/terrain, Feature 5 historical inventory, Feature 3 IoT tilt/pore pressure)
- **River Stage Telemetry** (Feature 8 CWC/hydrological telemetry)
- **Road Access Status** (Feature 9 OSM road segment blockages/degradations)
- **Shelter Safety Status** (Feature 10 configured shelter suitability scores)

### Primary vs. Secondary Hazard Selection
- When multiple hazards trigger simultaneously (e.g. Flood Risk = 78%, Landslide Risk = 62%), the engine selects the dominant contributor as `primary_hazard` and lists all others under `secondary_hazards`.
- The `combined_severity` reflects the maximum risk state, avoiding fragmented alerts.

---

## 4. Alert Severity & Operational Action Mapping

Alert severity adheres strictly to existing APADA MITRA thresholds:
- **LOW (< 25.0):** Operational action `MONITOR`.
- **MODERATE (25.0 – 50.0):** Operational action `PREPARE`.
- **HIGH (50.0 – 75.0):** Operational action `PREPARE_EVACUATION` or `EVACUATE_HIGH_RISK_AREAS`. If evacuation lead-time is insufficient, action escalates to `IMMEDIATE_ACTION_REQUIRED`.
- **CRITICAL (≥ 75.0):** Operational action `EVACUATE` or `IMMEDIATE_ACTION_REQUIRED`.

---

## 5. Evacuation & Shelter Context Integration (Features 6, 9, 10)

Each alert is enriched with deterministic evacuation intelligence:
- **Available Lead-Time (mins)** vs. **Required Evacuation Time (mins)** (Feature 6)
- **Decision Status:** `ENOUGH_TIME`, `MARGINAL`, `INSUFFICIENT_TIME`, or `UNKNOWN`
- **Selected Shelter:** ID, name, capacity, suitability score (Feature 10)
- **Route Safety & Navigation:** Route distance (km), estimated travel time (mins), route safety score, and list of blocked/degraded OSM road segments (Feature 9)
- **No Safe Shelter Guard:** If all shelters or routes are compromised, `selected_shelter_id` is set to `null` and the reason explicitly declares `NO_SAFE_SHELTER`.

---

## 6. Multilingual Alert Messaging (5 Supported Languages)

Alert messages are generated from dynamic parametric templates across the 5 supported languages ensuring 100% semantic equivalence:

| Language | Header Format | Sample Action Text | Sample Shelter / Route Text |
|:---|:---|:---|:---|
| **English** | `APADA MITRA [SEVERITY] WARNING — [Village]` | `Action: PREPARE. Review evacuation preparedness.` | `Evacuation Target: [Shelter] (4.5 km, 10.8 min)` |
| **Hindi** | `आपदा मित्र [गंभीरता] चेतावनी — [Village]` | `कार्रवाई: तैयारी करें (PREPARE)। जरूरी सामान समेटें।` | `निकासी केंद्र: [Shelter] (दूरी: 4.5 किमी, समय: 10.8 मिनट)` |
| **Garhwali** | `आपदा मित्र [गंभीरता] चेतावनी — [Village]` | `कार्रवाई: तैयरी करा (PREPARE)। जरूरी सामान समेटा।` | `सुरक्षित ठौर: [Shelter] (दूरी: 4.5 किमी, लगण वाळू बखत: 10.8 मिनट)` |
| **Kumaoni** | `आपदा मित्र [गंभीरता] चेतावनी — [Village]` | `कार्रवाई: तयारी करा (PREPARE)। जरूरी सामान जोड़ा।` | `सुरक्षित थान: [Shelter] (दूरी: 4.5 किमी, अनुमानित टैम: 10.8 मिनट)` |
| **Nepali** | `आपदा मित्र [गंभीरता] चेतावनी — [Village]` | `कार्रवाई: तयारी अवस्थामा रहनुहोस् (PREPARE)।` | `सुरक्षित आश्रयस्थल: [Shelter] (दूरी: 4.5 किमी, अनुमानित समय: 10.8 मिनेट)` |

---

## 7. Deduplication & Escalation Lifecycle

- **Deterministic Fingerprinting:** Alerts compute an MD5 hash of `f"{village_id}:{severity}:{primary_hazard}:{risk_bucket}:{evac_required}:{shelter_id}"`.
- **Deduplication:** Successive alert generation requests for the same village under identical hazard states return the existing alert without spamming or creating redundant records (`is_duplicate = True`).
- **Escalation (MODERATE → HIGH → CRITICAL):** When a material risk change occurs, a new alert is generated, the prior alert is transitioned to `ESCALATED`, and historical alert records are preserved.
- **Lifecycle Transitions:** `NEW` → `ACKNOWLEDGED` → `ESCALATED` / `RESOLVED` with explicit audit trails.

---

## 8. Audit Trail Architecture

Every automated generation and manual state change is logged with zero tampering:
- `timestamp`: UTC ISO-8601 timestamp
- `alert_id`: Unique identifier (e.g. `ALT-VIL-001-20260905-001`)
- `village_id`: Village code
- `action`: `GENERATED`, `DEDUPLICATED`, `ACKNOWLEDGED`, `ESCALATED`, `RESOLVED`
- `previous_state` & `new_state`
- `reason`: Machine-extracted rationale
- `actor`: `SYSTEM` (for automated engine triggers) or verified operator role
- `source`: Engine or API origin

---

## 9. Notification Provider Architecture & Delivery Integrity

### Notification Provider Interface
```python
class NotificationProvider(ABC):
    @abstractmethod
    def prepare_alert_payload(self, alert: MultiHazardAlertRecord) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_delivery_status(self, alert: MultiHazardAlertRecord) -> AlertDeliveryStatusResponse:
        pass
```

### Critical Honesty Rule & Boundary
- `SimulationNotificationProvider` is the active default.
- No external paid APIs (Twilio, WhatsApp Business, AWS SNS, Firebase FCM, SMTP) are required or connected.
- All alerts explicitly expose:
  - `delivery_status`: `NOT_DELIVERED`
  - `delivery_mode`: `SIMULATION`
  - `channel`: `LOCAL_DASHBOARD` / `SMS_SIMULATION`
- **Zero False Claims:** The system never reports alerts as "sent to citizens" or "delivered to government authorities".

---

## 10. Runtime Verification: Monitored Himalayan Villages

### Village 1: VIL-001 (Pipalkoti, Chamoli)
- **Alert ID:** `ALT-VIL-001-20260905-001`
- **Severity:** `MODERATE`
- **Risk Score:** `35.8%`
- **Primary Hazard:** `LANDSLIDE`
- **Secondary Hazards:** `[]`
- **Key Contributing Factors:**
  - `Terrain slope 25.8° indicates moderate landslide susceptibility`
  - `1 historical landslides recorded in vicinity (nearest 0.0 km)`
- **Recommended Action:** `PREPARE`
- **Evacuation Lead Time:** Available 720.0 mins | Required 10.8 mins (`ENOUGH_TIME`)
- **Selected Shelter:** `SH-01` (Pipalkoti Central High School Relief Complex, Chamoli, Capacity: 1,500)
- **Route Safety:** 4.5 km, 10.8 mins, Safety Score 0.90 (`SAFE`)
- **Data State:** `OFFLINE_DEMO`
- **Confidence:** `0.85`
- **Delivery Status:** `NOT_DELIVERED` (`SIMULATION`)
- **5-Language Preview:**
  - **EN:** `🚨 APADA MITRA MODERATE WARNING — Pipalkoti\nHazard: Landslide (Risk Score: 35.8/100)\nAction: PREPARE\nEvacuation Target: Pipalkoti Central High School Relief Complex\nDistance: 4.5 km, Est. Travel Time: 10.8 mins\nLead Time Window: ENOUGH_TIME`
  - **HI:** `🚨 आपदा मित्र MODERATE चेतावनी — Pipalkoti\nखतरा: भूस्खलन (Landslide) (जोखिम स्कोर: 35.8/100)\nकार्रवाई: तैयारी करें (PREPARE)। जरूरी सामान समेटें।\nनिकासी केंद्र: Pipalkoti Central High School Relief Complex\nदूरी: 4.5 किमी, अनुमानित समय: 10.8 मिनट\nनिकासी समय स्थिति: ENOUGH_TIME`
  - **Garhwali:** `🚨 आपदा मित्र MODERATE चेतावनी — Pipalkoti\nखतरो: प्वार गिरण / पहाड़ खिसकण (Landslide) (जोखिम स्कोर: 35.8/100)\nकार्रवाई: तैयरी करा (PREPARE)। जरूरी सामान समेटा।\nसुरक्षित ठौर: Pipalkoti Central High School Relief Complex\nदूरी: 4.5 किमी, लगण वाळू बखत: 10.8 मिनट\nनिकासी बखत स्थिति: ENOUGH_TIME`
  - **Kumaoni:** `🚨 आपदा मित्र MODERATE चेतावनी — Pipalkoti\nखतरो: पथर/डांग खिसकण (Landslide) (जोखिम स्कोर: 35.8/100)\nकार्रवाई: तयारी करा (PREPARE)। जरूरी सामान जोड़ा।\nसुरक्षित थान: Pipalkoti Central High School Relief Complex\nदूरी: 4.5 किमी, अनुमानित टैम: 10.8 मिनट\nनिकासी टैम स्थिति: ENOUGH_TIME`
  - **Nepali:** `🚨 आपदा मित्र MODERATE चेतावनी — Pipalkoti\nखतरा: पहिरो / भूस्खलन (Landslide) (जोखिम स्कोर: 35.8/100)\nकार्रवाई: तयारी अवस्थामा रहनुहोस् (PREPARE)।\nसुरक्षित आश्रयस्थल: Pipalkoti Central High School Relief Complex\nदूरी: 4.5 किमी, अनुमानित समय: 10.8 मिनेट\nनिकासी समय स्थिति: ENOUGH_TIME`

### Village 2: VIL-003 (Govindghat, Chamoli)
- **Alert ID:** `ALT-VIL-003-20260905-002`
- **Severity:** `MODERATE`
- **Risk Score:** `40.8%`
- **Primary Hazard:** `LANDSLIDE`
- **Secondary Hazards:** `['FLASH_FLOOD']`
- **Key Contributing Factors:**
  - `Terrain slope 31.2° indicates elevated landslide susceptibility`
  - `Flow accumulation 45000 cells indicates significant runoff concentration`
  - `1 historical landslides recorded in vicinity (nearest 0.0 km)`
- **Recommended Action:** `PREPARE`
- **Evacuation Lead Time:** Available 720.0 mins | Required 65.3 mins (`ENOUGH_TIME`)
- **Selected Shelter:** `SH-01` (Pipalkoti Central High School Relief Complex, Chamoli, Capacity: 1,500)
- **Route Safety:** 31.0 km, 65.3 mins, Safety Score 0.90 (`SAFE`)
- **Data State:** `OFFLINE_DEMO`
- **Confidence:** `0.85`
- **Delivery Status:** `NOT_DELIVERED` (`SIMULATION`)

---

## 11. Test & Build Quality Gate Results

### Dedicated Feature 11 Tests (`backend/tests/test_feature_11_alerts.py`)
- `test_severity_classification_mapping`: **PASSED**
- `test_low_alert_generation_and_monitoring_action`: **PASSED**
- `test_critical_alert_generation_and_immediate_action`: **PASSED**
- `test_multi_hazard_detection_and_correlation`: **PASSED**
- `test_evacuation_and_shelter_context_integration`: **PASSED**
- `test_multilingual_message_consistency` (EN, HI, Garhwali, Kumaoni, Nepali + No Telugu): **PASSED**
- `test_alert_deduplication`: **PASSED**
- `test_alert_escalation_lifecycle`: **PASSED**
- `test_alert_acknowledgement_and_resolution`: **PASSED**
- `test_notification_provider_simulation_honesty`: **PASSED**
- `test_api_alerts_endpoints` (5 languages verification): **PASSED**
- `test_features_1_to_10_integrity_preserved`: **PASSED**

**Feature 11 Test Summary:** 12 passed in 11.94s (100% pass rate).

### Full Backend Pytest Suite
- Ran all tests across Features 1 through 11.
- **Result:** **171 passed** (0 failed, 0 errors).

### Frontend Production Build
- Command: `npm.cmd run build`
- **Result:** `vite v5.4.21 building for production... ✓ built in 3.79s` (0 errors).

---

## 12. REAL vs. SIMULATION Boundary & Limitations

1. **Alert Engine & Multi-Hazard Synthesis (REAL):** Deterministic risk correlation, severity classification, 5-language template formatting (English, Hindi, Garhwali, Kumaoni, Nepali), route/shelter integration, deduplication, lifecycle transitions, and audit trail are fully functional, verified, and test-backed.
2. **Notification Delivery (SIMULATION):** No real SMS/WhatsApp/Voice broadcast gateway is connected. All notifications are marked `NOT_DELIVERED` (`SIMULATION`).
3. **Data Quality Propagation (HONEST):** Alert records reflect the exact data state of underlying engines (`REAL_LIVE_INPUT`, `ESTIMATED_FROM_LIVE_DATA`, `CACHED`, or `OFFLINE_DEMO`).
4. **Machine Learning Disclaimer:** No fictitious ML confidence score is claimed; statistical confidence from underlying terrain/meteorological pipelines is propagated.
