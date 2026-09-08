# APADA MITRA — DATA QUALITY & VALIDATION VERIFICATION

## Executive Summary
This document records the verification of the **Data Quality Engine** and canonical environmental observation validation layer in APADA MITRA.

The data quality layer acts as an automated firewall between external/internal data sources and the core multi-hazard risk engine. It enforces physical limits, missing field penalties, staleness degradation, and explicit data state tracking (`LIVE`, `CACHED`, `OFFLINE_DEMO`, `UNAVAILABLE`).

---

## 1. Quality Validation Rules & Bounds

| Feature | Physical Bounds | Negative Value Handling | Overflow Handling | Missing Value Strategy |
| :--- | :--- | :--- | :--- | :--- |
| `current_rainfall_mm_hr` | $0.0 - 300.0$ mm/h | Rejected $\rightarrow$ set to `None`, warning logged | Capped at $300.0$ mm/h with warning | Neutral normalized value ($0.3$), penalizes confidence |
| `forecast_rainfall_24h_mm` | $0.0 - 1000.0$ mm | Rejected $\rightarrow$ set to `None`, warning logged | Capped at $1000.0$ mm with warning | Neutral normalized value ($0.3$), penalizes confidence |
| `soil_saturation_pct` | $0.0 - 100.0$ % | Rejected $\rightarrow$ set to `None`, warning logged | Capped at $100.0$% with warning | Neutral normalized value ($0.3$), penalizes confidence |
| `river_water_level_m` | $0.0 - 15.0$ m | Rejected $\rightarrow$ set to `None`, warning logged | Capped at $15.0$ m with warning | Hydrological stage baseline used |
| `freshness_seconds` | $< 10800$s (3h) | N/A | $>3$ hours $\rightarrow$ `DEGRADED` state | Tracked via observation timestamp |

---

## 2. Quality Level Classification (`DataQualityLevel`)

1. **`GOOD`**: All primary features present, valid, fresh, and within bounds.
2. **`WARNING`**: Non-critical feature overflow or boundary cap warning logged.
3. **`DEGRADED`**: Feature stale ($>3$ hours) or single feature missing.
4. **`CRITICAL_MISSING`**: 3 or more features missing. Confidence degraded to minimum safe baseline ($10.0\%$).

---

## 3. Data Quality API (`GET /api/v1/data-quality`)

Returns real-time health metrics:
```json
{
  "overall_state": "LIVE",
  "active_source": "Open-Meteo Weather API",
  "data_mode": "LIVE API METEOROLOGICAL INGESTION ACTIVE",
  "total_sources": 2,
  "sources": [
    {
      "source_name": "Open-Meteo Weather API",
      "source_type": "METEOROLOGICAL_API",
      "state": "LIVE",
      "quality": "GOOD",
      "timestamp": "2026-09-04T11:08:03Z",
      "age_minutes": 0.0,
      "missing_fields": ["river_water_level_m", "discharge_cumecs"],
      "validation_warnings": []
    },
    {
      "source_name": "APADA MITRA Himalayan Demo Dataset",
      "source_type": "OFFLINE_DEMO",
      "state": "OFFLINE_DEMO",
      "quality": "GOOD",
      "timestamp": "2026-09-04T11:08:03Z",
      "age_minutes": 0.0,
      "missing_fields": [],
      "validation_warnings": ["SIH Deterministic Scenario Dataset Active"]
    }
  ],
  "last_validated": "2026-09-04T11:08:03Z"
}
```

---

## 4. Verification Results

- **Negative Rainfall Rejection**: Tested & verified (`test_data_quality_negative_values_rejected`).
- **Rainfall Overflow Capping**: Tested & verified (`test_data_quality_overflow_capped`).
- **Staleness Handling**: Tested & verified (`test_data_quality_staleness_detection`).
- **API Endpoint Verification**: `GET /api/data-quality` returns 200 OK with valid JSON schema.
