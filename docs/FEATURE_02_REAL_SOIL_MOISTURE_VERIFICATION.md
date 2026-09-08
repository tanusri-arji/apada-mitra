# Feature 2 — Real Soil Moisture Data Flow Verification Report

**Scope:** End-to-end integration of real Open-Meteo soil moisture data from API adapter through pipeline normalization, risk engine feature mapping, and XAI explainability factor breakdowns.

---

## 1. Open-Meteo REST API Endpoint & Field

* **API Endpoint**:  
  `https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=precipitation,rain,showers&hourly=precipitation,soil_moisture_0_to_7cm&forecast_days=1`
* **Exact Open-Meteo Field**:  
  `hourly.soil_moisture_0_to_7cm` (Volumetric water content in $m^3/m^3$ for 0–7 cm topsoil layer).
* **Data Classification**:  
  **Open-Meteo Meteorological REST API Data** (modelled/external weather API data). *Explicitly NOT physical IoT sensors or government telemetry.*

---

## 2. Root Cause & Architectural Fix

### Original Bug
In `DataIngestionPipeline.convert_to_risk_feature_snapshot()` (`backend/app/data_pipeline.py`), live soil moisture (`obs.soil_saturation_pct`) was wrapped in `safe_val(obs.soil_saturation_pct, demo_snapshot["soil_saturation"], "max")` for `HEAVY_RAIN` and `EXTREME_RAIN` scenarios. This caused real Open-Meteo soil moisture readings to be overwritten or blended with synthetic scenario demo data whenever the demo value was higher.

### Fix Implemented
Real live soil moisture (`obs.soil_saturation_pct`) passes through directly unchanged into the feature snapshot whenever present. Synthetic demo scenario values are used **only** as an explicit missing-data fallback when `obs.soil_saturation_pct` is `None`. Real and demo soil moisture are **never** blended.

---

## 3. End-to-End Live Data Trace (Pipalkoti `VIL-001`)

| Stage | Metric / Field | Actual Live Runtime Value |
| :--- | :--- | :--- |
| **Raw Open-Meteo API** | `hourly.soil_moisture_0_to_7cm` | **`0.4107 m³/m³`** (avg over 24h) |
| **Normalized Observation** | `soil_saturation_pct` | **`82.1%`** |
| **Risk Feature Snapshot** | `soil_saturation` | **`82.1%`** |
| **Flood-Risk Engine Input** | `raw_features["soil_saturation"]` | **`82.1%`** |
| **Normalized Engine Input** | `normalized_features["soil_saturation"]` | **`0.821`** (82.1 / 100.0) |
| **XAI Raw Value** | `soil_factor.raw_value` | **`82.1%`** |
| **XAI Points Contribution** | `soil_factor.contribution_points` | **`12.31 pts`** ($0.821 \times 0.15 \times 100$) |
| **XAI Percent Contribution** | `soil_factor.contribution_percent` | **`34.3%`** of total flood risk score |
| **Data State** | `obs.data_state` | **`LIVE`** (`LIVE_EXTERNAL_API`) |

---

## 4. Fallback Behaviour

If live Open-Meteo API calls fail or return missing (`None`) soil moisture data, the pipeline falls back to the deterministic scenario snapshot value (e.g., Pipalkoti `HEAVY_RAIN` demo soil saturation = **`83.0%`**). Synthetic data is used exclusively as an explicit missing-data fallback.

---

## 5. Automated Regression Test Suite

* **Test Suite File**: `backend/tests/test_feature_02_real_soil_moisture.py`
* **Test Results**: **6 passed in 0.27s**
  1. `test_open_meteo_adapter_normalizes_soil_moisture`: Verifies volumetric $m^3/m^3$ array conversion to saturation percentage ($47.0\%$).
  2. `test_snapshot_preserves_low_soil_moisture`: Verifies low soil moisture ($15.0\%$) passes through without demo max blending under `HEAVY_RAIN`.
  3. `test_snapshot_preserves_high_soil_moisture`: Verifies high soil moisture ($92.0\%$) passes through without demo blending under `HEAVY_RAIN`.
  4. `test_snapshot_preserves_live_soil_moisture_across_all_scenarios`: Verifies live soil moisture ($25.0\%$) is preserved across `NORMAL`, `HEAVY_RAIN`, and `EXTREME_RAIN`.
  5. `test_risk_engine_and_xai_use_same_live_soil_moisture`: Verifies end-to-end alignment between snapshot, engine `raw_features`, and XAI `raw_value`.
  6. `test_missing_live_soil_moisture_falls_back_to_demo`: Verifies missing soil moisture (`None`) falls back to deterministic scenario snapshot.

---

## 6. System Limitations

1. **Topsoil Layer Depth**: Open-Meteo provides topsoil moisture for $0–7\text{ cm}$. Deep soil moisture ($7–28\text{ cm}$, $28–100\text{ cm}$) is not evaluated.
2. **Volumetric Scaling Assumption**: Scaling assumes field saturation cap at $0.50\text{ m}^3/\text{m}^3$ for Himalayan clay/loam soils.
3. **Data Source Type**: Open-Meteo soil moisture is derived from ECMWF IFS / GFS land-surface model assimilations, not physical in-situ TDR sensors.
