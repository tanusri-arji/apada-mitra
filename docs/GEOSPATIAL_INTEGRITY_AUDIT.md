# APADA MITRA — CRITICAL GEOSPATIAL INTEGRITY AUDIT
**Project:** SIH26192 | APADA MITRA  
**Theme:** Disaster Management  
**Scope:** Read-Only Geospatial Integrity Audit across all 15 stations (`ST-01` to `ST-15` / `VIL-001` to `VIL-015`), backend pipelines, frontend map components, weather telemetry, terrain models, historical catalogs, road/shelter topology, demographic stores, and multilingual alert registries.  
**Constraint:** READ-ONLY AUDIT. No code, data, formulas, coordinates, station names, or risk weights have been modified.

---

## Final Status Declaration

```
╔═══════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                               ║
║                     STATUS: CRITICAL GEOSPATIAL INTEGRITY FAILURE                             ║
║                                                                                               ║
║  • Code & Test Baseline: 171/171 Tests PASS | Frontend Build PASS                             ║
║  • Scientific/Physics Ground-Truth: 100% of underlying coordinates & graphs are Uttarakhand   ║
║  • Data Integrity Defect: Frontend labels & languages for ST-13 (HP) and ST-14/15 (Kerala)   ║
║    are attached to Chamoli/Rudraprayag (Uttarakhand) coordinates and physical routing.        ║
║                                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## A. Complete 15-Station Master Audit Table

| Stn # | Village ID | Displayed Name | Lat (°N) | Lon (°E) | District | State | Region (UI) | Frontend Metadata Source | Backend Metadata Source | Map Marker Coords | Open-Meteo Query Coords | Terrain DEM Coords | Population Census PCA Mapping | Historical Landslide Catalog | Road Graph Segment | Shelter Allocation | Language Mapping (Primary → Fallback → Tech) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **#01** | `VIL-001` | Pipalkoti | `30.4300` | `79.4300` | Chamoli | Uttarakhand | Alaknanda Valley | `stationMetadata.ts` | `dataset.py` | `30.4300, 79.4300` | `30.4300, 79.4300` | `30.4300, 79.4300` | PCA Code `042235` (Pipalkoti, Chamoli) | Pakhi 2018 (`30.432, 79.431`) | `ROAD-001`, `ROAD-005`, `ROAD-013`, `ROAD-014` | `SH-01` (Pipalkoti Central High School Relief Complex) | Garhwali → Hindi → English |
| **#02** | `VIL-002` | Helang | `30.5200` | `79.5100` | Chamoli | Uttarakhand | Alaknanda Valley | `stationMetadata.ts` | `dataset.py` | `30.5200, 79.5100` | `30.5200, 79.5100` | `30.5200, 79.5100` | PCA Code `042078` (Helang, Chamoli) | Pakhi / Joshimath Sector | `ROAD-001`, `ROAD-002` | `SH-02` (Joshimath High School via `ROAD-002`) | Garhwali → Hindi → English |
| **#03** | `VIL-003` | Govindghat | `30.6200` | `79.5600` | Chamoli | Uttarakhand | Hemkund Corridor | `stationMetadata.ts` | `dataset.py` | `30.6200, 79.5600` | `30.6200, 79.5600` | `30.6200, 79.5600` | PCA Code `042031` (Govindghat, Chamoli) | Govindghat 2013 (`30.624, 79.563`) | `ROAD-002`, `ROAD-003` | `SH-02` (Joshimath High School) | Garhwali → Hindi → English |
| **#04** | `VIL-004` | Pandukeshwar *(Backend: Badrinath Base)* | `30.7400` | `79.4900` | Chamoli | Uttarakhand | Badrinath Highway | `stationMetadata.ts` | `dataset.py` | `30.7400, 79.4900` | `30.7400, 79.4900` | `30.7400, 79.4900` | PCA Code `800913` (Nagar Panchayat Badrinath) | Upper Alaknanda Sector | `ROAD-003`, `ROAD-020` | `SH-06` (Badrinath Safe Ridge) | Garhwali → Hindi → English |
| **#05** | `VIL-005` | Joshimath Lower *(Backend: Karnaprayag)* | `30.2600` | `79.2200` | Chamoli | Uttarakhand | Dhauliganga Confluence | `stationMetadata.ts` | `dataset.py` | `30.2600, 79.2200` | `30.2600, 79.2200` | `30.2600, 79.2200` | PCA Code `800916` (Karnaprayag Palika) | Pindar-Alaknanda Sector | `ROAD-004` | `SH-01` (Pipalkoti via Nandaprayag) | Garhwali → Hindi → English |
| **#06** | `VIL-006` | Rini *(Backend: Nandaprayag)* | `30.3300` | `79.3200` | Chamoli | Uttarakhand | Rishi Ganga Gorge | `stationMetadata.ts` | `dataset.py` | `30.3300, 79.3200` | `30.3300, 79.3200` | `30.3300, 79.3200` | PCA Code `800915` (Nandaprayag Panchayat) | Raini 2021 (`30.485, 79.712`) | `ROAD-004`, `ROAD-005` | `SH-01` (Pipalkoti via `ROAD-005`) | Garhwali → Hindi → English |
| **#07** | `VIL-007` | Tapovan *(Backend: Rudraprayag Sangam)* | `30.2850` | `78.9800` | Rudraprayag | Uttarakhand | Dhauliganga Basin | `stationMetadata.ts` | `dataset.py` | `30.2850, 78.9800` | `30.2850, 78.9800` | `30.2850, 78.9800` | PCA Code `800919` (Rudraprayag Palika) | Lower Mandakini Sector | `ROAD-006`, `ROAD-016` | `SH-03` (Rudraprayag Army Base Camp) | Garhwali → Hindi → English |
| **#08** | `VIL-008` | Surothota *(Backend: Tilwara)* | `30.3500` | `79.0300` | Rudraprayag | Uttarakhand | Upper Niti Valley | `stationMetadata.ts` | `dataset.py` | `30.3500, 79.0300` | `30.3500, 79.0300` | `30.3500, 79.0300` | PCA Code `042654` (Tilwara, Rudraprayag) | Mandakini Valley Sector | `ROAD-006`, `ROAD-007` | `SH-03` (Rudraprayag Army Camp) | Garhwali → Hindi → English |
| **#09** | `VIL-009` | Sonprayag *(Backend: Augustmuni)* | `30.3900` | `79.0800` | Rudraprayag | Uttarakhand | Mandakini Valley | `stationMetadata.ts` | `dataset.py` | `30.3900, 79.0800` | `30.3900, 79.0800` | `30.3900, 79.0800` | PCA Code `042621` (Augustmuni, Rudraprayag) | Middle Mandakini Sector | `ROAD-007`, `ROAD-008` | `SH-03` / `SH-04` | Garhwali → Hindi → English |
| **#10** | `VIL-010` | Gaurikund *(Backend: Guptkashi)* | `30.5250` | `79.0800` | Rudraprayag | Uttarakhand | Mandakini Gorge | `stationMetadata.ts` | `dataset.py` | `30.5250, 79.0800` | `30.5250, 79.0800` | `30.5250, 79.0800` | PCA Code `042592` (Guptkashi, Rudraprayag) | Mandakini Slope Sector | `ROAD-008`, `ROAD-009`, `ROAD-011` | `SH-04` (Ukhimath High Plateau) | Garhwali → Hindi → English |
| **#11** | `VIL-011` | Phata | `30.5700` | `79.0500` | Rudraprayag | Uttarakhand | Mandakini Valley | `stationMetadata.ts` | `dataset.py` | `30.5700, 79.0500` | `30.5700, 79.0500` | `30.5700, 79.0500` | PCA Code `042581` (Phata, Rudraprayag) | Kedarnath Access Sector | `ROAD-009`, `ROAD-010`, `ROAD-018` | `SH-04` / `SH-05` | Garhwali → Hindi → English |
| **#12** | `VIL-012` | Guptkashi *(Backend: Sonprayag)* | `30.6300` | `79.0100` | Rudraprayag | Uttarakhand | Mandakini Ridge | `stationMetadata.ts` | `dataset.py` | `30.6300, 79.0100` | `30.6300, 79.0100` | `30.6300, 79.0100` | PCA Code `042575` (Sonprayag, Rudraprayag) | Kedarnath 2013 (`30.734, 79.066`) | `ROAD-010`, `ROAD-019` | `SH-05` (Kedarnath Valley Base Camp) | Garhwali → Hindi → English |
| **#13** | `VIL-013` | **Aut Basin** *(Backend: Ukhimath Crest)* | `30.5100` | `79.1300` | Rudraprayag *(UI: Mandi)* | Uttarakhand *(UI: HP)* | Beas Gorge, Mandi | `stationMetadata.ts` | `dataset.py` | `30.5100, 79.1300` *(Ukhimath, UK)* | `30.5100, 79.1300` *(Ukhimath, UK)* | `30.5100, 79.1300` *(Ukhimath, UK)* | PCA Code `800920` (Ukhimath Panchayat, UK) | Mandakini Ridge Sector | `ROAD-011`, `ROAD-012`, `ROAD-017` | `SH-04` (Ukhimath Ridge High Plateau) | **UI: Mandyali → Hindi → English** *(Backend Physics: Garhwali)* |
| **#14** | `VIL-014` | **Meppadi Hills** *(Backend: Chopta Ridge)* | `30.4900` | `79.1800` | Rudraprayag *(UI: Wayanad)* | Uttarakhand *(UI: Kerala)* | Vythiri Basin, Wayanad | `stationMetadata.ts` | `dataset.py` | `30.4900, 79.1800` *(Chopta, UK)* | `30.4900, 79.1800` *(Chopta, UK)* | `30.4900, 79.1800` *(Chopta, UK)* | PCA Code `042588` (Chopta Hamlet, UK) | Tungnath Alpine Slope | `ROAD-012` *(connects Ukhimath to Chopta)* | `SH-04` (Ukhimath Shelter via `ROAD-012`) | **UI: Malayalam → English** *(Backend Physics: Garhwali)* |
| **#15** | `VIL-015` | **Chooralmala** *(Backend: Gopeshwar)* | `30.4100` | `79.3300` | Chamoli *(UI: Wayanad)* | Uttarakhand *(UI: Kerala)* | Vellarimala Slope, Wayanad | `stationMetadata.ts` | `dataset.py` | `30.4100, 79.3300` *(Gopeshwar, UK)* | `30.4100, 79.3300` *(Gopeshwar, UK)* | `30.4100, 79.3300` *(Gopeshwar, UK)* | PCA Code `800917` (Gopeshwar Palika, UK) | Chamoli Terrace Sector | `ROAD-013`, `ROAD-015` *(connects Pipalkoti to Gopeshwar)* | `SH-02` (Gopeshwar District Sports Stadium) | **UI: Malayalam → English** *(Backend Physics: Garhwali)* |

---

## B. Current Coordinates Analysis

- **Geographic Bounding Box in Code:**
  - Latitude: `30.2600° N` (Karnaprayag) to `30.7400° N` (Badrinath)
  - Longitude: `78.9800° E` (Rudraprayag Sangam) to `79.5600° E` (Govindghat)
- **Coordinate System:** WGS84 decimal degrees (standard geographic coordinates).
- **Coordinate Precision:** 4 decimal places (~11.1 meters resolution).
- **Physical Extent:** A contiguous ~60 km × 55 km mountain watershed in the Garhwal Himalayas (Chamoli and Rudraprayag districts, Uttarakhand).

---

## C. Geographic Identity of Plotted Points vs Real Features

1. `(30.4300, 79.4300)`: **Pipalkoti Town**, Alaknanda Valley, NH-7, Chamoli District, Uttarakhand.
2. `(30.5200, 79.5100)`: **Helang Village / Urgam Valley Confluence**, NH-7, Chamoli District, Uttarakhand.
3. `(30.6200, 79.5600)`: **Govindghat**, Confluence of Alaknanda and Lakshman Ganga, Chamoli District, Uttarakhand.
4. `(30.7400, 79.4900)`: **Badrinath Base Valley Floor**, Upper Alaknanda, Chamoli District, Uttarakhand.
5. `(30.2600, 79.2200)`: **Karnaprayag Sangam**, Confluence of Alaknanda and Pindar Rivers, Chamoli District, Uttarakhand.
6. `(30.3300, 79.3200)`: **Nandaprayag Sangam**, Confluence of Alaknanda and Nandakini Rivers, Chamoli District, Uttarakhand.
7. `(30.2850, 78.9800)`: **Rudraprayag Sangam**, Confluence of Alaknanda and Mandakini Rivers, Rudraprayag District, Uttarakhand.
8. `(30.3500, 79.0300)`: **Tilwara**, Mandakini Valley, Rudraprayag District, Uttarakhand.
9. `(30.3900, 79.0800)`: **Augustmuni**, Mandakini Valley, Rudraprayag District, Uttarakhand.
10. `(30.5250, 79.0800)`: **Guptkashi**, Mandakini Valley Ridge, Rudraprayag District, Uttarakhand.
11. `(30.5700, 79.0500)`: **Phata**, Mandakini Valley, Rudraprayag District, Uttarakhand.
12. `(30.6300, 79.0100)`: **Sonprayag**, Confluence of Mandakini and Songanga Rivers, Rudraprayag District, Uttarakhand.
13. `(30.5100, 79.1300)`: **Ukhimath Crest / Nagar Panchayat**, Mandakini Ridge, Rudraprayag District, Uttarakhand.
14. `(30.4900, 79.1800)`: **Chopta Alpine Ridge / Tungnath Base**, Rudraprayag District, Uttarakhand.
15. `(30.4100, 79.3300)`: **Gopeshwar Town**, District Headquarters of Chamoli, Uttarakhand.

---

## D. Expected Geographic Architecture vs Current State

```
+--------------------------------------------------------------------------------------------------+
|                               REQUIRED THREE-REGION ARCHITECTURE                                 |
+--------------------------------------------------------------------------------------------------+
|  GROUP 1: STATIONS #01–#12 (Chamoli & Rudraprayag, Uttarakhand)                                  |
|  - Real Coordinates: 30.26°N - 30.74°N, 78.98°E - 79.56°E                                        |
|  - Language Pipeline: Garhwali (Local) -> Hindi (Fallback) -> English (Technical)                |
|                                                                                                  |
|  GROUP 2: STATION #13 (Mandi / Aut Basin, Himachal Pradesh)                                      |
|  - Expected Real Coordinates: ~31.7450°N, 77.2050°E (Beas River Gorge, Mandi, HP)                 |
|  - Language Pipeline: Mandyali (Local) -> Hindi (Fallback) -> English (Technical)                |
|                                                                                                  |
|  GROUP 3: STATIONS #14–#15 (Wayanad, Kerala)                                                     |
|  - Expected Real Coordinates: ~11.5510°N, 76.1260°E (Meppadi) & ~11.5280°N, 76.1680°E (Chooral.) |
|  - Language Pipeline: Malayalam (Local) -> English (Technical)                                    |
+--------------------------------------------------------------------------------------------------+
```

---

## E. Coordinate & Geographic Mismatches

### Critical Cross-State Mismatches (Stations #13, #14, #15)
1. **Station #13 (Aut Basin, Mandi, Himachal Pradesh):**
   - **Plotted Coordinates:** `30.5100° N, 79.1300° E` $\rightarrow$ **Ukhimath, Rudraprayag, Uttarakhand**.
   - **Actual Coordinates of Aut, Mandi, HP:** `~31.7450° N, 77.2050° E` (Beas River Basin).
   - **Discrepancy Distance:** **~183 km** north-west across state borders.
   - **Impact:** Weather is fetched for Ukhimath, slope is computed from Copernicus DEM for Ukhimath, and road network connects it via `ROAD-011` to Guptkashi, Uttarakhand.
2. **Station #14 (Meppadi Hills, Wayanad, Kerala):**
   - **Plotted Coordinates:** `30.4900° N, 79.1800° E` $\rightarrow$ **Chopta Ridge, Rudraprayag, Uttarakhand**.
   - **Actual Coordinates of Meppadi, Kerala:** `~11.5510° N, 76.1260° E` (Western Ghats).
   - **Discrepancy Distance:** **~2,125 km** south across peninsular India.
   - **Impact:** Live rainfall queries Open-Meteo for high Himalayan alpine ridge (2,680m elevation), while UI claims it is a plantation hill in Wayanad.
3. **Station #15 (Chooralmala, Wayanad, Kerala):**
   - **Plotted Coordinates:** `30.4100° N, 79.3300° E` $\rightarrow$ **Gopeshwar Town, Chamoli, Uttarakhand**.
   - **Actual Coordinates of Chooralmala, Kerala:** `~11.5280° N, 76.1680° E` (Vellarimala).
   - **Discrepancy Distance:** **~2,128 km** south.
   - **Impact:** Road `ROAD-013` connects "Chooralmala" to Pipalkoti, Uttarakhand (12 km away).

### Non-Critical Within-Watershed Label Drift (Stations #04–#10, #12)
- **#04:** Coords point to Badrinath Base Valley; UI displays "Pandukeshwar".
- **#05:** Coords point to Karnaprayag; UI displays "Joshimath Lower".
- **#06:** Coords point to Nandaprayag; UI displays "Rini".
- **#07:** Coords point to Rudraprayag Sangam; UI displays "Tapovan" in Chamoli.
- **#08:** Coords point to Tilwara; UI displays "Surothota".
- **#09:** Coords point to Augustmuni; UI displays "Sonprayag".
- **#10:** Coords point to Guptkashi; UI displays "Gaurikund".
- **#12:** Coords point to Sonprayag; UI displays "Guptkashi".

---

## F. Backend Coordinate Source Tracing

- **Source File:** `backend/app/data/dataset.py` (`DEMO_VILLAGES` list)
- **Direct Consumers:**
  - `backend/app/api/routes.py`: `compute_village_risk_detail` passes `latitude`/`longitude` to `pipeline_instance.get_normalized_observation()`.
  - `backend/app/data_pipeline.py`: Uses coordinates for live Open-Meteo REST calls and cache indexing.
  - `backend/app/adapters/open_elevation.py`: Queries Copernicus DEM / Open-Elevation API using `latitude`/`longitude`.
  - `backend/app/adapters/landslide_inventory.py`: Computes Haversine distance from `(village.latitude, village.longitude)` to historical events.

---

## G. Frontend Coordinate Source Tracing

- **Source Files:**
  - `frontend/src/views/PredictionView.tsx` & `LiveMonitoringView.tsx`: Fetch village objects containing `latitude`, `longitude`, `village_name`, and `village_id` from `/api/villages` and `/api/scenarios/baseline`.
  - `frontend/src/utils/stationMetadata.ts`: `STATION_METADATA_MAP` maps `VIL-001`..`VIL-015` to display names, region strings, state strings, and languages.
  - `frontend/src/components/MapView.tsx`: Directly passes `[v.latitude, v.longitude]` to Leaflet `<Marker>` components and computes bounds via `L.latLngBounds(villages.map(v => [v.latitude, v.longitude]))`.

---

## H. Weather Coordinate Source Tracing

- **Adapter File:** `backend/app/adapters/open_meteo.py`
- **REST URL Generated:** `https://api.open-meteo.com/v1/forecast?latitude={latitude:.4f}&longitude={longitude:.4f}&current=precipitation,rain,showers&hourly=precipitation,soil_moisture_0_to_7cm&forecast_days=1`
- **Result:**
  - When Station #13 is queried, Open-Meteo receives `latitude=30.5100, longitude=79.1300` (Ukhimath, UK).
  - When Station #14 is queried, Open-Meteo receives `latitude=30.4900, longitude=79.1800` (Chopta, UK).
  - When Station #15 is queried, Open-Meteo receives `latitude=30.4100, longitude=79.3300` (Gopeshwar, UK).
