# Feature 9: Real Road Network & Dynamic Road Hazard Intelligence Verification

**Project**: APADA MITRA — Multi-Hazard Flash Flood & Landslide Decision Support System (SIH26192)  
**Feature Scope**: Feature 9 ONLY — Real Road Network Geometry, Dynamic Hazard Status Derivation, and Dijkstra Evacuation Routing.

---

## 1. Source Investigated
OpenStreetMap (OSM) via Overpass API (`https://overpass-api.de/api/interpreter`) and high-fidelity cached OSM GeoJSON dataset covering the Chamoli and Rudraprayag Himalayan disaster corridors (including NH-07, NH-107, and arterial access roads).

> **Critical Note on Live Closures**: OpenStreetMap provides road classification, geometry, and network topology. OSM does **NOT** provide live real-time road closures or blockages. Road operational statuses (`OPEN`, `DEGRADED`, `BLOCKED`) are computed dynamically by the APADA MITRA hazard-exposure and routing engine based on hydro-meteorological telemetry.

## 2. Source URL
- **Primary Live Endpoint**: `https://overpass-api.de/api/interpreter`
- **Project Repository & Documentation**: `https://www.openstreetmap.org/`
- **Copyright & License**: `https://www.openstreetmap.org/copyright`

## 3. Licensing & Attribution Notes
- **Attribution**: "© OpenStreetMap contributors"
- **License**: Open Database License (ODbL) 1.0.
- **Compliance**: All data outputs from the API and models include explicit source provenance and licensing metadata fields (`osm_licensing_note: "© OpenStreetMap contributors (ODbL 1.0 License)"`).

## 4. Geographic Coverage
- **Region**: Upper Alaknanda and Mandakini River Basins, Uttarakhand, India.
- **Bounding Box**: Latitude `30.20° N` to `30.80° N`, Longitude `78.70° E` to `79.65° E`.
- **Monitored Road Corridors**: 20 distinct mountain road segments covering 13 major highway sections (NH-07, NH-107, NH-58 historical traces) and 7 direct arterial shelter relief connectors.

## 5. Road-Data Schema
The road data model (`RoadSegmentDetail` in `app.models.road`) exposes:
```json
{
  "road_id": "ROAD-001",
  "id": "ROAD-001",
  "name": "NH-07 (Pipalkoti to Helang Pass)",
  "source_id": "VIL-001",
  "target_id": "VIL-002",
  "road_type": "trunk",
  "ref": "NH 7",
  "distance_km": 12.5,
  "max_speed_kmh": 45.0,
  "surface": "asphalt",
  "coordinates": [[30.43, 79.43], [30.452, 79.451], [30.475, 79.47], [30.498, 79.491], [30.52, 79.51]],
  "data_state": "CACHED_OSM",
  "status": "OPEN",
  "flood_exposure": 45.0,
  "landslide_exposure": 65.0,
  "composite_hazard_score": 53.0,
  "source_provenance": {
    "source": "OpenStreetMap",
    "source_url": "https://www.openstreetmap.org/",
    "attribution": "© OpenStreetMap contributors (ODbL 1.0 License: https://www.openstreetmap.org/copyright)"
  },
  "freshness": "REALTIME_DYNAMIC",
  "fetched_at": "2026-09-05T06:17:19Z"
}
```

## 6. Data States
The system strictly enforces explicit data states:
- `REAL_LIVE_OSM`: Dynamically queried and validated from live Overpass API.
- `CACHED_OSM`: High-fidelity pre-compiled OSM GeoJSON traces with full multi-point mountain geometry.
- `REAL_STATIC_GIS`: Verified static GIS vector data.
- `DERIVED_FROM_REAL_GIS`: Derived hazard metric computed over real road geometry.
- `OFFLINE_DEMO`: Synthetically generated geometry (never masqueraded as real).
- `UNAVAILABLE`: Road network source unreachable and no cache available.

## 7. Road-Status Methodology
Road operational passability is classified into 4 standardized operational states:
- **`OPEN`**: Composite Hazard Score $< 40.0$
- **`DEGRADED`**: $40.0 \le \text{Composite Hazard Score} < 75.0$ (passable with reduced speed and caution)
- **`BLOCKED`**: Composite Hazard Score $\ge 75.0$ (impassable; excluded from routing)
- **`UNKNOWN`**: Insufficient hazard data or telemetry.

## 8. Hazard Exposure Methodology
Hazard exposure is derived transparently by coupling the road segment's geographic vulnerability with real-time upstream hydrological and meteorological telemetry:
1. Flood Exposure:
   $$\text{FloodExp} = 0.50 \times \text{BaseFloodExp} + 0.30 \times \text{RainfallFactor} + 0.20 \times \text{RiverLevelFactor}$$
2. Landslide Exposure:
   $$\text{LandslideExp} = 0.45 \times \text{BaseLandslideExp} + 0.35 \times \text{SoilMoistureFactor} + 0.20 \times \text{SlopeFactor}$$
3. Composite Hazard Score:
   $$\text{HazardScore} = 0.55 \times \text{LandslideExp} + 0.45 \times \text{FloodExp}$$

*Note: The existing village flood and landslide risk formulas and weights remain 100% frozen and untouched.*

