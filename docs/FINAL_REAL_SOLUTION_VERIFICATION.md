# APADA MITRA — Final Real-Solution Engineering & Verification Report
**SIH Problem Statement: SIH26192**
**System Title:** APADA MITRA — Terrain-Aware Multi-Hazard Flash Flood Risk & Evacuation Intelligence Engine

---

## 1. Real Data Sources
- **Meteorological API Integration**: Open-Meteo REST API (`https://api.open-meteo.com/v1/forecast`) provides real-time hourly precipitation rates (`current.precipitation` in mm/hr), 24-hour cumulative precipitation forecast (`hourly.precipitation`), and top-soil moisture saturation (`hourly.soil_moisture_0_to_7cm`).
- **Target Coordinates**: 15 monitored Himalayan villages across the Alaknanda & Mandakini watersheds (e.g., Pipalkoti: `30.4300°N, 79.4300°E`, Guptkashi: `30.5250°N, 79.0800°E`, Sonprayag: `30.6300°N, 79.0100°E`).
- **Data Transport & Normalization**: Data is fetched by `OpenMeteoRainfallAdapter` and converted into canonical `NormalizedEnvironmentObservation` records.

---

## 2. Data States & System Readiness
APADA MITRA enforces four data states:

| Data State | Description | Quality Status | System Health Label |
| :--- | :--- | :--- | :--- |
| **LIVE** | Recent valid external meteorological observations successfully retrieved via REST API. | `GOOD` or `DEGRADED` | `LIVE API METEOROLOGICAL INGESTION ACTIVE` |
| **CACHED** | External request timed out or failed; returning last valid cached observation within 3h TTL. | `WARNING` | `CACHED OBSERVATIONS ACTIVE` |
| **OFFLINE_DEMO** | External networks unreachable; using deterministic SIH watershed scenario dataset. | `DEGRADED` | `OFFLINE DEMONSTRATION MODE — SIH DATASET` |
| **UNAVAILABLE** | No observation exists for target coordinates or critical features missing. | `CRITICAL_MISSING` | `SYSTEM DEGRADED — FALLBACK ACTIVE` |

> **Operational Safety Rule**: Synthetic scenario data is NEVER labeled as `LIVE`. System readiness indicator shows `SYSTEM DEGRADED — FALLBACK ACTIVE` if live telemetry is disconnected or critical features are unverified.

---

## 3. Verified End-to-End Runtime Data Path
The exact runtime execution chain verified on live Open-Meteo data:

```
Open-Meteo REST API (HTTP 200 OK)
  │ (Raw current precipitation: 0.5 mm/hr)
  ▼
OpenMeteoRainfallAdapter
  │ (Normalizes payload to NormalizedEnvironmentObservation)
  ▼
DataQualityEngine
  │ (Validates bounds, freshness, flags missing river fields)
  ▼
DataIngestionPipeline
  │ (Blends live rainfall + topsoil with static terrain features into Risk Snapshot)
  ▼
Flash Flood Risk Engine
  │ (Calculates multi-factor risk score: 57.98%, Risk Level: HIGH)
  ▼
XAI Engine
  │ (Computes SHAP-inspired factor contributions: Top Driver = Rainfall Rate 24.1%)
  ▼
Exposure Engine
  │ (Calculates headcount exposure: 1,509 / 2,450 residents)
  ▼
Landslide Engine
  │ (Computes terrain-slope risk: 61.82%, HIGH)
  ▼
Evacuation Priority Engine
  │ (Calculates multi-hazard index: 55.53, Urgency Rank #1)
  ▼
Dijkstra Routing Engine
  │ (Computes safe path VIL-001 -> SH-01, Route Safety Score: 83.0%)
  ▼
Shelter Allocation Engine
  │ (Recommends Pipalkoti Central High School Relief Complex, 1,050 beds available)
  ▼
Multilingual Operator Alert & Local SMS Simulation
  │ (Generates decision-support alert with explicit DM authority disclaimers)
```

---

## 4. Flash Flood Risk Methodology
- **Multi-Factor Weighted Index**: Combines Current Rainfall Rate (25%), 24h Forecast Cumulative Rainfall (20%), Soil Moisture Saturation (15%), Hydrological River Water Level Stage (20%), Terrain Slope (10%), and Flow Accumulation Index (10%).
- **Penalty for Missing Telemetry**: If inputs are missing (e.g. unmonitored river gauge), confidence drops from 95% to 75% or lower, penalizing confidence while maintaining risk estimation using domain baselines.

---

## 5. XAI (Explainable AI) Methodology
- **SHAP-Inspired Contribution Allocation**: Measures exact numerical percentage contribution of each hydro-meteorological feature towards the total risk score.
- **Transparency**: Every risk calculation exposes top drivers (e.g. Current Rainfall Rate 24.1%, Soil Saturation 21.3%) so operators can verify calculation rationale.

---

## 6. Terrain Data Methodology & Provenance
- **Derived GIS & Benchmark Dataset**: Terrain slope angles (15° - 42°), flow accumulation log indices (1.0 - 5.2), elevation (990m - 3,250m), and river channel proximity (meters) are static GIS features compiled from SRTM DEM baselines for the Alaknanda watershed.
- **Data Provenance Transparency**: Exposed as static spatial benchmark features. They are not faked as live satellite streams.

