# APADA MITRA — COMPLETE FORENSIC AUDIT REPORT
**SIH26192 | Flash Flood Prediction System for Hilly Regions**
**Audit Date:** 2026-09-16 | Codebase: `c:\Users\Tanusri\Downloads\sih 2\sih 2`

> **METHODOLOGY:** Every finding is traced to a specific file and line. Nothing is assumed from filenames alone. All statuses are derived from actual code inspection and live test execution.

---

## PART 1 — PROJECT INVENTORY

| Category | Count |
|---|---|
| Backend Python source files (app/) | ~60 |
| Backend test files | 22 |
| Frontend TypeScript/TSX files | ~35 |
| Data files (JSON + Python static) | 8 |
| ML model weight files | 1 (`flood_lstm_weights.json`, 463 KB) |
| Documentation files (docs/) | 44 |
| Deployment config | 1 (`frontend/vercel.json`) |
| Environment files | 1 (`backend/.env`) — ⚠️ SECRETS INSIDE |
| Dead backup scripts | 3 (`restore_imd_cap_adapter.py`, etc.) |
| Legacy folder | `frontend/src_backup_redesign/` — UNUSED |

### Core Architecture

```
External APIs → Adapters → data_pipeline.py → Engines → routes.py → React 18 frontend

Adapters:
  open_meteo.py      LIVE (NORMAL scenario only) — rainfall, soil
  cwc_adapter.py     SKELETON — always returns None
  imd_cap_adapter.py LIVE (CAP RSS feed, 5-min cache)
  open_elevation.py  LIVE attempt (Copernicus DEM), fallback to static
  offline_demo.py    Deterministic fallback for all other scenarios

Engines (all formula-based unless stated):
  risk_engine.py           6-factor flood risk (WEIGHTED FORMULA)
  landslide_engine.py      5-factor landslide risk (WEIGHTED FORMULA)
  priority_engine.py       4-factor evacuation priority
  routing_engine.py        Dijkstra over 24-segment static road graph
  shelter_suitability_engine.py   Shelter scoring (63 candidates)
  simulation_engine.py     What-If (no global state mutation)
  hydro_lstm_engine.py     2-Layer LSTM, NumPy inference (ML — only ML component)
  alert_engine.py          Threshold-based multilingual alerts
  exposure_engine.py       Population exposure calculation
```

---

## PART 2 — TECHNOLOGY STACK

### Frontend (from `frontend/package.json`)
| Tech | Status |
|---|---|
| React 18 | USED |
| TypeScript 5.3 | USED |
| Vite 5 | USED |
| Tailwind CSS 3.4 | USED |
| Leaflet 1.9 / react-leaflet 4.2 | USED (primary map) |
| MapLibre GL 6.7 | In package.json; `GeospatialMonitoringMap.tsx` = 82 bytes, stub only |
| lucide-react | USED |
| Redux / Zustand | NOT USED |
| React Query / SWR | NOT USED — manual fetch via `api/client.ts` |

### Backend (from `backend/requirements.txt`)
| Tech | Status |
|---|---|
| Python 3.10+ | USED |
| FastAPI | USED |
| Uvicorn | USED |
| Pydantic v2 | USED |
| NumPy 1.26+ | USED at runtime (LSTM inference) |
| pandas 2.2+ | Training script only — NOT at runtime |
| python-dotenv | USED |
| Any SQL/ORM | CONFIRMED ABSENT |
| PyTorch | Training script only — NOT at runtime |

### Infrastructure
| Component | Status |
|---|---|
| Vercel (frontend) | CONFIGURED — `vercel.json` confirmed |
| Render (backend) | README claim only — no `render.yaml` found |
| AWS EC2 / RDS / S3 | NOT FOUND anywhere in codebase |
| Docker | NOT FOUND — no Dockerfile |
| GitHub Actions / Jenkins | NOT FOUND |
| Any database | CONFIRMED ABSENT |

---

## PART 3 — COMPLETE DATA AUDIT (per source)

