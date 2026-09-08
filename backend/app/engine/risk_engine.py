"""
Flash Flood Risk Engine.
Implements terrain-aware probabilistic feature normalization, weighted scoring, missing feature resilience,
confidence degradation, and risk classification.
"""
from typing import Dict, Any, List, Tuple
from app.config import (
    FEATURE_WEIGHTS,
    FEATURE_BOUNDS,
    RISK_LEVEL_THRESHOLDS,
    MISSING_FEATURE_PENALTY_MULTIPLIER,
    BASE_CONFIDENCE,
)
from app.models.domain import RiskLevel, DecisionStatus, DataQualityStatus


def normalize_feature(feature_key: str, raw_value: float) -> float:
    """Normalizes a raw feature value to [0.0, 1.0] range based on domain bounds."""
    max_bound = FEATURE_BOUNDS.get(feature_key, 100.0)
    if feature_key == "river_water_level":
        # Water level factor starts at 1.0 (normal). Range [1.0, 3.0] mapped to [0.0, 1.0]
        norm = max(0.0, (raw_value - 1.0) / (max_bound - 1.0))
        return min(1.0, norm)
    
    norm = max(0.0, raw_value / max_bound)
    return min(1.0, norm)


def classify_risk_level(risk_score: float) -> RiskLevel:
    """Classifies risk score (0-100) into RiskLevel enum."""
    if risk_score >= 75.0:
        return RiskLevel.CRITICAL
    elif risk_score >= 50.0:
        return RiskLevel.HIGH
    elif risk_score >= 25.0:
        return RiskLevel.MODERATE
    else:
        return RiskLevel.LOW


def determine_decision_status(risk_level: RiskLevel, exposure_score: float) -> DecisionStatus:
    """Derives decision support recommendation based on risk level and population exposure."""
    if risk_level == RiskLevel.CRITICAL:
        return DecisionStatus.EVACUATION_READINESS
    elif risk_level == RiskLevel.HIGH:
        return DecisionStatus.EVACUATION_READINESS if exposure_score > 60.0 else DecisionStatus.PREPARE
    elif risk_level == RiskLevel.MODERATE:
        return DecisionStatus.PREPARE
    else:
        return DecisionStatus.MONITOR


def calculate_flash_flood_risk(feature_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes flash flood risk score, probability, confidence, missing features, and factor normalized values.
    
    Returns:
        Dict containing:
        - flash_flood_risk_score (0.0 - 100.0)
        - risk_probability (0.0 - 1.0)
        - confidence (0.0 - 100.0)
        - risk_level (RiskLevel)
        - missing_features (List[str])
        - normalized_features (Dict[str, float])
        - raw_features (Dict[str, float])
    """
    missing_features: List[str] = []
    normalized_features: Dict[str, float] = {}
    raw_features: Dict[str, float] = {}

    total_weight = sum(FEATURE_WEIGHTS.values())
    weighted_score_sum = 0.0
    missing_weight_sum = 0.0

    for feature_key, weight in FEATURE_WEIGHTS.items():
        raw_val = feature_snapshot.get(feature_key)
        status = feature_snapshot.get("feature_statuses", {}).get(feature_key, DataQualityStatus.OK)

        if raw_val is None or status == DataQualityStatus.MISSING:
            missing_features.append(feature_key)
            missing_weight_sum += weight
            # Fallback neutral normalized value (0.3) so missing data does not collapse risk score to zero
            norm_val = 0.3
            raw_features[feature_key] = 0.0
        else:
            raw_features[feature_key] = float(raw_val)
            norm_val = normalize_feature(feature_key, float(raw_val))

        normalized_features[feature_key] = norm_val
        weighted_score_sum += norm_val * weight

    # Final Risk Score (0.0 - 100.0)
    risk_score = round(min(100.0, max(0.0, weighted_score_sum * 100.0)), 2)

    # Risk Probability (0.0 - 1.0)
    risk_prob = round(min(1.0, max(0.0, risk_score / 100.0)), 4)

    # Confidence calculation: Start from BASE_CONFIDENCE, penalize for missing weight proportion
    confidence_penalty = missing_weight_sum * MISSING_FEATURE_PENALTY_MULTIPLIER
    confidence = round(min(100.0, max(10.0, BASE_CONFIDENCE - confidence_penalty)), 1)

    risk_level = classify_risk_level(risk_score)

    return {
        "flash_flood_risk_score": risk_score,
        "risk_probability": risk_prob,
        "confidence": confidence,
        "risk_level": risk_level,
        "missing_features": missing_features,
        "normalized_features": normalized_features,
        "raw_features": raw_features,
    }
