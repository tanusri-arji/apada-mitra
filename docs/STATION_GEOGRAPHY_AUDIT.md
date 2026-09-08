# APADA MITRA — STATION GEOGRAPHY AUDIT
**Project:** SIH26192 | APADA MITRA  
**Theme:** Disaster Management  
**Scope:** Comprehensive Audit of all 15 Monitored Stations (ST-01 to ST-15 / VIL-001 to VIL-015) across Geography, Coordinates, Administrative Mapping, Road Topology, Census Demographics, and Multilingual Settings.  
**Constraint:** READ-ONLY AUDIT. No code, data, formulas, or coordinates have been modified.

---

## 1. Executive Summary & Verification Objective

The verification audit examined all 15 stations across:
- Backend Ground-Truth Dataset (`backend/app/data/dataset.py`)
- Census 2011 Primary Census Abstract Demographic Store (`backend/app/data/census_population_data.py`)
- Mountain Road Network Topology & Geometry (`backend/app/data/road_network.py`)
- Shelter Allocation & Evacuation Mapping (`backend/app/data/shelters.py`)
- Frontend Metadata & Multilingual Mapping (`frontend/src/utils/stationMetadata.ts`)
- Multi-Hazard Risk & Alert Generation Engine (`backend/app/engine/alert_engine.py`)

### Core Verification Findings:
1. **Underlying Physics & Geospatial Foundation:** **100% of the physical coordinates** (`30.2600°N - 30.7400°N`, `78.9800°E - 79.5600°E`), DEM elevation profiles, Open-Meteo weather grid queries, Copernicus terrain slope, CWC river gauge baselines, Census 2011 village codes, and Dijkstra road graph segments are located in **Chamoli and Rudraprayag districts, Uttarakhand (Alaknanda & Mandakini Basins)**.
2. **ST-13 Discrepancy (Himachal Pradesh):** Frontend `stationMetadata.ts` displays ST-13 as **"Aut Basin, Mandi, Himachal Pradesh"** with **Mandyali** language. However, its coordinates (`30.5100°N, 79.1300°E`) physically point to **Ukhimath, Rudraprayag, Uttarakhand**. Actual Aut, Mandi is ~180 km away in Himachal Pradesh (`~31.745°N, 77.205°E`).
3. **ST-14 & ST-15 Discrepancies (Kerala):** Frontend `stationMetadata.ts` displays ST-14 as **"Meppadi Hills, Wayanad, Kerala"** and ST-15 as **"Chooralmala, Wayanad, Kerala"** with **Malayalam** language. However, their coordinates (`30.4900°N, 79.1800°E` and `30.4100°N, 79.3300°E`) physically point to **Chopta** and **Gopeshwar** in **Uttarakhand**. Actual Wayanad is >2,100 km away in the Western Ghats of Kerala (`~11.55°N, 76.13°E`).
4. **ST-04 to ST-12 Local Naming Drift:** Several Uttarakhand stations have a label drift between `dataset.py` (e.g. Badrinath Base Valley, Karnaprayag, Nandaprayag, Rudraprayag, Tilwara, Augustmuni) and `stationMetadata.ts` (e.g. Pandukeshwar, Joshimath Lower, Rini, Tapovan, Surothota, Gaurikund).

---

## 2. Master Station Geography & Mapping Audit Table