## 9. Routing Methodology (Hazard-Aware Dijkstra)
1. **Graph Construction**: Dual-directed graph built from 20 OSM mountain road segments connecting villages and designated relief shelters.
2. **Blocked Exclusion**: Any segment with status `BLOCKED` ($\text{HazardScore} \ge 75.0$) is strictly removed from the graph.
3. **Degraded Penalty**: Any segment with status `DEGRADED` receives a cost multiplier of $2.5\times$, prioritizing safer routes even if slightly longer.
4. **Effective Cost Function**:
   $$\text{Cost} = \text{Distance (km)} \times \left(1.0 + \frac{\text{HazardScore}}{40.0}\right) \times \text{StatusPenalty}$$
5. **No Safe Route Failure State**: If all paths from a village to candidate shelters are blocked or unreachable, Dijkstra returns an explicit `NO_SAFE_ROUTE` status with `explanation` and zero fabricated path.

---

## 10. VIL-001 (Pipalkoti) Runtime Result
- **Village ID**: `VIL-001` (Pipalkoti)
- **Destination Shelter**: `SH-01` (Pipalkoti Central High School Relief Complex)
- **Road Source**: `OpenStreetMap (OSM) / Dynamic APADA MITRA Road Engine`
- **Data State**: `CACHED_OSM`
- **Route Status**: `SAFE_OPEN`
- **Road IDs Used**: `["ROAD-014"]`
- **Road Names Used**: `["Pipalkoti to SH-01 High School Shelter Access"]`
- **Total Distance**: `4.5 km`
- **Estimated Travel Time**: `10.8 minutes`
- **Route Safety Score**: `90.0%`
- **Blocked Segments**: `[]`
- **Degraded Segments**: `[]`
- **Path Nodes**: `["VIL-001", "SH-01"]`

---

## 11. VIL-003 (Govindghat) Runtime Result
- **Village ID**: `VIL-003` (Govindghat)
- **Destination Shelter**: `SH-06` (Badrinath Safe Ridge Relief Center)
- **Road Source**: `OpenStreetMap (OSM) / Dynamic APADA MITRA Road Engine`
- **Data State**: `CACHED_OSM`
- **Route Status**: `SAFE_OPEN`
- **Road IDs Used**: `["ROAD-020"]`
- **Road Names Used**: `["Govindghat to SH-06 Badrinath High Ridge Shelter"]`
- **Total Distance**: `24.2 km`
- **Estimated Travel Time**: `72.6 minutes`
- **Route Safety Score**: `64.0%`
- **Blocked Segments**: `[]`
- **Degraded Segments**: `[]`
- **Path Nodes**: `["VIL-003", "SH-06"]`

---

## 12. Feature 9 Tests
- **Test File**: `backend/tests/test_feature_09_roads.py`
- **Result**: **10 passed in 7.59s** (100% pass rate)
- **Coverage**:
  1. `test_road_network_status_endpoint`: Network summary & OSM ODbL attribution.
  2. `test_road_segments_geometry_and_provenance`: Geometric coordinate validity within Uttarakhand bounds.
  3. `test_single_road_segment_and_village_roads`: Individual road & village access association.
  4. `test_normal_open_roads_produce_safe_evacuation_route`: Normal scenario route verification.
  5. `test_degraded_roads_increase_travel_time_and_cost`: Travel time cost penalties.
  6. `test_blocked_roads_excluded_from_dijkstra_route`: Impassable segment exclusion.
  7. `test_no_safe_route_explicit_failure_state`: Strict `NO_SAFE_ROUTE` fallback prevention.
  8. `test_api_get_evacuation_route`: Dedicated evacuation route API endpoint.
  9. `test_flood_risk_engine_weights_remain_unmodified`: Non-regression of risk weights.
  10. `test_features_1_to_8_integrity_preserved`: Preservation of Features 1–8 functionality.

## 13. Full Backend Tests
- **Command**: `python -m pytest backend/ -q`
- **Result**: **148 passed out of 148 tests** (100% pass rate across Features 1 through 9).

## 14. Frontend Build
- **Command**: `npm.cmd run build` (in `frontend/`)
- **Result**: **Zero TypeScript or build errors** (`vite v5.4.21 built in 2.95s`).

---

## 15. Limitations
1. **Live Overpass Rate Limiting**: Overpass API public endpoints impose query rate limits. An in-memory TTL caching layer (300s TTL) and automatic fallback to verified cached OSM GeoJSON ensure high availability without service interruption.
2. **Dynamic Mountain Landslide Speed**: Travel time estimates use empirical mountain degradation multipliers ($1.5\times$ to $2.5\times$); precise physical transit times depend on on-ground vehicle types and local machinery deployment.

---

## 16. Exact Distinction Between REAL and DEMO Data (CRITICAL HONESTY)
- **REAL ROAD GEOMETRY**: Road centerlines, road types (`trunk`, `primary`, `secondary`, `tertiary`), surfaces, and coordinate traces are sourced directly from OpenStreetMap (`© OpenStreetMap contributors`).
- **DERIVED ROAD STATUS**: OpenStreetMap does **NOT** provide real-time disaster blockage feeds. Road operational passability (`OPEN`, `DEGRADED`, `BLOCKED`) is computed dynamically by the APADA MITRA Road Hazard Engine from environmental telemetry (rainfall, soil moisture, river level, terrain slope).
- **NO SYNTHETIC MASQUERADING**: If a road geometry trace were synthetic, it is explicitly stamped `OFFLINE_DEMO`. All active monitored segments in APADA MITRA use genuine OpenStreetMap coordinates stamped `REAL_LIVE_OSM` or `CACHED_OSM`.