---

## 7. Routing & Road Network Methodology
- **Hazard-Weighted Dijkstra Algorithm**: Traverses the mountain road network graph (`DEMO_ROADS_BASE`).
- **Dynamic Segment Penalties**:
  - `OPEN`: Standard road traversal.
  - `DEGRADED`: Multiplied by 2.5x distance penalty due to partial hazard exposure.
  - `BLOCKED`: Excluded from graph traversal when flood exposure $\ge 85\%$ or landslide exposure $\ge 85\%$ (e.g. `ROAD-010` Phata-Sonprayag gorge during extreme rain).

---

## 8. Relief Shelter Allocation Methodology
- **Strict Capacity Enforcement**: Rejects any shelter with `available_capacity <= 0`.
- **Composite Suitability Score**: Weights Route Safety (45%), Distance (25%), and Shelter Hazard Exposure (30%) to recommend the safest available shelter (`SH-01` to `SH-06`).

---

## 9. Failure Handling & Resilience Strategy
Tested across 9 failure modes (HTTP timeouts, 500 errors, network disconnection, missing fields, malformed JSON, invalid numerical ranges):
1. **Graceful Fallback**: Automatically switches from `LIVE` to `CACHED` or `OFFLINE_DEMO` without crashing.
2. **Confidence Degradation**: Calculation confidence automatically drops when inputs are missing or unverified.
3. **HTTP Exception Handling**: API returns valid structured Pydantic fallback payloads.

---

## 10. Hydrology Limitation & CWC Adapter Architecture
- **Honest Hydrological Label**: River water levels and discharge rates are labeled as **"HYDROLOGICAL INPUT — MODELLED / DEMO"**.
- **CWC/WIMS Adapter Interface**: `backend/app/adapters/cwc_adapter.py` defines the official interface for Central Water Commission (CWC) telemetry integration. When unconfigured, it safely returns `None`, activating transparent fallback without pretending to query unauthorized endpoints.

---

## 11. Incident Command & Decision Safety
- **Operational Incident Lifecycle**: Villages crossing `HIGH` or `CRITICAL` thresholds create structured `OperationalIncident` records (`INC-VIL-xxx`).
- **Operator Actions**: Supports local application state transitions (`ACKNOWLEDGE`, `ESCALATE`, `MARK_EVACUATION_ACTIVE`, `PREPARE_ALERT`).
- **Legal & Operational Safety Disclaimer**:
  > *"RECOMMENDED ACTION. FINAL EVACUATION / PUBLIC WARNING DECISION REMAINS WITH AUTHORIZED DISASTER MANAGEMENT AUTHORITIES."*
- **Local SMS Simulation**: Alert preview is explicitly tagged **`LOCAL SMS SIMULATION — NOT TRANSMITTED (DEMO ONLY)`**. No paid external SMS gateways or real telephone numbers are collected.

---

## 12. Component Categorization

| Component | Status / Classification | Description |
| :--- | :--- | :--- |
| Meteorological Weather API | **REAL** | Live Open-Meteo REST API connection for precipitation and soil moisture |
| Terrain & Elevation Data | **DERIVED GIS / STATIC** | SRTM DEM benchmark spatial attributes for 15 Himalayan villages |
| Hydrological Telemetry | **MODELLED / DEMO** | Baseline river stage factors; CWC adapter ready for authorized keys |
| Risk & XAI Engines | **VERIFIED ALGORITHMIC** | Mathematical multi-hazard weighting and SHAP-inspired explainability |
| Routing & Shelters | **VERIFIED ALGORITHMIC** | Dijkstra hazard-aware pathfinding and capacity constraint allocation |
| Local SMS Alert Preview | **SIMULATED** | Local UI demonstration preview; not transmitted to public networks |

---

## 13. Test Results Summary

```
REAL DATA PATH:      PASS
LIVE MODE:          PASS
CACHE MODE:         PASS
OFFLINE MODE:       PASS
FAILURE RECOVERY:   PASS
RISK INTEGRATION:   PASS
XAI INTEGRATION:    PASS
ROUTING:            PASS
SHELTER:            PASS
ALERT:              PASS
INCIDENT COMMAND:   PASS
AUDIT TRAIL:        PASS
BROWSER HTTP:       PASS (HTTP 200 frontend & backend active)
PYTEST:             PASS (52 passed in 9.84s)
FRONTEND BUILD:     PASS (vite v5.4.21 built in 2.94s)
```

---

## 14. Remaining System Limitations
1. **Government Hydrological Telemetry**: Direct CWC live river stream gauge telemetry requires official API keys and clearance; the system uses modelled hydrological baselines via the pluggable `CWCHydrologicalAdapter`.
2. **Public SMS Gateway**: Emergency public alert broadcasting is simulated locally for safety; integration with national emergency alert networks (e.g. CAP / NDMA Sanchar Saathi) requires government deployment authorization.
3. **Spatial Scope**: The benchmark dataset currently models 15 critical villages and 6 relief shelters in the Alaknanda/Mandakini watersheds. Expansion across Uttarakhand requires further GIS layer ingestion.