| Station ID | Village ID | Backend Dataset Name | Frontend Displayed Name | Lat (°N) | Lon (°E) | Coordinate-Derived Physical Location | Displayed Region & State | Displayed Primary Language | Actual Regional Language | Provenance Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ST-01** | `VIL-001` | Pipalkoti | Pipalkoti | `30.4300` | `79.4300` | Pipalkoti, Chamoli, Uttarakhand | Alaknanda Valley, Chamoli, Uttarakhand | Garhwali | Garhwali / Hindi | **Real** (Census Code: 042235) |
| **ST-02** | `VIL-002` | Helang | Helang | `30.5200` | `79.5100` | Helang / Urgam Confluence, Chamoli, UK | Alaknanda Valley, Chamoli, Uttarakhand | Garhwali | Garhwali / Hindi | **Real** (Census Code: 042078) |
| **ST-03** | `VIL-003` | Govindghat | Govindghat | `30.6200` | `79.5600` | Govindghat (Hemkund Track), Chamoli, UK | Hemkund Corridor, Chamoli, Uttarakhand | Garhwali | Garhwali / Hindi | **Real** (Census Code: 042031) |
| **ST-04** | `VIL-004` | Badrinath Base Valley | Pandukeshwar | `30.7400` | `79.4900` | Badrinath Valley, Chamoli, UK | Badrinath Highway, Chamoli, Uttarakhand | Garhwali | Garhwali / Hindi | **Real Coordinates / Display Label Mismatch** |
| **ST-05** | `VIL-005` | Karnaprayag Reach | Joshimath Lower | `30.2600` | `79.2200` | Karnaprayag (Pindar Sangam), Chamoli, UK | Dhauliganga Confluence, Chamoli, Uttarakhand | Garhwali | Garhwali / Hindi | **Real Coordinates / Display Label Mismatch** |
| **ST-06** | `VIL-006` | Nandaprayag Basin | Rini | `30.3300` | `79.3200` | Nandaprayag, Chamoli, UK | Rishi Ganga Gorge, Chamoli, Uttarakhand | Garhwali | Garhwali / Hindi | **Real Coordinates / Display Label Mismatch** |
| **ST-07** | `VIL-007` | Rudraprayag Sangam | Tapovan | `30.2850` | `78.9800` | Rudraprayag Sangam, Rudraprayag, UK | Dhauliganga Basin, Chamoli, Uttarakhand | Garhwali | Garhwali / Hindi | **Real Coordinates / Display Label Mismatch** |
| **ST-08** | `VIL-008` | Tilwara Valley | Surothota | `30.3500` | `79.0300` | Tilwara (Mandakini Valley), Rudraprayag, UK | Upper Niti Valley, Chamoli, Uttarakhand | Garhwali | Garhwali / Hindi | **Real Coordinates / Display Label Mismatch** |
| **ST-09** | `VIL-009` | Augustmuni Stream | Sonprayag | `30.3900` | `79.0800` | Augustmuni, Rudraprayag, UK | Mandakini Valley, Rudraprayag, Uttarakhand | Garhwali | Garhwali / Hindi | **Real Coordinates / Display Label Mismatch** |
| **ST-10** | `VIL-010` | Guptkashi Slope | Gaurikund | `30.5250` | `79.0800` | Guptkashi, Rudraprayag, UK | Mandakini Gorge, Rudraprayag, Uttarakhand | Garhwali | Garhwali / Hindi | **Real Coordinates / Display Label Mismatch** |
| **ST-11** | `VIL-011` | Phata Funnel | Phata | `30.5700` | `79.0500` | Phata, Rudraprayag, UK | Mandakini Valley, Rudraprayag, Uttarakhand | Garhwali | Garhwali / Hindi | **Real** (Census Code: 042581) |
| **ST-12** | `VIL-012` | Sonprayag Confluence | Guptkashi | `30.6300` | `79.0100` | Sonprayag, Rudraprayag, UK | Mandakini Ridge, Rudraprayag, Uttarakhand | Garhwali | Garhwali / Hindi | **Real Coordinates / Display Label Mismatch** |
| **ST-13** | `VIL-013` | Ukhimath Crest | Aut Basin | `30.5100` | `79.1300` | Ukhimath, Rudraprayag, UK | Beas Gorge, Mandi, Himachal Pradesh | Mandyali | Garhwali / Hindi | **CRITICAL MISMATCH: HP Label on UK Coordinates** |
| **ST-14** | `VIL-014` | Chopta Ridge Village | Meppadi Hills | `30.4900` | `79.1800` | Chopta Ridge, Rudraprayag, UK | Vythiri Basin, Wayanad, Kerala | Malayalam | Garhwali / Hindi | **CRITICAL MISMATCH: Kerala Label on UK Coordinates** |
| **ST-15** | `VIL-015` | Gopeshwar Terrace | Chooralmala | `30.4100` | `79.3300` | Gopeshwar, Chamoli, UK | Vellarimala Slope, Wayanad, Kerala | Malayalam | Garhwali / Hindi | **CRITICAL MISMATCH: Kerala Label on UK Coordinates** |

