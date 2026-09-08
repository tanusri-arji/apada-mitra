# APADA MITRA - Master Specification

**Project Title**: APADA MITRA  
**Technical Title**: Terrain-Aware Multi-Hazard Disaster Intelligence & Evacuation Platform  
**SIH Problem Statement**: SIH26192 (Flash Flood Prediction System for Hilly Regions using Multi-Source Data)  
**Theme**: Disaster Management  
**Category**: Software  
**Hard Demo / Deadline**: September 6, 2026  

---

## 1. Executive Summary & Core Promise

APADA MITRA is an emergency intelligence platform designed for hilly and mountainous regions prone to flash floods, landslides, and extreme weather events.

### Core Architecture Flow
**Predict → Explain → Prioritize → Evacuate → Respond**

1. **Predict**: Process multi-source data (elevation, slope, flow accumulation, rainfall intensity, soil saturation, river stage) to compute transparent, terrain-aware risk scores.
2. **Explain**: Break down each village's risk into specific contributing factors (e.g., +32% due to extreme 24h rainfall, +25% due to high flow accumulation channel proximity).
3. **Prioritize**: Quantify human population exposure and critical infrastructure vulnerability to rank villages by emergency intervention urgency.
4. **Evacuate**: *(Planned Day 2)* Compute dynamic safe evacuation routes avoiding flooded streams and active hazards.
5. **Respond**: *(Planned Day 2)* Coordinate field rescue teams, shelter allocation, and multi-channel citizen warnings.

---

## 2. Current Scope (Day 1 - Implemented)

- **Multi-Source Scenario Data Engine**: Deterministic dataset representing 15 Himalayan villages in the Alaknanda watershed with synthetic elevation (DEM), slope, flow accumulation, soil saturation, rainfall intensity, and river stage metrics.
- **Terrain-Aware Flash Flood Risk Engine**: Configurable mathematical pipeline computing:
  - `flash_flood_risk_score` (0–100)
  - `risk_probability` (0.0–1.0)
  - `confidence` (0–100 %)
  - `risk_level` (`LOW`: 0–24, `MODERATE`: 25–49, `HIGH`: 50–74, `CRITICAL`: 75–100)
- **Explainable AI (XAI)**: Structured calculation of factor contributions for every village without arbitrary random text generation.
- **Village Exposure Metrics**: Exposed population count, schools, medical centers, critical bridges, and overall `exposure_score` (0–100).
- **FastAPI Backend REST Service**: Pydantic validated endpoints (`/api/health`, `/api/scenario`, `/api/villages`, `/api/villages/{id}`, `/api/risk`, `/api/impact`).
- **Interactive Command Center UI**: High-performance dark-themed GIS dashboard with Leaflet map markers, live metrics top-bar, village intelligence side-panel, and scenario controls.
- **Scenario Control Simulator**: Toggle between `NORMAL`, `HEAVY RAIN`, and `EXTREME RAIN` to trigger live server-side recalculations and frontend state updates.
- **Missing Data Resilience**: Graceful handling of missing sensor features with automatic confidence degradation.

---

## 3. Future Scope (Planned Day 2+)

- **Landslide Susceptibility Integration**: Combined multi-hazard scoring (Slope instability + saturation + rainfall trigger).
- **Dynamic Evacuation Routing**: Graph-based pathfinding across accessible mountain roads avoiding high-risk flood zones.
- **Shelter Allocation & Capacity Tracking**: Real-time tracking of relief camps and resource allocation.
- **Resource Management**: Tracking deployment of rescue boats, NDRF teams, earth movers, and emergency medical kits.
- **Multilingual Citizen Alerts**: Automated SMS / Push notification generation in Hindi, Garhwali, and English.
- **Interactive What-If Simulator**: Custom slider inputs for rainfall, dam release, and soil saturation parameters.
- **Offline Field Response Mode**: PWA offline sync for ground responders in low-connectivity valleys.

---

## 4. System Architecture

```
+-------------------------------------------------------------------+
|                        APADA MITRA UI                             |
|       (React + TypeScript + Vite + Tailwind CSS + Leaflet)        |
+-------------------------------------------------------------------+
                                  ^
                                  | REST JSON API
                                  v
+-------------------------------------------------------------------+
|                     FastAPI Backend Server                        |
|  +-------------------------------------------------------------+  |
|  |                 Scenario Control Engine                      |  |
|  +-------------------------------------------------------------+  |
|  |                 Flash Flood Risk Engine                     |  |
|  | (Normalization, Weighted Probabilities, Missing Handling)   |  |
|  +-------------------------------------------------------------+  |
|  |                  Explainability Engine                      |  |
|  |       (Factor Impact Breakdown & Contribution Scores)        |  |
|  +-------------------------------------------------------------+  |
|  |                   Exposure Risk Engine                      |  |
|  +-------------------------------------------------------------+  |
|  |             Deterministic Multi-Source Dataset              |  |
|  +-------------------------------------------------------------+  |
+-------------------------------------------------------------------+
```

---

## 5. Risk Calculation Formula & Parameters

$$\text{Risk Score} = \sum_{i} (w_i \cdot N(x_i)) \times 100$$

Where $N(x_i)$ is the normalized value $[0, 1]$ of feature $i$, and $w_i$ is its configured weight.

| Feature | Weight | Normalization Rule |
| :--- | :--- | :--- |
| **Current Rainfall** | 0.25 | $\min(1.0, \text{rainfall} / 100.0 \text{ mm/h})$ |
| **Forecast Rainfall (24h)** | 0.20 | $\min(1.0, \text{forecast} / 250.0 \text{ mm})$ |
| **Soil Saturation** | 0.15 | $\text{saturation} / 100.0$ |
| **River Water Level Factor**| 0.15 | $\min(1.0, \text{factor} / 3.0)$ |
| **Flow Accumulation** | 0.15 | $\log_{10}(1 + \text{flow}) / 5.0$ |
| **Slope Gradient** | 0.10 | $\min(1.0, \text{slope} / 45.0^\circ)$ |

### Confidence Calculation
$$\text{Confidence} = 100 - \text{Penalty}_{\text{missing}}$$
Each missing feature incurs a weight-proportional penalty on overall confidence score.

---

## 6. Data Quality & Labeling

All data used in Day 1 demo is **SYNTHETIC / DEMO DATA** representing typical topographic and hydro-meteorological conditions in the Chamoli/Rudraprayag region of Uttarakhand, India. It is clearly labeled in the user interface as `DEMO SCENARIO - SYNTHETIC DATA`.
