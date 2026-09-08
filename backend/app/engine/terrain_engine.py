"""
GIS Terrain Intelligence Engine for APADA MITRA.
Manages DEM retrieval, caching, 2D vector gradient slope derivation, D8 flow accumulation, and data quality fallbacks.
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.adapters.open_elevation import OpenElevationDEMAdapter
from app.models.terrain import VillageTerrainDetail, TerrainQualityStatus


class GISTerrainEngine:
    """
    Central GIS Terrain Engine.
    Provides verified DEM elevation, 2D vector gradient slope, and D8 flow accumulation for watershed villages.
    """

    def __init__(self):
        self.dem_adapter = OpenElevationDEMAdapter()
        self._cache: Dict[str, VillageTerrainDetail] = {}

    def get_village_terrain(self, village_data: Dict[str, Any], force_offline: bool = False) -> VillageTerrainDetail:
        """
        Retrieves real GIS terrain intelligence for given village coordinates.
        Priority:
        1. Real GIS DEM fetch & derivation (REAL_GIS)
        2. In-memory DEM cache (CACHED_GIS)
        3. Deterministic SIH Dataset (OFFLINE_DEMO)
        """
        from app.data.dataset import DEMO_VILLAGES
        village_id = village_data.get("id", "VIL-001")
        village_name = village_data.get("name", "Unknown Village")

        static_v = next((v for v in DEMO_VILLAGES if v["id"] == village_id), None)
        lat = float(village_data.get("latitude", static_v["latitude"] if static_v else 30.4300))
        lon = float(village_data.get("longitude", static_v["longitude"] if static_v else 79.4300))
        now_iso = datetime.now(timezone.utc).isoformat()

        # Check for invalid coordinates
        if not (-90 <= lat <= 90 and -180 <= lon <= 180) or abs(lat) > 89 or abs(lon) > 179:
            return VillageTerrainDetail(
                village_id=village_id,
                village_name=village_name,
                latitude=0.0,
                longitude=0.0,
                elevation_m=0.0,
                elevation_source="UNAVAILABLE",
                slope_deg=0.0,
                slope_source="UNAVAILABLE",
                flow_accumulation=0.0,
                flow_accumulation_source="UNAVAILABLE",
                flow_accumulation_cells=0.0,
                terrain_status=TerrainQualityStatus.UNAVAILABLE,
                terrain_source="UNAVAILABLE",
                dem_resolution="N/A",
                dem_window_size="N/A",
                processing_method="UNAVAILABLE",
                retrieved_at=now_iso,
            )

        # 1. Check in-memory cache if not forced offline
        if village_id in self._cache and not force_offline:
            cached_detail = self._cache[village_id]
            if cached_detail.terrain_status == TerrainQualityStatus.REAL_GIS:
                # Return as CACHED_GIS
                return VillageTerrainDetail(
                    village_id=cached_detail.village_id,
                    village_name=cached_detail.village_name,
                    latitude=cached_detail.latitude,
                    longitude=cached_detail.longitude,
                    elevation_m=cached_detail.elevation_m,
                    elevation_source=f"CACHED ({cached_detail.elevation_source})",
                    slope_deg=cached_detail.slope_deg,
                    slope_source=cached_detail.slope_source,
                    flow_accumulation=cached_detail.flow_accumulation,
                    flow_accumulation_source=cached_detail.flow_accumulation_source,
                    flow_accumulation_cells=cached_detail.flow_accumulation_cells,
                    terrain_status=TerrainQualityStatus.CACHED_GIS,
                    terrain_source=cached_detail.terrain_source,
                    dem_resolution=cached_detail.dem_resolution,
                    dem_window_size=cached_detail.dem_window_size,
                    processing_method=cached_detail.processing_method,
                    retrieved_at=cached_detail.retrieved_at,
                )

        # 2. Live DEM Raster Fetch & Derivation
        if not force_offline:
            try:
                raster_data = self.dem_adapter.fetch_raster_grid(lat, lon, grid_size=9)
                if raster_data is not None:
                    matrix = raster_data["matrix"]
                    elevation_m = float(raster_data["center_elevation"])
                    slope_deg = self.dem_adapter.derive_slope(matrix)
                    acc_matrix, flow_acc_log, raw_cells = self.dem_adapter.derive_d8_flow_accumulation(matrix)

                    source_name = raster_data["source"]

                    detail = VillageTerrainDetail(
                        village_id=village_id,
                        village_name=village_name,
                        latitude=lat,
                        longitude=lon,
                        elevation_m=elevation_m,
                        elevation_source=source_name,
                        slope_deg=slope_deg,
                        slope_source="DERIVED_FROM_DEM_VECTOR_GRADIENT",
                        flow_accumulation=flow_acc_log,
                        flow_accumulation_source="DERIVED_FROM_DEM_D8_FLOW_ACCUMULATION",
                        flow_accumulation_cells=raw_cells,
                        terrain_status=TerrainQualityStatus.REAL_GIS,
                        terrain_source=source_name,
                        dem_resolution=raster_data["resolution"],
                        dem_window_size=raster_data["window_size"],
                        processing_method="D8_HYDROLOGICAL_ROUTING_WITH_DEPRESSION_HANDLING",
                        retrieved_at=raster_data["timestamp"],
                    )
                    self._cache[village_id] = detail
                    return detail
            except Exception:
                pass  # Fall through to offline demo

        # 3. Offline Demo Fallback
        return VillageTerrainDetail(
            village_id=village_id,
            village_name=village_name,
            latitude=lat,
            longitude=lon,
            elevation_m=float(village_data.get("elevation", 1000.0)),
            elevation_source="OFFLINE_DEMO",
            slope_deg=float(village_data.get("slope", 25.0)),
            slope_source="OFFLINE_DEMO",
            flow_accumulation=float(village_data.get("flow_accumulation", 4.0)),
            flow_accumulation_source="OFFLINE_DEMO",
            flow_accumulation_cells=None,
            terrain_status=TerrainQualityStatus.OFFLINE_DEMO,
            terrain_source="OFFLINE_DEMO",
            dem_resolution="Static Demo Grid",
            dem_window_size="Static Demo Grid",
            processing_method="OFFLINE_DEMO_BASELINE",
            retrieved_at=now_iso,
        )

    def clear_cache(self):
        """Clears in-memory terrain cache (for testing)."""
        self._cache.clear()


# Global Singleton Terrain Engine Instance
terrain_engine_instance = GISTerrainEngine()
