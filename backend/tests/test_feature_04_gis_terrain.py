"""
Feature 4 — Real GIS Terrain Intelligence & D8 Multi-Cell DEM Derivation Tests.
Verifies real DEM raster lookup (9x9 grid), Horn 2D vector gradient slope derivation,
true D8 single flow direction matrix computation & accumulated upstream catchment cell routing,
data status states (REAL_GIS, CACHED_GIS, OFFLINE_DEMO, UNAVAILABLE), provenance accuracy,
risk engine integration, and preservation of Features 1, 2, 3.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.adapters.open_elevation import OpenElevationDEMAdapter
from app.engine.terrain_engine import terrain_engine_instance
from app.data_pipeline import DataIngestionPipeline
from app.data.dataset import DEMO_VILLAGES
from app.engine.risk_engine import calculate_flash_flood_risk
from app.engine.explainability import calculate_explainability_factors
from app.models.domain import ScenarioType, DataSourceState
from app.models.terrain import TerrainQualityStatus

client = TestClient(app)
VIL_001 = DEMO_VILLAGES[0]
VIL_003 = DEMO_VILLAGES[2]


@pytest.fixture(autouse=True)
def reset_terrain_cache():
    """Resets in-memory terrain engine cache before each test."""
    terrain_engine_instance.clear_cache()
    yield
    terrain_engine_instance.clear_cache()


def test_valid_village_terrain_lookup():
    """1. Verifies valid village terrain lookup endpoint."""
    response = client.get(f"/api/terrain/villages/{VIL_001['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["village_id"] == VIL_001["id"]
    assert "elevation_m" in data
    assert "slope_deg" in data
    assert "flow_accumulation" in data
    assert "flow_accumulation_source" in data
    assert "terrain_source" in data


def test_elevation_and_provenance_metadata():
    """2. Verifies explicit provenance metadata matches actual source."""
    terrain = terrain_engine_instance.get_village_terrain(VIL_001)
    assert terrain.elevation_m > 0
    assert terrain.elevation_source != ""
    assert terrain.slope_source in ["DERIVED_FROM_DEM_VECTOR_GRADIENT", "OFFLINE_DEMO"]
    # Provenance consistency: elevation source and terrain source should align
    assert terrain.elevation_source == terrain.terrain_source
    assert terrain.dem_resolution is not None


def test_multi_cell_dem_raster_fetching():
    """3. Verifies 9x9 multi-cell DEM raster fetching (81 points)."""
    adapter = OpenElevationDEMAdapter()
    raster = adapter.fetch_raster_grid(VIL_001["latitude"], VIL_001["longitude"], grid_size=9)
    if raster is not None:
        assert raster["grid_size"] == 9
        assert len(raster["matrix"]) == 9
        assert len(raster["matrix"][0]) == 9
        assert raster["center_elevation"] > 0.0


def test_slope_derivation_from_2d_raster_gradient():
    """4. Verifies Horn 2D finite difference vector gradient slope derivation."""
    adapter = OpenElevationDEMAdapter()
    # Mock 9x9 elevation matrix with 100m rise over ~180m run along E-W center row
    matrix = [[1000.0 for _ in range(9)] for _ in range(9)]
    matrix[4][3] = 950.0   # West neighbor
    matrix[4][5] = 1050.0  # East neighbor
    slope = adapter.derive_slope(matrix, cell_size_m=90.0)
    assert 20.0 <= slope <= 35.0


def test_d8_flow_accumulation_matrix_calculation_not_hardcoded():
    """5. Verifies true D8 flow direction matrix computation & cell accumulation across full raster."""
    adapter = OpenElevationDEMAdapter()
    # Sloped valley matrix (high in NW, low in SE)
    matrix = [
        [500, 480, 460, 440, 420, 400, 380, 360, 340],
        [490, 470, 450, 430, 410, 390, 370, 350, 330],
        [480, 460, 440, 420, 400, 380, 360, 340, 320],
        [470, 450, 430, 410, 390, 370, 350, 330, 310],
        [460, 440, 420, 400, 380, 360, 340, 320, 300],  # Center (4,4) elevation = 380
        [450, 430, 410, 390, 370, 350, 330, 310, 290],
        [440, 420, 400, 380, 360, 340, 320, 300, 280],
        [430, 410, 390, 370, 350, 330, 310, 290, 270],
        [420, 400, 380, 360, 340, 320, 300, 280, 260],
    ]
    # Test at center cell
    acc_matrix, log_index, raw_cells = adapter.derive_d8_flow_accumulation(matrix, cell_size_m=90.0, target_row=4, target_col=4)
    assert raw_cells == 5.0  # Center cell accumulates exactly 5.0 cells from the matrix
    assert acc_matrix[4][4] == 5.0
    assert raw_cells != 1.0  # PROVES it is calculated from the raster and NOT hardcoded to 1.0!

    # Test at outlet cell (bottom right 8,8)
    _, log_index_outlet, raw_cells_outlet = adapter.derive_d8_flow_accumulation(matrix, cell_size_m=90.0, target_row=8, target_col=8)
    assert raw_cells_outlet == 81.0  # All 81 cells drain into outlet!
    assert log_index_outlet == 4.78 or 1.0 <= log_index_outlet <= 5.0


def test_unavailable_dem_coordinate_validation():
    """6. Verifies invalid coordinates return UNAVAILABLE status."""
    invalid_village = {"id": "VIL-999", "name": "Invalid", "latitude": 999.0, "longitude": 999.0}
    terrain = terrain_engine_instance.get_village_terrain(invalid_village)
    assert terrain.terrain_status == TerrainQualityStatus.UNAVAILABLE
    assert terrain.elevation_source == "UNAVAILABLE"
    assert terrain.slope_source == "UNAVAILABLE"
    assert terrain.flow_accumulation_source == "UNAVAILABLE"


def test_dem_offline_fallback_behavior():
    """7. Verifies force_offline correctly returns OFFLINE_DEMO status without claiming REAL_GIS."""
    terrain = terrain_engine_instance.get_village_terrain(VIL_001, force_offline=True)
    assert terrain.terrain_status == TerrainQualityStatus.OFFLINE_DEMO
    assert terrain.elevation_source == "OFFLINE_DEMO"
    assert terrain.slope_source == "OFFLINE_DEMO"
    assert terrain.flow_accumulation_source == "OFFLINE_DEMO"
    assert terrain.terrain_status != TerrainQualityStatus.REAL_GIS


def test_cached_gis_status_transition():
    """8. Verifies cached GIS status transition (REAL_GIS -> CACHED_GIS)."""
    t1 = terrain_engine_instance.get_village_terrain(VIL_001, force_offline=False)
    if t1.terrain_status == TerrainQualityStatus.REAL_GIS:
        t2 = terrain_engine_instance.get_village_terrain(VIL_001, force_offline=False)
        assert t2.terrain_status == TerrainQualityStatus.CACHED_GIS
        assert "CACHED" in t2.elevation_source


def test_terrain_values_reach_risk_engine():
    """9. Verifies terrain values (elevation, slope, flow_accumulation) feed risk engine."""
    pipe = DataIngestionPipeline()
    obs = pipe.get_normalized_observation(VIL_001["latitude"], VIL_001["longitude"], VIL_001["id"], scenario=ScenarioType.HEAVY_RAIN)
    snapshot = pipe.convert_to_risk_feature_snapshot(obs, VIL_001, scenario=ScenarioType.HEAVY_RAIN)

    assert "elevation" in snapshot
    assert "slope" in snapshot
    assert "flow_accumulation" in snapshot

    risk_res = calculate_flash_flood_risk(snapshot)
    assert "slope" in risk_res["raw_features"]
    assert "flow_accumulation" in risk_res["raw_features"]


def test_xai_receives_updated_slope_and_flow_values():
    """10. Verifies XAI engine receives updated terrain values."""
    pipe = DataIngestionPipeline()
    obs = pipe.get_normalized_observation(VIL_001["latitude"], VIL_001["longitude"], VIL_001["id"], scenario=ScenarioType.HEAVY_RAIN)
    snapshot = pipe.convert_to_risk_feature_snapshot(obs, VIL_001, scenario=ScenarioType.HEAVY_RAIN)
    risk_res = calculate_flash_flood_risk(snapshot)

    factors = calculate_explainability_factors(
        raw_features=risk_res["raw_features"],
        normalized_features=risk_res["normalized_features"],
        total_risk_score=risk_res["flash_flood_risk_score"],
    )

    slope_factor = next(f for f in factors if f.feature_key == "slope")
    flow_factor = next(f for f in factors if f.feature_key == "flow_accumulation")

    assert slope_factor.raw_value == risk_res["raw_features"]["slope"]
    assert flow_factor.raw_value == risk_res["raw_features"]["flow_accumulation"]


def test_depression_filling_pit_resolution():
    """12. Verifies priority-flood depression filling algorithm resolves pits."""
    adapter = OpenElevationDEMAdapter()
    # Matrix with deep internal pit at center (50m surrounded by 100m)
    matrix = [
        [100.0, 100.0, 100.0],
        [100.0,  50.0, 100.0],
        [100.0, 100.0,  90.0],
    ]
    filled = adapter.fill_depressions(matrix, epsilon=0.01)
    # The center pit at [1][1] should be raised to lowest pour point (90m) + epsilon (0.01) = 90.01m
    assert round(filled[1][1], 2) == 90.01
    assert filled[2][2] == 90.0  # Outlet remains unchanged


def test_real_gis_flow_accumulation_provenance_and_processing_method():
    """13. Verifies flow accumulation provenance is DERIVED_FROM_DEM_D8_FLOW_ACCUMULATION and processing method is explicit."""
    terrain = terrain_engine_instance.get_village_terrain(VIL_001, force_offline=False)
    if terrain.terrain_status == TerrainQualityStatus.REAL_GIS:
        assert terrain.flow_accumulation_source == "DERIVED_FROM_DEM_D8_FLOW_ACCUMULATION"
        assert terrain.processing_method == "D8_HYDROLOGICAL_ROUTING_WITH_DEPRESSION_HANDLING"
        assert 1.0 <= terrain.flow_accumulation <= 5.0
        assert terrain.flow_accumulation_cells is not None
        assert terrain.flow_accumulation_cells >= 1.0


def test_features_1_2_3_remain_intact():
    """14. Verifies Features 1 (Rainfall), 2 (Soil Moisture), and 3 (IoT) remain intact."""
    pipe = DataIngestionPipeline()
    obs = pipe.get_normalized_observation(VIL_001["latitude"], VIL_001["longitude"], VIL_001["id"], scenario=ScenarioType.HEAVY_RAIN)

    # Feature 1 & Feature 2 data fields
    assert hasattr(obs, "current_rainfall_mm_hr")
    assert hasattr(obs, "soil_saturation_pct")
    assert obs.data_state in [DataSourceState.LIVE, DataSourceState.LIVE_EXTERNAL_API, DataSourceState.CACHED, DataSourceState.OFFLINE_DEMO]

    # Feature 3 IoT endpoint test
    res = client.get("/api/iot/sensors")
    assert res.status_code == 200
