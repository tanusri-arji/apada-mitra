"""
Landslide Susceptibility Risk Engine for APADA MITRA.
Calculates terrain-aware landslide risk using slope, rainfall, soil saturation, elevation and geology features.
"""
from typing import Dict, Any, List
from app.models.domain import LandslideRiskDetail, RiskLevel, FactorContribution, DataQualityStatus
from app.engine.risk_engine import classify_risk_level, normalize_feature

LANDSLIDE_WEIGHTS: Dict[str, float] = {
    "slope": 0.35,              # Slope steepness is primary physical driver of landsliding
    "soil_saturation": 0.25,    # Pore water pressure from saturation
    "current_rainfall": 0.20,   # Trigger rainfall rate
    "forecast_rainfall": 0.15,  # Cumulative 24h forecast
    "river_water_level": 0.05,  # Toe erosion by swelling river streams
}

LANDSLIDE_METADATA: Dict[str, Dict[str, str]] = {
    "slope": {"label": "Terrain Slope Angle", "unit": "deg"},
    "soil_saturation": {"label": "Soil Moisture Saturation", "unit": "%"},
    "current_rainfall": {"label": "Trigger Rainfall Rate", "unit": "mm/h"},
    "forecast_rainfall": {"label": "24h Forecast Rainfall", "unit": "mm"},
    "river_water_level": {"label": "Stream Toe Erosion Factor", "unit": "x depth"},
}


def calculate_landslide_risk(
    village_id: str,
    village_name: str,
    feature_snapshot: Dict[str, Any],
) -> LandslideRiskDetail:
    """
    Computes terrain-aware landslide risk score (0-100), classification, and XAI contributions.
    """
    weighted_sum = 0.0
    missing_weights = 0.0
    contributions: List[FactorContribution] = []

    for feature_key, weight in LANDSLIDE_WEIGHTS.items():
        raw_val = feature_snapshot.get(feature_key)
        status = feature_snapshot.get("feature_statuses", {}).get(feature_key, DataQualityStatus.OK)

        if raw_val is None or status == DataQualityStatus.MISSING:
            missing_weights += weight
            norm_val = 0.3
            raw_val_num = 0.0
        else:
            raw_val_num = float(raw_val)
            norm_val = normalize_feature(feature_key, raw_val_num)

        pts = round(norm_val * weight * 100.0, 2)
        weighted_sum += norm_val * weight

        meta = LANDSLIDE_METADATA.get(feature_key, {"label": feature_key, "unit": ""})
        contributions.append(
            FactorContribution(
                feature_key=feature_key,
                feature_label=meta["label"],
                raw_value=round(raw_val_num, 2),
                unit=meta["unit"],
                normalized_value=round(norm_val, 3),
                weight=weight,
                contribution_points=pts,
                contribution_percent=0.0,  # Will update after total sum
            )
        )

    score = round(min(100.0, max(0.0, weighted_sum * 100.0)), 2)
    confidence = round(min(100.0, max(10.0, 95.0 - missing_weights * 80.0)), 1)
    risk_level = classify_risk_level(score)

    for c in contributions:
        if score > 0:
            c.contribution_percent = round((c.contribution_points / score) * 100.0, 1)

    contributions.sort(key=lambda x: x.contribution_points, reverse=True)

    # Supplementary historical evidence context
    hist_evidence = feature_snapshot.get("historical_landslide_evidence")
    hist_within_15km = feature_snapshot.get("historical_landslides_within_15km")
    hist_nearest_km = feature_snapshot.get("nearest_historical_landslide_km")

    if hist_evidence is None:
        try:
            from app.engine.landslide_inventory import historical_landslide_service
            summary = historical_landslide_service.get_village_historical_summary({
                "id": village_id,
                "name": village_name,
                "latitude": feature_snapshot.get("latitude", 30.43),
                "longitude": feature_snapshot.get("longitude", 79.43),
            })
            hist_evidence = summary.historical_susceptibility_evidence
            hist_within_15km = summary.events_within_15km
            hist_nearest_km = summary.nearest_event_distance_km
        except Exception:
            pass

    return LandslideRiskDetail(
        village_id=village_id,
        village_name=village_name,
        landslide_risk_score=score,
        risk_level=risk_level,
        confidence=confidence,
        contributing_factors=contributions,
        historical_landslide_evidence=hist_evidence,
        historical_landslides_within_15km=hist_within_15km,
        nearest_historical_landslide_km=hist_nearest_km,
    )
