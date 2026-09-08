"""
Dynamic Road Hazard & Evacuation Routing Engine for APADA MITRA (Feature 9).
Integrates real OpenStreetMap (OSM) road networks, dynamic flood/landslide exposure scoring,
operational road status derivation, and hazard-aware Dijkstra evacuation pathfinding.
"""
import heapq
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any, Set
from app.models.road import (
    RoadDataState,
    RoadOperationalStatus,
    RoadSegmentDetail,
    EvacuationRouteDetail,
    RoadNetworkStatusResponse,
)
from app.models.domain import ScenarioType
from app.adapters.osm_road_adapter import (
    osm_road_adapter_instance,
    CACHED_OSM_ROADS,
    OSM_ATTRIBUTION,
    OSM_SOURCE_URL,
)
from app.data.dataset import DEMO_VILLAGES
from app.data.shelters import get_shelters_list

# Operational Hazard Thresholds for Road Status
ROAD_OPEN_MAX_HAZARD: float = 40.0        # H < 40.0 -> OPEN
ROAD_BLOCKED_MIN_HAZARD: float = 75.0     # H >= 75.0 -> BLOCKED (Otherwise DEGRADED)


class RoadHazardEngine:
    """
    Evaluates dynamic road passability and calculates safe evacuation routes over the real road network.
    """

    def __init__(self):
        self.adapter = osm_road_adapter_instance

    def get_all_road_segments(
        self,
        scenario: ScenarioType = ScenarioType.NORMAL,
        force_offline: bool = False,
    ) -> List[RoadSegmentDetail]:
        """
        Retrieves all road segments with real geometry and dynamically derived hazard ratings.
        """
        raw_roads, data_state = self.adapter.fetch_road_network(force_offline=force_offline)
        now_iso = datetime.now(timezone.utc).isoformat()

        # Multipliers based on weather scenario
        scenario_flood_mult = {
            ScenarioType.NORMAL: 0.6,
            ScenarioType.HEAVY_RAIN: 1.0,
            ScenarioType.EXTREME_RAIN: 1.35,
        }.get(scenario, 1.0)

        scenario_ls_mult = {
            ScenarioType.NORMAL: 0.5,
            ScenarioType.HEAVY_RAIN: 1.0,
            ScenarioType.EXTREME_RAIN: 1.30,
        }.get(scenario, 1.0)

        results: List[RoadSegmentDetail] = []

        for r in raw_roads:
            f_exp = round(min(100.0, r["base_flood_exp"] * scenario_flood_mult), 1)
            l_exp = round(min(100.0, r["base_landslide_exp"] * scenario_ls_mult), 1)
            comp_h = round(max(f_exp, l_exp), 1)

            if comp_h >= ROAD_BLOCKED_MIN_HAZARD:
                status = RoadOperationalStatus.BLOCKED
                reason = f"Severe hazard exposure ({comp_h}%). Inundation / debris flow blockage risk."
            elif comp_h >= ROAD_OPEN_MAX_HAZARD:
                status = RoadOperationalStatus.DEGRADED
                reason = f"Moderate hazard exposure ({comp_h}%). Surface water pooling / rockfall risk."
            else:
                status = RoadOperationalStatus.OPEN
                reason = f"Low hazard exposure ({comp_h}%). Normal operational passability."

            results.append(
                RoadSegmentDetail(
                    road_id=r["road_id"],
                    id=r["road_id"],
                    name=r["name"],
                    source_id=r["source_id"],
                    target_id=r["target_id"],
                    road_type=r.get("road_type", "primary"),
                    ref=r.get("ref"),
                    coordinates=r["coordinates"],
                    distance_km=r["distance_km"],
                    max_speed_kmh=r.get("max_speed_kmh", 40.0),
                    surface=r.get("surface", "asphalt"),
                    source="OpenStreetMap (OSM) via Overpass API / Cached GeoJSON",
                    source_url=OSM_SOURCE_URL,
                    fetched_at=now_iso,
                    data_state=data_state,
                    freshness="LIVE_STREAM" if data_state == RoadDataState.REAL_LIVE_OSM else "CACHED",
                    status=status,
                    flood_exposure=f_exp,
                    landslide_exposure=l_exp,
                    composite_hazard_score=comp_h,
                    status_reason=reason,
                    assumptions=[
                        "Road centerline alignment and road classification sourced from OpenStreetMap (OSM).",
                        "CRITICAL LIMITATION: OSM provides physical mapping, NOT real-time disaster blockage. Road operational status is DERIVED by APADA MITRA from environmental hazard exposure.",
                        f"Evaluated under scenario {scenario.value} with composite hazard {comp_h}%."
                    ],
                )
            )

        return results

    def get_road_segment_by_id(
        self,
        road_id: str,
        scenario: ScenarioType = ScenarioType.NORMAL,
        force_offline: bool = False,
    ) -> Optional[RoadSegmentDetail]:
        """Retrieves a specific road segment by its unique identifier."""
        roads = self.get_all_road_segments(scenario=scenario, force_offline=force_offline)
        return next((r for r in roads if r.road_id == road_id), None)

    def get_village_roads(
        self,
        village_id: str,
        scenario: ScenarioType = ScenarioType.NORMAL,
        force_offline: bool = False,
    ) -> List[RoadSegmentDetail]:
        """Retrieves all road segments directly originating from or connected to a village."""
        roads = self.get_all_road_segments(scenario=scenario, force_offline=force_offline)
        return [r for r in roads if r.source_id == village_id or r.target_id == village_id]

    def get_network_status(
        self,
        scenario: ScenarioType = ScenarioType.NORMAL,
        force_offline: bool = False,
    ) -> RoadNetworkStatusResponse:
        """Returns overall operational status and segment statistics of the road network."""
        roads = self.get_all_road_segments(scenario=scenario, force_offline=force_offline)
        open_cnt = sum(1 for r in roads if r.status == RoadOperationalStatus.OPEN)
        deg_cnt = sum(1 for r in roads if r.status == RoadOperationalStatus.DEGRADED)
        blk_cnt = sum(1 for r in roads if r.status == RoadOperationalStatus.BLOCKED)
        now_iso = datetime.now(timezone.utc).isoformat()
        data_state = roads[0].data_state if roads else RoadDataState.CACHED_OSM

        return RoadNetworkStatusResponse(
            total_segments_count=len(roads),
            open_segments_count=open_cnt,
            degraded_segments_count=deg_cnt,
            blocked_segments_count=blk_cnt,
            data_state=data_state,
            source_authority="OpenStreetMap (OSM) Contributors",
            source_url=OSM_SOURCE_URL,
            osm_licensing_note=OSM_ATTRIBUTION,
            last_updated=now_iso,
            disclaimer="Road geometry is mapped from OpenStreetMap. Road hazard statuses are dynamically derived by APADA MITRA based on hydrometeorological and landslide susceptibility modeling."
        )

    def calculate_safest_evacuation_route(
        self,
        origin_village_id: str,
        destination_shelter_id: Optional[str] = None,
        scenario: ScenarioType = ScenarioType.NORMAL,
        force_offline: bool = False,
    ) -> EvacuationRouteDetail:
        """
        Calculates the safest evacuation path from origin village to the target relief shelter.
        If destination_shelter_id is omitted, automatically resolves to the safest accessible shelter.
        """
        villages = {v["id"]: v["name"] for v in DEMO_VILLAGES}
        shelters = {s.id: s.name for s in get_shelters_list()}

        if origin_village_id not in villages:
            raise ValueError(f"Origin village ID '{origin_village_id}' not found.")

        # Default shelter lookup if not specified
        if not destination_shelter_id:
            from app.engine.shelter_engine import recommend_safest_shelter
            shelter_rec = recommend_safest_shelter(origin_village_id, scenario=scenario)
            destination_shelter_id = shelter_rec.recommended_shelter.id

        if destination_shelter_id not in shelters:
            raise ValueError(f"Destination shelter ID '{destination_shelter_id}' not found.")

        origin_name = villages[origin_village_id]
        dest_name = shelters[destination_shelter_id]

        # Retrieve dynamic road segments
        segments = self.get_all_road_segments(scenario=scenario, force_offline=force_offline)
        data_state = segments[0].data_state if segments else RoadDataState.CACHED_OSM

        # Build adjacency graph
        # graph[node_id] = [(neighbor_id, segment, cost)]
        graph: Dict[str, List[Tuple[str, RoadSegmentDetail, float]]] = {}
        blocked_segments_logged: List[str] = []

        for seg in segments:
            if seg.status == RoadOperationalStatus.BLOCKED:
                blocked_segments_logged.append(f"{seg.name} ({seg.road_id}) [BLOCKED]")
                continue  # Strictly exclude blocked segments

            # Traversal cost: distance * hazard penalty multiplier * degradation penalty
            hazard_factor = 1.0 + (seg.composite_hazard_score / 40.0)
            status_penalty = 2.5 if seg.status == RoadOperationalStatus.DEGRADED else 1.0
            cost = seg.distance_km * hazard_factor * status_penalty

            if seg.source_id not in graph:
                graph[seg.source_id] = []
            if seg.target_id not in graph:
                graph[seg.target_id] = []

            graph[seg.source_id].append((seg.target_id, seg, cost))
            graph[seg.target_id].append((seg.source_id, seg, cost))

        # Dijkstra Shortest / Safest Path Search
        # Priority queue: (accumulated_cost, current_node, path_nodes, path_segments, total_distance)
        pq: List[Tuple[float, str, List[str], List[RoadSegmentDetail], float]] = [
            (0.0, origin_village_id, [origin_village_id], [], 0.0)
        ]
        visited: Set[str] = set()
        best_path: Optional[Tuple[List[str], List[RoadSegmentDetail], float, float]] = None

        while pq:
            acc_cost, curr_node, path_nodes, path_segs, tot_dist = heapq.heappop(pq)

            if curr_node == destination_shelter_id:
                best_path = (path_nodes, path_segs, acc_cost, tot_dist)
                break

            if curr_node in visited:
                continue
            visited.add(curr_node)

            for neighbor, seg, edge_cost in graph.get(curr_node, []):
                if neighbor not in visited:
                    heapq.heappush(
                        pq,
                        (
                            acc_cost + edge_cost,
                            neighbor,
                            path_nodes + [neighbor],
                            path_segs + [seg],
                            tot_dist + seg.distance_km,
                        ),
                    )

        # Handle No Safe Route state
        if not best_path:
            return EvacuationRouteDetail(
                origin_id=origin_village_id,
                origin_name=origin_name,
                destination_id=destination_shelter_id,
                destination_name=dest_name,
                road_ids=[],
                road_names=[],
                total_distance_km=0.0,
                estimated_travel_time_minutes=9999.0,
                route_safety_score=0.0,
                route_status="NO_SAFE_ROUTE",
                blocked_segments=blocked_segments_logged,
                degraded_segments=[],
                path_nodes=[origin_village_id],
                data_state=data_state,
                source_provenance={
                    "source": "OpenStreetMap (OSM) / Dynamic APADA MITRA Road Engine",
                    "source_url": OSM_SOURCE_URL,
                    "attribution": OSM_ATTRIBUTION,
                },
                calculation_method="HAZARD_WEIGHTED_DIJKSTRA",
                explanation=f"CRITICAL: No safe passable evacuation route to {dest_name}. All connecting corridors are blocked by severe flood/landslide hazards.",
                assumptions=["Immediate vertical evacuation / shelter-in-place protocol required."],
            )

        path_nodes, path_segs, total_cost, tot_dist = best_path

        # Compute travel time taking speed and degraded penalties into account
        total_time_mins = 0.0
        hazard_scores = []
        degraded_segs_logged: List[str] = []

        for seg in path_segs:
            spd = seg.max_speed_kmh or 35.0
            seg_time = (seg.distance_km / spd) * 60.0
            if seg.status == RoadOperationalStatus.DEGRADED:
                seg_time *= 1.8  # Speed reduction on degraded roads
                degraded_segs_logged.append(f"{seg.name} ({seg.road_id}) [DEGRADED]")
            total_time_mins += seg_time
            hazard_scores.append(seg.composite_hazard_score)

        avg_hazard = sum(hazard_scores) / len(hazard_scores) if hazard_scores else 0.0
        route_safety = round(max(0.0, min(100.0, 100.0 - avg_hazard)), 1)
        travel_time_final = round(total_time_mins, 1)

        # Classify Route Status
        if degraded_segs_logged:
            route_status = "SAFE_DEGRADED"
        elif len(blocked_segments_logged) > 0:
            route_status = "HIGH_HAZARD_REROUTED"
        else:
            route_status = "SAFE_OPEN"

        return EvacuationRouteDetail(
            origin_id=origin_village_id,
            origin_name=origin_name,
            destination_id=destination_shelter_id,
            destination_name=dest_name,
            road_ids=[s.road_id for s in path_segs],
            road_names=[s.name for s in path_segs],
            total_distance_km=round(tot_dist, 2),
            estimated_travel_time_minutes=travel_time_final,
            route_safety_score=route_safety,
            route_status=route_status,
            blocked_segments=blocked_segments_logged,
            degraded_segments=degraded_segs_logged,
            path_nodes=path_nodes,
            data_state=data_state,
            source_provenance={
                "source": "OpenStreetMap (OSM) / Dynamic APADA MITRA Road Engine",
                "source_url": OSM_SOURCE_URL,
                "attribution": OSM_ATTRIBUTION,
            },
            calculation_method="HAZARD_WEIGHTED_DIJKSTRA",
            explanation=f"Safest route selected via {len(path_segs)} road segment(s) totaling {round(tot_dist, 1)} km (Travel Time: {travel_time_final} mins, Safety: {route_safety}%).",
            assumptions=[
                "Road network geometry sourced from OpenStreetMap (OSM).",
                "Route travel time calculated from design speed with empirical mountain road degradation adjustments."
            ],
        )


road_hazard_engine_instance = RoadHazardEngine()