---

## 3. Station-by-Station Deep Dive Audit

### Station 01: `VIL-001` — Pipalkoti
- **Backend Dataset:** Pipalkoti, Dasholi block, Chamoli, UK
- **Coordinates:** `30.4300° N, 79.4300° E` (Elevation 1,260m)
- **Census 2011 PCA Record:** Code `042235`, Pop: 2,411 (Verified)
- **Frontend Display:** "Pipalkoti", Alaknanda Valley, Chamoli, Uttarakhand
- **Language Mapping:** Garhwali (Primary), Hindi (Fallback), English (Technical)
- **Road & Shelter Topology:** Linked to Helang via NH-7 (`ROAD-001`), Nandaprayag (`ROAD-005`), Gopeshwar (`ROAD-013`), and Shelter `SH-01` (Pipalkoti Central High School Relief Complex, 4.5km).
- **Audit Assessment:** **FULL MATCH / REAL SETTLEMENT**.

---

### Station 02: `VIL-002` — Helang
- **Backend Dataset:** Helang, Joshimath block, Chamoli, UK
- **Coordinates:** `30.5200° N, 79.5100° E` (Elevation 1,540m)
- **Census 2011 PCA Record:** Code `042078`, Pop: 1,814 (Verified)
- **Frontend Display:** "Helang", Alaknanda Valley, Chamoli, Uttarakhand
- **Language Mapping:** Garhwali (Primary), Hindi (Fallback), English (Technical)
- **Road & Shelter Topology:** Linked to Pipalkoti (`ROAD-001`), Govindghat (`ROAD-002`), and Shelter `SH-02` (Joshimath Higher Secondary School, 8.5km).
- **Audit Assessment:** **FULL MATCH / REAL SETTLEMENT**.

---

### Station 03: `VIL-003` — Govindghat
- **Backend Dataset:** Govindghat, Joshimath block, Chamoli, UK
- **Coordinates:** `30.6200° N, 79.5600° E` (Elevation 1,820m)
- **Census 2011 PCA Record:** Code `042031`, Pop: 1,237 (Verified)
- **Frontend Display:** "Govindghat", Hemkund Corridor, Chamoli, Uttarakhand
- **Language Mapping:** Garhwali (Primary), Hindi (Fallback), English (Technical)
- **Road & Shelter Topology:** Linked to Helang (`ROAD-002`), Badrinath (`ROAD-003`), and Shelter `SH-02` (Joshimath High School, 14.2km).
- **Audit Assessment:** **FULL MATCH / REAL SETTLEMENT**.

---

### Station 04: `VIL-004` — Badrinath Base Valley / Pandukeshwar
- **Backend Dataset:** Badrinath Base Valley, Joshimath block, Chamoli, UK
- **Coordinates:** `30.7400° N, 79.4900° E` (Elevation 3,100m)
- **Census 2011 PCA Record:** Code `800913` (Nagar Panchayat Badrinath), Pop: 2,438 (Verified)
- **Frontend Display:** "Pandukeshwar", Badrinath Highway, Chamoli, Uttarakhand
- **Language Mapping:** Garhwali (Primary), Hindi (Fallback), English (Technical)
- **Discrepancy:** Coordinates (`30.7400, 79.4900`) point to Badrinath town valley. Pandukeshwar is located further south along NH-7 at `30.6400° N, 79.5400° E`.
- **Audit Assessment:** **NAME/COORDINATE DRIFT**. Physical model tracks Badrinath; UI displays Pandukeshwar.

---