| Data | Provider | File | Live? | Scenario | Fallback |
|---|---|---|---|---|---|
| Current rainfall | Open-Meteo API | `adapters/open_meteo.py` | YES — NORMAL only | NORMAL | wttr.in → OFFLINE_DEMO |
| 24h forecast rainfall | Open-Meteo API | `adapters/open_meteo.py` | YES — NORMAL only | NORMAL | OFFLINE_DEMO |
| Soil saturation | Open-Meteo (soil_moisture_0_to_7cm) | `adapters/open_meteo.py` | YES — NORMAL only | NORMAL | OFFLINE_DEMO |
| River water level | CWC/WIMS — no credentials | `adapters/cwc_adapter.py` | **NEVER — always None** | All | Demo baseline |
| DEM elevation/terrain | Open-Meteo Elevation (Copernicus GLO-90) | `adapters/open_elevation.py` | Attempted (3.5s timeout) | All | Static village data |
| Slope | Derived via Horn gradient from DEM | `adapters/open_elevation.py` | Derived | All | Static village |
| Flow accumulation | Derived via D8 from DEM | `adapters/open_elevation.py` | Derived | All | Static village |
| Historical landslides | GSI/ISRO NRSC Atlas — 15 events | `data/isro_gsi_landslides.json` | **NO — STATIC** | Context | — |
| Village parameters | Developer-constructed | `data/dataset.py` | **NO — SYNTHETIC** | All | — |
| Population | Census of India 2011 DCHB | `data/census_population_data.py` | **NO — STATIC 2011** | Exposure | — |
| Infrastructure counts | Developer-defined | `data/dataset.py` | **NO — SYNTHETIC** | Priority | — |
| Roads | Developer-defined (OSM-inspired names) | `data/road_network.py` | **NO — SYNTHETIC** | Routing | — |
| Road conditions | Computed from hazard scores | `data/road_network.py` L226–274 | **LOCALLY DERIVED** | All | — |
| Shelters | USDMA/DDMP docs (63 candidates) | `adapters/shelter_adapter.py` | **NO — STATIC** | Shelter | — |
| IoT sensors | In-memory (no real devices) | `engine/iot_store.py` | **EMPTY AT STARTUP** | All | — |
| IMD/NDMA alerts | CAP RSS feed (S3-hosted) | `adapters/imd_cap_adapter.py` | YES (attempted, 4s TTL) | All | Empty list |
| Alert delivery (SMS/WhatsApp) | SimulationNotificationProvider | `adapters/notification_provider.py` | **SIMULATION ONLY** | — | — |
| Telegram | Telegram Bot API | `send_telegram_alert.py` | YES (standalone script) | Manual | — |
| Hydrograph stages | LSTM inference | `engine/hydro_lstm_engine.py` | **LOCALLY DERIVED** | ML view | — |

> **KEY DESIGN FACT (`data_pipeline.py` L146):**
> `scenario_forces_offline = (scenario != ScenarioType.NORMAL)`
> For HEAVY_RAIN and EXTREME_RAIN, ALL met inputs come from the SYNTHETIC demo dataset.
> Open-Meteo is NOT called for scenario demonstrations.

---

## PART 4 — LIVE vs STATIC vs SIMULATED (NORMAL scenario, right now)

| Metric | Classification | Evidence |
|---|---|---|
| Current rainfall | LIVE or OFFLINE_DEMO | `open_meteo.py`, `data_pipeline.py` L146 |
| Soil saturation | LIVE (NWP model-derived) or OFFLINE_DEMO | NOT a physical soil probe |
| River level | DEMO BASELINE | `cwc_adapter.py` L41-43: always `None` |
| Flood risk score | LOCALLY DERIVED — weighted formula | `risk_engine.py` |
| Landslide risk score | LOCALLY DERIVED — weighted formula | `landslide_engine.py` |
| Evacuation priority | LOCALLY DERIVED | `priority_engine.py` |
| Road conditions | LOCALLY DERIVED from risk | `road_network.py` L226-274 |
| Shelter capacity | STATIC (govt DDMP, many UNKNOWN) | `shelter_adapter.py` |
| IoT readings | NONE | `iot_store.py` L32 |
| IMD alerts | LIVE (CAP feed) or EMPTY | `imd_cap_adapter.py` L25 |
| Hydrograph | LOCALLY DERIVED (LSTM) | `hydro_lstm_engine.py` |
| Route | LOCALLY DERIVED (Dijkstra) | `routing_engine.py` |
| Shelter recommendation | LOCALLY DERIVED (scoring) | `shelter_suitability_engine.py` |
| What-If output | LOCALLY DERIVED (no state mutation) | `simulation_engine.py` |
| SMS delivery | SIMULATION ONLY | `notification_provider.py` L80 |

