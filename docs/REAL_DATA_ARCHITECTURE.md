# APADA MITRA — REAL DATA INTEGRATION & VALIDATION ARCHITECTURE

## 1. System Inspection & Data Flow Audit (Pre-Change Baseline)

Before introducing the real data integration layer, the existing APADA MITRA data flow was audited as follows:

```
[ Synthetic / Scenario Data ]
         ↓
  `dataset.py` (get_village_feature_snapshot)
         ↓
  `risk_engine.py` (calculate_flash_flood_risk)
         ↓
  ┌───────────────────────┬───────────────────────┬───────────────────────┐
  ↓                       ↓                       ↓                       ↓
`explainability.py`  `exposure_engine.py`   `landslide_engine.py`  `priority_engine.py`
  ↓                       ↓                       ↓                       ↓
Factor Contributions Exposed Population  Landslide Susceptibility Evacuation Rank
  └───────────────────────┴───────────────────────┴───────────────────────┘
                                  ↓
                        `routing_engine.py` & `shelter_engine.py`
                                  ↓
                        `/api` REST Endpoints
                                  ↓
                        React + Leaflet Frontend
```

### Key Discoveries from Baseline Inspection
1. **Input Data Schema**: `MultiSourceFeatureData` and dict snapshots in `dataset.py` define six core feature keys:
   - `current_rainfall` (mm/h)
   - `forecast_rainfall` (mm 24h)
   - `soil_saturation` (%)
   - `river_water_level` (stage multiplier 1.0–3.0)
   - `flow_accumulation` (log scale)
   - `slope` (degrees)
2. **Scenario Data Delivery**: Scenario types (`NORMAL`, `HEAVY_RAIN`, `EXTREME_RAIN`) dynamically construct feature snapshots.
3. **Risk Engine Contract**: `calculate_flash_flood_risk()` expects a feature snapshot dictionary with `raw_val` and `feature_statuses`.
4. **Resilience**: The existing risk engine already gracefully handles `DataQualityStatus.MISSING` by applying a confidence penalty (`MISSING_FEATURE_PENALTY_MULTIPLIER = 80.0`).

---

## 2. Hardened Architecture: Real Data Adapter & Quality Pipeline

The solution introduces a clean, decoupled data pipeline between external providers and the existing risk engines:

```
                          ┌────────────────────────┐
                          │   Real Public APIs     │
                          │ (Open-Meteo / IMD)     │
                          └───────────┬────────────┘
                                      │ (HTTP Fetch)
                                      ▼
                          ┌────────────────────────┐
                          │  DataSourceAdapter     │
                          │  - OpenMeteoAdapter   │
                          │  - OfflineDemoAdapter  │
                          └───────────┬────────────┘
                                      │ (Fetch & Raw Payload)
                                      ▼
                          ┌────────────────────────┐
                          │  Canonical Validation  │
                          │  (DataQualityEngine)   │
                          │  - Range bounds check  │
                          │  - Staleness check     │
                          │  - Missing value check │
                          └───────────┬────────────┘
                                      │ (Normalized Observation)
                                      ▼
                          ┌────────────────────────┐
                          │ Data State Manager     │
                          │ LIVE / CACHED /        │
                          │ OFFLINE_DEMO           │
                          └───────────┬────────────┘
                                      │ (Validated Feature Snapshot)
                                      ▼
                          ┌────────────────────────┐
                          │  Existing APADA MITRA  │
                          │  Multi-Hazard Engines  │
                          └────────────────────────┘
```

---

## 3. Data State Model

The environment data pipeline strictly enforces four explicit operational data states:

| Data State | Trigger Condition | Output Label |
| :--- | :--- | :--- |
| `LIVE` | External authoritative API successfully returns valid recent observation data. | `LIVE DATA — OPEN-METEO API` |
| `CACHED` | External API request fails or times out, but a previously retrieved valid observation exists within cache ttl. | `CACHED DATA — RECENT OBS` |
| `OFFLINE_DEMO` | No external API or cache available; deterministic SIH Himalayan dataset is used. | `OFFLINE DEMO — SIH DATASET` |
| `UNAVAILABLE` | Critical calculation data missing and no fallback available; calculations safely aborted/degraded. | `UNAVAILABLE — INSUFFICIENT DATA` |

