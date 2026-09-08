"""
Evacuation Priority Engine for APADA MITRA.
Calculates multi-hazard evacuation priority index (0-100) and urgency ranking across watershed villages.
Calculates exact weighted contributions for Flash Flood, Landslide, Exposed Population, and Critical Infrastructure.
"""
from typing import List, Dict, Any
from app.models.domain import EvacuationPriority, RiskLevel, VillageRiskDetail, LandslideRiskDetail
from app.engine.risk_engine import classify_risk_level


def calculate_evacuation_priorities(
    villages_flood: List[VillageRiskDetail],
    villages_landslide: Dict[str, LandslideRiskDetail],
) -> List[EvacuationPriority]:
    """
    Computes transparent multi-hazard evacuation priority index (0-100) and numerical urgency ranks for all villages.
    """
    priorities: List[EvacuationPriority] = []

    for f_detail in villages_flood:
        vid = f_detail.village_id
        ls_detail = villages_landslide.get(vid)
        ls_score = ls_detail.landslide_risk_score if ls_detail else 0.0

        pop_exp = f_detail.exposure.population_exposed
        infra_count = f_detail.exposure.infrastructure.critical_structures_count

        # Factor weighted point contributions
        # Weights: Flood Risk (35%), Landslide Risk (25%), Exposed Population Density (25%), Critical Infra (15%)
        flood_pts = round(f_detail.flash_flood_risk_score * 0.35, 2)
        landslide_pts = round(ls_score * 0.25, 2)
        
        pop_norm = min(1.0, pop_exp / 3500.0)
        pop_pts = round(pop_norm * 100.0 * 0.25, 2)

        infra_norm = min(1.0, infra_count / 10.0)
        infra_pts = round(infra_norm * 100.0 * 0.15, 2)

        # Total Evacuation Priority Score (0.0 - 100.0)
        priority_score = round(
            min(
                100.0,
                max(0.0, flood_pts + landslide_pts + pop_pts + infra_pts),
            ),
            2,
        )

        priority_level = classify_risk_level(priority_score)

        # Factor breakdown summary text for transparency
        summary_str = (
            f"Flood: +{flood_pts} pts | Landslide: +{landslide_pts} pts | "
            f"Exposed Pop ({pop_exp:,}): +{pop_pts} pts | Infra ({infra_count} assets): +{infra_pts} pts"
        )

        # Formulate top urgency drivers for all 15 villages
        contrib_list = [
            ("Flood Risk", flood_pts, f"{round(f_detail.flash_flood_risk_score)}%"),
            ("Landslide Threat", landslide_pts, f"{round(ls_score)}%"),
            ("Exposed Population", pop_pts, f"{pop_exp:,} residents"),
            ("Critical Infrastructure", infra_pts, f"{infra_count} assets"),
        ]
        # Sort factors by point contribution descending
        contrib_list.sort(key=lambda x: x[1], reverse=True)

        top1, top2 = contrib_list[0], contrib_list[1]
        primary_reason = f"Top Drivers: {top1[0]} ({top1[2]} / +{top1[1]} pts) & {top2[0]} ({top2[2]} / +{top2[1]} pts)"

        priorities.append(
            EvacuationPriority(
                village_id=vid,
                village_name=f_detail.village_name,
                evacuation_priority_score=priority_score,
                priority_level=priority_level,
                rank=1,  # Placeholder, will rank below
                flash_flood_risk_score=f_detail.flash_flood_risk_score,
                landslide_risk_score=ls_score,
                population_exposed=pop_exp,
                critical_infrastructure_count=infra_count,
                flood_contribution_pts=flood_pts,
                landslide_contribution_pts=landslide_pts,
                population_contribution_pts=pop_pts,
                infrastructure_contribution_pts=infra_pts,
                factor_breakdown_summary=summary_str,
                primary_urgency_reason=primary_reason,
            )
        )

    # Sort descending by evacuation_priority_score to assign 1-based ranks (#1 to #15)
    priorities.sort(key=lambda p: p.evacuation_priority_score, reverse=True)
    for rank_idx, p in enumerate(priorities, start=1):
        p.rank = rank_idx

    return priorities