---

## PART 5 — ENGINE FORMULA AUDIT

### Flood Risk Engine (`risk_engine.py`)
```
Weights (sum = 1.00 ✅):
  current_rainfall     = 0.25  (bound: 100 mm/h)
  forecast_rainfall    = 0.20  (bound: 250 mm)
  soil_saturation      = 0.15  (bound: 100%)
  river_water_level    = 0.15  (norm: (val-1.0)/2.0)
  flow_accumulation    = 0.15  (bound: 5.0 log scale)
  slope                = 0.10  (bound: 45 degrees)

Missing feature fill: 0.3 neutral (NOT 0.0)
risk_score = clamp(weighted_sum × 100, 0.0, 100.0)
confidence = clamp(95.0 − missing_weight_sum × 80.0, 10.0, 100.0)
```

### Landslide Engine (`landslide_engine.py`)
```
Classification: RULE-BASED WEIGHTED SCORING — NOT ML

Weights (sum = 1.00 ✅):
  slope            = 0.35
  soil_saturation  = 0.25
  current_rainfall = 0.20
  forecast_rainfall= 0.15
  river_water_level= 0.05

Historical events from isro_gsi_landslides.json = CONTEXT NARRATIVE ONLY
(does NOT influence the numeric score)
```

### Priority Engine (`priority_engine.py`)
```
flood_pts      = flood_risk_score × 0.35
landslide_pts  = landslide_risk_score × 0.25
pop_norm       = clamp(population_exposed / 3500.0, 0.0, 1.0)
pop_pts        = pop_norm × 100 × 0.25
infra_norm     = clamp(critical_structures_count / 10.0, 0.0, 1.0)
infra_pts      = infra_norm × 100 × 0.15
priority_score = clamp(sum, 0.0, 100.0)
Rank 1 = highest priority_score
```

### Routing Engine (`routing_engine.py`)
```
Graph: 24 road segments, UNDIRECTED, 3 disconnected subgraphs
  (Uttarakhand, Himachal Pradesh, Kerala — no cross-region roads)
BLOCKED / hazard ≥ 85% roads: excluded entirely
Edge cost = distance_km × (1 + hazard_max/40) × (2.5 if DEGRADED else 1.0)
Safety score = clamp(100 − max_hazard × 0.85, 5.0, 100.0)
Speed = 25 km/h (safety>60) or 18 km/h
No route → ValueError → HTTP error
```

---

## PART 6 — DATASET STATISTICS

| Dataset | Count | Source | Classification |
|---|---|---|---|
| Villages | 15 | dataset.py | SYNTHETIC (locations real, parameters synthetic) |
| Roads | 24 segments | road_network.py | SYNTHETIC (self-labeled) |
| Shelter candidates | 63 | shelter_adapter.py | STATIC govt DDMP docs |
| Historical landslides | 15 events (2012–2023) | isro_gsi_landslides.json | REAL (GSI/ISRO sourced) |
| CWC stations | 8 registered | hydrology_engine.py | INTERFACE ONLY — 0 live |
| IoT sensors active | 0 at startup | iot_store.py | Empty store |
| LSTM training hours | 87,600 | hydro_training_data.py | SYNTHETIC (seed=42) |
| API endpoints | ~35 | routes.py + ml_routes.py | Implemented |
| Tests | 218 collected | pytest | **206 pass, 12 FAIL** |

**Total monitored population (Census 2011):** 37,581 residents across 15 villages

---

## PART 7 — GIS / COORDINATE AUDIT

