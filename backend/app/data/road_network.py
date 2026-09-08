"""
Deterministic Mountain Road Network Graph for APADA MITRA.
Contains road segments connecting villages and relief shelters in the Alaknanda watershed.
Explicitly labeled as DEMO / SYNTHETIC DATA.
"""
from typing import List, Dict, Any
from app.models.domain import RoadSegment, RoadStatus, ScenarioType

DEMO_ROADS_BASE: List[Dict[str, Any]] = [
    {
        "id": "ROAD-001",
        "name": "NH-58 (Pipalkoti to Helang Pass)",
        "source_id": "VIL-001",
        "target_id": "VIL-002",
        "distance_km": 12.5,
        "base_flood_exp": 45.0,
        "base_landslide_exp": 65.0,
        "coordinates": [[30.4300, 79.4300], [30.4750, 79.4700], [30.5200, 79.5100]]
    },
    {
        "id": "ROAD-002",
        "name": "NH-58 (Helang to Govindghat)",
        "source_id": "VIL-002",
        "target_id": "VIL-003",
        "distance_km": 14.0,
        "base_flood_exp": 70.0,
        "base_landslide_exp": 80.0,
        "coordinates": [[30.5200, 79.5100], [30.5700, 79.5350], [30.6200, 79.5600]]
    },
    {
        "id": "ROAD-003",
        "name": "Govindghat to Badrinath Base Road",
        "source_id": "VIL-003",
        "target_id": "VIL-004",
        "distance_km": 18.2,
        "base_flood_exp": 55.0,
        "base_landslide_exp": 75.0,
        "coordinates": [[30.6200, 79.5600], [30.6800, 79.5250], [30.7400, 79.4900]]
    },
    {
        "id": "ROAD-004",
        "name": "NH-58 (Karnaprayag to Nandaprayag)",
        "source_id": "VIL-005",
        "target_id": "VIL-006",
        "distance_km": 11.0,
        "base_flood_exp": 60.0,
        "base_landslide_exp": 30.0,
        "coordinates": [[30.2600, 79.2200], [30.2950, 79.2700], [30.3300, 79.3200]]
    },
    {
        "id": "ROAD-005",
        "name": "Nandaprayag to Pipalkoti Highway",
        "source_id": "VIL-006",
        "target_id": "VIL-001",
        "distance_km": 15.5,
        "base_flood_exp": 50.0,
        "base_landslide_exp": 40.0,
        "coordinates": [[30.3300, 79.3200], [30.3800, 79.3750], [30.4300, 79.4300]]
    },
    {
        "id": "ROAD-006",
        "name": "Rudraprayag to Tilwara Bypass",
        "source_id": "VIL-007",
        "target_id": "VIL-008",
        "distance_km": 9.5,
        "base_flood_exp": 40.0,
        "base_landslide_exp": 25.0,
        "coordinates": [[30.2850, 78.9800], [30.3175, 79.0050], [30.3500, 79.0300]]
    },
    {
        "id": "ROAD-007",
        "name": "Tilwara to Augustmuni Valley Road",
        "source_id": "VIL-008",
        "target_id": "VIL-009",
        "distance_km": 6.8,
        "base_flood_exp": 65.0,
        "base_landslide_exp": 35.0,
        "coordinates": [[30.3500, 79.0300], [30.3700, 79.0550], [30.3900, 79.0800]]
    },
    {
        "id": "ROAD-008",
        "name": "Augustmuni to Guptkashi Hill Climb",
        "source_id": "VIL-009",
        "target_id": "VIL-010",
        "distance_km": 16.0,
        "base_flood_exp": 30.0,
        "base_landslide_exp": 70.0,
        "coordinates": [[30.3900, 79.0800], [30.4575, 79.0800], [30.5250, 79.0800]]
    },
    {
        "id": "ROAD-009",
        "name": "Guptkashi to Phata Corridor",
        "source_id": "VIL-010",
        "target_id": "VIL-011",
        "distance_km": 8.0,
        "base_flood_exp": 50.0,
        "base_landslide_exp": 85.0,
        "coordinates": [[30.5250, 79.0800], [30.5475, 79.0650], [30.5700, 79.0500]]
    },
    {
        "id": "ROAD-010",
        "name": "Phata to Sonprayag Gorge Road",
        "source_id": "VIL-011",
        "target_id": "VIL-012",
        "distance_km": 10.2,
        "base_flood_exp": 85.0,
        "base_landslide_exp": 90.0,  # Highly vulnerable to blockages in storm
        "coordinates": [[30.5700, 79.0500], [30.6000, 79.0300], [30.6300, 79.0100]]
    },
    # Region A Shelter Access Roads (Uttarakhand)
    {
        "id": "ROAD-014",
        "name": "Pipalkoti to SH-01 High School Shelter Access",
        "source_id": "VIL-001",
        "target_id": "SH-01",
        "distance_km": 4.5,
        "base_flood_exp": 15.0,
        "base_landslide_exp": 20.0,
        "coordinates": [[30.4300, 79.4300], [30.4350, 79.4200], [30.4400, 79.4100]]
    },
    {
        "id": "ROAD-015",
        "name": "Pipalkoti to SH-02 Gopeshwar Sports Complex Access",
        "source_id": "VIL-001",
        "target_id": "SH-02",
        "distance_km": 12.0,
        "base_flood_exp": 15.0,
        "base_landslide_exp": 20.0,
        "coordinates": [[30.4300, 79.4300], [30.4250, 79.3750], [30.4200, 79.3200]]
    },
    {
        "id": "ROAD-016",
        "name": "Rudraprayag to SH-03 District Relief Camp",
        "source_id": "VIL-007",
        "target_id": "SH-03",
        "distance_km": 5.2,
        "base_flood_exp": 25.0,
        "base_landslide_exp": 20.0,
        "coordinates": [[30.2850, 78.9800], [30.2900, 78.9700], [30.2950, 78.9600]]
    },
    {
        "id": "ROAD-017",
        "name": "Guptkashi to SH-04 High Plateau Shelter",
        "source_id": "VIL-010",
        "target_id": "SH-04",
        "distance_km": 6.5,
        "base_flood_exp": 15.0,
        "base_landslide_exp": 25.0,
        "coordinates": [[30.5250, 79.0800], [30.5225, 79.1100], [30.5200, 79.1400]]
    },
    {
        "id": "ROAD-018",
        "name": "Phata to SH-04 High Plateau Detour",
        "source_id": "VIL-011",
        "target_id": "SH-04",
        "distance_km": 11.5,
        "base_flood_exp": 30.0,
        "base_landslide_exp": 40.0,
        "coordinates": [[30.5700, 79.0500], [30.5450, 79.0950], [30.5200, 79.1400]]
    },
    {
        "id": "ROAD-019",
        "name": "Sonprayag to SH-05 Valley Ridge Shelter",
        "source_id": "VIL-012",
        "target_id": "SH-05",
        "distance_km": 7.0,
        "base_flood_exp": 45.0,
        "base_landslide_exp": 55.0,
        "coordinates": [[30.6300, 79.0100], [30.6350, 79.0300], [30.6400, 79.0500]]
    },
    {
        "id": "ROAD-020",
        "name": "Badrinath to SH-06 Upper Base Camp",
        "source_id": "VIL-004",
        "target_id": "SH-06",
        "distance_km": 6.0,
        "base_flood_exp": 20.0,
        "base_landslide_exp": 35.0,
        "coordinates": [[30.7400, 79.4900], [30.7450, 79.4800], [30.7500, 79.4700]]
    },
    # Region B Road Network (Aut / Mandi, Himachal Pradesh)
    {
        "id": "ROAD-021",
        "name": "Aut to SH-07 Mandi Relief Camp Access",
        "source_id": "VIL-013",
        "target_id": "SH-07",
        "distance_km": 3.5,
        "base_flood_exp": 15.0,
        "base_landslide_exp": 20.0,
        "coordinates": [[31.7400, 77.1600], [31.7425, 77.1650], [31.7450, 77.1700]]
    },
    # Region C Road Network (Wayanad, Kerala)
    {
        "id": "ROAD-022",
        "name": "Meppadi to Chooralmala Wayanad Corridor",
        "source_id": "VIL-014",
        "target_id": "VIL-015",
        "distance_km": 8.5,
        "base_flood_exp": 40.0,
        "base_landslide_exp": 60.0,
        "coordinates": [[11.5500, 76.1200], [11.5300, 76.1450], [11.5100, 76.1700]]
    },
    {
        "id": "ROAD-023",
        "name": "Meppadi to SH-08 Wayanad Relief Shelter Access",
        "source_id": "VIL-014",
        "target_id": "SH-08",
        "distance_km": 2.8,
        "base_flood_exp": 10.0,
        "base_landslide_exp": 15.0,
        "coordinates": [[11.5500, 76.1200], [11.5550, 76.1250], [11.5600, 76.1300]]
    },
    {
        "id": "ROAD-024",
        "name": "Chooralmala to SH-08 Wayanad Relief Shelter Access",
        "source_id": "VIL-015",
        "target_id": "SH-08",
        "distance_km": 7.2,
        "base_flood_exp": 25.0,
        "base_landslide_exp": 30.0,
        "coordinates": [[11.5100, 76.1700], [11.5350, 76.1500], [11.5600, 76.1300]]
    }
]


