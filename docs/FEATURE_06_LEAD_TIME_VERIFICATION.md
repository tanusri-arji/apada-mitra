# APADA MITRA — FEATURE 6: REAL LEAD-TIME & EVACUATION WINDOW ENGINE
**SIH Problem Statement ID:** SIH26192  
**Implementation Date:** 2026-09-05  
**Component:** Lead-Time Calculation & Evacuation Decision Support Engine  

---

## 1. Executive Purpose & Scope

The **Lead-Time Engine** is an operational decision-support module designed to evaluate whether emergency managers and village communities have an actionable time window to mobilize and safely evacuate prior to environmental risk thresholds escalating to critical levels.

> [!IMPORTANT]
> **Operational Decision Support Disclaimer**:
> This engine provides **operational emergency evacuation decision-support** based on meteorological forecast thresholds, standard community mobilization buffers, and road graph shortest-path travel times.
> It is **NOT** a hydrodynamic flood-wave propagation simulation or a geotechnical landslide rupture timer. It does not fabricate hydraulic arrival velocities or unverified propagation constants.

---

## 2. Mathematical Formulations & Logic

### 2.1 Evacuation Time Components
$$\text{Total Required Evacuation Time } (T_{\text{required}}) = T_{\text{prep}} + T_{\text{travel}}$$

Where:
- $T_{\text{prep}}$ = Community Preparation & Mobilization Buffer ($\text{default } 25.0 \text{ minutes}$).
- $T_{\text{travel}}$ = Shortest safe path travel time in minutes, computed dynamically via Dijkstra routing (`recommend_safest_shelter(village_id)`).

### 2.2 Available Lead Time ($T_{\text{lead}}$)
Calculated from forward-looking meteorological forecasts (Open-Meteo 1-hourly / 3-hourly forecast array) and hazard escalation tracking:
- If current risk score $R \ge 75.0$ (Critical Action Threshold):  
  $$T_{\text{lead}} = 0.0 \text{ minutes (Immediate emergency action)}$$
- If forecasted cumulative rainfall intensity $\ge 50.0 \text{ mm/hr}$ within the forecast horizon:  
  $$T_{\text{lead}} = \text{time in minutes until threshold intensity is reached}$$
- If risk is currently moderate and no extreme rainfall spike is forecasted within 12 hours ($720 \text{ min}$):  
  $$T_{\text{lead}} = 360.0 \text{ minutes (Standard 6-hour operational planning window)}$$

### 2.3 Safety Margin & Decision Status
$$\text{Safety Margin } (M_{\text{safety}}) = T_{\text{lead}} - T_{\text{required}}$$

| Decision Status | Condition | Operational Meaning |
| :--- | :--- | :--- |
| **`SAFE`** | $M_{\text{safety}} \ge 60.0 \text{ minutes}$ | Sufficient time available for safe evacuation under normal procedures. |
| **`TIGHT`** | $0.0 \le M_{\text{safety}} < 60.0 \text{ minutes}$ | Evacuation window is narrow; urgent mobilization recommended. |
| **`INSUFFICIENT`**| $M_{\text{safety}} < 0.0 \text{ minutes}$ | Required evacuation time exceeds available window; shelter-in-place / rapid vertical evacuation protocol required. |
| **`UNKNOWN`** | Missing forecast or invalid live data | Insufficient operational data to compute a defensible lead time. |

---

## 3. Consolidated Configuration Constants

All thresholds and parameters are declared centrally in `backend/app/engine/lead_time_engine.py` without magic numbers:

```python
DEFAULT_PREPARATION_TIME_MINUTES = 25.0          # Standard mobilization buffer
SAFE_SAFETY_MARGIN_MINUTES = 60.0                # Margin >= 60 min -> SAFE
CRITICAL_ACTION_RISK_THRESHOLD = 75.0            # Risk >= 75 -> Imminent hazard
HIGH_ACTION_RISK_THRESHOLD = 50.0                # Risk >= 50 -> High hazard threshold
EXTREME_RAINFALL_THRESHOLD_MM_HR = 50.0          # Flash flood trigger rate
MAX_OPERATIONAL_FORECAST_WINDOW_MINUTES = 720.0  # 12h horizon
DEFAULT_BASE_LEAD_TIME_MINUTES = 360.0           # 6h default window
```

---

## 4. Data Provenance & Confidence Degradation

