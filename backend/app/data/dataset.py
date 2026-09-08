"""
Deterministic Multi-Source Demo Dataset for APADA MITRA.
Contains 15 villages in the Alaknanda & Mandakini River valleys (Himalayan Hilly Region).
Clearly labelled as DEMO / SYNTHETIC DATA.
"""
from typing import Dict, List, Any
from app.models.domain import ScenarioType, DataQualityStatus

# Labeling flag for data origin
DATA_ORIGIN_LABEL = "DEMO SCENARIO - SYNTHETIC DATA"

DEMO_VILLAGES: List[Dict[str, Any]] = [
    {
        "id": "VIL-001",
        "name": "Pipalkoti",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "block": "Dasholi",
        "latitude": 30.4300,
        "longitude": 79.4300,
        "population": 2411,
        "elevation": 1260.0,  # meters
        "slope": 28.5,         # degrees
        "flow_accumulation": 4.2,  # log scale
        "drainage_proximity_m": 85.0,
        "road_accessibility_score": 75.0,
        "infrastructure": {
            "schools": 3,
            "health_facilities": 1,
            "bridges_and_roads": 2,
            "critical_structures_count": 6
        }
    },
    {
        "id": "VIL-002",
        "name": "Helang",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "block": "Joshi Math",
        "latitude": 30.5200,
        "longitude": 79.5100,
        "population": 1814,
        "elevation": 1540.0,
        "slope": 34.0,
        "flow_accumulation": 4.6,
        "drainage_proximity_m": 45.0,
        "road_accessibility_score": 60.0,
        "infrastructure": {
            "schools": 2,
            "health_facilities": 1,
            "bridges_and_roads": 3,
            "critical_structures_count": 6
        }
    },
    {
        "id": "VIL-003",
        "name": "Govindghat",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "block": "Joshi Math",
        "latitude": 30.6200,
        "longitude": 79.5600,
        "population": 1237,
        "elevation": 1820.0,
        "slope": 36.5,
        "flow_accumulation": 4.8,
        "drainage_proximity_m": 30.0,
        "road_accessibility_score": 45.0,
        "infrastructure": {
            "schools": 1,
            "health_facilities": 1,
            "bridges_and_roads": 2,
            "critical_structures_count": 4
        }
    },
    {
        "id": "VIL-004",
        "name": "Badrinath Base Valley",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "block": "Joshi Math",
        "latitude": 30.7400,
        "longitude": 79.4900,
        "population": 2438,
        "elevation": 3100.0,
        "slope": 22.0,
        "flow_accumulation": 3.9,
        "drainage_proximity_m": 120.0,
        "road_accessibility_score": 50.0,
        "infrastructure": {
            "schools": 2,
            "health_facilities": 2,
            "bridges_and_roads": 4,
            "critical_structures_count": 8
        }
    },
    {
        "id": "VIL-005",
        "name": "Karnaprayag Reach",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "block": "Karnaprayag",
        "latitude": 30.2600,
        "longitude": 79.2200,
        "population": 4180,
        "elevation": 860.0,
        "slope": 18.0,
        "flow_accumulation": 4.5,
        "drainage_proximity_m": 65.0,
        "road_accessibility_score": 90.0,
        "infrastructure": {
            "schools": 5,
            "health_facilities": 2,
            "bridges_and_roads": 3,
            "critical_structures_count": 10
        }
    },
    {
        "id": "VIL-006",
        "name": "Nandaprayag Basin",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "block": "Nandaprayag",
        "latitude": 30.3300,
        "longitude": 79.3200,
        "population": 1641,
        "elevation": 910.0,
        "slope": 21.0,
        "flow_accumulation": 4.1,
        "drainage_proximity_m": 90.0,
        "road_accessibility_score": 80.0,
        "infrastructure": {
            "schools": 3,
            "health_facilities": 1,
            "bridges_and_roads": 2,
            "critical_structures_count": 6
        }
    },
    {
        "id": "VIL-007",
        "name": "Rudraprayag Sangam",
        "district": "Rudraprayag",
        "state": "Uttarakhand",
        "block": "Rudraprayag",
        "latitude": 30.2850,
        "longitude": 78.9800,
        "population": 5680,
        "elevation": 895.0,
        "slope": 19.5,
        "flow_accumulation": 4.7,
        "drainage_proximity_m": 40.0,
        "road_accessibility_score": 85.0,
        "infrastructure": {
            "schools": 6,
            "health_facilities": 3,
            "bridges_and_roads": 4,
            "critical_structures_count": 13
        }
    },
    {
        "id": "VIL-008",
        "name": "Tilwara Valley",
        "district": "Rudraprayag",
        "state": "Uttarakhand",
        "block": "Augustmuni",
        "latitude": 30.3500,
        "longitude": 79.0300,
        "population": 1580,
        "elevation": 980.0,
        "slope": 16.0,
        "flow_accumulation": 3.8,
        "drainage_proximity_m": 150.0,
        "road_accessibility_score": 85.0,
        "infrastructure": {
            "schools": 2,
            "health_facilities": 1,
            "bridges_and_roads": 1,
            "critical_structures_count": 4
        }
    },
    {
        "id": "VIL-009",
        "name": "Augustmuni Stream",
        "district": "Rudraprayag",
        "state": "Uttarakhand",
        "block": "Augustmuni",
        "latitude": 30.3900,
        "longitude": 79.0800,
        "population": 2870,
        "elevation": 1020.0,
        "slope": 24.0,
        "flow_accumulation": 4.4,
        "drainage_proximity_m": 55.0,
        "road_accessibility_score": 75.0,
        "infrastructure": {
            "schools": 4,
            "health_facilities": 1,
            "bridges_and_roads": 2,
            "critical_structures_count": 7
        }
    },
    {
        "id": "VIL-010",
        "name": "Guptkashi Slope",
        "district": "Rudraprayag",
        "state": "Uttarakhand",
        "block": "Ukhimath",
        "latitude": 30.5250,
        "longitude": 79.0800,
        "population": 2080,
        "elevation": 1320.0,
        "slope": 31.0,
        "flow_accumulation": 3.6,
        "drainage_proximity_m": 310.0,
        "road_accessibility_score": 70.0,
        "infrastructure": {
            "schools": 3,
            "health_facilities": 1,
            "bridges_and_roads": 1,
            "critical_structures_count": 5
        }
    },
    {
        "id": "VIL-011",
        "name": "Phata Funnel",
        "district": "Rudraprayag",
        "state": "Uttarakhand",
        "block": "Ukhimath",
        "latitude": 30.5700,
        "longitude": 79.0500,
        "population": 1380,
        "elevation": 1500.0,
        "slope": 37.5,
        "flow_accumulation": 4.7,
        "drainage_proximity_m": 35.0,
        "road_accessibility_score": 50.0,
        "infrastructure": {
            "schools": 1,
            "health_facilities": 1,
            "bridges_and_roads": 2,
            "critical_structures_count": 4
        }
    },
    {
        "id": "VIL-012",
        "name": "Sonprayag Confluence",
        "district": "Rudraprayag",
        "state": "Uttarakhand",
        "block": "Ukhimath",
        "latitude": 30.6300,
        "longitude": 79.0100,
        "population": 1120,
        "elevation": 1820.0,
        "slope": 38.0,
        "flow_accumulation": 4.9,
        "drainage_proximity_m": 25.0,
        "road_accessibility_score": 40.0,
        "infrastructure": {
            "schools": 1,
            "health_facilities": 1,
            "bridges_and_roads": 3,
            "critical_structures_count": 5
        }
    },
    {
        "id": "VIL-013",
        "name": "Aut / Mandi",
        "district": "Mandi",
        "state": "Himachal Pradesh",
        "block": "Mandi / Aut Basin",
        "latitude": 31.7400,
        "longitude": 77.1600,
        "population": 2300,
        "elevation": 1050.0,
        "slope": 26.0,
        "flow_accumulation": 3.1,
        "drainage_proximity_m": 450.0,
        "road_accessibility_score": 80.0,
        "infrastructure": {
            "schools": 3,
            "health_facilities": 1,
            "bridges_and_roads": 1,
            "critical_structures_count": 5
        }
    },
    {
        "id": "VIL-014",
        "name": "Meppadi / Wayanad",
        "district": "Wayanad",
        "state": "Kerala",
        "block": "Vythiri / Meppadi",
        "latitude": 11.5500,
        "longitude": 76.1200,
        "population": 650,
        "elevation": 780.0,
        "slope": 24.0,
        "flow_accumulation": 2.2,
        "drainage_proximity_m": 950.0,
        "road_accessibility_score": 60.0,
        "infrastructure": {
            "schools": 1,
            "health_facilities": 0,
            "bridges_and_roads": 1,
            "critical_structures_count": 2
        }
    },
    {
        "id": "VIL-015",
        "name": "Chooralmala / Vellarimala",
        "district": "Wayanad",
        "state": "Kerala",
        "block": "Vythiri / Meppadi",
        "latitude": 11.5100,
        "longitude": 76.1700,
        "population": 6200,
        "elevation": 820.0,
        "slope": 28.0,
        "flow_accumulation": 2.9,
        "drainage_proximity_m": 620.0,
        "road_accessibility_score": 95.0,
        "infrastructure": {
            "schools": 8,
            "health_facilities": 3,
            "bridges_and_roads": 2,
            "critical_structures_count": 13
        }
    }
]