### Station 05: `VIL-005` — Karnaprayag Reach / Joshimath Lower
- **Backend Dataset:** Karnaprayag Reach, Karnaprayag block, Chamoli, UK
- **Coordinates:** `30.2600° N, 79.2200° E` (Elevation 860m)
- **Census 2011 PCA Record:** Code `800916` (Nagar Palika Parishad Karnaprayag), Pop: 4,200 (Verified)
- **Frontend Display:** "Joshimath Lower", Dhauliganga Confluence, Chamoli, Uttarakhand
- **Language Mapping:** Garhwali (Primary), Hindi (Fallback), English (Technical)
- **Discrepancy:** Coordinates (`30.2600, 79.2200`) point to Karnaprayag Sangam in southern Chamoli. Frontend displays "Joshimath Lower" / Dhauliganga Confluence, which is >50 km upstream to the northeast.
- **Audit Assessment:** **NAME/REGION DRIFT**. Physical model tracks Karnaprayag; UI displays Joshimath Lower.

---

### Station 06: `VIL-006` — Nandaprayag Basin / Rini
- **Backend Dataset:** Nandaprayag Basin, Nandaprayag block, Chamoli, UK
- **Coordinates:** `30.3300° N, 79.3200° E` (Elevation 910m)
- **Census 2011 PCA Record:** Code `800915` (Nagar Panchayat Nandaprayag), Pop: 1,950 (Verified)
- **Frontend Display:** "Rini", Rishi Ganga Gorge, Chamoli, Uttarakhand
- **Language Mapping:** Garhwali (Primary), Hindi (Fallback), English (Technical)
- **Discrepancy:** Coordinates (`30.3300, 79.3200`) point to Nandaprayag (confluence of Alaknanda & Nandakini). Frontend displays "Rini" (Rishi Ganga gorge near Tapovan, `~30.48° N, 79.69° E`).
- **Audit Assessment:** **NAME/REGION DRIFT**. Physical model tracks Nandaprayag; UI displays Rini.

---

### Station 07: `VIL-007` — Rudraprayag Sangam / Tapovan
- **Backend Dataset:** Rudraprayag Sangam, Rudraprayag block, Rudraprayag, UK
- **Coordinates:** `30.2850° N, 78.9800° E` (Elevation 895m)
- **Census 2011 PCA Record:** Code `800919` (Nagar Palika Rudraprayag), Pop: 5,800 (Verified)
- **Frontend Display:** "Tapovan", Dhauliganga Basin, Chamoli, Uttarakhand
- **Language Mapping:** Garhwali (Primary), Hindi (Fallback), English (Technical)
- **Discrepancy:** Coordinates (`30.2850, 78.9800`) point to Rudraprayag Sangam in Rudraprayag District. Frontend displays "Tapovan", which is in eastern Chamoli (`~30.49° N, 79.62° E`).
- **Audit Assessment:** **NAME/DISTRICT DRIFT**. Physical model tracks Rudraprayag; UI displays Tapovan in Chamoli.

---

### Station 08: `VIL-008` — Tilwara Valley / Surothota
- **Backend Dataset:** Tilwara Valley, Augustmuni block, Rudraprayag, UK
- **Coordinates:** `30.3500° N, 79.0300° E` (Elevation 980m)
- **Census 2011 PCA Record:** Code `042654`, Pop: 1,600 (Verified)
- **Frontend Display:** "Surothota", Upper Niti Valley, Chamoli, Uttarakhand
- **Language Mapping:** Garhwali (Primary), Hindi (Fallback), English (Technical)
- **Discrepancy:** Coordinates (`30.3500, 79.0300`) point to Tilwara on Mandakini River. Frontend displays "Surothota" (Niti Valley border zone in Chamoli, `~30.56° N, 79.77° E`).
- **Audit Assessment:** **NAME/REGION DRIFT**. Physical model tracks Tilwara; UI displays Surothota.

---

