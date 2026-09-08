"""
Village Exposure and Vulnerability Engine for APADA MITRA (Feature 7).
Calculates human population exposure, multi-hazard footprint analysis, and critical infrastructure risk scores.
Integrates authoritative Census of India 2011 demographics with transparent hazard-specific exposure breakdowns.
"""
from typing import Dict, List, Optional, Any
from app.models.domain import ExposureMetrics, InfrastructureExposure, RiskLevel, ScenarioType
from app.models.population import (
    VillagePopulationRecord,
    VillageExposureDetail,
    HazardExposureBreakdown,
    PopulationDataState,
    ExposureCalculationMethod,
)
from app.data.census_population_data import get_village_census_population, get_all_census_population_records
from app.data.dataset import DEMO_VILLAGES, get_village_feature_snapshot
from app.engine.risk_engine import calculate_flash_flood_risk
from app.engine.landslide_engine import calculate_landslide_risk


def calculate_village_exposure(
    population: int,
    infra_dict: Dict[str, int],
    risk_level: RiskLevel,
    risk_probability: float,
) -> ExposureMetrics:
    """
    Legacy exposure calculation function preserved for backwards compatibility with existing pipelines.
    Calculates population exposure and composite exposure index (0-100).
    """
    infra = InfrastructureExposure(**infra_dict)

    # Exposed population multiplier depends on risk probability
    # Higher risk probability -> higher fraction of village population directly in inundation footprint
    if risk_level == RiskLevel.CRITICAL:
        exposure_fraction = 0.75 + 0.20 * risk_probability
    elif risk_level == RiskLevel.HIGH:
        exposure_fraction = 0.50 + 0.20 * risk_probability
    elif risk_level == RiskLevel.MODERATE:
        exposure_fraction = 0.25 + 0.15 * risk_probability
    else:
        exposure_fraction = 0.05 + 0.10 * risk_probability

    population_exposed = int(round(population * min(1.0, exposure_fraction)))

    # Compute composite exposure score (0 - 100)
    # Population factor: max 50 points (5000 pop = 50 pts)
    pop_pts = min(50.0, (population / 5000.0) * 50.0)

    # Infrastructure factor: max 50 points
    # Critical bridges (10 pts each), health facilities (8 pts each), schools (4 pts each)
    infra_pts = min(
        50.0,
        (infra.bridges_and_roads * 10.0)
        + (infra.health_facilities * 8.0)
        + (infra.schools * 4.0)
    )

    exposure_score = round(min(100.0, pop_pts + infra_pts), 1)

    return ExposureMetrics(
        population_exposed=population_exposed,
        exposure_score=exposure_score,
        infrastructure=infra,
    )