- **Integrity Failure:** Meteorological telemetry displayed for Mandi and Wayanad is **100% Uttarakhand weather data**.

---

## I. Terrain Coordinate Source Tracing

- **Adapter Files:** `backend/app/adapters/open_elevation.py` & `backend/app/engine/terrain_engine.py`
- **Elevation Grid Fetches:** Queries elevation at `(latitude, longitude)` and calculates 8-point cardinal directional slope matrices around `(latitude, longitude)`.
- **Integrity Failure:** The terrain elevation and slope displayed for Station #14 ("Meppadi Hills") is calculated for Chopta Ridge (2,680m Himalayan altitude), not Wayanad (700–1,100m Western Ghats).

---

## J. Risk-Data Geographic Consistency

- **Flash Flood & Landslide Risk Formulas:**
  - Consume rainfall from Open-Meteo (`latitude, longitude`).
  - Consume soil moisture from Open-Meteo (`latitude, longitude`).
  - Consume terrain slope and flow accumulation from `dataset.py`.
- **Integrity Assessment:** The risk math is computationally consistent with the **plotted Uttarakhand coordinates**, but **geographically invalid** for the displayed entities of Mandi (HP) and Wayanad (Kerala).

---

## K. Historical Landslide Data Consistency

- **Catalog File:** `backend/app/data/isro_gsi_landslides.json`
- **Events in Catalog:**
  - `LS-UK-2021-001`: Raini / Rishiganga Gorge, Chamoli (`30.4850, 79.7120`)
  - `LS-UK-2013-001`: Kedarnath & Rambara Reach, Rudraprayag (`30.7340, 79.0660`)
  - `LS-UK-2013-002`: Govindghat Confluence, Chamoli (`30.6240, 79.5630`)
  - `LS-UK-2018-001`: Pakhi / Pipalkoti Sector, Chamoli (`30.4320, 79.4310`)
