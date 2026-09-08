"""
Hydrological Telemetry Engine for APADA MITRA (Feature 8).
Coordinates river stage monitoring, CWC station registry, 4-tier source priority selection,
IoT water-level integration, and seamless feeding into the existing flood risk engine.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from app.models.hydrology import (
    HydrologicalStationRecord,
    HydrologicalObservation,
    HydrologySystemStatus,
    HydrologyDataState,
    HydrologyFreshnessStatus,
)
from app.models.domain import ScenarioType
from app.adapters.cwc_adapter import CWCHydrologicalAdapter
from app.engine.iot_store import iot_store_instance, IoTFreshnessStatus, IoTSensorType
from app.data.dataset import DEMO_VILLAGES, get_village_feature_snapshot

# Authoritative CWC Station Registry for Alaknanda and Mandakini River Basins
CWC_STATIONS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "CWC-001": {
        "station_id": "CWC-001",
        "station_name": "Joshimath Telemetry Station",
        "river_name": "Alaknanda River",
        "basin_name": "Ganga Basin - Upper Alaknanda Sub-basin",
        "latitude": 30.5500,
        "longitude": 79.5600,
        "warning_level_m": 1370.0,
        "danger_level_m": 1372.5,
        "hfl_m": 1374.8,
        "upstream_downstream_relationship": "Upstream gauge governing Alaknanda gorge down to Helang and Pipalkoti reaches.",
        "associated_village_ids": ["VIL-002"],
        "official_authority": "Central Water Commission (CWC), Middle Ganga Division",
    },
    "CWC-002": {
        "station_id": "CWC-002",
        "station_name": "Pipalkoti / Marwari Gauge Station",
        "river_name": "Alaknanda River",
        "basin_name": "Ganga Basin - Upper Alaknanda Sub-basin",
        "latitude": 30.4350,
        "longitude": 79.4280,
        "warning_level_m": 1245.0,
        "danger_level_m": 1248.0,
        "hfl_m": 1251.2,
        "upstream_downstream_relationship": "Middle Alaknanda valley station monitoring flood crest propagation towards Chamoli.",
        "associated_village_ids": ["VIL-001"],
        "official_authority": "Central Water Commission (CWC), Middle Ganga Division",
    },
    "CWC-003": {
        "station_id": "CWC-003",
        "station_name": "Govindghat / Bhyundar Confluence Gauge",
        "river_name": "Lakshman Ganga / Alaknanda River",
        "basin_name": "Ganga Basin - Bhyundar Ganga Tributary",
        "latitude": 30.6220,
        "longitude": 79.5620,
        "warning_level_m": 1815.0,
        "danger_level_m": 1818.0,
        "hfl_m": 1821.5,
        "upstream_downstream_relationship": "High-altitude confluence gauge monitoring glacial melt and cloudburst surges into Alaknanda.",
        "associated_village_ids": ["VIL-003", "VIL-004"],
        "official_authority": "Central Water Commission (CWC) / Uttarakhand Irrigation Dept",
    },
    "CWC-004": {
        "station_id": "CWC-004",
        "station_name": "Karnaprayag Confluence Gauge",
        "river_name": "Pindar & Alaknanda Rivers",
        "basin_name": "Ganga Basin - Pindar Sub-basin Confluence",
        "latitude": 30.2580,
        "longitude": 79.2180,
        "warning_level_m": 775.0,
        "danger_level_m": 778.0,
        "hfl_m": 781.0,
        "upstream_downstream_relationship": "Major confluence junction tracking flood discharge from Pindar glacial valley.",
        "associated_village_ids": ["VIL-005", "VIL-006"],
        "official_authority": "Central Water Commission (CWC), Middle Ganga Division",
    },
    "CWC-005": {
        "station_id": "CWC-005",
        "station_name": "Rudraprayag Sangam Hydrometric Station",
        "river_name": "Mandakini & Alaknanda Rivers",
        "basin_name": "Ganga Basin - Mandakini Confluence",
        "latitude": 30.2860,
        "longitude": 78.9810,
        "warning_level_m": 610.0,
        "danger_level_m": 613.0,
        "hfl_m": 616.5,
        "upstream_downstream_relationship": "Key Sangam confluence measuring combined flood volume from Kedarnath/Mandakini and Badrinath/Alaknanda basins.",
        "associated_village_ids": ["VIL-007", "VIL-008"],
        "official_authority": "Central Water Commission (CWC), Middle Ganga Division",
    },
    "CWC-006": {
        "station_id": "CWC-006",
        "station_name": "Kund / Ukhimath Mandakini Gauge",
        "river_name": "Mandakini River",
        "basin_name": "Ganga Basin - Upper Mandakini Sub-basin",
        "latitude": 30.5050,
        "longitude": 79.1150,
        "warning_level_m": 1100.0,
        "danger_level_m": 1103.5,
        "hfl_m": 1107.2,
        "upstream_downstream_relationship": "Upper Mandakini monitoring station below Kedarnath valley funnel.",
        "associated_village_ids": ["VIL-009", "VIL-010", "VIL-011", "VIL-012"],
        "official_authority": "Central Water Commission (CWC) / Uttarakhand Jal Vidyut Nigam",
    },
    "CWC-007": {
        "station_id": "CWC-007",
        "station_name": "Srinagar H.E. Reservoir Gauge",
        "river_name": "Alaknanda River",
        "basin_name": "Ganga Basin - Lower Alaknanda Reach",
        "latitude": 30.2180,
        "longitude": 78.7820,
        "warning_level_m": 535.0,
        "danger_level_m": 536.0,
        "hfl_m": 539.0,
        "upstream_downstream_relationship": "Downstream terminal reservoir reach regulating peak discharge to Devprayag.",
        "associated_village_ids": [],
        "official_authority": "Central Water Commission (CWC) / Alaknanda Hydro Power",
    },
}


class HydrologyEngine:
    """
    Central Hydrological Integration Engine.
    Implements 4-Tier Source Priority:
      Tier 1: REAL_LIVE_OFFICIAL (CWC / WIMS REST API if configured with active credentials)
      Tier 2: REAL_LIVE_IOT (Fresh water-level IoT sensor from Feature 3 registry)
      Tier 3: CACHED_OFFICIAL (Cached official observation within TTL)
      Tier 4: OFFLINE_DEMO (Modelled baseline from benchmark dataset, clearly labelled)
    """

    def __init__(self):
        self.cwc_adapter = CWCHydrologicalAdapter()
        self._cached_official_telemetry: Dict[str, Dict[str, Any]] = {}
        self._official_api_configured: bool = False
        self._last_checked_at = datetime.now(timezone.utc)

    def get_system_status(self) -> HydrologySystemStatus:
        """Returns the official connectivity status and architecture metadata."""
        now_iso = datetime.now(timezone.utc).isoformat()
        active_iot_sensors = [
            s for s in iot_store_instance.get_all_sensors()
            if s.sensor_type == IoTSensorType.WATER_LEVEL.value and s.status == IoTFreshnessStatus.LIVE
        ]

        official_status = "CONNECTED" if self._official_api_configured else "LIVE_OFFICIAL_SOURCE_UNAVAILABLE"

        return HydrologySystemStatus(
            official_live_status=official_status,
            official_authority="Central Water Commission (CWC) & India-WRIS (NWIC), Ministry of Jal Shakti, GoI",
            official_api_url="https://india-wris.gov.in/ / https://nwdp.nwic.gov.in/",
            registered_stations_count=len(CWC_STATIONS_REGISTRY),
            active_iot_water_sensors_count=len(active_iot_sensors),
            source_priority_order=[
                "1. REAL_LIVE_OFFICIAL (CWC / India-WRIS live telemetry)",
                "2. REAL_LIVE_IOT (Verified field ultrasound/radar water-level sensor)",
                "3. CACHED_OFFICIAL (Locally cached verified official telemetry)",
                "4. OFFLINE_DEMO (Hydrological terrain baseline, strictly labelled as demo)"
            ],
            last_checked_at=now_iso,
            disclaimer="Direct CWC API telemetry requires official government credentials / API gateway keys. In accordance with honesty principles, when unconfigured the system explicitly flags LIVE_OFFICIAL_SOURCE_UNAVAILABLE rather than fabricating live data."
        )

    def get_all_stations(self) -> List[HydrologicalStationRecord]:
        """Retrieves all registered CWC hydrological gauging stations."""
        return [HydrologicalStationRecord(**st) for st in CWC_STATIONS_REGISTRY.values()]

    def get_station_by_id(self, station_id: str) -> Optional[HydrologicalStationRecord]:
        """Retrieves a specific CWC station record by ID."""
        st = CWC_STATIONS_REGISTRY.get(station_id)
        if not st:
            return None
        return HydrologicalStationRecord(**st)

    def find_nearest_station_for_village(self, village_id: str) -> Optional[HydrologicalStationRecord]:
        """Maps a village ID to its primary hydrological reach station."""
        for st in CWC_STATIONS_REGISTRY.values():
            if village_id in st.get("associated_village_ids", []):
                return HydrologicalStationRecord(**st)
        
        # Fallback to CWC-002 for Chamoli or CWC-006 for Rudraprayag (Uttarakhand stations only)
        v = next((v for v in DEMO_VILLAGES if v["id"] == village_id), None)
        if v:
            if v.get("district") == "Rudraprayag":
                return HydrologicalStationRecord(**CWC_STATIONS_REGISTRY["CWC-006"])
            elif v.get("district") == "Chamoli":
                return HydrologicalStationRecord(**CWC_STATIONS_REGISTRY["CWC-002"])
        return None

    def evaluate_threshold_warning_status(
        self,
        water_level_m: Optional[float],
        station: Optional[HydrologicalStationRecord],
    ) -> Tuple[str, str]:
        """
        Evaluates warning status against station thresholds.

        Hydrology station warning/danger levels are defined in meters above Mean Sea Level (m MSL),
        whereas observed water levels represent local river stage depth in meters (m above local channel datum).
        Because the station gauge zero datum RL (elevation in m MSL) is unconfigured and cannot be
        established confidently without guessing or inventing measurements, direct comparison
        is marked as UNKNOWN rather than producing a misleading risk state.
        """
        if water_level_m is None:
            return "UNKNOWN", "Threshold comparison UNAVAILABLE: observation water level is missing."

        if not station or (station.warning_level_m is None and station.danger_level_m is None):
            return "UNKNOWN", "Threshold comparison UNAVAILABLE: station warning/danger thresholds not configured."

        return (
            "UNKNOWN",
            f"Threshold comparison UNKNOWN: Station {station.station_id} thresholds are in meters MSL "
            f"(Warning: {station.warning_level_m}m, Danger: {station.danger_level_m}m) while observation "
            f"({water_level_m}m) is in local gauge stage depth. Gauge zero datum is unconfigured; "
            "direct threshold comparison withheld to prevent misleading risk states."
        )

    def get_village_hydrology(
        self,
        village_id: str,
        scenario: ScenarioType = ScenarioType.NORMAL,
        force_offline: bool = False,
    ) -> Optional[HydrologicalObservation]:
        """
        Calculates the hydrological observation for a given village applying strict 4-tier source priority.
        """
        village = next((v for v in DEMO_VILLAGES if v["id"] == village_id), None)
        if not village:
            return None

        station = self.find_nearest_station_for_village(village_id)
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()

        default_river = (
            "Beas River" if village.get("district") == "Mandi"
            else ("Iruvaipuzha River" if village.get("district") == "Wayanad" else "Alaknanda River")
        )
        local_river = station.river_name if station else default_river

        # -------------------------------------------------------------
        # TIER 1: Official Live CWC Telemetry
        # -------------------------------------------------------------
        if not force_offline and self._official_api_configured:
            raw_cwc = self.cwc_adapter.fetch(village["latitude"], village["longitude"])
            if raw_cwc:
                obs_time = raw_cwc.get("timestamp", now_iso)
                stage_m = raw_cwc.get("water_level_m", 1.0)
                discharge = raw_cwc.get("discharge_cumecs")
                stage_ratio = raw_cwc.get("river_stage_ratio", 1.0)

                # Compute flood risk contribution (0 - 10 pts)
                # Normalization maps stage_ratio [1.0, 3.0] to [0.0, 1.0] -> * 10 pts
                norm_stage = max(0.0, min(1.0, (stage_ratio - 1.0) / 2.0))
                risk_pts = round(norm_stage * 10.0, 2)
                warning_stat, threshold_note = self.evaluate_threshold_warning_status(stage_m, station)

                return HydrologicalObservation(
                    station_id=station.station_id if station else None,
                    station_name=station.station_name if station else None,
                    village_id=village_id,
                    village_name=village["name"],
                    river_name=local_river,
                    latitude=village["latitude"],
                    longitude=village["longitude"],
                    water_level_m=stage_m,
                    river_stage_ratio=stage_ratio,
                    discharge_cumecs=discharge,
                    observation_time=obs_time,
                    fetched_at=now_iso,
                    source="Central Water Commission (CWC) Official Telemetry API",
                    source_url="https://india-wris.gov.in/",
                    data_state=HydrologyDataState.REAL_LIVE_OFFICIAL,
                    freshness=HydrologyFreshnessStatus.LIVE,
                    freshness_seconds=0.0,
                    upstream_downstream_relationship=station.upstream_downstream_relationship if station else None,
                    quality_status="GOOD",
                    warning_status=warning_stat,
                    risk_contribution_pts=risk_pts,
                    assumptions=[
                        "Live official CWC telemetry feed directly connected.",
                        threshold_note,
                    ],
                )

        # -------------------------------------------------------------
        # TIER 2: Real Live IoT Water-Level Sensor (Feature 3)
        # -------------------------------------------------------------
        if not force_offline:
            village_sensors = iot_store_instance.get_village_sensors(village_id)
            live_water_sensor = next(
                (s for s in village_sensors if s.sensor_type == IoTSensorType.WATER_LEVEL.value and s.status == IoTFreshnessStatus.LIVE),
                None
            )
            if live_water_sensor is not None:
                val = float(live_water_sensor.value)
                stage_ratio = round(max(1.0, val), 2)
                norm_stage = max(0.0, min(1.0, (stage_ratio - 1.0) / 2.0))
                risk_pts = round(norm_stage * 10.0, 2)

                age_secs = live_water_sensor.freshness_seconds
                freshness = HydrologyFreshnessStatus.LIVE if age_secs <= 900.0 else HydrologyFreshnessStatus.FRESH
                warning_stat, threshold_note = self.evaluate_threshold_warning_status(val, station)

                return HydrologicalObservation(
                    station_id=station.station_id if station else None,
                    station_name=station.station_name if station else None,
                    village_id=village_id,
                    village_name=village["name"],
                    river_name=station.river_name if station else "Local River Channel",
                    latitude=village["latitude"],
                    longitude=village["longitude"],
                    water_level_m=val,
                    river_stage_ratio=stage_ratio,
                    discharge_cumecs=None,
                    observation_time=live_water_sensor.timestamp,
                    fetched_at=now_iso,
                    source=f"IoT Water-Level Sensor ({live_water_sensor.sensor_id})",
                    source_url="https://apada-mitra.local/api/iot/sensors",
                    data_state=HydrologyDataState.REAL_LIVE_IOT,
                    freshness=freshness,
                    freshness_seconds=age_secs,
                    upstream_downstream_relationship=station.upstream_downstream_relationship if station else "Local stream stage sensor",
                    quality_status="GOOD",
                    warning_status=warning_stat,
                    risk_contribution_pts=risk_pts,
                    assumptions=[
                        f"Live telemetry ingested from physical IoT water-level sensor {live_water_sensor.sensor_id}.",
                        f"Reported water depth/gauge level: {val} m.",
                        threshold_note,
                    ],
                )

        # -------------------------------------------------------------
        # TIER 3: Cached Official Observation
        # -------------------------------------------------------------
        cached = self._cached_official_telemetry.get(village_id)
        if cached and not force_offline:
            obs_time = cached.get("timestamp", now_iso)
            try:
                age_secs = (now_dt - datetime.fromisoformat(obs_time)).total_seconds()
            except Exception:
                age_secs = 600.0

            if age_secs < 10800.0:  # 3 hours TTL
                freshness = (
                    HydrologyFreshnessStatus.FRESH if age_secs <= 3600.0
                    else HydrologyFreshnessStatus.STALE
                )
                stage_ratio = cached.get("river_stage_ratio", 1.0)
                norm_stage = max(0.0, min(1.0, (stage_ratio - 1.0) / 2.0))
                risk_pts = round(norm_stage * 10.0, 2)
                cached_stage = cached.get("water_level_m", 1.0)
                warning_stat, threshold_note = self.evaluate_threshold_warning_status(cached_stage, station)

                return HydrologicalObservation(
                    station_id=station.station_id if station else None,
                    station_name=station.station_name if station else None,
                    village_id=village_id,
                    village_name=village["name"],
                    river_name=local_river,
                    latitude=village["latitude"],
                    longitude=village["longitude"],
                    water_level_m=cached_stage,
                    river_stage_ratio=stage_ratio,
                    discharge_cumecs=cached.get("discharge_cumecs"),
                    observation_time=obs_time,
                    fetched_at=now_iso,
                    source="Cached CWC Hydrological Telemetry",
                    source_url="https://india-wris.gov.in/",
                    data_state=HydrologyDataState.CACHED_OFFICIAL,
                    freshness=freshness,
                    freshness_seconds=round(age_secs, 1),
                    upstream_downstream_relationship=station.upstream_downstream_relationship if station else None,
                    quality_status="GOOD",
                    warning_status=warning_stat,
                    risk_contribution_pts=risk_pts,
                    assumptions=[
                        "Observation retrieved from local high-availability cache.",
                        threshold_note,
                    ],
                )

        # -------------------------------------------------------------
        # TIER 4: Offline Modelled Baseline (Clearly Labelled)
        # -------------------------------------------------------------
        demo_snapshot = get_village_feature_snapshot(village["id"], scenario)
        demo_river_level = float(demo_snapshot.get("river_water_level", 1.0))
        norm_stage = max(0.0, min(1.0, (demo_river_level - 1.0) / 2.0))
        risk_pts = round(norm_stage * 10.0, 2)
        warning_stat, threshold_note = self.evaluate_threshold_warning_status(demo_river_level, station)

        return HydrologicalObservation(
            station_id=station.station_id if station else None,
            station_name=station.station_name if station else None,
            village_id=village_id,
            village_name=village["name"],
            river_name=local_river,
            latitude=village["latitude"],
            longitude=village["longitude"],
            water_level_m=demo_river_level,
            river_stage_ratio=demo_river_level,
            discharge_cumecs=round(demo_river_level * 145.0, 1),
            observation_time=now_iso,
            fetched_at=now_iso,
            source="Offline Hydrological Model Baseline",
            source_url="https://apada-mitra.local/data/demo",
            data_state=HydrologyDataState.OFFLINE_DEMO,
            freshness=HydrologyFreshnessStatus.OFFLINE,
            freshness_seconds=0.0,
            upstream_downstream_relationship=station.upstream_downstream_relationship if station else None,
            quality_status="DEMO",
            warning_status=warning_stat,
            risk_contribution_pts=risk_pts,
            assumptions=[
                "Official CWC live API credentials unconfigured (LIVE_OFFICIAL_SOURCE_UNAVAILABLE).",
                "No live IoT water-level sensor active for this village.",
                f"Falling back to scenario hydrological baseline ({scenario.value}: {demo_river_level}x stage depth).",
                threshold_note,
                "DISCLAIMER: This observation is explicitly labelled OFFLINE_DEMO and is NOT a verified real-time CWC reading."
            ],
        )

    def get_station_observation(
        self,
        station_id: str,
        scenario: ScenarioType = ScenarioType.NORMAL,
        force_offline: bool = False,
    ) -> Optional[HydrologicalObservation]:
        """Calculates observation for a specific CWC gauging station."""
        station = self.get_station_by_id(station_id)
        if not station:
            return None

        paired_village_id = station.associated_village_ids[0] if station.associated_village_ids else "VIL-001"
        obs = self.get_village_hydrology(paired_village_id, scenario=scenario, force_offline=force_offline)
        if obs:
            obs.station_id = station.station_id
            obs.station_name = station.station_name
            obs.river_name = station.river_name
            obs.latitude = station.latitude
            obs.longitude = station.longitude
            obs.upstream_downstream_relationship = station.upstream_downstream_relationship
            warning_stat, threshold_note = self.evaluate_threshold_warning_status(obs.water_level_m, station)
            obs.warning_status = warning_stat
            if threshold_note and threshold_note not in obs.assumptions:
                if obs.assumptions and "OFFLINE_DEMO" in obs.assumptions[-1]:
                    obs.assumptions.insert(-1, threshold_note)
                else:
                    obs.assumptions.append(threshold_note)
        return obs


hydrology_engine_instance = HydrologyEngine()
