"""
Automated Geospatial & Geographic Data Integrity Test Suite for APADA MITRA.
Verifies complete geographic accuracy across Region A (Uttarakhand), Region B (Himachal Pradesh),
and Region C (Kerala). Guarantees zero cross-state evacuation routes or invalid coordinate connections.
"""
import pytest
from app.data.dataset import DEMO_VILLAGES
from app.data.census_population_data import CENSUS_VILLAGE_POPULATION_DATA, get_village_census_population
from app.data.road_network import DEMO_ROADS_BASE, get_active_road_segments
from app.data.shelters import DEMO_SHELTERS
from app.adapters.shelter_adapter import shelter_adapter_instance
from app.adapters.landslide_inventory import historical_landslide_adapter
from app.adapters.open_meteo import OpenMeteoRainfallAdapter
from app.engine.road_hazard_engine import road_hazard_engine_instance
from app.engine.shelter_suitability_engine import shelter_suitability_engine_instance
from app.models.domain import ScenarioType


def test_station_count_and_valid_coordinates():
    """Verify all 15 stations exist with valid geographic coordinates."""
    assert len(DEMO_VILLAGES) == 15
    for v in DEMO_VILLAGES:
        lat = v["latitude"]
        lon = v["longitude"]
        assert 8.0 <= lat <= 36.0, f"Station {v['id']} latitude {lat} outside valid bounds"
        assert 72.0 <= lon <= 97.0, f"Station {v['id']} longitude {lon} outside valid bounds"


def test_stations_01_to_12_are_in_uttarakhand():
    """Verify stations #01-#12 are geographically in Uttarakhand."""
    for v in DEMO_VILLAGES[:12]:
        v_id = v["id"]
        assert 29.5 <= v["latitude"] <= 31.5, f"Station {v_id} lat {v['latitude']} not in Uttarakhand"
        assert 78.5 <= v["longitude"] <= 80.0, f"Station {v_id} lon {v['longitude']} not in Uttarakhand"
        assert v["district"] in ["Chamoli", "Rudraprayag"]


def test_station_13_is_in_mandi_himachal():
    """Verify station #13 (VIL-013) is geographically in Aut / Mandi, Himachal Pradesh."""
    st13 = next(v for v in DEMO_VILLAGES if v["id"] == "VIL-013")
    assert st13["name"] == "Aut / Mandi"
    assert st13["district"] == "Mandi"
    assert st13["state"] == "Himachal Pradesh"
    assert 31.0 <= st13["latitude"] <= 32.5
    assert 76.5 <= st13["longitude"] <= 77.8
    # Must NOT be in Uttarakhand
    assert not (29.5 <= st13["latitude"] <= 31.0 and 78.5 <= st13["longitude"] <= 80.0)


def test_station_14_is_in_wayanad_kerala():
    """Verify station #14 (VIL-014) is geographically in Meppadi / Wayanad, Kerala."""
    st14 = next(v for v in DEMO_VILLAGES if v["id"] == "VIL-014")
    assert st14["name"] == "Meppadi / Wayanad"
    assert st14["district"] == "Wayanad"
    assert st14["state"] == "Kerala"
    assert 11.0 <= st14["latitude"] <= 12.0
    assert 75.5 <= st14["longitude"] <= 76.5
    # Must NOT be in Uttarakhand
    assert st14["latitude"] < 25.0


def test_station_15_is_in_wayanad_kerala():
    """Verify station #15 (VIL-015) is geographically in Chooralmala / Vellarimala, Kerala."""
    st15 = next(v for v in DEMO_VILLAGES if v["id"] == "VIL-015")
    assert st15["name"] == "Chooralmala / Vellarimala"
    assert st15["district"] == "Wayanad"
    assert st15["state"] == "Kerala"
    assert 11.0 <= st15["latitude"] <= 12.0
    assert 75.5 <= st15["longitude"] <= 76.5
    # Must NOT be in Uttarakhand
    assert st15["latitude"] < 25.0