| Village | Name | Lat | Lon | State | Status |
|---|---|---|---|---|---|
| VIL-001 | Pipalkoti | 30.43 | 79.43 | Uttarakhand | ✅ Plausible |
| VIL-002 | Helang | 30.52 | 79.51 | Uttarakhand | ✅ Plausible |
| VIL-003 | Govindghat | 30.62 | 79.56 | Uttarakhand | ✅ Plausible |
| VIL-004 | Badrinath Base | 30.74 | 79.49 | Uttarakhand | ✅ Plausible |
| VIL-005 | Karnaprayag | 30.26 | 79.22 | Uttarakhand | ✅ Plausible |
| VIL-006 | Nandaprayag | 30.33 | 79.32 | Uttarakhand | ✅ Plausible |
| VIL-007 | Rudraprayag Sangam | 30.285 | 78.98 | Uttarakhand | ✅ Plausible |
| VIL-008 | Tilwara | 30.35 | 79.03 | Uttarakhand | ✅ Plausible |
| VIL-009 | Augustmuni | 30.39 | 79.08 | Uttarakhand | ✅ Plausible |
| VIL-010 | Guptkashi | 30.525 | 79.08 | Uttarakhand | ✅ Plausible |
| VIL-011 | Phata | 30.57 | 79.05 | Uttarakhand | ✅ Plausible |
| VIL-012 | Sonprayag | 30.63 | 79.01 | Uttarakhand | ✅ Plausible |
| VIL-013 | Aut / Mandi | 31.74 | 77.16 | Himachal Pradesh | ✅ Plausible |
| VIL-014 | Meppadi | 11.55 | 76.12 | Kerala | ⚠️ ~3 km offset from actual |
| VIL-015 | Chooralmala | 11.51 | 76.17 | Kerala | ✅ Plausible |

> **CRITICAL:** Three disconnected geographic subgraphs. No roads connect Uttarakhand ↔ HP ↔ Kerala. Cross-region routing always fails with "No safe route" error. Correct behavior but must be known before demo.

---

## PART 8 — ML / HYDROGRAPH AUDIT

### Architecture
- **2-Layer LSTM** (hidden_size=32) + FC output layer (6 steps)
- **Runtime: pure NumPy** (no PyTorch dependency at inference)
- **Weights:** `data/weights/flood_lstm_weights.json` (463 KB) — committed to repo

### Training Data
Generated by `data/hydro_training_data.py.generate_catchment_hydrograph_series(num_hours=87600, seed=42)`
- **100% SYNTHETIC** — physics-based (monsoon envelope + gamma storm arrivals + Horton infiltration + kinematic wave routing)
- **NOT real CWC measured river stage data**

### Performance Metrics
```python
# ml_models.py lines 39-44 — HARDCODED Pydantic defaults from training run:
"nash_sutcliffe_efficiency": 0.882
"coefficient_of_determination_r2": 0.914
"root_mean_squared_error_m": 0.142
"peak_crest_timing_error_hours": 0.42
```
These are hardcoded constants computed against **synthetic validation data**, NOT real gauge validation.
They are NOT recalculated at runtime.

### Hardcoded Post-LSTM Additions
```python
kinematic_wave_profile = [0.35, 0.82, 1.00, 0.86, 0.62, 0.42]  # surge shape
initial_stage_m = 2.2 + upstream_offset + (precip × 0.035)       # not from CWC
```

---

## PART 9 — IoT / ALERT / NOTIFICATION AUDIT

### IoT Store (`iot_store.py`)
- Type: In-memory Python dict — no persistence
- Startup: **EMPTY** — `self._sensors: Dict[str, IoTSensorRecord] = {}`
- Auth on `/api/iot/ingest`: **NONE** — open endpoint (security risk)
- Freshness: LIVE ≤600s | STALE ≤1800s | OFFLINE >1800s
- **No physical sensors connected**

### Alert Engine (`alert_engine.py` + `notification_provider.py`)
- Alerts generated automatically from risk score thresholds
- 5 languages: EN, HI, Garhwali, Kumaoni, Nepali — **template-based, NOT machine translation**
- Delivery provider: `SimulationNotificationProvider`
  - `DeliveryStatus.NOT_DELIVERED`
  - `DeliveryMode.SIMULATION`
  - SMS: `"SIMULATION_ONLY"`
  - WhatsApp: `"EXTERNAL_PROVIDER_UNAVAILABLE"`

### Telegram (`send_telegram_alert.py`)
- **STANDALONE SCRIPT** — NOT connected to main app runtime
- Sends a single hardcoded test message
- Token hardcoded as fallback in line 8: `8930236949:AAF4IO2am0V31BonD-bciYLuQHJCdK02NXc`
- App does NOT auto-dispatch Telegram on alert generation

