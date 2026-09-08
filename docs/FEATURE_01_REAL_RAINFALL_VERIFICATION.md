# Feature 1 — Real Rainfall Data Flow Verification

**Scope:** Preserve live Open-Meteo current rainfall through adapter → observation → risk snapshot → flood risk engine → XAI.  
**Out of scope:** soil moisture changes, IoT, river telemetry, GIS, historical landslides, routing, alerts, UI redesign.

---

## Original bug

Open-Meteo returned approximately **0.5 mm/h** current precipitation. The risk feature snapshot (and therefore XAI) showed approximately **56 mm/h**.

## Root cause

Not a unit-conversion error in `OpenMeteoRainfallAdapter`. The adapter copied `current.precipitation` into `NormalizedEnvironmentObservation.current_rainfall_mm_hr` as **0.5**.

The break was in `DataIngestionPipeline.convert_to_risk_feature_snapshot` (`backend/app/data_pipeline.py`). For `DataSourceState.LIVE` it blended live rainfall with the synthetic scenario snapshot:

- `HEAVY_RAIN`: `max(live, demo)` → `max(0.5, 56.0) = 56.0`
- `EXTREME_RAIN`: `live * 2.0` then `max` with demo (75–110 mm/h)
- `NORMAL`: `min(live, demo)` for current rain; forecast always replaced by demo

Pipalkoti (`VIL-001`) HEAVY_RAIN demo rainfall is exactly:

`35 + (65 − 35) × ((1 × 7) % 10) / 10 = 56.0 mm/h`

The `* 2.0` EXTREME_RAIN factor was scenario stress, **not** a unit conversion.

## Units (no extra conversion added)

Open-Meteo `current.precipitation` is millimetres for the preceding hour. That quantity is already equivalent to **mm/h**. The adapter already assigned it to `current_rainfall_mm_hr` with `float(...)` only. Feature 1 does not introduce a scale factor.

Hourly forecast remains a **sum** of `hourly.precipitation` → `forecast_rainfall_24h_mm` (mm / 24 h), which is a cumulative total, not an intensity conversion.

---

## Files changed

| File | Change |
| :--- | :--- |
| `backend/app/data_pipeline.py` | Live/present rainfall copied unchanged into the snapshot; demo used only if rainfall is `None`. Soil/river blend unchanged. |
| `backend/tests/test_feature_01_real_rainfall.py` | New regression tests (0.5, 10.0, all scenarios, XAI alignment, missing-value fallback). |
| `docs/FEATURE_01_REAL_RAINFALL_VERIFICATION.md` | This report. |

Risk engine (`risk_engine.py`) and XAI (`explainability.py`) were **not** redesigned.

---

## End-to-end values (Feature 1 proof)

Replay of the audited case: live observation with Open-Meteo-shaped rainfall, Pipalkoti, `HEAVY_RAIN`.

| Stage | Field | Value |
| :--- | :--- | :--- |
| Raw Open-Meteo | `current.precipitation` | **0.5** mm (≡ 0.5 mm/h) |
| Normalized observation | `current_rainfall_mm_hr` | **0.5 mm/h** |
| Risk feature snapshot | `current_rainfall` | **0.5 mm/h** |
| Flood risk engine input | `raw_features["current_rainfall"]` | **0.5 mm/h** |
| XAI factor | `feature_key=current_rainfall` `raw_value` | **0.5 mm/h** |
| XAI contribution | normalized / points / % of score | **0.005** / **0.12 pts** / **0.3%** |

Companion forecast in the same replay (not blended away): snapshot `forecast_rainfall` = **11.2 mm** (live 24 h sum).

Illustrative engine score with this snapshot (soil/river still use existing fallback/blend; rainfall is live): `flash_flood_risk_score` = **36.6**.

Second regression value: live **10.0 mm/h** → snapshot **10.0 mm/h** (no hardcoded 56 or ×112).

---

## Fallback behaviour

If `current_rainfall_mm_hr` is **missing** (`None`) on the observation, the snapshot uses the deterministic scenario value (Pipalkoti HEAVY_RAIN → **56.0 mm/h**). Same for missing 24 h forecast → **105.0 mm**. Synthetic rainfall is used only as an explicit missing-data fallback, never as a silent replacement of a live reading.

Offline demo observations from `OfflineDemoAdapter` still carry dataset rainfall through the same pass-through (`obs` value if present).

Soil saturation and river stage are **unchanged** from pre–Feature 1 blending (out of scope).

---

## Tests

```bash
cd backend
python -m pytest tests/test_feature_01_real_rainfall.py -v
# 6 passed

python -m pytest
# 58 passed, 1 warning
```

Feature 1 cases:

1. Adapter normalize: raw `precipitation: 0.5` → observation `0.5`
2. Snapshot HEAVY_RAIN: live `0.5` → snapshot `0.5` (not `56.0`)
3. Snapshot: live `10.0` → snapshot `10.0`
4. Snapshot: live `0.5` preserved for NORMAL, HEAVY_RAIN, EXTREME_RAIN
5. Risk engine `raw_features` and XAI `raw_value` both `0.5`; contribution 0.12 pts
6. Missing live rainfall falls back to demo 56.0 / 105.0

---

## Frontend build

```bash
cd frontend
npm run build
# npx tsc && vite build
# ✓ 1524 modules transformed
# dist/index.html 1.14 kB, index-CR9ZMM3d.css 35.70 kB, index-xVL7Wlg8.js 423.41 kB
# built in 46.64s
# Exit code: 0
```

No UI files were changed for this feature.
