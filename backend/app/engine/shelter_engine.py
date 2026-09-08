"""
Shelter Recommendation & Allocation Engine for APADA MITRA.
Evaluates candidate shelters by available capacity, route safety, distance, and shelter vulnerability.
Enforces capacity constraints so over-capacity shelters are never recommended.
"""
from typing import List, Optional, Tuple
from app.models.domain import (
    RoadSegment,
    Shelter,
    ShelterRecommendationResult,
    EvacuationRouteResult,
    ScenarioType,
)
from app.data.shelters import get_shelters_list
from app.data.dataset import DEMO_VILLAGES
from app.engine.routing_engine import calculate_safest_route


def recommend_safest_shelter(
    village_id: str,
    scenario: ScenarioType,
) -> ShelterRecommendationResult:
    """
    Finds and recommends the safest capacity-available relief shelter for a given village.
    """
    village = next((v for v in DEMO_VILLAGES if v["id"] == village_id), None)
    if not village:
        raise ValueError(f"Village {village_id} not found.")

    v_name = village["name"]
    shelters = get_shelters_list()

    candidates: List[Tuple[float, Shelter, EvacuationRouteResult]] = []

    for shelter in shelters:
        # STRICT CONSTRAINT: Reject over-capacity or full shelters (if published)
        if shelter.available_capacity is not None and shelter.available_capacity <= 0:
            continue

        try:
            route = calculate_safest_route(
                origin_village_id=village_id,
                destination_shelter_id=shelter.id,
                scenario=scenario,
            )
        except ValueError:
            # Route was blocked or unnavigable under current scenario
            continue

        # Distance penalty: max 100km mapped to 0-100 pts
        dist_score = min(100.0, route.total_distance_km * 2.0)
        shelter_safety = 100.0 - shelter.hazard_exposure_score

        # Composite Suitability Index (0-100)
        # Weights: Route Safety (45%), Distance (25%), Shelter Safety (30%)
        suitability = (
            (route.route_safety_score * 0.45)
            + ((100.0 - dist_score) * 0.25)
            + (shelter_safety * 0.30)
        )

        candidates.append((suitability, shelter, route))

    if not candidates:
        raise ValueError(
            f"No safe capacity-available shelter accessible from {v_name} under scenario {scenario}."
        )

    # Sort descending by suitability score
    candidates.sort(key=lambda c: c[0], reverse=True)

    best_suitability, best_shelter, best_route = candidates[0]

    reason = (
        f"Selected {best_shelter.name} as primary relief destination: "
        f"High route safety ({best_route.route_safety_score}%), distance {best_route.total_distance_km}km, "
        f"and {best_shelter.available_capacity:,} available shelter beds."
    )

    return ShelterRecommendationResult(
        village_id=village_id,
        village_name=v_name,
        recommended_shelter=best_shelter,
        route=best_route,
        recommendation_reason=reason,
    )


def recommend_shelter_for_village_over_graph(
    village_id: str,
    village_name: str,
    custom_roads: List[RoadSegment],
    shelters: List[Shelter],
) -> ShelterRecommendationResult:
    """
    Finds and recommends safest capacity-available relief shelter over a custom road graph.
    Enforces strict capacity constraint (rejects shelters with available_capacity <= 0).
    """
    from app.engine.routing_engine import compute_dijkstra_route_over_graph

    candidates: List[Tuple[float, Shelter, EvacuationRouteResult]] = []

    for shelter in shelters:
        if shelter.available_capacity <= 0:
            continue

        try:
            route = compute_dijkstra_route_over_graph(
                origin_village_id=village_id,
                destination_shelter_id=shelter.id,
                segments=custom_roads,
            )
        except ValueError:
            continue

        dist_score = min(100.0, route.total_distance_km * 2.0)
        shelter_safety = 100.0 - shelter.hazard_exposure_score

        suitability = (
            (route.route_safety_score * 0.45)
            + ((100.0 - dist_score) * 0.25)
            + (shelter_safety * 0.30)
        )

        candidates.append((suitability, shelter, route))

    if not candidates:
        raise ValueError(
            f"No safe capacity-available shelter accessible from {village_name} under simulation."
        )

    candidates.sort(key=lambda c: c[0], reverse=True)
    best_suitability, best_shelter, best_route = candidates[0]

    reason = (
        f"Selected {best_shelter.name} as primary relief destination: "
        f"Route safety ({best_route.route_safety_score}%), distance {best_route.total_distance_km}km, "
        f"and {best_shelter.available_capacity:,} available beds."
    )

    return ShelterRecommendationResult(
        village_id=village_id,
        village_name=village_name,
        recommended_shelter=best_shelter,
        route=best_route,
        recommendation_reason=reason,
    )