- **Integrity Assessment:** **0% of the catalog covers Himachal Pradesh or Kerala**. Proximity calculations for ST-13, ST-14, ST-15 compute distance to Uttarakhand disasters (e.g. ST-13 Ukhimath calculates distance to Kedarnath 2013).

---

## L. Population & Demographic Data Consistency

- **Source File:** `backend/app/data/census_population_data.py`
- **Census Records:**
  - `VIL-013`: Nagar Panchayat Ukhimath (Census Code: `800920`, Rudraprayag, Uttarakhand, Pop: 2,296).
  - `VIL-014`: Chopta Ridge Hamlet (Census Code: `042588`, Rudraprayag, Uttarakhand, Pop: 640).
  - `VIL-015`: Nagar Palika Parishad Chamoli-Gopeshwar (Census Code: `800917`, Chamoli, Uttarakhand, Pop: 6,150).
- **Integrity Assessment:** All demographic records are official Census 2011 Primary Census Abstract entries for **Uttarakhand**. None exist for Mandi (HP) or Wayanad (KL).

---

## M. Road Network & Shelter Evacuation Consistency

- **Road Graph:** `backend/app/data/road_network.py`
  - `ROAD-011`: Connects `VIL-010` (Guptkashi) to `VIL-013` (7.5 km).
  - `ROAD-012`: Connects `VIL-013` to `VIL-014` (18.0 km).
  - `ROAD-013`: Connects `VIL-001` (Pipalkoti) to `VIL-015` (12.0 km).
  - `ROAD-017`: Connects `VIL-013` to Shelter `SH-04` (Ukhimath High Plateau, 4.0 km).
  - `ROAD-015`: Connects `VIL-015` to Shelter `SH-02` (Gopeshwar Stadium, 3.0 km).