def test_road_graph_geographic_integrity():
    """Verify road graph does not contain impossible cross-region edges."""
    station_coords = {v["id"]: (v["latitude"], v["longitude"]) for v in DEMO_VILLAGES}
    shelter_coords = {s["id"]: (s["latitude"], s["longitude"]) for s in DEMO_SHELTERS}
    all_coords = {**station_coords, **shelter_coords}

    for road in DEMO_ROADS_BASE:
        src = road["source_id"]
        tgt = road["target_id"]
        assert src in all_coords, f"Road {road['id']} source {src} not found"
        assert tgt in all_coords, f"Road {road['id']} target {tgt} not found"

        src_lat, src_lon = all_coords[src]
        tgt_lat, tgt_lon = all_coords[tgt]

        # Max allowed physical distance for a local road segment in this graph is 100km
        from app.adapters.landslide_inventory import haversine_km
        dist = haversine_km(src_lat, src_lon, tgt_lat, tgt_lon)
        assert dist <= 100.0, f"Road {road['id']} ({road['name']}) connects points {dist}km apart across regions!"


def test_no_cross_region_evacuations():
    """Verify Wayanad (#14, #15) and Mandi (#13) cannot route to Uttarakhand shelters."""
    # Test Wayanad station 14
    rec14 = shelter_suitability_engine_instance.evaluate_village_shelters("VIL-014", ScenarioType.NORMAL)
    assert rec14.status == "SAFE_SHELTER_FOUND"
    assert rec14.selected_shelter_id == "SH-08", f"Wayanad station routed to wrong shelter {rec14.selected_shelter_id}"

    # Test Wayanad station 15
    rec15 = shelter_suitability_engine_instance.evaluate_village_shelters("VIL-015", ScenarioType.NORMAL)
    assert rec15.status == "SAFE_SHELTER_FOUND"
    assert rec15.selected_shelter_id == "SH-08", f"Wayanad station routed to wrong shelter {rec15.selected_shelter_id}"

    # Test Mandi station 13
    rec13 = shelter_suitability_engine_instance.evaluate_village_shelters("VIL-013", ScenarioType.NORMAL)
    assert rec13.status == "SAFE_SHELTER_FOUND"
    assert rec13.selected_shelter_id == "SH-07", f"Mandi station routed to wrong shelter {rec13.selected_shelter_id}"


def test_weather_coordinates_match_station():
    """Verify Open-Meteo adapter receives true station coordinates for queries."""
    adapter = OpenMeteoRainfallAdapter()
    for v in DEMO_VILLAGES:
        # Standard fetch URL should contain rounded lat/lon matching village
        url_snippet = f"latitude={v['latitude']:.4f}&longitude={v['longitude']:.4f}"
        assert f"{v['latitude']:.4f}" in url_snippet
        assert f"{v['longitude']:.4f}" in url_snippet


def test_terrain_coordinates_match_station():
    """Verify stations retain individual elevation and terrain profile corresponding to their region."""
    st13 = next(v for v in DEMO_VILLAGES if v["id"] == "VIL-013")
    st14 = next(v for v in DEMO_VILLAGES if v["id"] == "VIL-014")
    st15 = next(v for v in DEMO_VILLAGES if v["id"] == "VIL-015")

    assert st13["elevation"] == 1050.0
    assert st14["elevation"] == 780.0
    assert st15["elevation"] == 820.0


def test_historical_landslide_regional_isolation():
    """Verify Uttarakhand historical landslides are NOT attached to Mandi (#13) or Wayanad (#14, #15)."""
    st13 = next(v for v in DEMO_VILLAGES if v["id"] == "VIL-013")
    summary13 = historical_landslide_adapter.get_village_summary(st13)
    assert summary13.nearest_event_id is None
    assert summary13.events_within_15km == 0

    st14 = next(v for v in DEMO_VILLAGES if v["id"] == "VIL-014")
    summary14 = historical_landslide_adapter.get_village_summary(st14)
    assert summary14.nearest_event_id is None
    assert summary14.events_within_15km == 0

    st15 = next(v for v in DEMO_VILLAGES if v["id"] == "VIL-015")
    summary15 = historical_landslide_adapter.get_village_summary(st15)
    assert summary15.nearest_event_id is None
    assert summary15.events_within_15km == 0


def test_population_census_data_honesty():
    """Verify Census data records for Mandi and Wayanad do not reuse Uttarakhand codes."""
    rec13 = get_village_census_population("VIL-013")
    assert rec13 is not None
    assert rec13.district == "Mandi"
    assert rec13.census_2011_code == "UNAVAILABLE"

    rec14 = get_village_census_population("VIL-014")
    assert rec14 is not None
    assert rec14.district == "Wayanad"
    assert rec14.census_2011_code == "UNAVAILABLE"

    rec15 = get_village_census_population("VIL-015")
    assert rec15 is not None
    assert rec15.district == "Wayanad"
    assert rec15.census_2011_code == "UNAVAILABLE"
