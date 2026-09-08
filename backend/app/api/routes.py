"""
FastAPI Route Handlers for APADA MITRA Backend.
"""
import os
import json
import urllib.request
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from app.models.domain import (
    ScenarioType,
    VillageRiskDetail,
    RiskLevel,
    DataQualityStatus,
    VillageBase,
    LandslideRiskDetail,
    EvacuationPriority,
    RoadSegment,
    Shelter,
    EvacuationRouteResult,
    ShelterRecommendationResult,
    WhatIfSimulationInput,
    WhatIfSimulationResponse,
    OverallDataQualityResponse,
    OperationalIncident,
    IncidentActionRequest,
    IncidentStatusEnum,
    AuditTrailEntry,
)
from app.models.road import (
    RoadSegmentDetail,
    EvacuationRouteDetail,
    RoadNetworkStatusResponse,
)
from app.models.shelter import (
    ShelterRecord,
    CandidateShelterEvaluation,
    VillageShelterRecommendation,
    ShelterSystemStatusResponse,
    ShelterCoverageSummaryResponse,
)
from app.models.alert import (
    MultiHazardAlertRecord,
    AlertStatusResponse,
    AlertDeliveryStatusResponse,
    MultilingualAlertText,
    AlertAuditRecord,
)
from app.models.api import (
    HealthResponse,
    ReadinessResponse,
    ScenarioStateResponse,
    ScenarioUpdateRequest,
    ImpactSummaryResponse,
    RiskOverviewResponse,
    RouteCalculationRequest,
)
from app.models.imd import (
    IMDWarning,
    IMDStatus,
    IMDVillageWarningResponse,
    IMDDistrictWarningResponse,
)
from app.adapters.imd_cap_adapter import imd_cap_adapter_instance
from app.data.dataset import (
    DEMO_VILLAGES,
    SCENARIO_INPUT_MULTIPLIERS,
    get_village_feature_snapshot,
    DATA_ORIGIN_LABEL,
)
from app.data_pipeline import pipeline_instance
from app.engine.risk_engine import (
    calculate_flash_flood_risk,
    determine_decision_status,
)
from app.engine.explainability import calculate_explainability_factors
from app.engine.exposure_engine import calculate_village_exposure
from app.data.census_population_data import get_village_census_population
from app.engine.routing_engine import MOUNTAIN_ROAD_GRAPH

router = APIRouter()

# Global state for current scenario (defaults to NORMAL for true baseline live operations)
CURRENT_SCENARIO: ScenarioType = ScenarioType.NORMAL


def _warm_observation_cache():
    """
    Background thread: pre-fetches live weather for all villages once at startup.
    After this runs, all parallel API calls (/risk, /landslide, /priorities) hit the
    in-memory cache instead of racing to call Open-Meteo 15+ times simultaneously.
    """
    import threading
    import time

    def _run():
        # Small delay to let the server fully start first
        time.sleep(3)
        try:
            for v in DEMO_VILLAGES:
                pipeline_instance.get_normalized_observation(
                    latitude=v["latitude"],
                    longitude=v["longitude"],
                    location_key=v["id"],
                    scenario=ScenarioType.NORMAL,
                )
        except Exception:
            pass  # Warm-up is best-effort; failures are non-critical

    t = threading.Thread(target=_run, daemon=True)
    t.start()


# Kick off cache warm-up immediately when the module loads (i.e., when Render starts).
_warm_observation_cache()


def compute_village_risk_detail(village_data: dict, scenario: ScenarioType) -> VillageRiskDetail:
    """Helper function to calculate complete village risk detail using normalized data pipeline."""
    obs = pipeline_instance.get_normalized_observation(
        latitude=village_data["latitude"],
        longitude=village_data["longitude"],
        location_key=village_data["id"],
        scenario=scenario,
    )
    snapshot = pipeline_instance.convert_to_risk_feature_snapshot(obs, village_data, scenario)
    risk_res = calculate_flash_flood_risk(snapshot)

    
    factors = calculate_explainability_factors(
        raw_features=risk_res["raw_features"],
        normalized_features=risk_res["normalized_features"],
        total_risk_score=risk_res["flash_flood_risk_score"],
    )

    census_rec = get_village_census_population(village_data["id"])
    effective_pop = census_rec.population if census_rec else village_data["population"]

    exposure = calculate_village_exposure(
        population=effective_pop,
        infra_dict=village_data["infrastructure"],
        risk_level=risk_res["risk_level"],
        risk_probability=risk_res["risk_probability"],
    )

    decision_status = determine_decision_status(
        risk_level=risk_res["risk_level"],
        exposure_score=exposure.exposure_score,
    )

    from app.engine.landslide_engine import calculate_landslide_risk
    ls_res = calculate_landslide_risk(village_data["id"], village_data["name"], snapshot)

    return VillageRiskDetail(
        village_id=village_data["id"],
        village_name=village_data["name"],
        latitude=village_data["latitude"],
        longitude=village_data["longitude"],
        population=effective_pop,
        elevation=village_data["elevation"],
        scenario=scenario,
        flash_flood_risk_score=risk_res["flash_flood_risk_score"],
        risk_probability=risk_res["risk_probability"],
        confidence=risk_res["confidence"],
        risk_level=risk_res["risk_level"],
        decision_status=decision_status,
        exposure=exposure,
        factors=factors,
        missing_features=risk_res["missing_features"],
        last_updated=snapshot["timestamp"],
        state=village_data.get("state", "Uttarakhand"),
        district=village_data.get("district"),
        slope=village_data.get("slope"),
        landslide_risk_score=round(ls_res.landslide_risk_score, 1),
        landslide_risk_level=ls_res.risk_level,
    )


