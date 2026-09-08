"""
What-If Disaster Cascade Simulator Engine for APADA MITRA.
Performs dynamic cascade calculations for custom rainfall inputs without mutating global state.
"""
from typing import List, Dict, Any, Optional
from app.models.domain import (
    WhatIfSimulationInput,
    WhatIfSimulationResponse,
    VillageRiskDetail,
    LandslideRiskDetail,
    EvacuationPriority,
    RoadSegment,
    RoadStatus,
    Shelter,
    ShelterRecommendationResult,
    SimulationComparisonSummary,
    ComparisonMetric,
    EmergencyOperatorAlert,
    MultilingualAlert,
    RiskLevel,
    ScenarioType,
)
from app.data.dataset import DEMO_VILLAGES, get_village_feature_snapshot
from app.data.road_network import DEMO_ROADS_BASE, get_active_road_segments
from app.data.shelters import get_shelters_list
from app.engine.risk_engine import calculate_flash_flood_risk, determine_decision_status
from app.engine.explainability import calculate_explainability_factors
from app.engine.exposure_engine import calculate_village_exposure
from app.engine.landslide_engine import calculate_landslide_risk
from app.engine.priority_engine import calculate_evacuation_priorities
from app.engine.routing_engine import compute_dijkstra_route_over_graph
from app.engine.shelter_engine import recommend_shelter_for_village_over_graph
import app.api.routes as routes


def build_simulated_village_detail(v_dict: dict, snapshot: dict) -> VillageRiskDetail:
    """Helper function to calculate simulated village risk detail from custom snapshot."""
    risk_res = calculate_flash_flood_risk(snapshot)
    
    factors = calculate_explainability_factors(
        raw_features=risk_res["raw_features"],
        normalized_features=risk_res["normalized_features"],
        total_risk_score=risk_res["flash_flood_risk_score"],
    )

    exposure = calculate_village_exposure(
        population=v_dict["population"],
        infra_dict=v_dict["infrastructure"],
        risk_level=risk_res["risk_level"],
        risk_probability=risk_res["risk_probability"],
    )

    decision_status = determine_decision_status(
        risk_level=risk_res["risk_level"],
        exposure_score=exposure.exposure_score,
    )

    from app.engine.landslide_engine import calculate_landslide_risk
    ls_res = calculate_landslide_risk(v_dict["id"], v_dict["name"], snapshot)

    return VillageRiskDetail(
        village_id=v_dict["id"],
        village_name=v_dict["name"],
        latitude=v_dict["latitude"],
        longitude=v_dict["longitude"],
        population=v_dict["population"],
        elevation=v_dict["elevation"],
        scenario=ScenarioType.HEAVY_RAIN,
        flash_flood_risk_score=risk_res["flash_flood_risk_score"],
        risk_probability=risk_res["risk_probability"],
        confidence=risk_res["confidence"],
        risk_level=risk_res["risk_level"],
        decision_status=decision_status,
        exposure=exposure,
        factors=factors,
        missing_features=risk_res["missing_features"],
        last_updated=snapshot["timestamp"],
        state=v_dict.get("state", "Uttarakhand"),
        district=v_dict.get("district"),
        slope=v_dict.get("slope"),
        landslide_risk_score=round(ls_res.landslide_risk_score, 1),
        landslide_risk_level=ls_res.risk_level,
    )


