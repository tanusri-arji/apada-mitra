"""
Hazard-Aware Evacuation Routing Engine (Dijkstra Pathfinding) for APADA MITRA.
Calculates safest evacuation routes avoiding flood inundations, active landslide hazards, and road blockages.
"""
import heapq
from typing import List, Dict, Tuple, Optional, Set
from app.models.domain import RoadSegment, RoadStatus, EvacuationRouteResult, ScenarioType
from app.data.road_network import get_active_road_segments, DEMO_ROADS_BASE
from app.data.shelters import get_shelters_list
from app.data.dataset import DEMO_VILLAGES


class MountainRoadGraph:
    """Graph structure wrapper for mountain road network readiness check."""
    def __init__(self):
        self.nodes = set()
        for r in DEMO_ROADS_BASE:
            self.nodes.add(r["source_id"])
            self.nodes.add(r["target_id"])


MOUNTAIN_ROAD_GRAPH = MountainRoadGraph()


def calculate_safest_route(
    origin_village_id: str,
    destination_shelter_id: str,
    scenario: ScenarioType,
) -> EvacuationRouteResult:
    """
    Computes hazard-weighted Dijkstra route from origin village to target shelter under scenario.
    """
    segments = get_active_road_segments(scenario)
    return compute_dijkstra_route_over_graph(origin_village_id, destination_shelter_id, segments)


def compute_dijkstra_route_over_graph(
    origin_village_id: str,
    destination_shelter_id: str,
    segments: List[RoadSegment],
) -> EvacuationRouteResult:
    """
    Computes hazard-weighted Dijkstra route over custom road segments graph.
    Completely excludes BLOCKED roads and heavily penalizes DEGRADED / high hazard roads.
    """
    villages = {v["id"]: v["name"] for v in DEMO_VILLAGES}
    shelters = {s.id: s.name for s in get_shelters_list()}

    if origin_village_id not in villages:
        raise ValueError(f"Origin village ID '{origin_village_id}' is invalid or not found.")
    if destination_shelter_id not in shelters:
        raise ValueError(f"Destination shelter ID '{destination_shelter_id}' is invalid or not found.")

    origin_name = villages[origin_village_id]
    dest_name = shelters[destination_shelter_id]

    # Build adjacency graph
    # graph[node_id] = [(neighbor_id, segment, cost), ...]
    graph: Dict[str, List[Tuple[str, RoadSegment, float]]] = {}
    
    # Store rejected dangerous edges for logging
    rejected_alternatives: List[str] = []

    for seg in segments:
        if seg.status == RoadStatus.BLOCKED:
            rejected_alternatives.append(f"{seg.name} [BLOCKED - Flood/Landslide Risk]")
            continue  # Exclude blocked road completely from traversal graph

        if seg.landslide_exposure >= 85.0 or seg.flood_exposure >= 85.0:
            rejected_alternatives.append(
                f"{seg.name} [REJECTED - High Hazard Exposure: Landslide {seg.landslide_exposure}%, Flood {seg.flood_exposure}%]"
            )
            continue  # Exclude dangerously exposed road

        # Calculate hazard penalty multiplier
        hazard_max = max(seg.flood_exposure, seg.landslide_exposure)
        status_mult = 2.5 if seg.status == RoadStatus.DEGRADED else 1.0
        
        # Hazard-weighted effective cost
        cost = seg.distance_km * (1.0 + (hazard_max / 40.0)) * status_mult

        if seg.source_id not in graph:
            graph[seg.source_id] = []
        if seg.target_id not in graph:
            graph[seg.target_id] = []

        graph[seg.source_id].append((seg.target_id, seg, cost))
        graph[seg.target_id].append((seg.source_id, seg, cost))  # Undirected mountain roads

    # Dijkstra Algorithm
    # Priority Queue entries: (accumulated_cost, current_node, path_nodes, path_segments, total_distance)
    pq: List[Tuple[float, str, List[str], List[RoadSegment], float]] = [
        (0.0, origin_village_id, [origin_village_id], [], 0.0)
    ]
    visited: Set[str] = set()

    best_result: Optional[Tuple[List[str], List[RoadSegment], float, float]] = None

    while pq:
        acc_cost, curr_node, path_nodes, path_segs, tot_dist = heapq.heappop(pq)

        if curr_node == destination_shelter_id:
            best_result = (path_nodes, path_segs, tot_dist, acc_cost)
            break

        if curr_node in visited:
            continue
        visited.add(curr_node)

        for neighbor, seg, cost in graph.get(curr_node, []):
            if neighbor not in visited:
                heapq.heappush(
                    pq,
                    (
                        acc_cost + cost,
                        neighbor,
                        path_nodes + [neighbor],
                        path_segs + [seg],
                        tot_dist + seg.distance_km,
                    ),
                )

    if not best_result:
        raise ValueError(
            f"No safe evacuation route accessible from {origin_name} to {dest_name} due to severe road blockages."
        )

    path_nodes, path_segs, total_dist, total_cost = best_result

    # Construct coordinates polyline
    path_coords: List[List[float]] = []
    hazards_encountered: List[str] = []
    max_hazard_found = 0.0

    for seg in path_segs:
        path_coords.extend(seg.coordinates)
        hazard = max(seg.flood_exposure, seg.landslide_exposure)
        if hazard > max_hazard_found:
            max_hazard_found = hazard

        if seg.status == RoadStatus.DEGRADED:
            hazards_encountered.append(
                f"Degraded road on {seg.name} (Landslide {seg.landslide_exposure}%, Flood {seg.flood_exposure}%)"
            )

    # Route safety score (0-100)
    safety_score = round(max(5.0, min(100.0, 100.0 - max_hazard_found * 0.85)), 1)
    
    # Travel time estimation (average mountain speed ~30 km/h on open, ~15 km/h on degraded)
    avg_speed = 25.0 if safety_score > 60 else 18.0
    est_mins = int(round((total_dist / avg_speed) * 60.0))

    return EvacuationRouteResult(
        origin_village_id=origin_village_id,
        origin_village_name=origin_name,
        destination_shelter_id=destination_shelter_id,
        destination_shelter_name=dest_name,
        path_village_and_shelter_ids=path_nodes,
        road_segment_ids=[s.id for s in path_segs],
        total_distance_km=round(total_dist, 1),
        estimated_travel_time_mins=est_mins,
        route_safety_score=safety_score,
        path_coordinates=path_coords,
        hazards_encountered=hazards_encountered,
        rejected_dangerous_alternatives=rejected_alternatives,
    )