> **Strict Truthfulness Guarantee**: Synthetic data is **NEVER** labeled as `LIVE`. Source metadata explicitly identifies whether data originated from an external API, cached store, or offline demo dataset.

---

## 4. Normalized Observation Schema (`NormalizedEnvironmentObservation`)

The internal canonical observation contract includes:
- `latitude` & `longitude` (WGS84)
- `observation_timestamp` (ISO UTC)
- `current_rainfall_mm_hr` (mm/h)
- `forecast_rainfall_24h_mm` (mm)
- `soil_saturation_pct` (%)
- `river_water_level_m` (meters / stage factor)
- `source_name` (e.g., `"Open-Meteo Weather API"`, `"SIH Deterministic Dataset"`)
- `source_type` (e.g., `"METEOROLOGICAL_API"`, `"OFFLINE_DEMO"`)
- `data_state` (`LIVE`, `CACHED`, `OFFLINE_DEMO`, `UNAVAILABLE`)
- `quality_status` (`GOOD`, `WARNING`, `DEGRADED`, `CRITICAL_MISSING`)
- `freshness_seconds` (age of data in seconds)
- `missing_fields` (List of missing parameters)
- `validation_warnings` (List of data quality warnings)

---

## 5. Data Quality Engine Rules

The validation engine performs automated data verification before risk calculations:
1. **Range Validation**:
   - `current_rainfall_mm_hr`: $0.0 \le x \le 300.0$ mm/h
   - `forecast_rainfall_24h_mm`: $0.0 \le x \le 1000.0$ mm
   - `soil_saturation_pct`: $0.0 \le x \le 100.0$ %
   - `river_water_level_m`: $0.0 \le x \le 15.0$ m
2. **Anomaly & Impossible Value Rejection**:
   - Negative values ($<0$) are flagged as invalid and converted to missing fields with a warning.
   - Values exceeding physical limits (e.g., rainfall $>300$ mm/h) are rejected or capped with a warning.
3. **Staleness Verification**: Observations older than 3 hours are flagged as `DEGRADED` quality and transitioned to `CACHED` status.
4. **Missing Field Resilience**: Missing fields lower system confidence (`BASE_CONFIDENCE - penalty`) without crashing the application.

---

## 6. Endpoints Introduced

- `GET /api/v1/data-quality`: Returns real-time health, source state (`LIVE`/`CACHED`/`OFFLINE_DEMO`), freshness, missing fields, and validation warnings across all ingestion sources.

---

## 7. Official IMD/NDMA CAP Alert Integration (Problem 24)

### 7.1 Architecture & Scope
APADA MITRA genuinely ingests official live disaster and weather warning evidence from the authoritative India Meteorological Department (IMD) / National Disaster Management Authority (NDMA) Common Alerting Protocol (CAP) public RSS/XML feed:
- **Feed Endpoint**: `https://cap-sources.s3.amazonaws.com/in-imd-en/rss.xml`
- **Data Model**: OASIS CAP v1.2 / RSS 2.0
- **Access Nature**: Publicly accessible, machine-readable, live XML stream (no institutional API credentials required).
- **Geographic Resolution**: **District and Sub-division level** (e.g. Chamoli, Rudraprayag, Mandi, Wayanad, Uttarakhand).

### 7.2 Strict Provenance & Methodological Non-Overclaiming
- **Authoritative Macro Evidence**: IMD warnings operate at district/sub-division scale.
- **Village Risk Downscaling**: APADA MITRA combines official IMD district warning evidence with 30m SRTM terrain physics, micro-drainage log indices, and exposure data for village-level decision support.
- **Explicit Provenance States**:
  - `REAL_LIVE_OFFICIAL`: Successfully fetched and parsed from the live IMD CAP RSS/XML feed.
  - `CACHED_OFFICIAL`: Utilizing cached official warning data on transient network error.
  - `UNAVAILABLE`: Feed unreachable and no cached warning available.
- **Raw IMD FFGS Grid Limitation**: Direct raw IMD FFGS numerical grid API remains restricted to authorized institutional government networks (MoES MoU). APADA MITRA ingests official published CAP feeds and bulletins truthfully without simulating unauthorized API gateways.