### Station 09: `VIL-009` — Augustmuni Stream / Sonprayag
- **Backend Dataset:** Augustmuni Stream, Augustmuni block, Rudraprayag, UK
- **Coordinates:** `30.3900° N, 79.0800° E` (Elevation 1,020m)
- **Census 2011 PCA Record:** Code `042621`, Pop: 2,900 (Verified)
- **Frontend Display:** "Sonprayag", Mandakini Valley, Rudraprayag, Uttarakhand
- **Language Mapping:** Garhwali (Primary), Hindi (Fallback), English (Technical)
- **Discrepancy:** Coordinates (`30.3900, 79.0800`) point to Augustmuni town. Frontend displays "Sonprayag" (which is actually at `30.6300, 79.0100`, mapped to ST-12).
- **Audit Assessment:** **NAME SWAP DRIFT**. Physical model tracks Augustmuni; UI displays Sonprayag.

---

### Station 10: `VIL-010` — Guptkashi Slope / Gaurikund
- **Backend Dataset:** Guptkashi Slope, Ukhimath block, Rudraprayag, UK
- **Coordinates:** `30.5250° N, 79.0800° E` (Elevation 1,320m)
- **Census 2011 PCA Record:** Code `042592`, Pop: 2,100 (Verified)
- **Frontend Display:** "Gaurikund", Mandakini Gorge, Rudraprayag, Uttarakhand
- **Language Mapping:** Garhwali (Primary), Hindi (Fallback), English (Technical)
- **Discrepancy:** Coordinates (`30.5250, 79.0800`) point to Guptkashi. Frontend displays "Gaurikund" (Kedarnath base, `~30.65° N, 79.03° E`).
- **Audit Assessment:** **NAME SWAP DRIFT**. Physical model tracks Guptkashi; UI displays Gaurikund.

---

### Station 11: `VIL-011` — Phata Funnel / Phata
- **Backend Dataset:** Phata Funnel, Ukhimath block, Rudraprayag, UK
- **Coordinates:** `30.5700° N, 79.0500° E` (Elevation 1,500m)
- **Census 2011 PCA Record:** Code `042581`, Pop: 1,400 (Verified)
- **Frontend Display:** "Phata", Mandakini Valley, Rudraprayag, Uttarakhand
- **Language Mapping:** Garhwali (Primary), Hindi (Fallback), English (Technical)
- **Road & Shelter Topology:** Linked to Guptkashi (`ROAD-009`), Sonprayag (`ROAD-010`), and Shelter `SH-05` (Phata GMVN Tourist Complex, 0.8km).
- **Audit Assessment:** **FULL MATCH / REAL SETTLEMENT**.

---

### Station 12: `VIL-012` — Sonprayag Confluence / Guptkashi
- **Backend Dataset:** Sonprayag Confluence, Ukhimath block, Rudraprayag, UK
- **Coordinates:** `30.6300° N, 79.0100° E` (Elevation 1,820m)
- **Census 2011 PCA Record:** Code `042575`, Pop: 1,120 (Verified)
- **Frontend Display:** "Guptkashi", Mandakini Ridge, Rudraprayag, Uttarakhand
- **Language Mapping:** Garhwali (Primary), Hindi (Fallback), English (Technical)
- **Discrepancy:** Coordinates (`30.6300, 79.0100`) point to Sonprayag Confluence. Frontend displays "Guptkashi".
- **Audit Assessment:** **NAME SWAP DRIFT**. Physical model tracks Sonprayag; UI displays Guptkashi.

---

### Station 13: `VIL-013` — Ukhimath Crest vs. Aut Basin (Mandi, HP)
- **Backend Dataset:** Ukhimath Crest, Ukhimath block, Rudraprayag, UK
- **Coordinates:** `30.5100° N, 79.1300° E` (Elevation 1,450m)
- **Census 2011 PCA Record:** Code `800920` (Nagar Panchayat Ukhimath, Uttarakhand), Pop: 2,296
- **Road Connections:** `ROAD-011` connects Guptkashi (`30.525, 79.08`) to Ukhimath (`30.510, 79.13`) across 7.5 km. `ROAD-012` connects Ukhimath to Chopta across 18.0 km.
- **Frontend Display:** "Aut Basin", Region: "Beas Gorge, Mandi", State: "Himachal Pradesh"
- **Frontend Language:** Mandyali (Primary), Hindi (Fallback), English (Technical)
- **Actual Coordinates of Aut, Mandi, HP:** `~31.7450° N, 77.2050° E` (Beas River basin, Mandi District, Himachal Pradesh).
- **Physical Distance Between Claimed Display and Actual Plotted Point:** **~183 km across state lines**.
- **Audit Assessment:** **CRITICAL CROSS-STATE MISMATCH**.
  - If considered "Aut Basin, HP": The coordinates, weather calls, DEM slopes, Census PCA codes, and road graph are completely wrong (pointing to Ukhimath, UK).
  - If considered "Ukhimath, UK": The backend data is 100% physically coherent and connected to the Mandakini road graph, but the frontend metadata title ("Aut Basin", "Himachal Pradesh", "Mandyali") is a synthetic UI hallucination.