- **Integrity Failure:** If ST-13 were in Mandi and ST-14/15 were in Kerala:
  - "Meppadi Hills, Wayanad" is routed via an 18 km mountain road to "Aut Basin, Mandi, HP" and then to Ukhimath Shelter in Uttarakhand!
  - "Chooralmala, Wayanad" is routed via a 3 km local road to Gopeshwar Stadium in Chamoli, Uttarakhand!

---

## N. Language Registry Consistency

- **Frontend Specification (`stationMetadata.ts`):**
  - ST-01 to ST-12: Primary `Garhwali`, Fallback `Hindi`, Technical `English`
  - ST-13: Primary `Mandyali`, Fallback `Hindi`, Technical `English`
  - ST-14 & ST-15: Primary `Malayalam`, Technical `English`
- **Backend Alert Engine (`backend/app/models/alert.py` & `alert_engine.py`):**
  - Generates 5 official languages: `en` (English), `hi` (Hindi), `garhwali` (Garhwali), `kumaoni` (Kumaoni), `nepali` (Nepali).
- **Integrity Assessment:**
  - Mandyali and Malayalam are present as metadata strings in the frontend, but the backend alert engine generates Garhwali/Kumaoni/Nepali/Hindi/English.

---

## O. Map Rendering & Coordinate System