# Synchronize resident population with authoritative Census 2011 dataset
from app.data.census_population_data import CENSUS_VILLAGE_POPULATION_DATA

for _village in DEMO_VILLAGES:
    if _village["id"] in CENSUS_VILLAGE_POPULATION_DATA:
        _village["population"] = CENSUS_VILLAGE_POPULATION_DATA[_village["id"]]["population"]

# Scenario-dependent hydro-meteorological inputs
SCENARIO_INPUT_MULTIPLIERS: Dict[ScenarioType, Dict[str, Any]] = {
    ScenarioType.NORMAL: {
        "description": "Baseline clear to light seasonal drizzle. Minimal flood threat.",
        "rainfall_range": (2.0, 12.0),       # current mm/h
        "forecast_24h_range": (10.0, 35.0), # forecast mm
        "soil_saturation_range": (25.0, 45.0), # %
        "river_level_range": (1.0, 1.2),      # stage multiplier
        "quality": DataQualityStatus.OK,
    },
    ScenarioType.HEAVY_RAIN: {
        "description": "Monsoonal heavy downpour across watershed. High stream runoff.",
        "rainfall_range": (35.0, 65.0),
        "forecast_24h_range": (90.0, 140.0),
        "soil_saturation_range": (65.0, 85.0),
        "river_level_range": (1.5, 2.1),
        "quality": DataQualityStatus.OK,
    },
    ScenarioType.EXTREME_RAIN: {
        "description": "Cloudburst event in upper catchments. Severe torrential flash flood emergency.",
        "rainfall_range": (75.0, 110.0),
        "forecast_24h_range": (180.0, 260.0),
        "soil_saturation_range": (88.0, 99.0),
        "river_level_range": (2.3, 2.95),
        "quality": DataQualityStatus.OK,
    }
}