---

## PART 10 — SECURITY AUDIT

| Finding | Severity | Evidence |
|---|---|---|
| Telegram Bot token hardcoded in `.env` AND `send_telegram_alert.py` L8 | **HIGH** | `TELEGRAM_BOT_TOKEN=8930236949:AAF...` |
| `.env` committed to git repository | **HIGH** | File present at `backend/.env` |
| `/api/iot/ingest` unauthenticated | MEDIUM | Anyone can inject false sensor readings |
| No rate limiting on API | MEDIUM | No throttling middleware |
| No SQL injection risk | N/A | No SQL queries anywhere |
| No secrets in frontend | ✅ Clean | `client.ts` only uses relative `/api` paths |
| Debug mode | ✅ Not detected | |

---

## PART 11 — DATABASE AUDIT

**Finding: NO DATABASE OF ANY KIND EXISTS.**

`requirements.txt` contains: `fastapi`, `uvicorn`, `pydantic`, `pytest`, `httpx`, `pandas`, `numpy` — zero database drivers.
No SQL queries. No ORM. No connection strings. No migration files.
All data: Python in-memory structures + static JSON/Python files.

---

## PART 12 — TESTING AUDIT (ACTUAL EXECUTION)

**Command:** `python -m pytest tests/ --tb=no -q`
**Result: `12 failed, 206 passed, 2 warnings in 13.02s`**

### Failed Tests
| File | # | Root Cause |
|---|---|---|
| `test_data_adapters.py::test_pipeline_risk_snapshot_translation` | 1 | Design change: HEAVY_RAIN now forces offline |
| `test_feature_01_real_rainfall.py` | 5 | Tests expect live rainfall in HEAVY_RAIN; code uses synthetic |
| `test_feature_02_real_soil_moisture.py` | 5 | Same root cause |
| `test_feature_03_iot_ingestion.py::test_iot_rainfall_source_priority` | 1 | IoT priority logic changed with offline redesign |

> **README claims "218 Passing" — THIS IS FACTUALLY INCORRECT.**
> Actual verified count: **206 passing, 12 failing.**

### Passing Coverage
Risk engine ✅ | Landslide ✅ | Priority ✅ | Dijkstra ✅ | Shelter ✅ | What-If ✅ | Hydrology ✅ | LSTM ML ✅ | Alerts ✅ | IMD CAP ✅ | Geospatial ✅

---

## PART 13 — DOCUMENTATION CONTRADICTIONS

| Claim | Finding | Verdict |
|---|---|---|
| "218 Passing tests" | 206 passing, 12 failing | ❌ CONTRADICTED |
| "63 shelter candidate network" (L49) | 63 entries confirmed | ✅ CORRECT |
| "33 shelter candidate network" (L121) | Same file has 63 entries | ❌ INTERNAL CONTRADICTION |
| "AWS-based" | No AWS code or config | ❌ NOT FOUND |
| "RDS database" | No database at all | ❌ NOT FOUND |
| "live data" | Only Open-Meteo for NORMAL scenario | ⚠️ PARTIAL |
| "AI-powered" | LSTM for hydrograph; risk = formula | ⚠️ PARTIAL |
| "CWC integration" | Adapter always returns None | ⚠️ INTERFACE ONLY |
| "Telegram emergency dispatch" | Standalone script, not app-integrated | ⚠️ PARTIAL |
| "NSE 0.882, R² 0.914" | Hardcoded, synthetic validation only | ⚠️ NEEDS QUALIFICATION |
| "Dijkstra routing" | Correctly implemented | ✅ SUPPORTED |
| "5 languages" | Templates confirmed | ✅ SUPPORTED |
| "87,600 timesteps / 10 seasons" | `num_hours=87600, seed=42` confirmed | ✅ SUPPORTED (synthetic) |
| "SMS alerts" | SIMULATION_ONLY, NOT_DELIVERED | ❌ NOT DELIVERED |

---

## PART 14 — JUDGE Q&A (Verified Answers with Evidence)

