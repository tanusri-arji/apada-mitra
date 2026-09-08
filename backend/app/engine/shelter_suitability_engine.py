"""
Feature 10: Shelter Suitability & Multi-Hazard Allocation Engine for APADA MITRA.
Evaluates candidate relief shelters using dynamic road network Dijkstra routing,
route safety, physical distance, shelter multi-hazard vulnerability, and capacity constraints.
Strictly returns NO_SAFE_SHELTER when all candidate paths are blocked or hazardous.
"""
from typing import List, Optional, Tuple, Dict, Any
from app.models.shelter import (
    ShelterRecord,
    ShelterDataState,
    ShelterHazardLevel,
    CapacityStatus,
    CandidateShelterEvaluation,
    VillageShelterRecommendation,
    ShelterSystemStatusResponse,
    ShelterCoverageItem,
    ShelterCoverageSummaryResponse,
)
from app.models.domain import ScenarioType, Shelter, ShelterRecommendationResult, EvacuationRouteResult
from app.adapters.shelter_adapter import shelter_adapter_instance, USDMA_AUTHORITY_NAME, USDMA_PORTAL_URL
from app.data.dataset import DEMO_VILLAGES
from app.engine.road_hazard_engine import road_hazard_engine_instance


SUITABILITY_WEIGHTS = {
    "route_safety": 0.45,
    "inverse_distance": 0.25,
    "inverse_shelter_hazard": 0.30,
}


def classify_shelter_hazard_level(score: float) -> ShelterHazardLevel:
    """Classifies numerical shelter hazard score into categorical levels."""
    if score < 25.0:
        return ShelterHazardLevel.LOW
    elif score < 50.0:
        return ShelterHazardLevel.MODERATE
    elif score < 75.0:
        return ShelterHazardLevel.HIGH
    else:
        return ShelterHazardLevel.CRITICAL