def get_village_feature_snapshot(village_id: str, scenario: ScenarioType) -> Dict[str, Any]:
    """
    Returns a deterministic snapshot of multi-source inputs for a given village under a specific weather scenario.
    """
    village = next((v for v in DEMO_VILLAGES if v["id"] == village_id), None)
    if not village:
        raise ValueError(f"Village ID {village_id} not found.")

    sc_config = SCENARIO_INPUT_MULTIPLIERS[scenario]
    
    # Deterministic index-based variance generation so output is always identical for same village+scenario
    v_index = int(village_id.split("-")[1])
    var_factor = (v_index % 5) / 5.0  # 0.0, 0.2, 0.4, 0.6, 0.8

    min_rf, max_rf = sc_config["rainfall_range"]
    curr_rf = round(min_rf + (max_rf - min_rf) * ((v_index * 7) % 10) / 10.0, 1)

    min_fc, max_fc = sc_config["forecast_24h_range"]
    fc_rf = round(min_fc + (max_fc - min_fc) * ((v_index * 3) % 10) / 10.0, 1)

    min_sat, max_sat = sc_config["soil_saturation_range"]
    soil_sat = round(min_sat + (max_sat - min_sat) * ((v_index * 9) % 10) / 10.0, 1)

    min_riv, max_riv = sc_config["river_level_range"]
    riv_lvl = round(min_riv + (max_riv - min_riv) * ((v_index * 11) % 10) / 10.0, 2)

    # Simulate missing data test case for VIL-014 in EXTREME_RAIN (to test failure handling)
    feature_statuses = {
        "current_rainfall": DataQualityStatus.OK,
        "forecast_rainfall": DataQualityStatus.OK,
        "soil_saturation": DataQualityStatus.OK,
        "river_water_level": DataQualityStatus.OK,
        "slope": DataQualityStatus.OK,
        "flow_accumulation": DataQualityStatus.OK
    }

    if village_id == "VIL-014" and scenario == ScenarioType.EXTREME_RAIN:
        feature_statuses["soil_saturation"] = DataQualityStatus.MISSING
        soil_sat = None  # Missing feature

    return {
        "village_id": village["id"],
        "village_name": village["name"],
        "elevation": village["elevation"],
        "slope": village["slope"],
        "flow_accumulation": village["flow_accumulation"],
        "drainage_proximity_m": village["drainage_proximity_m"],
        "current_rainfall": curr_rf,
        "forecast_rainfall": fc_rf,
        "soil_saturation": soil_sat,
        "river_water_level": riv_lvl,
        "feature_statuses": feature_statuses,
        "timestamp": "2026-09-03T22:30:00Z"
    }