- **Map Component:** `frontend/src/components/MapView.tsx`
- **Leaflet Configuration:**
  - Base Center: `[30.45, 79.25]` (Chamoli/Rudraprayag, Uttarakhand)
  - Zoom: 10
  - Coordinate system: Unprojected standard WGS84 lat/lon.
  - River Overlays: Hardcoded polyline tracks `ALAKNANDA_RIVER_COORDS` (`30.74, 79.49` to `30.285, 78.98`) and `MANDAKINI_RIVER_COORDS` (`30.73, 79.07` to `30.285, 78.98`).
- **Integrity Assessment:** The map renders standard geographic coordinates with no distortion. However, because all 15 stations have Uttarakhand coordinates, **all 15 station markers appear clustered together inside the Uttarakhand valley**, even though markers #14 and #15 are labeled "Wayanad, Kerala".

---

## P. List of Critical Errors

1. **CRITICAL-01:** Stations #14 and #15 are labeled as "Wayanad, Kerala" in frontend metadata, but their coordinates point to Chopta (`30.49, 79.18`) and Gopeshwar (`30.41, 79.33`) in Uttarakhand (>2,120 km discrepancy).
2. **CRITICAL-02:** Station #13 is labeled as "Aut Basin, Mandi, Himachal Pradesh" in frontend metadata, but its coordinates point to Ukhimath (`30.51, 79.13`) in Uttarakhand (>180 km discrepancy).
3. **CRITICAL-03:** Live Open-Meteo weather and soil moisture requests for Stations #13, #14, and #15 query Uttarakhand GPS coordinates.
4. **CRITICAL-04:** Evacuation routes for Stations #14 and #15 connect across the Uttarakhand mountain road network to Uttarakhand relief shelters (`SH-04` and `SH-02`).
5. **CRITICAL-05:** Demographic Census 2011 records for Stations #13, #14, and #15 point to Uttarakhand tehsils (Ukhimath and Dasholi).

