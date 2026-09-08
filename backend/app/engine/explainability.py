"""
Explainability (XAI) Engine for APADA MITRA.
Calculates deterministic factor breakdowns and point/percentage contributions for risk score features.
"""
from typing import List, Dict, Any
from app.config import FEATURE_WEIGHTS
from app.models.domain import FactorContribution

FEATURE_METADATA: Dict[str, Dict[str, str]] = {
    "current_rainfall": {"label": "Current Rainfall Rate", "unit": "mm/h"},
    "forecast_rainfall": {"label": "Forecast 24h Rainfall", "unit": "mm"},
    "soil_saturation": {"label": "Soil Saturation Level", "unit": "%"},
    "river_water_level": {"label": "River Water Stage Factor", "unit": "x depth"},
    "flow_accumulation": {"label": "Flow Accumulation Index", "unit": "log index"},
    "slope": {"label": "Terrain Slope Steepness", "unit": "deg"},
}


def calculate_explainability_factors(
    raw_features: Dict[str, float],
    normalized_features: Dict[str, float],
    total_risk_score: float,
) -> List[FactorContribution]:
    """
    Derives structured explainability factor contributions for a risk score calculation.
    """
    factors: List[FactorContribution] = []

    for feature_key, weight in FEATURE_WEIGHTS.items():
        norm_val = normalized_features.get(feature_key, 0.0)
        raw_val = raw_features.get(feature_key, 0.0)
        meta = FEATURE_METADATA.get(feature_key, {"label": feature_key, "unit": ""})

        # Contribution points out of 100 max possible score
        contrib_pts = round(norm_val * weight * 100.0, 2)

        # Contribution percentage of current total risk score
        if total_risk_score > 0:
            contrib_pct = round((contrib_pts / total_risk_score) * 100.0, 1)
        else:
            contrib_pct = 0.0

        factors.append(
            FactorContribution(
                feature_key=feature_key,
                feature_label=meta["label"],
                raw_value=round(raw_val, 2),
                unit=meta["unit"],
                normalized_value=round(norm_val, 3),
                weight=weight,
                contribution_points=contrib_pts,
                contribution_percent=contrib_pct,
            )
        )

    # Sort factors by contribution points descending so highest impact features appear first
    factors.sort(key=lambda f: f.contribution_points, reverse=True)
    return factors
