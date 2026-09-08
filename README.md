# APADA MITRA ⚡
> **Terrain-Aware Multi-Hazard Disaster Intelligence & Evacuation Platform**  
> *SIH Problem Statement SIH26192: Flash Flood Prediction System for Hilly Regions using Multi-Source Data*  
> **STATUS: APADA MITRA SIH26192 — STAGE-SAFE RELEASE VERIFIED**

---

> **SIH Demonstration Positioning Statement**:  
> APADA MITRA is a terrain-aware multi-hazard disaster intelligence and evacuation decision-support platform. The SIH demonstration uses a reproducible synthetic dataset to guarantee deterministic operation, while the architecture is designed for integration with real meteorological, hydrological and geospatial sources.

---

## 📌 Problem & Purpose
Hilly regions suffer from catastrophic flash floods driven by extreme cloudbursts, high slope runoff, channel funnels, and soil saturation. Conventional weather alerts operate at coarse district levels, missing micro-watershed flood dynamics. **APADA MITRA** delivers high-resolution, village-level flash flood risk intelligence, explainable factor breakdowns, exposure tracking, multi-hazard evacuation priority ranking, hazard-aware Dijkstra routing, capacity-constrained shelter allocation, and real-time What-If scenario simulation.

---

## 🚀 Core Platform Capabilities

- 🏔️ **Terrain-Aware Multi-Source Risk Scoring**: Combines elevation, slope, flow accumulation log index, soil saturation, river stage, and rainfall parameters into a transparent 0–100 risk index via a deterministic weighted multi-factor risk engine.
- 🎯 **15-Village Watershed Granularity**: Intelligence metrics for 15 villages across the high-vulnerability Alaknanda & Mandakini Himalayan watersheds.
- 💡 **Primary Risk Drivers Breakdown**: Deterministic weighted point contribution breakdown for top risk drivers.
- 🏥 **Exposure & Vulnerability Index**: Population at risk + vulnerable infrastructure asset counts (Schools, Health Clinics, Bridges).
- ⚡ **Multi-Hazard Evacuation Priority Ranking**: Ranks villages #1 to #15 based on weighted Flood (35%), Landslide (25%), Population (25%), and Infrastructure (15%) factors.
- 🗺️ **Hazard-Aware Dijkstra Evacuation Routing**: Dynamic pathfinder avoiding blocked roads, penalizing degraded segments, and computing route safety scores over OpenStreetMap road graphs (with hazard statuses dynamically derived by the risk engine, not live OSM closures).
- 🎪 **Capacity-Constrained Shelter Recommendation**: Recommends safest accessible relief shelter from a geographically distributed 63 shelter candidate network sourced from publicly documented facilities across Uttarakhand (Chamoli & Rudraprayag), Himachal Pradesh (Mandi), and Kerala (Wayanad), enforcing road access passability and capacity constraints without fabricating unpublished capacity.
- 🧪 **What-If Disaster Cascade Simulator**: Interactive hydro-meteorological sliders, Before/After delta comparison, 9-stage cascade chain, and shelter shortfall warnings.
- 🌐 **Multilingual Emergency Alerts**: Automated decision-support warnings generated in 5 regional languages: **English**, **Hindi (हिन्दी)**, **Garhwali (गढ़वाली)**, **Kumaoni (कुमाऊँनी)**, and **Nepali (नेपाली)** (local simulation mode; no external SMS delivered).
- 🛡️ **Single Health & Readiness System**: `/api/readiness` verifying backend, graph routing, simulation engine, and local fallback state (`SYSTEM READY`).
- 🔄 **Reliable Demo Reset**: One-click reset button (`RESET DEMO`) restoring initial scenario, selected village, map overlays, and simulation state.
- 🛡️ **Extreme Reliability Test Suite**: 180+ automated pytest tests across 18 test suites verifying bounds, monotonicity, missing feature resilience, adapters, and edge failure modes.

---

## 🛠️ Tech Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Leaflet JS (`react-leaflet`, `lucide-react`)
- **Backend**: Python 3.10+, FastAPI, Pydantic v2, Pytest, Uvicorn
- **Data Model**: Geo-spatial JSON data feed structured for future PostGIS / GIS sensor integration

---

## 📦 Installation & Startup Procedure

### Prerequisites
- Node.js (v18+)
- Python (v3.10+)

### 1. Backend Startup

```bash
cd backend
python -m uvicorn app.main:app --port 8000
```

### 2. Frontend Startup

```bash
cd frontend
npm run dev
```

The application will be accessible at `http://localhost:5173`. Backend API docs will be available at `http://localhost:8000/docs`.

No hidden manual configuration steps are required.

---

## 📊 API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | System health check and status |
| `GET` | `/api/readiness` | Single system readiness check (`SYSTEM READY` / `DEGRADED`) |
| `GET` | `/api/scenario` | Get active weather scenario & parameters |
| `POST` | `/api/scenario` | Change active scenario (`NORMAL`, `HEAVY_RAIN`, `EXTREME_RAIN`) |
| `GET` | `/api/villages` | List all monitored villages with location data |
| `GET` | `/api/villages/{id}` | Detailed risk, exposure, and XAI breakdown for a village |
| `GET` | `/api/risk` | Get complete risk calculations for all villages |
| `GET` | `/api/impact` | Aggregate regional impact metrics (Total exposed, high-risk count, avg confidence) |
| `GET` | `/api/landslide` | Get landslide susceptibility risk for all villages |
| `GET` | `/api/evacuation/priorities` | Get multi-hazard evacuation priority ranking (#1 to #15) |
| `GET` | `/api/roads` | Get mountain road graph with dynamic hazard statuses |
| `GET` | `/api/shelters` | List all emergency relief shelters and capacity |
| `POST` | `/api/evacuation/route` | Compute hazard-aware Dijkstra evacuation path |
| `GET` | `/api/evacuation/shelter-recommendation/{id}` | Recommend safest capacity-available relief shelter |
| `POST` | `/api/simulation/what-if` | Run What-If Disaster Cascade simulation under custom parameters |

---

## ⚠️ Data Transparency & Provenance Boundaries
APADA MITRA integrates real-world data adapters alongside transparent fallback states:
- **Meteorological Data**: Live Open-Meteo REST API integration for rainfall rates and NWP model-derived soil saturation (explicitly model-derived, not in-situ physical soil probe sensors).
- **Terrain & GIS Rasters**: Static Copernicus 30m DEM elevation and GSI historical landslide catalog records.
- **Road Network**: OpenStreetMap (OSM) road graph topology. Note: road hazard statuses (`OPEN`, `DEGRADED`, `BLOCKED`) are dynamically evaluated by the routing engine, as OSM does not provide live road closure telemetry.
- **Hydrology / River Stages**: Configured CWC baseline and watershed flow-accumulation models (direct live CWC API streaming is not publicly open).
- **Relief Shelters**: APADA MITRA maintains a geographically distributed 33 shelter candidate network sourced from publicly documented government facilities (USDMA/DDMP Chamoli, Rudraprayag, HPSDMA Mandi, and KSDMA Wayanad). Verification levels (`REAL_STATIC_GOVERNMENT`, `DERIVED_FROM_REAL_SOURCE`) and capacity availability are explicitly represented. The system does not fabricate shelter capacity or official designation. External live shelter occupancy/capacity feeds are not connected unless an official source is actually available.
- **Emergency Alerts**: Local decision-support dispatch simulation; no external SMS is transmitted to public carrier networks.
- **Offline / Demo Fallback**: When external services are unreachable, deterministic scenario datasets are utilized with explicit `CACHED` or `OFFLINE_DEMO` data-state labeling.