---

## Q. List of Non-Critical Errors

1. **NON-CRITICAL-01:** Station #04 display name is "Pandukeshwar", but backend coordinate `30.7400, 79.4900` points to Badrinath Base Valley (~15 km north).
2. **NON-CRITICAL-02:** Station #05 display name is "Joshimath Lower", but backend coordinate `30.2600, 79.2200` points to Karnaprayag Reach (~50 km south-west).
3. **NON-CRITICAL-03:** Station #06 display name is "Rini", but backend coordinate `30.3300, 79.3200` points to Nandaprayag Basin.
4. **NON-CRITICAL-04:** Station #07 display name is "Tapovan", but backend coordinate `30.2850, 78.9800` points to Rudraprayag Sangam.
5. **NON-CRITICAL-05:** Stations #08, #09, #10, #12 have localized name swap drifts across the Mandakini Valley.

---

## R. Recommended Correction Plan

*(To be implemented only after user review and explicit approval)*

### Recommended Solution: Unified 3-Region Multi-Basin Geospatial Architecture

To faithfully fulfill the required architecture:
- **Group 1 (ST-01 to ST-12):** Chamoli & Rudraprayag, Uttarakhand. Keep current coordinates and align display names with actual valley features.
- **Group 2 (ST-13):** Mandi / Aut Basin, Himachal Pradesh.
  - Set coordinates to real Aut coordinates: `31.7450° N, 77.2050° E`.
  - Add local Mandi/Beas road segment and a dedicated Mandi emergency shelter.
  - Provide Census 2011 PCA data for Mandi district.