def run_what_if_simulation(input_data: WhatIfSimulationInput) -> WhatIfSimulationResponse:
    """
    Executes what-if cascade simulation without mutating active global scenario state.
    """
    current_scenario = routes.CURRENT_SCENARIO

    # 1. Calculate simulated flood & landslide risk for all 15 villages
    simulated_villages_flood: List[VillageRiskDetail] = []
    simulated_landslides: Dict[str, LandslideRiskDetail] = {}

    for base_v in DEMO_VILLAGES:
        vid = base_v["id"]
        # Base snapshot
        snapshot = get_village_feature_snapshot(vid, current_scenario)
        
        # Override with custom what-if simulation inputs
        snapshot["current_rainfall"] = input_data.current_rainfall_mm_hr
        snapshot["forecast_rainfall"] = input_data.forecast_rainfall_24h_mm
        snapshot["soil_saturation"] = input_data.soil_saturation_pct
        snapshot["river_water_level"] = input_data.river_level_m

        # Compute simulated risk details
        v_flood = build_simulated_village_detail(base_v, snapshot)
        simulated_villages_flood.append(v_flood)

        v_ls = calculate_landslide_risk(vid, base_v["name"], snapshot)
        simulated_landslides[vid] = v_ls

    simulated_ls_list = list(simulated_landslides.values())

    # 2. Compute simulated evacuation priorities
    simulated_priorities = calculate_evacuation_priorities(simulated_villages_flood, simulated_landslides)

    # 3. Compute simulated road segment statuses dynamically
    simulated_roads: List[RoadSegment] = []
    village_flood_map = {v.village_id: v.flash_flood_risk_score for v in simulated_villages_flood}
    village_ls_map = {v.village_id: v.landslide_risk_score for v in simulated_ls_list}

    for base_road in DEMO_ROADS_BASE:
        f_exp1 = village_flood_map.get(base_road["source_id"], 0.0)
        f_exp2 = village_flood_map.get(base_road["target_id"], 0.0)
        f_avg = (f_exp1 + f_exp2) / 2.0

        ls_exp1 = village_ls_map.get(base_road["source_id"], 0.0)
        ls_exp2 = village_ls_map.get(base_road["target_id"], 0.0)
        ls_avg = (ls_exp1 + ls_exp2) / 2.0

        max_haz = max(f_avg, ls_avg)

        # Determine road status under custom simulated rainfall
        if max_haz >= 72.0 or input_data.current_rainfall_mm_hr >= 100.0 or input_data.forecast_rainfall_24h_mm >= 250.0:
            status = RoadStatus.BLOCKED
        elif max_haz >= 48.0 or input_data.current_rainfall_mm_hr >= 45.0 or input_data.forecast_rainfall_24h_mm >= 110.0:
            status = RoadStatus.DEGRADED
        else:
            status = RoadStatus.OPEN

        simulated_roads.append(
            RoadSegment(
                id=base_road["id"],
                name=base_road["name"],
                source_id=base_road["source_id"],
                target_id=base_road["target_id"],
                distance_km=base_road["distance_km"],
                flood_exposure=round(f_avg, 1),
                landslide_exposure=round(ls_avg, 1),
                status=status,
                coordinates=base_road["coordinates"],
            )
        )

    # 4. Simulated shelters
    simulated_shelters = get_shelters_list()

    # 5. Route pathfinding & shelter recommendation for target village
    target_vid = input_data.selected_village_id or (simulated_priorities[0].village_id if simulated_priorities else "VIL-011")
    target_flood = next((v for v in simulated_villages_flood if v.village_id == target_vid), simulated_villages_flood[0])

    shelter_rec: Optional[ShelterRecommendationResult] = None
    try:
        shelter_rec = recommend_shelter_for_village_over_graph(
            village_id=target_vid,
            village_name=target_flood.village_name,
            custom_roads=simulated_roads,
            shelters=simulated_shelters,
        )
    except Exception as e:
        pass

    # 6. Shelter Capacity Shortfall Analysis
    total_exposed_evac_pop = sum(v.exposure.population_exposed for v in simulated_villages_flood if v.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH])
    total_avail_shelter_beds = sum(s.available_capacity for s in simulated_shelters if s.available_capacity is not None)
    
    shelter_shortfall_count = max(0, total_exposed_evac_pop - total_avail_shelter_beds)
    shortfall_warning: Optional[str] = None
    if shelter_shortfall_count > 0:
        shortfall_warning = (
            f"SHELTER CAPACITY SHORTFALL: Total high-risk population requiring evacuation ({total_exposed_evac_pop:,}) "
            f"exceeds total available relief shelter capacity ({total_avail_shelter_beds:,}) by {shelter_shortfall_count:,} beds."
        )

    # 7. Operator Emergency Alert Generator with English, Hindi, Garhwali, Kumaoni, Nepali translations
    alert: Optional[EmergencyOperatorAlert] = None

    if target_flood:
        ls_target = simulated_landslides.get(target_vid)
        shelter_name = shelter_rec.recommended_shelter.name if shelter_rec else "High-Elevation Relief Center"
        
        blocked_road_names = [r.name for r in simulated_roads if r.status == RoadStatus.BLOCKED and (r.source_id == target_vid or r.target_id == target_vid)]
        if not blocked_road_names:
            blocked_road_names = [r.name for r in simulated_roads if r.status == RoadStatus.BLOCKED][:2]

        drivers = [
            f"Simulated Rainfall: {input_data.current_rainfall_mm_hr} mm/hr",
            f"Soil Saturation: {input_data.soil_saturation_pct}%",
            f"River Level Stage: {input_data.river_level_m}m",
            f"Flash Flood Threat: {round(target_flood.flash_flood_risk_score)}%",
        ]
        if ls_target:
            drivers.append(f"Landslide Threat: {round(ls_target.landslide_risk_score)}%")

        rec_action = "Initiate immediate evacuation protocols to assigned high-elevation shelter." if target_flood.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH] else "Maintain active monitoring and prepare emergency response teams."
        
        route_sum = f"Follow safe route to {shelter_name} ({shelter_rec.route.total_distance_km} km)" if shelter_rec else f"Proceed to {shelter_name}"
        avoid_str = ", ".join(blocked_road_names) if blocked_road_names else "High-hazard gorge roads"

        # Multilingual Operator Translations (English, Hindi, Garhwali, Kumaoni, Nepali)
        en_text = (
            f"OPERATOR DECISION ALERT: {target_flood.village_name} ({target_flood.risk_level.value} - {round(target_flood.flash_flood_risk_score)}%). "
            f"Action: {rec_action} Shelter: {shelter_name}. Avoid: {avoid_str}."
        )
        hi_text = (
            f"ऑपरेटर निर्णय चेतावनी: {target_flood.village_name} ({target_flood.risk_level.value} - {round(target_flood.flash_flood_risk_score)}%)। "
            f"कार्रवाई: {rec_action} आश्रय: {shelter_name}। इन मार्गों से बचें: {avoid_str}।"
        )
        gar_text = (
            f"आपदा मित्र निर्णय चेतावनी: {target_flood.village_name} ({target_flood.risk_level.value} - {round(target_flood.flash_flood_risk_score)}%)। "
            f"कार्रवाई: {rec_action} सुरक्षित ठौर: {shelter_name}। बाटो बचावा: {avoid_str}।"
        )
        kum_text = (
            f"आपदा मित्र निर्णय चेतावनी: {target_flood.village_name} ({target_flood.risk_level.value} - {round(target_flood.flash_flood_risk_score)}%)। "
            f"कार्रवाई: {rec_action} सुरक्षित थान: {shelter_name}। बाट बचावा: {avoid_str}।"
        )
        ne_text = (
            f"आपदा मित्र निर्णय चेतावनी: {target_flood.village_name} ({target_flood.risk_level.value} - {round(target_flood.flash_flood_risk_score)}%)। "
            f"कार्रवाई: {rec_action} सुरक्षित आश्रयस्थल: {shelter_name}। सडकबाट जोगिनुहोस्: {avoid_str}।"
        )

        alert = EmergencyOperatorAlert(
            village_id=target_vid,
            village_name=target_flood.village_name,
            risk_level=target_flood.risk_level,
            risk_score=target_flood.flash_flood_risk_score,
            primary_drivers=drivers,
            recommended_action=rec_action,
            shelter_name=shelter_name,
            safe_route_summary=route_sum,
            roads_to_avoid=blocked_road_names,
            translations=MultilingualAlert(
                english=en_text,
                hindi=hi_text,
                garhwali=gar_text,
                kumaoni=kum_text,
                nepali=ne_text,
            ),
        )

    # 8. Before (Current Active Scenario) vs After (Simulated) Comparison Summary Metrics
    curr_villages = [routes.compute_village_risk_detail(v, current_scenario) for v in DEMO_VILLAGES]
    curr_ls = [calculate_landslide_risk(v["id"], v["name"], get_village_feature_snapshot(v["id"], current_scenario)) for v in DEMO_VILLAGES]

    curr_avg_flood = sum(v.flash_flood_risk_score for v in curr_villages) / len(curr_villages)
    sim_avg_flood = sum(v.flash_flood_risk_score for v in simulated_villages_flood) / len(simulated_villages_flood)

    curr_avg_ls = sum(l.landslide_risk_score for l in curr_ls) / len(curr_ls)
    sim_avg_ls = sum(l.landslide_risk_score for l in simulated_ls_list) / len(simulated_ls_list)

    curr_crit = sum(1 for v in curr_villages if v.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH])
    sim_crit = sum(1 for v in simulated_villages_flood if v.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH])

    curr_pop = sum(v.exposure.population_exposed for v in curr_villages if v.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH])
    sim_pop = total_exposed_evac_pop

    curr_roads = get_active_road_segments(current_scenario)
    curr_blocked = sum(1 for r in curr_roads if r.status == RoadStatus.BLOCKED)
    sim_blocked = sum(1 for r in simulated_roads if r.status == RoadStatus.BLOCKED)

    curr_shortfall = max(0, curr_pop - total_avail_shelter_beds)

    comparison = SimulationComparisonSummary(
        avg_flood_risk=make_metric("Average Flood Risk", curr_avg_flood, sim_avg_flood, "%"),
        avg_landslide_risk=make_metric("Average Landslide Risk", curr_avg_ls, sim_avg_ls, "%"),
        critical_villages_count=make_metric("High/Critical Villages", curr_crit, sim_crit, "villages"),
        total_population_exposed=make_metric("Exposed Evacuation Population", curr_pop, sim_pop, "residents"),
        blocked_roads_count=make_metric("Blocked Road Segments", curr_blocked, sim_blocked, "segments"),
        shelter_shortfall_count=make_metric("Shelter Capacity Shortfall", curr_shortfall, shelter_shortfall_count, "beds"),
    )

    preset_name = detect_preset_name(input_data)

    return WhatIfSimulationResponse(
        input=input_data,
        preset_used=preset_name,
        comparison_summary=comparison,
        simulated_villages_flood=simulated_villages_flood,
        simulated_landslide_overview=simulated_ls_list,
        simulated_evacuation_priorities=simulated_priorities,
        simulated_roads=simulated_roads,
        simulated_shelters=simulated_shelters,
        simulated_route=shelter_rec.route if shelter_rec else None,
        simulated_shelter_recommendation=shelter_rec,
        shelter_shortfall_count=shelter_shortfall_count,
        shelter_shortfall_warning=shortfall_warning,
        operator_alert=alert,
    )


def make_metric(name: str, curr: float, sim: float, unit: str) -> ComparisonMetric:
    curr_r = round(curr, 1)
    sim_r = round(sim, 1)
    delta = round(sim_r - curr_r, 1)
    direction = "INCREASE" if delta > 0.0 else "DECREASE" if delta < 0.0 else "NEUTRAL"
    return ComparisonMetric(
        name=name,
        current_val=curr_r,
        simulated_val=sim_r,
        delta=delta,
        unit=unit,
        direction=direction,
    )


def detect_preset_name(inp: WhatIfSimulationInput) -> str:
    if inp.current_rainfall_mm_hr <= 15.0 and inp.forecast_rainfall_24h_mm <= 35.0:
        return "NORMAL"
    elif inp.current_rainfall_mm_hr >= 120.0 or inp.forecast_rainfall_24h_mm >= 300.0:
        return "EXTREME CLOUDBURST"
    elif inp.current_rainfall_mm_hr >= 45.0 or inp.forecast_rainfall_24h_mm >= 100.0:
        return "HEAVY RAIN"
    return "CUSTOM"