**Q1: Where does rainfall come from?**
For NORMAL (baseline): Open-Meteo public REST API (free, no key). For HEAVY_RAIN/EXTREME_RAIN demo scenarios: pre-defined synthetic parameters. `[data_pipeline.py L146]`

**Q2: Is it real-time?**
NORMAL scenario: yes, Open-Meteo (3-hour cache). Scenario demonstrations: no — reproducible synthetic values. `[open_meteo.py, data_pipeline.py]`

**Q3: Do you have CWC river level data?**
No. CWC/WIMS requires authorized government credentials. Interface exists (8 CWC stations registered), adapter always returns None, falls back to demo baseline. `[cwc_adapter.py L41-43]`

**Q4: Are IoT sensors deployed?**
No physical hardware. Complete IoT ingestion API exists (`POST /api/iot/ingest`): validates, stores, and prioritizes sensor readings with freshness tracking. Architecture ready for deployment. `[iot_store.py]`

**Q5: Is the prediction ML?**
Hydrograph prediction: yes — real 2-layer LSTM, NumPy inference, 463 KB trained weights. Flood/landslide risk scores: NO — transparent 6-factor/5-factor weighted formulas. `[hydro_lstm_engine.py, risk_engine.py]`

**Q6: What is the model accuracy?**
NSE=0.882, R²=0.914, RMSE=0.142m — computed against SYNTHETIC validation data (physics-based simulation). Not validated against real CWC gauge observations (unavailable publicly). `[ml_models.py L38-44]`

**Q7: Are roads live / real-time?**
No. Topology is synthetic (OSM-inspired names). Road conditions (OPEN/DEGRADED/BLOCKED) are derived at runtime from hazard scores — not from live road closure feeds. `[road_network.py L1-5, L226-274]`

**Q8: Are you sending SMS?**
No. `SimulationNotificationProvider` returns `NOT_DELIVERED / SIMULATION`. No SMS gateway connected. Telegram is a standalone demo script, not auto-triggered by the app. `[notification_provider.py L74-90]`

**Q9: Is this on AWS / RDS?**
No AWS code or config exists. Frontend: Vercel (vercel.json confirmed). Backend: Render (documentation claim, no render.yaml in repo). `[requirements.txt — no boto3, no psycopg2]`

**Q10: Why 12 tests failing if README says 218?**
A design change forced HEAVY_RAIN/EXTREME_RAIN scenarios to use synthetic offline data, but 12 feature tests that expected live API values in those scenarios were not updated. Correct count: 206 passing, 12 failing.

**Q11: Are shelters real?**
Names and locations derived from publicly documented USDMA/DDMP Chamoli, Rudraprayag, HPSDMA Mandi, KSDMA Wayanad government facilities. Static snapshot — not live occupancy. Many capacities are UNKNOWN (explicitly marked). `[shelter_adapter.py]`

**Q12: What if a route is completely blocked?**
`ValueError("No safe evacuation route accessible")` → HTTP error response to frontend. `[routing_engine.py L123-126]`

**Q13: Why Dijkstra not A*?**
24-edge graph — Dijkstra is trivially fast. No domain-specific admissible heuristic for hazard-weighted cost exists. Transparent and explainable.

**Q14: What is soil saturation?**
Derived from Open-Meteo `soil_moisture_0_to_7cm` NWP model field — not a physical in-situ soil moisture probe.

**Q15: What happens on API failure?**
Open-Meteo down → wttr.in → OFFLINE_DEMO. IMD CAP down → empty alert list. All labeled with data provenance: LIVE / CACHED / OFFLINE_DEMO / REAL_STATIC.

---

## PART 15 — FINAL TRUTH TABLE

