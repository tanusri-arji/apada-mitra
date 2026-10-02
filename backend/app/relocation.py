"""
Relocation Planning Module
Calculates long-term relocation priority based on current risk, exposure, and evacuation priority.
"""

THRESHOLD_HIGH_RISK = 70.0
THRESHOLD_HIGH_EXPOSURE = 500
THRESHOLD_MODERATE_RISK = 40.0
THRESHOLD_MODERATE_EXPOSURE = 200
THRESHOLD_HIGH_PRIORITY = 60.0

def calculate_relocation_priority(
    risk_score: float,
    exposed_population: int,
    evacuation_priority_score: float
) -> str:
    """
    Returns one of: "Immediate", "Short-term", "Medium-term" based on existing metrics.
    """
    if (risk_score >= THRESHOLD_HIGH_RISK or evacuation_priority_score >= THRESHOLD_HIGH_PRIORITY) and exposed_population >= THRESHOLD_HIGH_EXPOSURE:
        return "Immediate"
    elif risk_score >= THRESHOLD_MODERATE_RISK or exposed_population >= THRESHOLD_MODERATE_EXPOSURE:
        return "Short-term"
    return "Medium-term"
