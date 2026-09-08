"""
System configuration for APADA MITRA risk engine and backend services.
"""
from typing import Dict, Tuple

# Feature weights for flash flood risk calculation (sum to 1.0)
FEATURE_WEIGHTS: Dict[str, float] = {
    "current_rainfall": 0.25,        # Current hourly rainfall rate (mm/h)
    "forecast_rainfall": 0.20,       # 24h cumulative forecast rainfall (mm)
    "soil_saturation": 0.15,         # Soil saturation level (%)
    "river_water_level": 0.15,       # River stage / water level multiplier factor (1.0 - 3.0)
    "flow_accumulation": 0.15,       # Hydrological flow accumulation index (log scale 0 - 5)
    "slope": 0.10,                    # Terrain slope steepness (degrees 0 - 45)
}

# Normalization maximum bounds for feature normalization N(x) = min(1.0, val / max_val)
FEATURE_BOUNDS: Dict[str, float] = {
    "current_rainfall": 100.0,       # 100 mm/h is extreme cloudburst
    "forecast_rainfall": 250.0,      # 250 mm 24h forecast
    "soil_saturation": 100.0,        # 100% saturation
    "river_water_level": 3.0,        # 3.0x normal river depth
    "flow_accumulation": 5.0,        # 5.0 log10 units
    "slope": 45.0,                   # 45 degrees slope
}

# Risk Level Classification Thresholds
# Score bounds: [min, max]
RISK_LEVEL_THRESHOLDS: Dict[str, Tuple[float, float]] = {
    "LOW": (0.0, 24.99),
    "MODERATE": (25.0, 49.99),
    "HIGH": (50.0, 74.99),
    "CRITICAL": (75.0, 100.0),
}

# Missing feature confidence penalty per feature weight
MISSING_FEATURE_PENALTY_MULTIPLIER: float = 80.0

# Base system confidence when all features are valid
BASE_CONFIDENCE: float = 95.0