| Feature | Real External | Static | Synthetic | Derived Locally |
|---|---|---|---|---|
| Rainfall (NORMAL) | ✅ Open-Meteo | | | |
| Rainfall (HEAVY/EXTREME) | | | ✅ | |
| Soil moisture | ✅ Open-Meteo NWP | | | |
| River level | | | | ✅ Demo baseline |
| DEM elevation | ✅ Attempted Copernicus | ✅ fallback | | ✅ derived |
| Population | ✅ Census 2011 | ✅ | | |
| Historical landslides | ✅ GSI/ISRO | ✅ | | |
| Village parameters | | | ✅ | |
| Roads | | | ✅ | |
| Road conditions | | | | ✅ Formula |
| Shelters | ✅ Govt DDMP | ✅ | | |
| IMD alerts | ✅ CAP feed | | | |
| Flood risk score | | | | ✅ Formula |
| Landslide score | | | | ✅ Formula |
| Priority rank | | | | ✅ Formula |
| Route | | | | ✅ Dijkstra |
| Shelter recommendation | | | | ✅ Scoring |
| Hydrograph | | | | ✅ LSTM (synthetic-trained) |
| What-If cascade | | | | ✅ Local recalc |
| SMS delivery | | | | ✅ Simulation only |

---

## PART 16 — SAFE vs UNSAFE CLAIMS

### ✅ SAFE TO CLAIM
- "Transparent 6-factor flood risk scoring, weights sum to 1.00"
- "15 real Himalayan watershed villages (Chamoli, Rudraprayag, Wayanad)"
- "Census 2011 population data from official GOI DCHB"
- "15 historical landslides from ISRO NRSC Atlas and GSI NLSM"
- "63 shelter candidates from USDMA/DDMP government documents"
- "Hazard-weighted Dijkstra pathfinding (correctly implemented)"
- "2-Layer LSTM hydrograph on 87,600-timestep synthetic physics catchment data"
- "NSE=0.882 on synthetic validation set" (with caveat about synthetic data)
- "Multilingual template alerts: EN, HI, Garhwali, Kumaoni, Nepali"
- "What-If simulator with no global state mutation"
- "Live Open-Meteo integration for baseline NORMAL scenario"
- "IMD/NDMA CAP alert feed integration (live attempt, 5-min cache)"
- "IoT-ready ingestion API (architecture ready, no hardware deployed)"
- "206 automated pytest tests covering all major components"
- "Explicit data provenance labels: LIVE / CACHED / OFFLINE_DEMO / REAL_STATIC"

### ❌ DO NOT CLAIM
- "218 tests passing" — actual: 206 passing, 12 failing
- "Real-time CWC river data" — CWC adapter always returns None
- "AI-powered risk scores" — flood/landslide = weighted formula
- "SMS or WhatsApp alerts delivered" — SIMULATION_ONLY
- "AWS / EC2 / RDS" — not found in codebase
- "Database" — no database of any kind
- "Real-time for all scenarios" — only NORMAL uses live API
- "IoT sensors deployed" — empty store at startup
- "NSE validated against real gauge data" — synthetic validation only
- "Live road closures" — model-derived conditions

---

## PART 17 — TOP 5 FIXES BEFORE SIH DEMO

1. **Fix 12 failing tests** — update Feature 01/02/03 test expectations to match the current offline-for-HEAVY_RAIN design
2. **Fix README test count** — "218 Passing" → "206 passing"
3. **Fix README shelter count** — resolve "33" vs "63" contradiction
4. **Rotate Telegram Bot token** — remove from `.env` and hardcoded fallback in `send_telegram_alert.py`; generate a new token
5. **Prepare judge answers** — clear statements on LSTM synthetic training data, no AWS, no SMS delivery, no live CWC

---

## SUMMARY CARD

```
PROJECT:         APADA MITRA (SIH26192)
FRONTEND:        React 18 + TypeScript + Vite + Tailwind + Leaflet
BACKEND:         Python FastAPI (NO DATABASE — in-memory only)
ML:              1 LSTM (2-layer, h=32, NumPy inference, SYNTHETIC training)
CLOUD:           Vercel ✅ | Render (docs claim) | AWS ❌
DATABASE:        NONE
VILLAGES:        15 (real locations, synthetic parameters)
ROADS:           24 segments (SYNTHETIC — self-labeled)
SHELTERS:        63 candidates (static govt DDMP sources)
IOT ACTIVE:      0 (API ready, no hardware)
CWC LIVE:        0 of 8 stations (no credentials)
TESTS:           206 PASS / 12 FAIL (README incorrectly claims 218)
LIVE SOURCES:    Open-Meteo, wttr.in, Open-Elevation, IMD CAP (NORMAL scenario / attempted)
SECURITY ISSUE:  Telegram token exposed in .env and source code
```
