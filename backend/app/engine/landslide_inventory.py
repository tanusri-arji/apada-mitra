"""
Historical Landslide Inventory Service for APADA MITRA.
Coordinates historical landslide queries, caching, and village spatial analytics.
"""
from typing import Dict, Any, Optional
from app.adapters.landslide_inventory import historical_landslide_adapter, HistoricalLandslideInventoryAdapter
from app.models.landslide import (
    HistoricalLandslideInventoryResponse,
    VillageHistoricalLandslideSummary,
    LandslideDataState,
)


class HistoricalLandslideService:
    """
    Central service for historical landslide intelligence.
    Provides verified ISRO NRSC & GSI historical landslide records and village-level proximity analytics.
    """

    def __init__(self, adapter: Optional[HistoricalLandslideInventoryAdapter] = None):
        self.adapter = adapter or historical_landslide_adapter
        self._cache: Dict[str, VillageHistoricalLandslideSummary] = {}

    def get_inventory_overview(self, force_offline: bool = False) -> HistoricalLandslideInventoryResponse:
        """
        Retrieves the complete historical landslide catalog.
        """
        return self.adapter.get_all_events(force_offline=force_offline)

    def get_village_historical_summary(
        self, village_data: Dict[str, Any], force_offline: bool = False
    ) -> VillageHistoricalLandslideSummary:
        """
        Retrieves historical landslide proximity summary for a specific village.
        """
        village_id = village_data.get("id", "UNKNOWN")

        if village_id in self._cache and not force_offline:
            cached = self._cache[village_id]
            if cached.data_state == LandslideDataState.REAL_GIS:
                # Return cached state
                return cached

        summary = self.adapter.get_village_summary(village_data, force_offline=force_offline)
        if summary.data_state == LandslideDataState.REAL_GIS:
            self._cache[village_id] = summary

        return summary

    def clear_cache(self) -> None:
        """Clears in-memory cache for testing."""
        self._cache.clear()


# Global Singleton Service Instance
historical_landslide_service = HistoricalLandslideService()