Data states are explicitly tracked:
- **`REAL_LIVE_INPUT`**: Live verified forecast and sensor feeds.
- **`ESTIMATED_FROM_LIVE_DATA`**: Live data used with operational risk threshold extrapolations.
- **`CACHED`**: Up-to-date cached meteorological forecasts.
- **`OFFLINE_DEMO`**: Offline fallback datasets or default mock sensors.
- **`UNKNOWN`**: Data missing or corrupted.

### Confidence Matrix:
- Baseline live confidence: **95%**
- Live data estimation: **80%**
- Missing/degraded forecast input: **-25% to -50%**
- Fallback/demo mock state: **40% - 60%**

---

## 5. API Endpoints

### 5.1 Single Village Lead Time
`GET /api/lead-time/villages/{village_id}`

**Response (`VIL-001` Pipalkoti):**
```json
{
  "village_id": "VIL-001",
  "village_name": "Pipalkoti",
  "calculated_at": "2026-09-05T00:15:44.957367+00:00",
  "current_risk_score": 47.47,
  "current_risk_level": "MODERATE",
  "hazard_escalation_estimate_minutes": 360.0,
  "evacuation_time_minutes": 11.0,
  "preparation_time_minutes": 25.0,
  "total_required_time_minutes": 36.0,
  "available_lead_time_minutes": 360.0,
  "safety_margin_minutes": 324.0,
  "decision_status": "SAFE",
  "confidence": 80.0,
  "calculation_method": "OPERATIONAL_THRESHOLD_CROSSING_ESTIMATE",
  "data_state": "OFFLINE_DEMO",
  "assumptions": [
    "Standard community mobilization time: 25 minutes.",
    "Destination shelter: Pipalkoti Central High School Relief Complex via 4.5km route (Dijkstra travel time: 11 mins, Route Safety: 83%).",
    "Current risk is within manageable bounds (47.5/100). Estimated operational window before potential threshold breach is 360 mins.",
    "DISCLAIMER: This calculation provides operational emergency evacuation decision-support based on meteorological thresholds, mobilization buffers, and road graph travel times. It is NOT an exact hydrodynamic flood-wave propagation model."
  ]
}
```

### 5.2 All Monitored Villages Lead Time Summary
`GET /api/lead-time`

Returns array of all monitored village lead-time evaluations (`VIL-001` to `VIL-006`).

---

## 6. Verification & Test Suite

### 6.1 Dedicated Feature 6 Unit Tests (`backend/tests/test_feature_06_lead_time.py`)
- `test_lead_time_sufficient_safe_status`: Verifies `SAFE` decision state when safety margin $\ge 60\text{ min}$.
- `test_lead_time_tight_status`: Verifies `TIGHT` decision state when safety margin is between $0$ and $60\text{ min}$.
- `test_lead_time_insufficient_status`: Verifies `INSUFFICIENT` decision state when required evacuation exceeds available window.
- `test_lead_time_unknown_forecast`: Verifies `UNKNOWN` fallback and reduced confidence when forecast data is unavailable.
- `test_lead_time_offline_demo_confidence_reduction`: Verifies confidence penalty when running on fallback demo data.
- `test_lead_time_calculation_arithmetic`: Validates $T_{\text{required}} = T_{\text{prep}} + T_{\text{travel}}$ and $M_{\text{safety}} = T_{\text{lead}} - T_{\text{required}}$.
- `test_lead_time_invalid_village_404`: Validates 404 response for unknown village IDs.
- `test_api_get_lead_time_single_village`: Schema validation on FastAPI endpoints.
- `test_api_get_lead_time_all_villages`: Schema validation on multi-village list endpoint.
- `test_risk_engine_weights_unmodified`: Asserts flood ($0.4, 0.3, 0.2, 0.1$) and landslide ($0.35, 0.30, 0.20, 0.15$) weights remain strictly preserved.
- `test_features_1_to_5_integrity_preserved`: Verifies that live rainfall, soil moisture, IoT ingestion, GIS terrain, and landslide inventories remain intact.

---

## 7. Operational Limitations

1. **Hydrological Lag vs. Meteorological Forecast**: The engine uses forward rainfall and upstream thresholds; real-world basin hydrodynamics depend on local channel roughness and sediment damming.
2. **Road Condition Degradation**: Travel times assume passable roads calculated via current road safety weights; sudden rockfalls require dynamic route recalculations.
3. **Mobilization Dynamics**: Community preparation times may vary for night-time warnings, elderly populations, or disabled residents.