- **Group 3 (ST-14 & ST-15):** Wayanad, Kerala.
  - Set ST-14 coordinates to Meppadi: `11.5510° N, 76.1260° E`.
  - Set ST-15 coordinates to Chooralmala: `11.5280° N, 76.1680° E`.
  - Add local Wayanad road segments and dedicated Wayanad emergency shelters (e.g. Meppadi Government Higher Secondary School).
  - Provide Census 2011 PCA data for Vythiri / Wayanad.
  - Enable multi-region map views (tabs or pan-to-cluster controls) so the user can inspect Uttarakhand, Himachal Pradesh, and Kerala separately without rendering 2,000 km spanning lines.

---

## S. Station Provenance & Classification

| Station ID | Classification | Justification |
| :--- | :--- | :--- |
| **ST-01 (Pipalkoti)** | **REAL LOCATION** | Validated Census PCA `042235`, exact NH-7 coordinates, matching UI & backend. |
| **ST-02 (Helang)** | **REAL LOCATION** | Validated Census PCA `042078`, exact NH-7 coordinates, matching UI & backend. |
| **ST-03 (Govindghat)** | **REAL LOCATION** | Validated Census PCA `042031`, exact Bhyundar Ganga confluence coordinates. |
| **ST-04 (Badrinath / Pandukeshwar)** | **MISLOCATED (LABEL DRIFT)** | Coordinates are real Badrinath; displayed name is Pandukeshwar. |
| **ST-05 (Karnaprayag / Joshimath Lower)** | **MISLOCATED (LABEL DRIFT)** | Coordinates are real Karnaprayag; displayed name is Joshimath Lower. |
| **ST-06 (Nandaprayag / Rini)** | **MISLOCATED (LABEL DRIFT)** | Coordinates are real Nandaprayag; displayed name is Rini. |
| **ST-07 (Rudraprayag / Tapovan)** | **MISLOCATED (LABEL DRIFT)** | Coordinates are real Rudraprayag Sangam; displayed name is Tapovan. |
| **ST-08 (Tilwara / Surothota)** | **MISLOCATED (LABEL DRIFT)** | Coordinates are real Tilwara; displayed name is Surothota. |
| **ST-09 (Augustmuni / Sonprayag)** | **MISLOCATED (LABEL DRIFT)** | Coordinates are real Augustmuni; displayed name is Sonprayag. |
| **ST-10 (Guptkashi / Gaurikund)** | **MISLOCATED (LABEL DRIFT)** | Coordinates are real Guptkashi; displayed name is Gaurikund. |
| **ST-11 (Phata)** | **REAL LOCATION** | Validated Census PCA `042581`, exact Mandakini Valley coordinates. |
| **ST-12 (Sonprayag / Guptkashi)** | **MISLOCATED (LABEL DRIFT)** | Coordinates are real Sonprayag Confluence; displayed name is Guptkashi. |
| **ST-13 (Aut Basin / Ukhimath)** | **MISLOCATED (CROSS-STATE)** | Displayed as Mandi, HP; underlying coordinates & data are Ukhimath, Uttarakhand. |
| **ST-14 (Meppadi / Chopta)** | **MISLOCATED (INTER-REGIONAL)** | Displayed as Wayanad, Kerala; underlying coordinates & data are Chopta, Uttarakhand. |
| **ST-15 (Chooralmala / Gopeshwar)** | **MISLOCATED (INTER-REGIONAL)** | Displayed as Wayanad, Kerala; underlying coordinates & data are Gopeshwar, Uttarakhand. |

---

## 14. Verification Test Baseline

- **Backend Test Suite:**
  ```
  cd backend
  python -m pytest -q
  Result: 171 passed, 1 warning in 356.04s (100% PASS)
  ```
- **Frontend Build:**
  ```
  cd frontend
  npm run build
  Result: Built in 4.29s (100% PASS)
  ```

---
*End of Audit Report. No source files modified.*