---

### Station 14: `VIL-014` — Chopta Ridge Village vs. Meppadi Hills (Wayanad, Kerala)
- **Backend Dataset:** Chopta Ridge Village, Ukhimath block, Rudraprayag, UK
- **Coordinates:** `30.4900° N, 79.1800° E` (Elevation 2,680m)
- **Census 2011 PCA Record:** Code `042588` (Chopta Hamlet, Rudraprayag, Uttarakhand), Pop: 640
- **Road Connections:** `ROAD-012` connects Ukhimath (`30.510, 79.13`) to Chopta (`30.490, 79.18`) across 18.0 km.
- **Frontend Display:** "Meppadi Hills", Region: "Vythiri Basin, Wayanad", State: "Kerala"
- **Frontend Language:** Malayalam (Primary), English (Fallback), English (Technical)
- **Actual Coordinates of Meppadi, Wayanad, Kerala:** `~11.5510° N, 76.1260° E` (Western Ghats, Wayanad District, Kerala).
- **Physical Distance Between Claimed Display and Actual Plotted Point:** **~2,125 km across the Indian subcontinent**.
- **Audit Assessment:** **CRITICAL INTER-REGIONAL MISMATCH**.
  - If considered "Meppadi, Kerala": The coordinates, Open-Meteo queries, DEM slopes, Census PCA codes, and road graph are completely wrong (pointing to high Himalayan ridge in Chopta, UK).
  - If considered "Chopta, UK": The backend data is 100% physically coherent and connected to the Rudraprayag road network, but the frontend metadata ("Meppadi Hills", "Kerala", "Malayalam") is a synthetic UI hallucination.

---

### Station 15: `VIL-015` — Gopeshwar Terrace vs. Chooralmala (Wayanad, Kerala)
- **Backend Dataset:** Gopeshwar Terrace, Dasholi block, Chamoli, UK
- **Coordinates:** `30.4100° N, 79.3300° E` (Elevation 1,550m)
- **Census 2011 PCA Record:** Code `800917` (Nagar Palika Parishad Chamoli-Gopeshwar, Uttarakhand), Pop: 6,150
- **Road Connections:** `ROAD-013` connects Pipalkoti (`30.430, 79.43`) to Gopeshwar (`30.410, 79.33`) across 12.0 km.
- **Frontend Display:** "Chooralmala", Region: "Vellarimala Slope, Wayanad", State: "Kerala"
- **Frontend Language:** Malayalam (Primary), English (Fallback), English (Technical)
- **Actual Coordinates of Chooralmala, Wayanad, Kerala:** `~11.5280° N, 76.1680° E` (Wayanad, Kerala).
- **Physical Distance Between Claimed Display and Actual Plotted Point:** **~2,128 km across the Indian subcontinent**.
- **Audit Assessment:** **CRITICAL INTER-REGIONAL MISMATCH**.
  - If considered "Chooralmala, Kerala": The coordinates, weather queries, DEM slope, Census PCA codes, and road graph are completely wrong (pointing to Gopeshwar, Chamoli, UK).
  - If considered "Gopeshwar, UK": The backend data is 100% physically coherent and connected to the Chamoli road network, but the frontend metadata ("Chooralmala", "Kerala", "Malayalam") is a synthetic UI hallucination.