def get_active_road_segments(scenario: ScenarioType) -> List[RoadSegment]:
    """
    Returns dynamic status of road network segments for a given scenario.
    In EXTREME_RAIN, highly exposed mountain roads become DEGRADED or BLOCKED.
    """
    segments: List[RoadSegment] = []

    for r in DEMO_ROADS_BASE:
        base_fl = r["base_flood_exp"]
        base_ls = r["base_landslide_exp"]

        if scenario == ScenarioType.NORMAL:
            flood_exp = round(base_fl * 0.3, 1)
            landslide_exp = round(base_ls * 0.3, 1)
            status = RoadStatus.OPEN
        elif scenario == ScenarioType.HEAVY_RAIN:
            flood_exp = round(min(100.0, base_fl * 1.0), 1)
            landslide_exp = round(min(100.0, base_ls * 1.0), 1)
            if flood_exp >= 80.0 or landslide_exp >= 85.0:
                status = RoadStatus.DEGRADED
            else:
                status = RoadStatus.OPEN
        else:  # EXTREME_RAIN
            flood_exp = round(min(100.0, base_fl * 1.35), 1)
            landslide_exp = round(min(100.0, base_ls * 1.35), 1)
            
            # Block only from computed hazard exposure; no road ID is privileged.
            if flood_exp >= 88.0 or landslide_exp >= 92.0:
                status = RoadStatus.BLOCKED
            elif flood_exp >= 65.0 or landslide_exp >= 65.0:
                status = RoadStatus.DEGRADED
            else:
                status = RoadStatus.OPEN

        segments.append(
            RoadSegment(
                id=r["id"],
                name=r["name"],
                source_id=r["source_id"],
                target_id=r["target_id"],
                distance_km=r["distance_km"],
                flood_exposure=flood_exp,
                landslide_exposure=landslide_exp,
                status=status,
                coordinates=r["coordinates"],
            )
        )

    return segments