def calculate_village_exposure_detail(
    village_id: str,
    scenario: ScenarioType = ScenarioType.NORMAL,
) -> Optional[VillageExposureDetail]:
    """
    Feature 7: Comprehensive Multi-Hazard Population Exposure Assessment.
    Separates authoritative Census 2011 population data from dynamic hazard exposure calculations.
    """
    # 1. Locate village dataset
    v_data = next((v for v in DEMO_VILLAGES if v["id"] == village_id), None)
    if not v_data:
        return None

    # 2. Retrieve authoritative census demographic record
    census_rec = get_village_census_population(village_id)
    if census_rec:
        total_population = census_rec.population
        households = census_rec.households
        vulnerable_pop = census_rec.vulnerable_population or int(round(total_population * 0.165))
        data_state = census_rec.data_state
        confidence = census_rec.confidence
        source_name = census_rec.source
        source_url = census_rec.source_url
        source_year = census_rec.source_year
        geo_level = census_rec.geographic_level
        census_assumptions = list(census_rec.assumptions)
    else:
        # Fallback to dataset baseline
        total_population = v_data.get("population", 1000)
        households = int(round(total_population / 4.5))
        vulnerable_pop = int(round(total_population * 0.165))
        data_state = PopulationDataState.OFFLINE_DEMO
        confidence = 50.0
        source_name = "APADA MITRA Offline Demo Dataset"
        source_url = "https://apada-mitra.local/data/demo"
        source_year = 2024
        geo_level = "SYNTHETIC_BENCHMARK"
        census_assumptions = ["Census record not found; running on offline demo baseline."]

    # 3. Compute Risk Metrics via existing engines
    snapshot = get_village_feature_snapshot(v_data["id"], scenario)
    flood_res = calculate_flash_flood_risk(snapshot)
    ls_res = calculate_landslide_risk(v_data["id"], v_data["name"], snapshot)

    f_score = float(flood_res.get("flash_flood_risk_score", 0.0))
    f_level = flood_res.get("risk_level", RiskLevel.LOW)
    f_level_val = f_level.value if hasattr(f_level, "value") else str(f_level)

    l_score = float(ls_res.landslide_risk_score)
    l_level_val = ls_res.risk_level.value if hasattr(ls_res.risk_level, "value") else str(ls_res.risk_level)

    # 4. Calculate Flood Hazard Exposure Fraction
    if f_level_val == "CRITICAL":
        f_fraction = min(1.0, 0.45 + 0.35 * (f_score / 100.0))
    elif f_level_val == "HIGH":
        f_fraction = min(1.0, 0.25 + 0.25 * (f_score / 100.0))
    elif f_level_val == "MODERATE":
        f_fraction = min(1.0, 0.10 + 0.15 * (f_score / 100.0))
    else:
        f_fraction = min(1.0, 0.02 + 0.08 * (f_score / 100.0))

    f_exposed = min(total_population, int(round(total_population * f_fraction)))
    f_vuln = min(vulnerable_pop, int(round(vulnerable_pop * f_fraction)))

    flood_breakdown = HazardExposureBreakdown(
        hazard_type="FLASH_FLOOD",
        risk_score=round(f_score, 2),
        risk_level=f_level_val,
        exposed_population=f_exposed,
        exposure_fraction=round(f_fraction, 4),
        vulnerable_exposed=f_vuln,
    )

    # 5. Calculate Landslide Hazard Exposure Fraction
    if l_level_val == "CRITICAL":
        l_fraction = min(1.0, 0.40 + 0.30 * (l_score / 100.0))
    elif l_level_val == "HIGH":
        l_fraction = min(1.0, 0.20 + 0.20 * (l_score / 100.0))
    elif l_level_val == "MODERATE":
        l_fraction = min(1.0, 0.08 + 0.12 * (l_score / 100.0))
    else:
        l_fraction = min(1.0, 0.01 + 0.05 * (l_score / 100.0))

    l_exposed = min(total_population, int(round(total_population * l_fraction)))
    l_vuln = min(vulnerable_pop, int(round(vulnerable_pop * l_fraction)))

    landslide_breakdown = HazardExposureBreakdown(
        hazard_type="LANDSLIDE",
        risk_score=round(l_score, 2),
        risk_level=l_level_val,
        exposed_population=l_exposed,
        exposure_fraction=round(l_fraction, 4),
        vulnerable_exposed=l_vuln,
    )

    # 6. Multi-Hazard Non-Overlapping Spatial Exposure Union
    combined_fraction = 1.0 - ((1.0 - f_fraction) * (1.0 - l_fraction))
    total_exposed = min(
        total_population,
        max(f_exposed, l_exposed, int(round(total_population * combined_fraction)))
    )
    vulnerable_total_exposed = min(
        vulnerable_pop,
        max(f_vuln, l_vuln, int(round(vulnerable_pop * combined_fraction)))
    )
    exposure_percentage = round((total_exposed / total_population) * 100.0, 2) if total_population > 0 else 0.0

    # 7. Infrastructure Exposure
    infra_raw = v_data.get("infrastructure", {})
    infra_exposed = {
        "schools": infra_raw.get("schools", 0),
        "health_facilities": infra_raw.get("health_facilities", 0),
        "bridges_and_roads": infra_raw.get("bridges_and_roads", 0),
        "critical_structures_count": infra_raw.get("critical_structures_count", 0),
    }

    # 8. Composite Exposure Score (0-100)
    pop_pts = min(50.0, (total_population / 5000.0) * 50.0)
    infra_pts = min(
        50.0,
        (infra_exposed["bridges_and_roads"] * 10.0)
        + (infra_exposed["health_facilities"] * 8.0)
        + (infra_exposed["schools"] * 4.0)
    )
    composite_exposure_score = round(min(100.0, pop_pts + infra_pts), 1)

    # 9. Overall dominant hazard level
    overall_hazard_score = max(f_score, l_score)
    overall_hazard_level = f_level_val if f_score >= l_score else l_level_val

    # 10. Assumptions & Methodology Notes
    assumptions_list = census_assumptions + [
        f"Multi-hazard spatial union model combined flood fraction ({round(f_fraction*100, 1)}%) and landslide fraction ({round(l_fraction*100, 1)}%).",
        f"Total estimated exposed headcount: {total_exposed:,} of {total_population:,} residents ({exposure_percentage}%).",
        "DISCLAIMER: Population exposure is derived from Census 2011 Primary Census Abstract and hazard risk envelope modeling. It represents disaster decision support, not physical parcel-level building survey GIS."
    ]

    source_provenance = {
        "source": source_name,
        "source_url": source_url,
        "source_year": source_year,
        "geographic_level": geo_level,
        "census_2011_code": census_rec.census_2011_code if census_rec else None,
        "data_state": data_state.value,
        "confidence": confidence,
    }

    return VillageExposureDetail(
        village_id=village_id,
        village_name=v_data.get("name", village_id),
        district=v_data.get("district", "Chamoli"),
        sub_district_or_block=v_data.get("block", "Dasholi"),
        total_population=total_population,
        households=households,
        vulnerable_population=vulnerable_pop,
        exposed_population=total_exposed,
        vulnerable_exposed=vulnerable_total_exposed,
        exposure_percentage=exposure_percentage,
        overall_hazard_level=overall_hazard_level,
        overall_hazard_score=round(overall_hazard_score, 2),
        flood_exposure=flood_breakdown,
        landslide_exposure=landslide_breakdown,
        infrastructure_exposed=infra_exposed,
        composite_exposure_score=composite_exposure_score,
        calculation_method=ExposureCalculationMethod.MULTI_HAZARD_SPATIAL_INTERSECTION,
        data_state=data_state,
        confidence=confidence,
        source_provenance=source_provenance,
        assumptions=assumptions_list,
    )


def calculate_all_villages_exposure_detail(
    scenario: ScenarioType = ScenarioType.NORMAL,
) -> List[VillageExposureDetail]:
    """Calculates detailed multi-hazard exposure for all monitored villages."""
    results = []
    for v in DEMO_VILLAGES:
        detail = calculate_village_exposure_detail(v["id"], scenario=scenario)
        if detail:
            results.append(detail)
    return results