---

## 4. Multi-Layer Integrity Audit (Roads, Shelters, Demographics, Weather, Alerts)

```
+---------------------------------------------------------------------------------------------------+
|                               APADA MITRA SYSTEM GEOGRAPHY COHESION                                |
+---------------------------------------------------------------------------------------------------+
|  BACKEND ENGINE LAYER                |  FRONTEND DISPLAY LAYER        |  STATUS                   |
+--------------------------------------+--------------------------------+---------------------------+
|  Weather (Open-Meteo Lat/Lon)        |  Map Pin Lat/Lon               |  COHERENT (All Uttarakhand)|
|  DEM Slopes (Copernicus 30m)         |  Terrain 3D Elevation & Slope  |  COHERENT (All Uttarakhand)|
|  Roads (NH-7, NH-107, UK Links)      |  Leaflet Polylines             |  COHERENT (All Uttarakhand)|
|  Shelters (Chamoli/Rudraprayag)      |  Shelter Markers & Routes      |  COHERENT (All Uttarakhand)|
|  Census 2011 PCA (UK Codes)          |  Exposure Engine               |  COHERENT (All Uttarakhand)|
|  Alert Languages (Feature 11 Engine) |  EN, HI, GAR, KUM, NEP         |  COHERENT (Uttarakhand)   |
+--------------------------------------+--------------------------------+---------------------------+
|  ST-13 Title / Region / Lang         |  Aut Basin / Mandi / HP        |  MISMATCH with Lat/Lon    |
|  ST-14 Title / Region / Lang         |  Meppadi / Wayanad / KL        |  MISMATCH with Lat/Lon    |
|  ST-15 Title / Region / Lang         |  Chooralmala / Wayanad / KL    |  MISMATCH with Lat/Lon    |
+---------------------------------------------------------------------------------------------------+
```

### Key System Interdependencies:
1. **The Road Graph relies on Uttarakhand spatial contiguity:**
   - `ROAD-011` (`Guptkashi -> Ukhimath`): 7.5 km
   - `ROAD-012` (`Ukhimath -> Chopta`): 18.0 km
   - `ROAD-013` (`Pipalkoti -> Gopeshwar`): 12.0 km
   If ST-13 were placed in Mandi (HP) and ST-14/15 in Wayanad (KL), the Dijkstra shortest-path evacuation engine would fail because vehicles cannot drive 2,000 km across non-existent edges in an 18 km graph.
2. **The Weather & Landslide Engines query real GPS coordinates:**
   - Every 15-minute live telemetry cycle queries Open-Meteo API using the station's lat/lon.
   - For ST-14, the API queries `(30.49, 79.18)` — pulling live rainfall in Chopta, Uttarakhand, not Wayanad, Kerala.
3. **Census 2011 Demographics:**
   - `census_population_data.py` maps ST-13 to Nagar Panchayat Ukhimath (Code: `800920`), ST-14 to Chopta (Code: `042588`), and ST-15 to Chamoli-Gopeshwar (Code: `800917`).
   - None of the Census tables contain data for Himachal Pradesh or Kerala.

---

## 5. Provenance & Classification of All 15 Stations

| Category | Station IDs | Description |
| :--- | :--- | :--- |
| **Real & Fully Verified (Coordinates, Census, Roads, UI in Sync)** | `ST-01` (Pipalkoti)<br>`ST-02` (Helang)<br>`ST-03` (Govindghat)<br>`ST-11` (Phata) | Real Himalayan settlements with exact Census 2011 PCA codes, exact Open-Meteo rainfall coordinates, verified road connections on NH-7 / NH-107, and matching UI titles. |
| **Real Uttarakhand Settlements with Frontend Label/Index Drift** | `ST-04` (Badrinath)<br>`ST-05` (Karnaprayag)<br>`ST-06` (Nandaprayag)<br>`ST-07` (Rudraprayag)<br>`ST-08` (Tilwara)<br>`ST-09` (Augustmuni)<br>`ST-10` (Guptkashi)<br>`ST-12` (Sonprayag) | Real Uttarakhand locations with verified Census PCA codes and physical coordinates, but the frontend metadata assigns shifted names/regions from nearby valleys. |
| **Critical Cross-State Label Discrepancies** | `ST-13` (Ukhimath vs. Aut, Mandi, HP)<br>`ST-14` (Chopta vs. Meppadi, Wayanad, KL)<br>`ST-15` (Gopeshwar vs. Chooralmala, Wayanad, KL) | Backend physics, coordinates, DEM, weather, Census PCA, and road graph are **100% Uttarakhand** (Ukhimath, Chopta, Gopeshwar). The frontend `stationMetadata.ts` incorrectly presents them as Himachal Pradesh and Kerala stations with Mandyali and Malayalam language tags. |