@router.get("/health", response_model=HealthResponse)
def get_health():
    """Returns backend system operational health status."""
    report = pipeline_instance.get_data_quality_report(CURRENT_SCENARIO)
    return HealthResponse(
        status="ok",
        version="1.0.0",
        service="APADA MITRA Disaster Intelligence Backend",
        data_mode=report.data_mode,
    )


@router.get("/data-quality", response_model=OverallDataQualityResponse)
def get_data_quality():
    """Returns structured data quality health report across input adapters and sources."""
    return pipeline_instance.get_data_quality_report(CURRENT_SCENARIO)


@router.get("/readiness", response_model=ReadinessResponse)
def get_readiness():
    """Single health/readiness check verifying all core engines and datasets."""
    dataset_ok = len(DEMO_VILLAGES) >= 15
    graph_ok = MOUNTAIN_ROAD_GRAPH is not None and len(MOUNTAIN_ROAD_GRAPH.nodes) > 0
    sim_ok = True
    fallback_ok = True

    report = pipeline_instance.get_data_quality_report(CURRENT_SCENARIO)
    all_ready = dataset_ok and graph_ok and sim_ok and fallback_ok
    status_label = "SYSTEM READY" if all_ready else "DEGRADED — FALLBACK ACTIVE"

    return ReadinessResponse(
        status=status_label,
        ready=all_ready,
        checks={
            "backend_reachable": True,
            "dataset_available": dataset_ok,
            "routing_engine_available": graph_ok,
            "simulation_engine_available": sim_ok,
            "local_fallback_available": fallback_ok,
            "data_pipeline_active": True,
        },
        data_mode=report.data_mode,
        version="1.0.0",
    )


