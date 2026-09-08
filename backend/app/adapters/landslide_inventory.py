"""
Historical Landslide Inventory Adapter for APADA MITRA.
Loads and processes verified historical landslide catalogs from ISRO NRSC & GSI.
"""
import json
import math
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from app.models.landslide import (
    HistoricalLandslideEvent,
    VillageHistoricalLandslideSummary,
    HistoricalLandslideInventoryResponse,
    LandslideDataState,
)

logger = logging.getLogger(__name__)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two WGS84 coordinate pairs in kilometers.
    """
    R = 6371.0  # Earth's mean radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)


class HistoricalLandslideInventoryAdapter:
    """
    Adapter for authoritative historical landslide records (ISRO NRSC Landslide Atlas of India / GSI NLSM).
    """

    def __init__(self, data_file_path: Optional[str] = None):
        if data_file_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.data_file_path = os.path.join(base_dir, "data", "isro_gsi_landslides.json")
        else:
            self.data_file_path = data_file_path

        self._cached_events: Optional[List[HistoricalLandslideEvent]] = None
        self._load_catalog()

    @property
    def name(self) -> str:
        return "ISRO NRSC Landslide Atlas of India (2023) / GSI National Landslide Inventory"

    @property
    def source_type(self) -> str:
        return "AUTHORITATIVE_GOVERNMENT_GIS_INVENTORY"

    @property
    def source_url(self) -> str:
        return "https://www.nrsc.gov.in/Landslide_Atlas_of_India"

    @property
    def geographic_coverage(self) -> str:
        return "Uttarakhand Himalayan Region (Alaknanda & Mandakini River Basins, Chamoli & Rudraprayag Districts)"

    @property
    def limitations(self) -> str:
        return (
            "Contains major documented historical landslides from satellite InSAR, optical surveys, and GSI/BRO records. "
            "Micro-scale unrecorded slope failures may exist in unmonitored ravines."
        )

    def _load_catalog(self) -> None:
        """Loads and parses verified historical landslide records from storage."""
        if not os.path.exists(self.data_file_path):
            logger.warning(f"Historical landslide dataset not found at {self.data_file_path}")
            self._cached_events = []
            return

        try:
            with open(self.data_file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                parsed = [HistoricalLandslideEvent(**item) for item in raw_data]
                self._cached_events = parsed
                logger.info(f"Loaded {len(parsed)} authoritative historical landslide records.")
        except Exception as e:
            logger.error(f"Failed to load historical landslide dataset: {e}")
            self._cached_events = []

    def get_all_events(self, force_offline: bool = False) -> HistoricalLandslideInventoryResponse:
        """
        Returns all historical landslide events with full provenance metadata.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        if self._cached_events is None:
            self._load_catalog()

        events = self._cached_events or []
        state = (
            LandslideDataState.OFFLINE_DEMO
            if force_offline
            else LandslideDataState.REAL_GIS
            if len(events) > 0
            else LandslideDataState.UNAVAILABLE
        )

        return HistoricalLandslideInventoryResponse(
            total_records=len(events),
            data_state=state,
            source_name=self.name,
            source_type=self.source_type,
            source_url=self.source_url,
            geographic_coverage=self.geographic_coverage,
            retrieved_at=now_iso,
            events=events,
            limitations=self.limitations,
        )

    def get_village_summary(
        self, village_data: Dict[str, Any], force_offline: bool = False
    ) -> VillageHistoricalLandslideSummary:
        """
        Calculates spatial proximity, event density, and historical susceptibility evidence for a village.
        """
        village_id = village_data.get("id", "UNKNOWN")
        village_name = village_data.get("name", "Unknown Village")
        now_iso = datetime.now(timezone.utc).isoformat()

        try:
            lat = float(village_data.get("latitude", 0.0))
            lon = float(village_data.get("longitude", 0.0))
        except (ValueError, TypeError):
            lat, lon = 999.0, 999.0

        # Validate coordinate range
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0) or abs(lat) > 89.0 or abs(lon) > 179.0:
            return VillageHistoricalLandslideSummary(
                village_id=village_id,
                village_name=village_name,
                latitude=0.0,
                longitude=0.0,
                total_events_in_region=0,
                events_within_5km=0,
                events_within_15km=0,
                nearest_event_id=None,
                nearest_event_distance_km=None,
                nearest_event_location=None,
                nearest_event_date=None,
                nearest_event_type=None,
                recent_events_count_post_2015=0,
                historical_susceptibility_evidence="UNAVAILABLE",
                data_state=LandslideDataState.UNAVAILABLE,
                source_name=self.name,
                source_type=self.source_type,
                source_url=self.source_url,
                retrieved_at=now_iso,
                limitations="Invalid geographic coordinates provided.",
            )

        if self._cached_events is None:
            self._load_catalog()

        events = self._cached_events or []
        state = (
            LandslideDataState.OFFLINE_DEMO
            if force_offline
            else LandslideDataState.REAL_GIS
            if len(events) > 0
            else LandslideDataState.UNAVAILABLE
        )

        if not events:
            return VillageHistoricalLandslideSummary(
                village_id=village_id,
                village_name=village_name,
                latitude=lat,
                longitude=lon,
                total_events_in_region=0,
                events_within_5km=0,
                events_within_15km=0,
                nearest_event_id=None,
                nearest_event_distance_km=None,
                nearest_event_location=None,
                nearest_event_date=None,
                nearest_event_type=None,
                recent_events_count_post_2015=0,
                historical_susceptibility_evidence="LOW_HISTORICAL_RECORDS",
                data_state=state,
                source_name=self.name,
                source_type=self.source_type,
                source_url=self.source_url,
                retrieved_at=now_iso,
                limitations=self.limitations,
            )

        # Compute distances to all catalog events
        events_with_dist = []
        for ev in events:
            dist = haversine_km(lat, lon, ev.latitude, ev.longitude)
            events_with_dist.append((dist, ev))

        events_with_dist.sort(key=lambda x: x[0])

        nearest_dist, nearest_ev = events_with_dist[0]
        within_5km = [ev for dist, ev in events_with_dist if dist <= 5.0]
        within_15km = [ev for dist, ev in events_with_dist if dist <= 15.0]
        within_50km = [ev for dist, ev in events_with_dist if dist <= 50.0]

        # Check if any catalog event is within the station's geographic region (within 50km)
        if nearest_dist > 50.0 or not within_50km:
            return VillageHistoricalLandslideSummary(
                village_id=village_id,
                village_name=village_name,
                latitude=lat,
                longitude=lon,
                total_events_in_region=0,
                events_within_5km=0,
                events_within_15km=0,
                nearest_event_id=None,
                nearest_event_distance_km=None,
                nearest_event_location=None,
                nearest_event_date=None,
                nearest_event_type=None,
                recent_events_count_post_2015=0,
                historical_susceptibility_evidence="LOW_HISTORICAL_RECORDS",
                data_state=LandslideDataState.UNAVAILABLE,
                source_name=self.name,
                source_type=self.source_type,
                source_url=self.source_url,
                retrieved_at=now_iso,
                limitations=f"No verified historical landslide events recorded within {village_name} geographic region in current catalog.",
            )

        # Recent events (post 2015)
        recent_count = 0
        for ev in within_15km:
            if ev.date:
                try:
                    year = int(ev.date.split("-")[0])
                    if year >= 2015:
                        recent_count += 1
                except Exception:
                    pass

        # Determine qualitative evidence level
        if nearest_dist <= 3.0 or len(within_15km) >= 3 or len(within_5km) >= 1:
            evidence = "HIGH_HISTORICAL_ACTIVITY"
        elif nearest_dist <= 8.0 or len(within_15km) >= 1:
            evidence = "MODERATE_HISTORICAL_ACTIVITY"
        else:
            evidence = "LOW_HISTORICAL_RECORDS"

        return VillageHistoricalLandslideSummary(
            village_id=village_id,
            village_name=village_name,
            latitude=lat,
            longitude=lon,
            total_events_in_region=len(within_50km),
            events_within_5km=len(within_5km),
            events_within_15km=len(within_15km),
            nearest_event_id=nearest_ev.event_id,
            nearest_event_distance_km=nearest_dist,
            nearest_event_location=nearest_ev.location_name,
            nearest_event_date=nearest_ev.date,
            nearest_event_type=nearest_ev.landslide_type,
            recent_events_count_post_2015=recent_count,
            historical_susceptibility_evidence=evidence,
            data_state=state,
            source_name=self.name,
            source_type=self.source_type,
            source_url=self.source_url,
            retrieved_at=now_iso,
            limitations=self.limitations,
        )


# Global Singleton Adapter Instance
historical_landslide_adapter = HistoricalLandslideInventoryAdapter()
