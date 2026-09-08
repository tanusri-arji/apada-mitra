"""
Deterministic Relief Shelters Dataset for APADA MITRA.
Contains 6 emergency relief shelters located at safe high-elevation plateaus in the Alaknanda watershed.
Explicitly labeled as DEMO / SYNTHETIC DATA.
"""
from typing import List, Dict, Any
from app.models.domain import Shelter

DEMO_SHELTERS: List[Dict[str, Any]] = [
    {
        "id": "SH-01",
        "name": "Pipalkoti Central High School Relief Complex",
        "latitude": 30.4400,
        "longitude": 79.4100,
        "total_capacity": 1500,
        "current_occupancy": 450,
        "elevation": 1380.0,
        "accessibility_score": 85.0,
        "hazard_exposure_score": 15.0,
    },
    {
        "id": "SH-02",
        "name": "Gopeshwar District Sports Stadium & Hall",
        "latitude": 30.4200,
        "longitude": 79.3200,
        "total_capacity": 3000,
        "current_occupancy": 800,
        "elevation": 1620.0,
        "accessibility_score": 95.0,
        "hazard_exposure_score": 10.0,
    },
    {
        "id": "SH-03",
        "name": "Rudraprayag Army Base Emergency Camp",
        "latitude": 30.2950,
        "longitude": 78.9600,
        "total_capacity": 2500,
        "current_occupancy": 1200,
        "elevation": 990.0,
        "accessibility_score": 90.0,
        "hazard_exposure_score": 20.0,
    },
    {
        "id": "SH-04",
        "name": "Ukhimath Ridge High Plateau Shelter",
        "latitude": 30.5200,
        "longitude": 79.1400,
        "total_capacity": 1800,
        "current_occupancy": 350,
        "elevation": 1560.0,
        "accessibility_score": 80.0,
        "hazard_exposure_score": 12.0,
    },
    {
        "id": "SH-05",
        "name": "Kedarnath Valley Emergency Base Camp (Guptkashi Crest)",
        "latitude": 30.6400,
        "longitude": 79.0500,
        "total_capacity": 800,
        "current_occupancy": 780,  # Near full capacity to test capacity rejection
        "elevation": 1950.0,
        "accessibility_score": 70.0,
        "hazard_exposure_score": 25.0,
    },
    {
        "id": "SH-06",
        "name": "Badrinath Safe Ridge Relief Center",
        "latitude": 30.7500,
        "longitude": 79.4700,
        "total_capacity": 2000,
        "current_occupancy": 500,
        "elevation": 3250.0,
        "accessibility_score": 75.0,
        "hazard_exposure_score": 18.0,
    },
    {
        "id": "SH-07",
        "name": "Mandi / Aut Disaster Relief Camp",
        "latitude": 31.7450,
        "longitude": 77.1700,
        "total_capacity": 1800,
        "current_occupancy": 400,
        "elevation": 1080.0,
        "accessibility_score": 85.0,
        "hazard_exposure_score": 14.0,
    },
    {
        "id": "SH-08",
        "name": "Wayanad High Ridge Relief Shelter",
        "latitude": 11.5600,
        "longitude": 76.1300,
        "total_capacity": 2200,
        "current_occupancy": 600,
        "elevation": 860.0,
        "accessibility_score": 90.0,
        "hazard_exposure_score": 12.0,
    },
]


def get_shelters_list() -> List[Shelter]:
    """Returns list of all registered relief shelter candidates as domain Shelter objects."""
    from app.adapters.shelter_adapter import shelter_adapter_instance
    records, _ = shelter_adapter_instance.get_all_shelters()
    shelters: List[Shelter] = []
    for r in records:
        avail = r.available_capacity if r.available_capacity is not None else None
        shelters.append(
            Shelter(
                id=r.shelter_id,
                name=r.name,
                latitude=r.latitude,
                longitude=r.longitude,
                total_capacity=r.total_capacity,
                current_occupancy=r.current_occupancy,
                available_capacity=avail,
                elevation=r.elevation,
                accessibility_score=r.accessibility_score,
                hazard_exposure_score=r.combined_hazard_score or r.hazard_exposure_score or 15.0,
            )
        )
    return shelters