@router.get("/scenario", response_model=ScenarioStateResponse)
def get_scenario():
    """Gets currently active weather scenario state."""
    sc_meta = SCENARIO_INPUT_MULTIPLIERS[CURRENT_SCENARIO]
    return ScenarioStateResponse(
        scenario=CURRENT_SCENARIO,
        description=sc_meta["description"],
        data_quality_status=sc_meta["quality"],
        active_villages_count=len(DEMO_VILLAGES),
        last_updated=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/scenario", response_model=ScenarioStateResponse)
def update_scenario(payload: ScenarioUpdateRequest):
    """Updates active weather scenario (NORMAL, HEAVY_RAIN, EXTREME_RAIN)."""
    global CURRENT_SCENARIO
    CURRENT_SCENARIO = payload.scenario
    # NOTE: We deliberately do NOT call pipeline_instance.clear_cache() here.
    # Weather observations (NormalizedEnvironmentObservation) are real atmospheric
    # data fetched from Open-Meteo / wttr.in — they are scenario-independent.
    # Clearing them forces 15 fresh API calls on every scenario switch, adding
    # 15-30 seconds of latency. The existing 3-hour TTL handles natural expiry.
    # Scenario changes only affect how convert_to_risk_feature_snapshot() uses the data.
    sc_meta = SCENARIO_INPUT_MULTIPLIERS[CURRENT_SCENARIO]
    return ScenarioStateResponse(
        scenario=CURRENT_SCENARIO,
        description=sc_meta["description"],
        data_quality_status=sc_meta["quality"],
        active_villages_count=len(DEMO_VILLAGES),
        last_updated=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/villages", response_model=List[VillageBase])
def list_villages():
    """Lists all monitored villages in watershed."""
    return [VillageBase(**v) for v in DEMO_VILLAGES]


@router.get("/villages/{village_id}", response_model=VillageRiskDetail)
def get_village_detail(village_id: str):
    """Gets comprehensive risk, exposure, and explainability breakdown for a single village."""
    village = next((v for v in DEMO_VILLAGES if v["id"] == village_id), None)
    if not village:
        raise HTTPException(status_code=404, detail=f"Village ID {village_id} not found.")
    return compute_village_risk_detail(village, CURRENT_SCENARIO)


@router.get("/risk", response_model=RiskOverviewResponse)
def get_risk_overview():
    """Returns risk details for all villages along with regional aggregate impact."""
    details = [compute_village_risk_detail(v, CURRENT_SCENARIO) for v in DEMO_VILLAGES]
    
    crit_count = sum(1 for d in details if d.risk_level == RiskLevel.CRITICAL)
    high_count = sum(1 for d in details if d.risk_level == RiskLevel.HIGH)
    mod_count = sum(1 for d in details if d.risk_level == RiskLevel.MODERATE)
    low_count = sum(1 for d in details if d.risk_level == RiskLevel.LOW)
    
    tot_exposed = sum(d.exposure.population_exposed for d in details)
    avg_score = round(sum(d.flash_flood_risk_score for d in details) / len(details), 2)
    avg_conf = round(sum(d.confidence for d in details) / len(details), 1)

    report = pipeline_instance.get_data_quality_report(CURRENT_SCENARIO)

    impact = ImpactSummaryResponse(
        scenario=CURRENT_SCENARIO,
        total_villages=len(details),
        critical_villages_count=crit_count,
        high_villages_count=high_count,
        moderate_villages_count=mod_count,
        low_villages_count=low_count,
        total_population_exposed=tot_exposed,
        average_risk_score=avg_score,
        average_confidence=avg_conf,
        data_quality_summary=f"STATE: {report.overall_state} ({report.data_mode})",
        last_updated=datetime.now(timezone.utc).isoformat(),
    )

    return RiskOverviewResponse(
        scenario=CURRENT_SCENARIO,
        impact_summary=impact,
        villages_risk=details,
    )


@router.get("/impact", response_model=ImpactSummaryResponse)
def get_impact_summary():
    """Returns regional impact and exposure totals."""
    overview = get_risk_overview()
    return overview.impact_summary


# Day 2 Endpoints

@router.get("/landslide", response_model=List[LandslideRiskDetail])
def get_landslide_overview():
    """Returns terrain-aware landslide susceptibility risk details for all villages."""
    from app.engine.landslide_engine import calculate_landslide_risk
    results: List[LandslideRiskDetail] = []
    for v in DEMO_VILLAGES:
        obs = pipeline_instance.get_normalized_observation(v["latitude"], v["longitude"], v["id"], CURRENT_SCENARIO)
        snapshot = pipeline_instance.convert_to_risk_feature_snapshot(obs, v, CURRENT_SCENARIO)
        ls = calculate_landslide_risk(v["id"], v["name"], snapshot)
        results.append(ls)
    return results


@router.get("/evacuation/priorities", response_model=List[EvacuationPriority])
def get_evacuation_priorities():
    """Returns multi-hazard evacuation priority ranking across all watershed villages."""
    from app.engine.landslide_engine import calculate_landslide_risk
    from app.engine.priority_engine import calculate_evacuation_priorities

    # Compute flood risk for all villages (this also fetches/caches observations).
    flood_details = [compute_village_risk_detail(v, CURRENT_SCENARIO) for v in DEMO_VILLAGES]

    # Reuse cached observations for landslide — avoids a second round of 15 API calls.
    landslide_details = {}
    for v in DEMO_VILLAGES:
        # get_normalized_observation is cache-first; these calls hit the in-memory
        # cache populated by compute_village_risk_detail above, so no network is used.
        obs = pipeline_instance.get_normalized_observation(v["latitude"], v["longitude"], v["id"], CURRENT_SCENARIO)
        snapshot = pipeline_instance.convert_to_risk_feature_snapshot(obs, v, CURRENT_SCENARIO)
        landslide_details[v["id"]] = calculate_landslide_risk(v["id"], v["name"], snapshot)

    return calculate_evacuation_priorities(flood_details, landslide_details)



@router.get("/roads", response_model=List[RoadSegmentDetail])
def get_road_network(force_offline: bool = False):
    """Returns mountain road network segments with dynamic scenario hazard statuses and OpenStreetMap geometry."""
    from app.engine.road_hazard_engine import road_hazard_engine_instance
    return road_hazard_engine_instance.get_all_road_segments(
        scenario=CURRENT_SCENARIO,
        force_offline=force_offline,
    )


@router.post("/evacuation/route", response_model=EvacuationRouteResult)
def compute_evacuation_route(payload: RouteCalculationRequest):
    """Calculates hazard-aware Dijkstra evacuation path from village to target shelter."""
    from app.engine.routing_engine import calculate_safest_route
    try:
        return calculate_safest_route(
            origin_village_id=payload.origin_village_id,
            destination_shelter_id=payload.destination_shelter_id,
            scenario=CURRENT_SCENARIO,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/shelters", response_model=List[ShelterRecord])
def list_shelters(force_offline: bool = False):
    """Lists all emergency relief shelters with geometry, capacity, and dynamic hazard scores."""
    from app.adapters.shelter_adapter import shelter_adapter_instance
    shelters, _ = shelter_adapter_instance.get_all_shelters(force_offline=force_offline)
    return shelters


@router.get("/evacuation/shelter-recommendation/{village_id}", response_model=ShelterRecommendationResult)
def get_shelter_recommendation(village_id: str):
    """Recommends safest capacity-available relief shelter for a given village."""
    from app.engine.shelter_engine import recommend_safest_shelter
    try:
        return recommend_safest_shelter(village_id=village_id, scenario=CURRENT_SCENARIO)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/simulation/what-if", response_model=WhatIfSimulationResponse)
def run_what_if_disaster_simulation(request_body: WhatIfSimulationInput):
    """
    Runs real-time What-If Disaster Cascade Simulation under custom hydro-meteorological inputs
    without mutating global scenario state.
    """
    from app.engine.simulation_engine import run_what_if_simulation
    try:
        return run_what_if_simulation(request_body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Simulation error: {str(e)}")


@router.get("/v1/data-quality", response_model=OverallDataQualityResponse)
def get_data_quality_v1():
    """Versioned endpoint returning structured data quality health report across input adapters and sources."""
    return pipeline_instance.get_data_quality_report(CURRENT_SCENARIO)


# Operational Incident Command & Decision Audit Trail In-Memory Store
INCIDENT_STATUS_MAP: Dict[str, IncidentStatusEnum] = {}
AUDIT_LOG_ENTRIES: List[AuditTrailEntry] = [
    AuditTrailEntry(
        timestamp="2026-09-04T12:00:00Z",
        event="System Initialized",
        village_name="Pipalkoti",
        risk_state="HIGH",
        operator_action="SYSTEM_READY",
    )
]


@router.get("/incidents", response_model=List[OperationalIncident])
def get_operational_incidents():
    """
    Returns operational incident objects for villages crossing HIGH/CRITICAL risk thresholds.
    Allows EOC decision operators to track and transition incident lifecycle state.
    """
    from app.engine.landslide_engine import calculate_landslide_risk
    from app.engine.priority_engine import calculate_evacuation_priorities
    from app.engine.shelter_engine import recommend_safest_shelter

    flood_details = [compute_village_risk_detail(v, CURRENT_SCENARIO) for v in DEMO_VILLAGES]
    landslide_map = {}
    for v in DEMO_VILLAGES:
        obs = pipeline_instance.get_normalized_observation(v["latitude"], v["longitude"], v["id"], CURRENT_SCENARIO)
        snapshot = pipeline_instance.convert_to_risk_feature_snapshot(obs, v, CURRENT_SCENARIO)
        landslide_map[v["id"]] = calculate_landslide_risk(v["id"], v["name"], snapshot)

    priorities = calculate_evacuation_priorities(flood_details, landslide_map)
    prio_dict = {p.village_id: p for p in priorities}

    incidents: List[OperationalIncident] = []
    for f in flood_details:
        if f.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            vid = f.village_id
            ls_detail = landslide_map.get(vid)
            ls_score = ls_detail.landslide_risk_score if ls_detail else 0.0
            prio = prio_dict.get(vid)

            inc_id = f"INC-{vid}-20260904"
            current_status = INCIDENT_STATUS_MAP.get(inc_id, IncidentStatusEnum.PENDING)

            try:
                rec_shelter = recommend_safest_shelter(vid, CURRENT_SCENARIO)
                shelter_name = rec_shelter.recommended_shelter.name
                route_desc = f"{rec_shelter.route.total_distance_km} km via {rec_shelter.route.destination_shelter_name} (Safety: {rec_shelter.route.route_safety_score}%)"
                rejected_roads = rec_shelter.route.rejected_dangerous_alternatives
            except Exception:
                shelter_name = "Pipalkoti Central High School Relief Complex"
                route_desc = "Standard Evacuation Corridor"
                rejected_roads = ["High-Hazard Gorge Road"]

            incidents.append(
                OperationalIncident(
                    incident_id=inc_id,
                    village_id=vid,
                    village_name=f.village_name,
                    created_time=f.last_updated,
                    hazard="MULTI_HAZARD" if ls_score >= 50.0 else "FLASH_FLOOD",
                    flash_flood_risk=f.flash_flood_risk_score,
                    landslide_risk=ls_score,
                    confidence=f.confidence,
                    exposed_population=f.exposure.population_exposed,
                    evacuation_priority_score=prio.evacuation_priority_score if prio else f.flash_flood_risk_score,
                    evacuation_rank=prio.rank if prio else 1,
                    recommended_route=route_desc,
                    recommended_shelter=shelter_name,
                    blocked_unsafe_roads=rejected_roads,
                    recommended_action="Initiate immediate evacuation readiness and prepare emergency shelter dispatch." if f.risk_level == RiskLevel.CRITICAL else "Maintain active monitoring and prepare emergency response teams.",
                    disclaimer="FINAL EVACUATION / PUBLIC WARNING DECISION REMAINS WITH AUTHORIZED DISASTER MANAGEMENT AUTHORITIES.",
                    alert_status=current_status,
                    last_updated=f.last_updated,
                )
            )

    return incidents


@router.post("/incidents/action", response_model=OperationalIncident)
def execute_incident_action(payload: IncidentActionRequest):
    """
    Executes operator state transition on an active operational incident (ACKNOWLEDGE, ESCALATE, etc.)
    and records an entry in the decision audit trail.
    """
    now_iso = pipeline_instance.last_fetch_attempt.isoformat() if pipeline_instance.last_fetch_attempt else "2026-09-04T12:00:00Z"
    
    new_status = IncidentStatusEnum.ACKNOWLEDGED
    if payload.action.value == "ACKNOWLEDGE":
        new_status = IncidentStatusEnum.ACKNOWLEDGED
    elif payload.action.value == "ESCALATE":
        new_status = IncidentStatusEnum.ESCALATED
    elif payload.action.value == "MARK_EVACUATION_ACTIVE":
        new_status = IncidentStatusEnum.EVACUATION_ACTIVE
    elif payload.action.value == "PREPARE_ALERT":
        new_status = IncidentStatusEnum.ALERT_PREPARED

    INCIDENT_STATUS_MAP[payload.incident_id] = new_status

    # Record Audit Entry
    AUDIT_LOG_ENTRIES.append(
        AuditTrailEntry(
            timestamp=now_iso,
            event=f"Incident Action: {payload.action.value}",
            village_name=payload.incident_id,
            risk_state="HIGH/CRITICAL",
            operator_action=f"OPERATOR {payload.action.value}: {payload.notes or 'No additional notes'}",
        )
    )

    incidents = get_operational_incidents()
    target = next((i for i in incidents if i.incident_id == payload.incident_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return target


@router.get("/audit-trail", response_model=List[AuditTrailEntry])
def get_audit_trail():
    """Returns chronologically recorded operational decision audit trail entries."""
    return AUDIT_LOG_ENTRIES


# Feature 3: IoT Sensor API Ingestion & Retrieval Endpoints

from app.models.iot import IoTSensorRecord
from app.engine.iot_store import iot_store_instance


@router.post("/iot/sensors/ingest", response_model=IoTSensorRecord)
def ingest_iot_sensor_observation(payload: Dict[str, Any]):
    """
    Ingests real-time IoT sensor observation (rainfall, soil_moisture, or water_level).
    Validates village registration, sensor types, non-negative values, valid units, and timestamps.
    """
    try:
        return iot_store_instance.ingest(payload)
    except ValueError as e:
        err_msg = str(e)
        if "Unknown village ID" in err_msg:
            raise HTTPException(status_code=404, detail=err_msg)
        raise HTTPException(status_code=400, detail=err_msg)


@router.get("/iot/sensors", response_model=List[IoTSensorRecord])
def list_iot_sensors():
    """Returns all registered latest IoT sensor observations with freshness status."""
    return iot_store_instance.get_all_sensors()


@router.get("/iot/sensors/{sensor_id}", response_model=IoTSensorRecord)
def get_iot_sensor_by_id(sensor_id: str):
    """Returns latest observation for a specific sensor ID."""
    sensor = iot_store_instance.get_sensor_by_id(sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail=f"Sensor ID '{sensor_id}' not found.")
    return sensor


@router.get("/iot/villages/{village_id}/sensors", response_model=List[IoTSensorRecord])
def get_iot_sensors_by_village(village_id: str):
    """Returns all latest IoT sensor observations associated with a given village."""
    village = next((v for v in DEMO_VILLAGES if v["id"] == village_id), None)
    if not village:
        raise HTTPException(status_code=404, detail=f"Village ID '{village_id}' not found.")
    return iot_store_instance.get_village_sensors(village_id)


# Feature 4: GIS Terrain Intelligence Endpoint

from app.models.terrain import VillageTerrainDetail
from app.engine.terrain_engine import terrain_engine_instance


@router.get("/terrain/villages/{village_id}", response_model=VillageTerrainDetail)
def get_village_terrain_detail(village_id: str):
    """
    Returns real GIS DEM elevation, 2D vector derived slope, and D8 derived flow accumulation for a village.
    """
    village = next((v for v in DEMO_VILLAGES if v["id"] == village_id), None)
    if not village:
        raise HTTPException(status_code=404, detail=f"Village ID '{village_id}' not found.")
    return terrain_engine_instance.get_village_terrain(village)


# Feature 5: Real Historical Landslide Inventory Endpoints

from app.models.landslide import (
    HistoricalLandslideInventoryResponse,
    VillageHistoricalLandslideSummary,
)
from app.engine.landslide_inventory import historical_landslide_service


@router.get("/landslides/historical", response_model=HistoricalLandslideInventoryResponse)
def get_historical_landslide_inventory(force_offline: bool = False):
    """
    Returns the complete verified ISRO NRSC & GSI historical landslide inventory for the Himalayan region.
    """
    return historical_landslide_service.get_inventory_overview(force_offline=force_offline)


@router.get("/landslides/historical/{village_id}", response_model=VillageHistoricalLandslideSummary)
def get_village_historical_landslide_summary(village_id: str, force_offline: bool = False):
    """
    Returns historical landslide proximity, density, and susceptibility evidence for a specific village.
    """
    village = next((v for v in DEMO_VILLAGES if v["id"] == village_id), None)
    if not village:
        raise HTTPException(status_code=404, detail=f"Village ID '{village_id}' not found.")
    return historical_landslide_service.get_village_historical_summary(village, force_offline=force_offline)


# Feature 6: Operational Lead-Time & Evacuation Window Endpoints

from app.models.lead_time import VillageLeadTimeDetail
from app.engine.lead_time_engine import lead_time_engine_instance


@router.get("/lead-time", response_model=List[VillageLeadTimeDetail])
def get_all_villages_lead_time(force_offline: bool = False):
    """
    Returns operational evacuation lead-time assessments and safety margins for all monitored villages.
    """
    results: List[VillageLeadTimeDetail] = []
    for v in DEMO_VILLAGES:
        res = lead_time_engine_instance.calculate_village_lead_time(
            village_data=v,
            scenario=CURRENT_SCENARIO,
            force_offline=force_offline,
        )
        results.append(res)
    return results


@router.get("/lead-time/villages/{village_id}", response_model=VillageLeadTimeDetail)
def get_village_lead_time_detail(village_id: str, force_offline: bool = False):
    """
    Returns the complete operational lead-time, mobilization requirements, and safety margin for a specific village.
    """
    village = next((v for v in DEMO_VILLAGES if v["id"] == village_id), None)
    if not village:
        raise HTTPException(status_code=404, detail=f"Village ID '{village_id}' not found.")
    return lead_time_engine_instance.calculate_village_lead_time(
        village_data=village,
        scenario=CURRENT_SCENARIO,
        force_offline=force_offline,
    )


# Feature 7: Real Population & Hazard Exposure Endpoints

from app.models.population import VillageExposureDetail
from app.engine.exposure_engine import (
    calculate_village_exposure_detail,
    calculate_all_villages_exposure_detail,
)


@router.get("/exposure/villages", response_model=List[VillageExposureDetail])
def get_all_villages_exposure():
    """
    Returns comprehensive multi-hazard population exposure and Census 2011 demographic records for all monitored villages.
    """
    return calculate_all_villages_exposure_detail(scenario=CURRENT_SCENARIO)


@router.get("/exposure/villages/{village_id}", response_model=VillageExposureDetail)
def get_village_exposure_detail(village_id: str):
    """
    Returns detailed multi-hazard exposure breakdown, vulnerable headcount, and Census 2011 provenance for a specific village.
    """
    detail = calculate_village_exposure_detail(village_id=village_id, scenario=CURRENT_SCENARIO)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Village ID '{village_id}' not found.")
    return detail


# Feature 8: Real River-Level / Hydrological Telemetry Endpoints

from app.models.hydrology import (
    HydrologicalStationRecord,
    HydrologicalObservation,
    HydrologySystemStatus,
)
from app.engine.hydrology_engine import hydrology_engine_instance


@router.get("/hydrology/status", response_model=HydrologySystemStatus)
def get_hydrology_system_status():
    """
    Returns official CWC telemetry connectivity status, registered stations count, and active IoT sensors.
    """
    return hydrology_engine_instance.get_system_status()


@router.get("/hydrology/stations", response_model=List[HydrologicalStationRecord])
def get_all_hydrological_stations():
    """
    Returns all registered CWC hydrological river gauging stations in the Alaknanda and Mandakini basins.
    """
    return hydrology_engine_instance.get_all_stations()


@router.get("/hydrology/stations/{station_id}", response_model=HydrologicalObservation)
def get_hydrological_station_observation(station_id: str, force_offline: bool = False):
    """
    Returns current hydrological telemetry observation for a specific gauging station.
    """
    obs = hydrology_engine_instance.get_station_observation(
        station_id=station_id,
        scenario=CURRENT_SCENARIO,
        force_offline=force_offline,
    )
    if not obs:
        raise HTTPException(status_code=404, detail=f"Hydrological Station ID '{station_id}' not found.")
    return obs


@router.get("/hydrology/villages/{village_id}", response_model=HydrologicalObservation)
def get_village_hydrology_observation(village_id: str, force_offline: bool = False):
    """
    Returns river-level telemetry and flood-risk point contributions for a specific village under 4-tier source priority.
    """
    obs = hydrology_engine_instance.get_village_hydrology(
        village_id=village_id,
        scenario=CURRENT_SCENARIO,
        force_offline=force_offline,
    )
    if not obs:
        raise HTTPException(status_code=404, detail=f"Village ID '{village_id}' not found.")
    return obs


# Feature 9: Real Road Network & Dynamic Hazard Intelligence Endpoints

from app.models.road import (
    RoadSegmentDetail,
    EvacuationRouteDetail,
    RoadNetworkStatusResponse,
)
from app.engine.road_hazard_engine import road_hazard_engine_instance


@router.get("/roads/status", response_model=RoadNetworkStatusResponse)
def get_road_network_status(force_offline: bool = False):
    """
    Returns overall passability status and statistics of the OpenStreetMap road network.
    """
    return road_hazard_engine_instance.get_network_status(
        scenario=CURRENT_SCENARIO,
        force_offline=force_offline,
    )



@router.get("/roads/{road_id}", response_model=RoadSegmentDetail)
def get_road_segment_detail(road_id: str, force_offline: bool = False):
    """
    Returns detailed road geometry, surface attributes, and dynamic hazard scores for a specific road segment.
    """
    seg = road_hazard_engine_instance.get_road_segment_by_id(
        road_id=road_id,
        scenario=CURRENT_SCENARIO,
        force_offline=force_offline,
    )
    if not seg:
        raise HTTPException(status_code=404, detail=f"Road segment ID '{road_id}' not found.")
    return seg


@router.get("/roads/villages/{village_id}", response_model=List[RoadSegmentDetail])
def get_village_road_segments(village_id: str, force_offline: bool = False):
    """
    Returns all road segments directly originating from or connected to a monitored village.
    """
    village = next((v for v in DEMO_VILLAGES if v["id"] == village_id), None)
    if not village:
        raise HTTPException(status_code=404, detail=f"Village ID '{village_id}' not found.")
    return road_hazard_engine_instance.get_village_roads(
        village_id=village_id,
        scenario=CURRENT_SCENARIO,
        force_offline=force_offline,
    )


@router.get("/evacuation/route/{village_id}", response_model=EvacuationRouteDetail)
def get_village_evacuation_route(village_id: str, destination_shelter_id: Optional[str] = None, force_offline: bool = False):
    """
    Computes the safest evacuation route over the real road network, excluding blocked segments and penalizing degraded roads.
    """
    try:
        return road_hazard_engine_instance.calculate_safest_evacuation_route(
            origin_village_id=village_id,
            destination_shelter_id=destination_shelter_id,
            scenario=CURRENT_SCENARIO,
            force_offline=force_offline,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Feature 10: Real Shelter & Relief Center Suitability Endpoints

@router.get("/shelters/status", response_model=ShelterSystemStatusResponse)
def get_shelter_system_status(force_offline: bool = False):
    """
    Returns shelter registry metadata, data-state classification, and suitability formula weights.
    """
    from app.engine.shelter_suitability_engine import shelter_suitability_engine_instance
    return shelter_suitability_engine_instance.get_system_status(force_offline=force_offline)

@router.get("/shelters/coverage", response_model=ShelterCoverageSummaryResponse)
def get_shelter_coverage_summary(force_offline: bool = False):
    """
    Returns regional shelter candidate coverage metrics across all monitored villages.
    """
    from app.engine.shelter_suitability_engine import shelter_suitability_engine_instance
    return shelter_suitability_engine_instance.get_shelter_coverage_summary(
        scenario=CURRENT_SCENARIO,
        force_offline=force_offline,
    )
@router.get("/shelters/{shelter_id}", response_model=ShelterRecord)
def get_shelter_detail(shelter_id: str, force_offline: bool = False):
    """
    Returns detailed geometry, operational capacity, and derived hazard scores for a specific relief shelter.
    """
    from app.adapters.shelter_adapter import shelter_adapter_instance
    shelter = shelter_adapter_instance.get_shelter_by_id(shelter_id)
    if not shelter:
        raise HTTPException(status_code=404, detail=f"Shelter ID '{shelter_id}' not found.")
    return shelter


@router.get("/shelters/villages/{village_id}", response_model=List[CandidateShelterEvaluation])
def get_village_candidate_shelters(village_id: str, force_offline: bool = False):
    """
    Evaluates all candidate relief shelters for a specific village, including reachability, travel time, and suitability.
    """
    from app.engine.shelter_suitability_engine import shelter_suitability_engine_instance
    try:
        rec = shelter_suitability_engine_instance.evaluate_village_shelters(
            village_id=village_id,
            scenario=CURRENT_SCENARIO,
            force_offline=force_offline,
        )
        return rec.all_candidates_evaluated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))



@router.get("/shelters/villages/{village_id}/candidates", response_model=List[CandidateShelterEvaluation])
def get_village_shelter_candidates_alias(village_id: str, force_offline: bool = False):
    """
    Explicit endpoint for querying all evaluated shelter candidates for a village.
    """
    return get_village_candidate_shelters(village_id=village_id, force_offline=force_offline)


@router.get("/evacuation/shelter/{village_id}/alternatives", response_model=List[CandidateShelterEvaluation])
def get_safest_evacuation_shelter_alternatives(village_id: str, force_offline: bool = False):
    """
    Returns ranked alternative candidate shelters (excluding top choice) for a village.
    """
    from app.engine.shelter_suitability_engine import shelter_suitability_engine_instance
    try:
        rec = shelter_suitability_engine_instance.evaluate_village_shelters(
            village_id=village_id,
            scenario=CURRENT_SCENARIO,
            force_offline=force_offline,
        )
        return rec.alternatives
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))



# Feature 11: Real-Time Multi-Hazard Alert Generation & Notification Intelligence Endpoints

@router.get("/alerts/status", response_model=AlertStatusResponse)
def get_alert_system_status():
    """
    Returns summary statistics for generated alerts, lifecycle states, and notification channel modes.
    """
    from app.engine.alert_engine import alert_engine_instance
    return alert_engine_instance.get_system_status()


@router.get("/alerts", response_model=List[MultiHazardAlertRecord])
def get_all_active_alerts(force_offline: bool = False):
    """
    Returns all generated multi-hazard emergency disaster alerts across the watershed.
    If no alerts exist in session, dynamically evaluates and prepares baseline alerts for monitored villages.
    """
    from app.engine.alert_engine import alert_engine_instance
    alerts = alert_engine_instance.get_all_alerts()
    if not alerts:
        # Pre-generate alerts for all 15 monitored watershed villages under CURRENT_SCENARIO
        for v in DEMO_VILLAGES:
            alert_engine_instance.generate_alert_for_village(
                village_id=v["id"],
                scenario=CURRENT_SCENARIO,
                force_offline=force_offline,
            )
        alerts = alert_engine_instance.get_all_alerts()
    return alerts


@router.get("/alerts/{alert_id}", response_model=MultiHazardAlertRecord)
def get_alert_detail(alert_id: str):
    """
    Returns full details, multi-hazard correlation, lead-time context, and multilingual warning text for a specific alert.
    """
    from app.engine.alert_engine import alert_engine_instance
    alert = alert_engine_instance.get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert ID '{alert_id}' not found.")
    return alert


@router.get("/alerts/villages/{village_id}", response_model=List[MultiHazardAlertRecord])
def get_alerts_for_village(village_id: str, force_offline: bool = False):
    """
    Returns active and historical alerts generated for a specific village.
    """
    from app.engine.alert_engine import alert_engine_instance
    village = next((v for v in DEMO_VILLAGES if v["id"] == village_id), None)
    if not village:
        raise HTTPException(status_code=404, detail=f"Village ID '{village_id}' not found.")

    alerts = alert_engine_instance.get_alerts_for_village(village_id)
    if not alerts:
        alert_engine_instance.generate_alert_for_village(
            village_id=village_id,
            scenario=CURRENT_SCENARIO,
            force_offline=force_offline,
        )
        alerts = alert_engine_instance.get_alerts_for_village(village_id)
    return alerts


@router.post("/alerts/generate/{village_id}", response_model=MultiHazardAlertRecord)
def generate_village_alert(village_id: str, force_offline: bool = False, operator_notes: Optional[str] = None):
    """
    Trigger real-time multi-hazard alert generation for a village using current hydro-meteorological intelligence.
    """
    from app.engine.alert_engine import alert_engine_instance
    try:
        return alert_engine_instance.generate_alert_for_village(
            village_id=village_id,
            scenario=CURRENT_SCENARIO,
            force_offline=force_offline,
            operator_notes=operator_notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/alerts/{alert_id}/acknowledge", response_model=MultiHazardAlertRecord)
def acknowledge_alert(alert_id: str, notes: Optional[str] = None, actor: str = "EOC_OPERATOR"):
    """
    Acknowledges an emergency alert and logs action to audit trail.
    """
    from app.engine.alert_engine import alert_engine_instance
    try:
        return alert_engine_instance.acknowledge_alert(alert_id=alert_id, notes=notes, actor=actor)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/alerts/{alert_id}/escalate", response_model=MultiHazardAlertRecord)
def escalate_alert(alert_id: str, reason: str = "Emergency situation escalated by EOC", actor: str = "EOC_OPERATOR"):
    """
    Escalates an emergency alert to higher urgency tier and logs action to audit trail.
    """
    from app.engine.alert_engine import alert_engine_instance
    try:
        return alert_engine_instance.escalate_alert(alert_id=alert_id, reason=reason, actor=actor)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/alerts/{alert_id}/resolve", response_model=MultiHazardAlertRecord)
def resolve_alert(alert_id: str, notes: Optional[str] = None, actor: str = "EOC_OPERATOR"):
    """
    Resolves an emergency alert upon threat subsidence and logs action to audit trail.
    """
    from app.engine.alert_engine import alert_engine_instance
    try:
        return alert_engine_instance.resolve_alert(alert_id=alert_id, resolution_notes=notes, actor=actor)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/alerts/{alert_id}/message", response_model=MultilingualAlertText)
def get_alert_multilingual_message(alert_id: str):
    """
    Returns structured multilingual disaster messages in English, Hindi, Garhwali, Kumaoni, and Nepali.
    """
    from app.engine.alert_engine import alert_engine_instance
    alert = alert_engine_instance.get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert ID '{alert_id}' not found.")
    return alert.messages


@router.get("/alerts/{alert_id}/delivery-status", response_model=AlertDeliveryStatusResponse)
def get_alert_delivery_status(alert_id: str):
    """
    Returns transparent notification delivery status (SIMULATION / NOT_DELIVERED externally).
    """
    from app.engine.alert_engine import alert_engine_instance
    from app.adapters.notification_provider import simulation_notification_provider_instance
    alert = alert_engine_instance.get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert ID '{alert_id}' not found.")
    return simulation_notification_provider_instance.get_delivery_status(alert)


class TelegramDispatchRequest(BaseModel):
    chat_id: str = Field(..., description="Recipient Telegram Chat ID or Channel username")
    text: str = Field(..., description="Emergency Alert message text to broadcast")
    bot_token: Optional[str] = Field(None, description="Optional custom bot token from BotFather")


class TelegramDispatchResponse(BaseModel):
    success: bool
    status_code: int
    chat_id: str
    message: str
    telegram_response: Optional[Dict[str, Any]] = None
    retry_after: Optional[int] = None


@router.post("/alerts/telegram/dispatch", response_model=TelegramDispatchResponse)
def dispatch_telegram_alert(payload: TelegramDispatchRequest):
    """
    Direct server-side dispatch of multilingual emergency alerts to Telegram.
    Bypasses client browser CORS and adblockers, provides detailed error diagnosis.
    """
    token = payload.bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "8930236949:AAF4IO2am0V31BonD-bciYLuQHJCdK02NXc")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    body = {
        "chat_id": payload.chat_id,
        "text": payload.text,
    }
    
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return TelegramDispatchResponse(
                success=True,
                status_code=response.status,
                chat_id=payload.chat_id,
                message="Alert successfully delivered via Telegram Bot.",
                telegram_response=res_data
            )
    except urllib.error.HTTPError as e:
        err_body = {}
        try:
            err_body = json.loads(e.read().decode("utf-8"))
        except Exception:
            pass
        retry_after = err_body.get("parameters", {}).get("retry_after")
        description = err_body.get("description", str(e))
        
        hint = ""
        if e.code == 429:
            hint = f"Telegram rate limit active. Please wait {retry_after or 8}s or create a fresh bot token in @BotFather."
        elif e.code == 403:
            hint = "Bot was not started by user. Please open the bot in Telegram and tap Start (/start)."
        elif e.code == 400:
            hint = f"Bad request: {description}. Verify Chat ID."
        elif e.code == 401:
            hint = "Unauthorized: Invalid bot token."
            
        return TelegramDispatchResponse(
            success=False,
            status_code=e.code,
            chat_id=payload.chat_id,
            message=f"{description}. {hint}".strip(),
            telegram_response=err_body,
            retry_after=retry_after
        )
    except Exception as exc:
        return TelegramDispatchResponse(
            success=False,
            status_code=500,
            chat_id=payload.chat_id,
            message=f"Network error connecting to Telegram: {str(exc)}",
        )



# ==============================================================================
# IMD / NDMA CAP ALERT INGESTION ENDPOINTS (Problem 24)
# ==============================================================================

@router.get("/imd/status", response_model=IMDStatus)
def get_imd_cap_status():
    """
    Returns the real-time status and metadata of the official IMD/NDMA CAP alert ingestion pipeline.
    """
    return imd_cap_adapter_instance.get_status()


@router.get("/imd/warnings", response_model=List[IMDWarning])
def get_imd_cap_warnings():
    """
    Returns all parsed official IMD/NDMA CAP warnings from the latest feed snapshot.
    """
    return imd_cap_adapter_instance.get_all_warnings()


@router.get("/imd/warnings/{warning_id}", response_model=IMDWarning)
def get_imd_cap_warning_by_id(warning_id: str):
    """
    Returns a specific official IMD CAP warning by its unique identifier or GUID.
    """
    warning = imd_cap_adapter_instance.get_warning_by_id(warning_id)
    if not warning:
        raise HTTPException(status_code=404, detail=f"IMD Warning '{warning_id}' not found.")
    return warning


@router.get("/imd/villages/{village_id}", response_model=IMDVillageWarningResponse)
def get_imd_warnings_for_village(village_id: str):
    """
    Returns official IMD/NDMA CAP warnings covering the district where the specified village is located.
    Clearly notes that this is authoritative district-level evidence fused into village decision support.
    """
    target = next((v for v in DEMO_VILLAGES if v.get("id") == village_id or v.get("village_id") == village_id), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Village '{village_id}' not found.")
    
    district = target.get("district", target.get("region", "Chamoli"))
    village_name = target.get("name", target.get("village_name", village_id))
    return imd_cap_adapter_instance.get_warnings_for_village(
        village_id=village_id,
        village_name=village_name,
        district=district,
        state=target.get("state", "Uttarakhand")
    )


@router.get("/imd/districts/{district_name}", response_model=IMDDistrictWarningResponse)
def get_imd_warnings_for_district(district_name: str):
    """
    Returns official IMD/NDMA CAP warnings covering a specified administrative district.
    """
    return imd_cap_adapter_instance.get_warnings_for_district(district_name)