---

## 6. Recommended Correction Strategies (For Future Decision)

*(Presented for documentation purposes only; no code has been changed in this audit.)*

### Option A: Unified Uttarakhand Valley Catchment (Recommended)
- **Concept:** Align `stationMetadata.ts` directly with the backend reality (`dataset.py`, `census_population_data.py`, `road_network.py`).
- **Changes Needed:**
  - `ST-04` $\rightarrow$ Badrinath Base Valley (Chamoli, UK)
  - `ST-05` $\rightarrow$ Karnaprayag Reach (Chamoli, UK)
  - `ST-06` $\rightarrow$ Nandaprayag Basin (Chamoli, UK)
  - `ST-07` $\rightarrow$ Rudraprayag Sangam (Rudraprayag, UK)
  - `ST-08` $\rightarrow$ Tilwara Valley (Rudraprayag, UK)
  - `ST-09` $\rightarrow$ Augustmuni Stream (Rudraprayag, UK)
  - `ST-10` $\rightarrow$ Guptkashi Slope (Rudraprayag, UK)
  - `ST-12` $\rightarrow$ Sonprayag Confluence (Rudraprayag, UK)
  - `ST-13` $\rightarrow$ Ukhimath Crest (Rudraprayag, UK, Lang: Garhwali/Hindi)
  - `ST-14` $\rightarrow$ Chopta Ridge (Rudraprayag, UK, Lang: Garhwali/Hindi)
  - `ST-15` $\rightarrow$ Gopeshwar Terrace (Chamoli, UK, Lang: Garhwali/Hindi)
- **Advantages:**
  - 100% mathematically and geographically coherent.
  - Road network and Dijkstra shortest-path evacuation work seamlessly across the contiguous Alaknanda-Mandakini river systems.
  - Matches Feature 11 alert language system (Garhwali, Kumaoni, Hindi, Nepali, English).

### Option B: True Multi-Basin National Deployment
- **Concept:** Actually split the stations into 3 separate geographical clusters:
  - Cluster 1 (ST-01 to ST-12): Chamoli / Rudraprayag, Uttarakhand (`30.2°N - 30.7°N`)
  - Cluster 2 (ST-13): Mandi / Aut Basin, Himachal Pradesh (`31.745°N, 77.205°E`)
  - Cluster 3 (ST-14 & ST-15): Wayanad, Kerala (`11.55°N, 76.13°E`)
- **Changes Needed:**
  - Update `dataset.py` coordinates for ST-13, ST-14, ST-15 to real HP and Kerala GPS coordinates.
  - Split `road_network.py` into 3 disjoint subgraphs (one for Uttarakhand, one for Mandi HP, one for Wayanad KL) with local district shelters for each.
  - Fetch Census 2011 PCA codes for Mandi (HP) and Wayanad (KL).
  - Support Malayalam and Mandyali alert generation in the backend alert engine.

---

## 7. Conclusion

This audit formally records that **all 15 stations in the APADA MITRA backend currently operate on contiguous Chamoli and Rudraprayag (Uttarakhand) coordinates and topologies**. The appearance of Mandi (Himachal Pradesh) and Wayanad (Kerala) in the frontend is strictly a metadata presentation artifact that is disconnected from the backend's real GPS coordinates and road network graph.