class ShelterSuitabilityEngine:
    """
    Engine for evaluating and allocating relief shelters based on multi-hazard intelligence.
    """

    def __init__(self):
        self.weights = SUITABILITY_WEIGHTS

    def evaluate_village_shelters(
        self,
        village_id: str,
        scenario: ScenarioType = ScenarioType.NORMAL,
        force_offline: bool = False,
    ) -> VillageShelterRecommendation:
        """
        Evaluates geographically local candidate relief shelters for a given village (within 15km search radius),
        performs route safety checks, computes suitability scores, and selects the optimal shelter and alternatives.
        """
        village = next((v for v in DEMO_VILLAGES if v["id"] == village_id), None)
        if not village:
            raise ValueError(f"Village ID '{village_id}' not found.")

        v_name = village["name"]
        v_lat = village["latitude"]
        v_lon = village["longitude"]

        # Fetch local candidates strictly within local search radius (15 km Haversine)
        local_shelter_tuples = shelter_adapter_instance.get_local_shelter_candidates_for_village(
            village_id=village_id,
            village_lat=v_lat,
            village_lon=v_lon,
            radius_km=15.0,
            force_offline=force_offline,
        )
        _, data_state = shelter_adapter_instance.get_all_shelters(force_offline=force_offline)

        evaluations: List[CandidateShelterEvaluation] = []
        suitable_candidates: List[Tuple[float, ShelterRecord, CandidateShelterEvaluation, Any]] = []

        num_candidates = len(local_shelter_tuples)
        num_verified = sum(
            1 for dist, s in local_shelter_tuples
            if s.data_state in (ShelterDataState.REAL_OFFICIAL, ShelterDataState.REAL_STATIC_GOVERNMENT, ShelterDataState.DERIVED_FROM_REAL_SOURCE)
        )

        min_dist_candidate: Optional[float] = None
        min_dist_verified: Optional[float] = None

        for straight_line_dist, shelter in local_shelter_tuples:
            if min_dist_candidate is None or straight_line_dist < min_dist_candidate:
                min_dist_candidate = straight_line_dist

            is_gov_verified = shelter.data_state in (
                ShelterDataState.REAL_OFFICIAL,
                ShelterDataState.REAL_STATIC_GOVERNMENT,
                ShelterDataState.DERIVED_FROM_REAL_SOURCE,
            )
            if is_gov_verified and (min_dist_verified is None or straight_line_dist < min_dist_verified):
                min_dist_verified = straight_line_dist

            # Derived shelter hazard calculation based on scenario adjustments
            base_hazard = shelter.combined_hazard_score or shelter.hazard_exposure_score or 15.0
            if scenario == ScenarioType.EXTREME_RAIN:
                adjusted_hazard = min(100.0, base_hazard * 1.5 + 10.0)
            elif scenario == ScenarioType.HEAVY_RAIN:
                adjusted_hazard = min(100.0, base_hazard * 1.25 + 5.0)
            else:
                adjusted_hazard = base_hazard

            hazard_level = classify_shelter_hazard_level(adjusted_hazard)

            # 1. Capacity Check: Reject ONLY full shelters where capacity is published and available <= 0
            if shelter.available_capacity is not None and shelter.available_capacity <= 0:
                evaluations.append(
                    CandidateShelterEvaluation(
                        shelter_id=shelter.shelter_id,
                        shelter_name=shelter.name,
                        latitude=shelter.latitude,
                        longitude=shelter.longitude,
                        elevation=shelter.elevation,
                        is_accessible=False,
                        rejection_reason="FULL_CAPACITY",
                        straight_line_distance_km=straight_line_dist,
                        shelter_hazard_score=adjusted_hazard,
                        shelter_hazard_level=hazard_level,
                        total_capacity=shelter.total_capacity,
                        available_capacity=shelter.available_capacity,
                        capacity_status=CapacityStatus.FULL,
                        data_state=shelter.data_state,
                        source=shelter.source,
                    )
                )
                continue

            # 2. Severe Shelter Hazard Check
            if adjusted_hazard >= 80.0:
                evaluations.append(
                    CandidateShelterEvaluation(
                        shelter_id=shelter.shelter_id,
                        shelter_name=shelter.name,
                        latitude=shelter.latitude,
                        longitude=shelter.longitude,
                        elevation=shelter.elevation,
                        is_accessible=False,
                        rejection_reason="HIGH_SHELTER_HAZARD",
                        straight_line_distance_km=straight_line_dist,
                        shelter_hazard_score=adjusted_hazard,
                        shelter_hazard_level=hazard_level,
                        total_capacity=shelter.total_capacity,
                        available_capacity=shelter.available_capacity,
                        capacity_status=shelter.capacity_status,
                        data_state=shelter.data_state,
                        source=shelter.source,
                    )
                )
                continue

            # 3. Dynamic Road Network Route Calculation
            try:
                route_detail = road_hazard_engine_instance.calculate_safest_evacuation_route(
                    origin_village_id=village_id,
                    destination_shelter_id=shelter.shelter_id,
                    scenario=scenario,
                    force_offline=force_offline,
                )
            except ValueError:
                route_detail = None

            if not route_detail or route_detail.route_status == "NO_SAFE_ROUTE":
                evaluations.append(
                    CandidateShelterEvaluation(
                        shelter_id=shelter.shelter_id,
                        shelter_name=shelter.name,
                        latitude=shelter.latitude,
                        longitude=shelter.longitude,
                        elevation=shelter.elevation,
                        is_accessible=False,
                        rejection_reason="BLOCKED_ROUTE",
                        straight_line_distance_km=straight_line_dist,
                        shelter_hazard_score=adjusted_hazard,
                        shelter_hazard_level=hazard_level,
                        total_capacity=shelter.total_capacity,
                        available_capacity=shelter.available_capacity,
                        capacity_status=shelter.capacity_status,
                        data_state=shelter.data_state,
                        source=shelter.source,
                    )
                )
                continue

            # Route distance tracking
            dist_km = route_detail.total_distance_km

            # 4. Calculate Suitability Score (0-100)
            dist_score = min(100.0, dist_km * 2.0)
            shelter_safety = max(0.0, 100.0 - adjusted_hazard)

            suitability = (
                (route_detail.route_safety_score * self.weights["route_safety"])
                + ((100.0 - dist_score) * self.weights["inverse_distance"])
                + (shelter_safety * self.weights["inverse_shelter_hazard"])
            )
            
            # Apply small uncertainty penalty (3.0 pts) if published bed capacity is unknown
            if shelter.available_capacity is None:
                suitability = max(0.0, suitability - 3.0)

            suitability = round(max(0.0, min(100.0, suitability)), 2)

            cand_eval = CandidateShelterEvaluation(
                shelter_id=shelter.shelter_id,
                shelter_name=shelter.name,
                latitude=shelter.latitude,
                longitude=shelter.longitude,
                elevation=shelter.elevation,
                is_accessible=True,
                straight_line_distance_km=straight_line_dist,
                route_distance_km=dist_km,
                travel_time_minutes=route_detail.estimated_travel_time_minutes,
                route_safety_score=route_detail.route_safety_score,
                shelter_hazard_score=adjusted_hazard,
                shelter_hazard_level=hazard_level,
                suitability_score=suitability,
                total_capacity=shelter.total_capacity,
                available_capacity=shelter.available_capacity,
                capacity_status=shelter.capacity_status,
                data_state=shelter.data_state,
                source=shelter.source,
            )
            evaluations.append(cand_eval)
            suitable_candidates.append((suitability, shelter, cand_eval, route_detail))

        # Rejected candidate list
        rejected = [e for e in evaluations if not e.is_accessible]
        num_accessible = len(suitable_candidates)

        # Determine coverage status based on local accessible candidates
        if num_accessible >= 3:
            coverage_stat = "GOOD"
        elif num_accessible >= 1:
            coverage_stat = "LIMITED"
        else:
            coverage_stat = "NO_LOCAL_SHELTER"

        # 5. Check if any safe shelter exists
        if not suitable_candidates:
            return VillageShelterRecommendation(
                village_id=village_id,
                village_name=v_name,
                status="NO_SAFE_SHELTER",
                selected_shelter_id=None,
                selected_shelter_name=None,
                suitability_score=None,
                route_distance_km=None,
                travel_time_minutes=None,
                route_safety_score=None,
                shelter_hazard_score=None,
                shelter_hazard_level=None,
                capacity=None,
                available_capacity=None,
                capacity_status=None,
                road_status="IMPASSABLE",
                blocked_segments=[],
                degraded_segments=[],
                data_state=data_state,
                source=USDMA_AUTHORITY_NAME,
                source_url=USDMA_PORTAL_URL,
                alternatives=[],
                coverage_status="NO_SAFE_SHELTER",
                nearest_verified_shelter_distance=min_dist_verified,
                nearest_candidate_distance=min_dist_candidate,
                number_of_candidates=num_candidates,
                number_of_verified_shelters=num_verified,
                number_of_route_accessible_shelters=0,
                rejected_candidates=rejected,
                all_candidates_evaluated=evaluations,
                selection_reason=f"No safe, capacity-available relief shelter accessible from {v_name} under scenario {scenario.value if hasattr(scenario, 'value') else scenario}.",
            )

        # Sort descending by suitability score
        suitable_candidates.sort(key=lambda c: c[0], reverse=True)
        best_suitability, best_shelter, best_cand_eval, best_route = suitable_candidates[0]

        # Extract alternative candidates (up to 5)
        alt_candidates = [cand[2] for cand in suitable_candidates[1:6]]

        cap_desc = (
            f"{best_shelter.available_capacity} available beds"
            if best_shelter.available_capacity is not None
            else "Not published (Capacity: Baseline Candidate)"
        )

        reason = (
            f"Selected {best_shelter.name} as optimal emergency relief destination: "
            f"Route Safety {best_route.route_safety_score:.1f}%, Distance {best_route.total_distance_km:.1f} km "
            f"(Travel Time {best_route.estimated_travel_time_minutes:.1f} mins), Shelter Hazard {best_cand_eval.shelter_hazard_score:.1f}% "
            f"({best_cand_eval.shelter_hazard_level.value}), and {cap_desc}."
        )

        return VillageShelterRecommendation(
            village_id=village_id,
            village_name=v_name,
            status="SAFE_SHELTER_FOUND",
            selected_shelter_id=best_shelter.shelter_id,
            selected_shelter_name=best_shelter.name,
            suitability_score=best_suitability,
            route_distance_km=best_route.total_distance_km,
            travel_time_minutes=best_route.estimated_travel_time_minutes,
            route_safety_score=best_route.route_safety_score,
            shelter_hazard_score=best_cand_eval.shelter_hazard_score,
            shelter_hazard_level=best_cand_eval.shelter_hazard_level,
            capacity=best_shelter.total_capacity,
            available_capacity=best_shelter.available_capacity,
            capacity_status=best_shelter.capacity_status,
            road_status=best_route.route_status,
            blocked_segments=best_route.blocked_segments,
            degraded_segments=best_route.degraded_segments,
            data_state=data_state,
            source=best_shelter.source,
            source_url=best_shelter.source_url,
            alternatives=alt_candidates,
            coverage_status=coverage_stat,
            nearest_verified_shelter_distance=min_dist_verified,
            nearest_candidate_distance=min_dist_candidate,
            number_of_candidates=num_candidates,
            number_of_verified_shelters=num_verified,
            number_of_route_accessible_shelters=num_accessible,
            rejected_candidates=rejected,
            all_candidates_evaluated=evaluations,
            selection_reason=reason,
        )

    def get_shelter_coverage_summary(
        self,
        scenario: ScenarioType = ScenarioType.NORMAL,
        force_offline: bool = False,
    ) -> ShelterCoverageSummaryResponse:
        """
        Calculates shelter candidate coverage across all 15 monitored villages.
        """
        items: List[ShelterCoverageItem] = []
        good_cnt = 0
        limited_cnt = 0
        none_cnt = 0

        registered_shelters, _ = shelter_adapter_instance.get_all_shelters(force_offline=force_offline)
        total_candidates_cnt = len(registered_shelters)

        for v in DEMO_VILLAGES:
            rec = self.evaluate_village_shelters(v["id"], scenario=scenario, force_offline=force_offline)
            item = ShelterCoverageItem(
                village_id=v["id"],
                village_name=v["name"],
                district=v.get("district", "Unknown"),
                state=v.get("state", "Uttarakhand"),
                nearest_verified_shelter_distance=rec.nearest_verified_shelter_distance,
                nearest_candidate_distance=rec.nearest_candidate_distance,
                number_of_candidates=rec.number_of_candidates,
                number_of_verified_shelters=rec.number_of_verified_shelters,
                number_of_route_accessible_shelters=rec.number_of_route_accessible_shelters,
                recommended_shelter_id=rec.selected_shelter_id,
                recommended_shelter_name=rec.selected_shelter_name,
                coverage_status=rec.coverage_status,
            )
            items.append(item)

            if rec.coverage_status == "GOOD":
                good_cnt += 1
            elif rec.coverage_status == "LIMITED":
                limited_cnt += 1
            else:
                none_cnt += 1

        return ShelterCoverageSummaryResponse(
            total_monitored_villages=len(DEMO_VILLAGES),
            total_shelter_candidates=total_candidates_cnt,
            villages_with_good_coverage=good_cnt,
            villages_with_limited_coverage=limited_cnt,
            villages_with_no_safe_shelter=none_cnt,
            coverage_details=items,
        )

    def get_system_status(self, force_offline: bool = False) -> ShelterSystemStatusResponse:
        """Returns overall shelter system status and verification counts."""
        shelters, data_state = shelter_adapter_instance.get_all_shelters(force_offline=force_offline)
        official_count = sum(
            1 for s in shelters
            if s.data_state in (ShelterDataState.REAL_OFFICIAL, ShelterDataState.REAL_STATIC_GOVERNMENT)
        )
        unverified_count = len(shelters) - official_count

        formula_desc = "Suitability = (Route_Safety * 0.45) + ((100 - min(100, Distance*2)) * 0.25) + ((100 - Shelter_Hazard) * 0.30)"

        return ShelterSystemStatusResponse(
            total_registered_shelters=len(shelters),
            valid_shelters_count=len(shelters),
            verified_official_count=official_count,
            unverified_demo_count=unverified_count,
            data_state=data_state,
            official_authority=USDMA_AUTHORITY_NAME,
            official_source_url=USDMA_PORTAL_URL,
            suitability_formula=formula_desc,
            suitability_weights=self.weights,
            disclaimer="Configured shelter candidate network is sourced from Chamoli & Rudraprayag District Disaster Management Plans (DDMP), Himachal Pradesh SDMA, and Kerala KSDMA disaster documents. Verification and capacity status are explicitly tracked.",
        )


shelter_suitability_engine_instance = ShelterSuitabilityEngine()

