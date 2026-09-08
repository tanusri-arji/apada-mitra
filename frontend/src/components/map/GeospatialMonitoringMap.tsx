import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { VillageRiskDetail, RoadSegment, Shelter, EvacuationRouteResult, LandslideRiskDetail } from '../../types';
import { getRiskColorHex } from '../../utils/riskColors';
import { getStationMetadata } from '../../utils/stationMetadata';
import { CANONICAL_VILLAGES_MAP } from '../../data/canonicalVillages';
import { CANONICAL_SHELTERS_MAP } from '../../data/canonicalShelters';
import {
  RotateCcw,
  MapPin,
  Compass,
  CheckCircle2,
  Mountain,
  Layers,
} from 'lucide-react';

export type RegionFilter = 'ALL' | 'UTTARAKHAND' | 'HIMACHAL' | 'KERALA';
export type BasemapMode = 'TERRAIN' | 'SATELLITE';

export const BASEMAP_CONFIGS: Record<
  BasemapMode,
  {
    url: string;
    attribution: string;
    maxZoom: number;
    maxNativeZoom: number;
    subdomains?: string | string[];
  }
> = {
  TERRAIN: {
    url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    subdomains: ['a', 'b', 'c'],
    attribution: 'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, SRTM | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a>',
    maxZoom: 19,
    maxNativeZoom: 17,
  },
  SATELLITE: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
    maxZoom: 19,
    maxNativeZoom: 19,
  },
};

interface Props {
  villages: VillageRiskDetail[];
  roads?: RoadSegment[];
  shelters?: Shelter[];
  landslides?: LandslideRiskDetail[];
  activeRoute?: EvacuationRouteResult | null;
  selectedVillageId: string | null;
  onSelectVillage: (id: string) => void;
  isSimulationActive?: boolean;
}

// Bounding coordinates for authoritative project regions
const REGION_BOUNDS: Record<RegionFilter, L.LatLngBoundsExpression> = {
  ALL: [
    [11.40, 76.00],
    [31.90, 79.75],
  ],
  UTTARAKHAND: [
    [30.20, 78.90],
    [30.80, 79.65],
  ],
  HIMACHAL: [
    [31.68, 77.10],
    [31.80, 77.22],
  ],
  KERALA: [
    [11.45, 76.05],
    [11.60, 76.22],
  ],
};

/**
 * Normalizes state name string to standard RegionFilter key.
 */
export function normalizeStateToRegion(state?: string | null): RegionFilter {
  if (!state) return 'UTTARAKHAND';
  const clean = state.trim().toLowerCase();
  if (clean.includes('himachal')) return 'HIMACHAL';
  if (clean.includes('kerala')) return 'KERALA';
  if (clean.includes('uttarakhand')) return 'UTTARAKHAND';
  return 'UTTARAKHAND';
}

/**
 * Resolves explicit canonical state identity for a village entity or village ID.
 */
export function getVillageState(village: VillageRiskDetail | string | null | undefined): string {
  if (!village) return 'Uttarakhand';
  if (typeof village === 'string') {
    const meta = CANONICAL_VILLAGES_MAP[village];
    return meta?.state || 'Uttarakhand';
  }
  if (village.state) return village.state;
  if (village.district) {
    const d = village.district.toLowerCase();
    if (d.includes('mandi')) return 'Himachal Pradesh';
    if (d.includes('wayanad')) return 'Kerala';
    if (d.includes('chamoli') || d.includes('rudraprayag')) return 'Uttarakhand';
  }
  const meta = CANONICAL_VILLAGES_MAP[village.village_id];
  return meta?.state || 'Uttarakhand';
}

export function getRegionForVillage(village: VillageRiskDetail | string | null | undefined): RegionFilter {
  return normalizeStateToRegion(getVillageState(village));
}

/**
 * Resolves explicit canonical state identity for a relief shelter entity or shelter ID.
 */
export function getShelterState(shelter: Shelter | string | null | undefined): string {
  if (!shelter) return 'Uttarakhand';
  if (typeof shelter === 'string') {
    const meta = CANONICAL_SHELTERS_MAP[shelter];
    return meta?.state || 'Uttarakhand';
  }
  if (shelter.state) return shelter.state;
  if ((shelter as any).district) {
    const d = (shelter as any).district.toLowerCase();
    if (d.includes('mandi')) return 'Himachal Pradesh';
    if (d.includes('wayanad')) return 'Kerala';
    if (d.includes('chamoli') || d.includes('rudraprayag')) return 'Uttarakhand';
  }
  const meta = CANONICAL_SHELTERS_MAP[shelter.id];
  return meta?.state || 'Uttarakhand';
}

export function getRegionForShelter(shelter: Shelter | string | null | undefined): RegionFilter {
  return normalizeStateToRegion(getShelterState(shelter));
}

/**
 * Resolves state identity for graph nodes (either village or shelter).
 */
export function getNodeState(nodeId?: string | null): string {
  if (!nodeId) return 'Uttarakhand';
  if (CANONICAL_VILLAGES_MAP[nodeId]) {
    return CANONICAL_VILLAGES_MAP[nodeId].state;
  }
  if (CANONICAL_SHELTERS_MAP[nodeId]) {
    return CANONICAL_SHELTERS_MAP[nodeId].state;
  }
  return 'Uttarakhand';
}

/**
 * Resolves explicit state identity for a road segment via its canonical endpoint nodes.
 */
export function getRoadState(road: RoadSegment): string {
  if (road.state) return road.state;
  if (road.source_id) {
    return getNodeState(road.source_id);
  }
  if (road.target_id) {
    return getNodeState(road.target_id);
  }
  return 'Uttarakhand';
}

export function getRegionForRoad(road: RoadSegment): RegionFilter {
  return normalizeStateToRegion(getRoadState(road));
}

export const GeospatialMonitoringMap: React.FC<Props> = ({
  villages,
  roads = [],
  shelters = [],
  landslides = [],
  activeRoute = null,
  selectedVillageId,
  onSelectVillage,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);

  // Basemap Switcher State (Default: SATELLITE)
  const [basemapMode, setBasemapMode] = useState<BasemapMode>('SATELLITE');
  const tileLayerRef = useRef<L.TileLayer | null>(null);

  // Layer Group Refs
  const villageLayerRef = useRef<L.LayerGroup | null>(null);
  const roadLayerRef = useRef<L.LayerGroup | null>(null);
  const shelterLayerRef = useRef<L.LayerGroup | null>(null);
  const allShelterLayerRef = useRef<L.LayerGroup | null>(null); 
  const routeLayerRef = useRef<L.LayerGroup | null>(null);

  // Map Ready State to synchronize layer rendering
  const [isMapInitialized, setIsMapInitialized] = useState(false);

  // Region Filter State
  const [selectedRegion, setSelectedRegion] = useState<RegionFilter>('ALL');

  // Layer Visibility Toggles
  const [showVillages, setShowVillages] = useState(true);
  const [showRoads, setShowRoads] = useState(true);
  const [showShelters, setShowShelters] = useState(true);
  const [showRoute, setShowRoute] = useState(true);
  const [isLegendOpen, setIsLegendOpen] = useState(false);

  // Filtered Datasets based on Region
  const filteredVillages = useMemo(() => {
    if (selectedRegion === 'ALL') return villages;
    return villages.filter((v) => getRegionForVillage(v) === selectedRegion);
  }, [villages, selectedRegion]);

  const filteredRoads = useMemo(() => {
    if (selectedRegion === 'ALL') return roads;
    return roads.filter((r) => getRegionForRoad(r) === selectedRegion);
  }, [roads, selectedRegion]);

  // Initialize Leaflet Map Instance
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [30.45, 79.30],
      zoom: 11,
      minZoom: 4,
      maxZoom: 19,
      zoomControl: false,
      attributionControl: false,
      preferCanvas: true,
    });

    // Custom attribution control on bottom-left to prevent overlap with bottom-right legend
    L.control.attribution({
      position: 'bottomleft',
      prefix: false,
    }).addTo(map);

    L.control.zoom({ position: 'topright' }).addTo(map);
        roadLayerRef.current = L.layerGroup().addTo(map);
        shelterLayerRef.current = L.layerGroup().addTo(map);
        allShelterLayerRef.current = L.layerGroup().addTo(map);
        routeLayerRef.current = L.layerGroup().addTo(map);
        villageLayerRef.current = L.layerGroup().addTo(map);

    mapRef.current = map;
    setIsMapInitialized(true);

    map.fitBounds(REGION_BOUNDS.UTTARAKHAND, { padding: [40, 40], maxZoom: 11 });

    const resizeObserver = new ResizeObserver(() => {
      map.invalidateSize();
    });
    resizeObserver.observe(mapContainerRef.current);

    // Initial size invalidation safeguards for smooth flexbox layout rendering
    const t1 = setTimeout(() => map.invalidateSize(), 150);
    const t2 = setTimeout(() => map.invalidateSize(), 500);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      resizeObserver.disconnect();
      map.remove();
      mapRef.current = null;
      setIsMapInitialized(false);
    };
  }, []);

  // Synchronize Active Basemap Tile Layer
  useEffect(() => {
    if (!mapRef.current || !isMapInitialized) return;
    const map = mapRef.current;

    if (tileLayerRef.current) {
      map.removeLayer(tileLayerRef.current);
      tileLayerRef.current = null;
    }

    const config = BASEMAP_CONFIGS[basemapMode];
    const newTileLayer = L.tileLayer(config.url, {
      maxZoom: config.maxZoom,
      maxNativeZoom: config.maxNativeZoom,
      subdomains: config.subdomains || 'abc',
      attribution: config.attribution,
    });

    newTileLayer.on('tileerror', (error) => {
      console.warn(`[Basemap] Error loading tile for ${basemapMode}:`, error);
    });

    newTileLayer.addTo(map);
    newTileLayer.bringToBack();
    tileLayerRef.current = newTileLayer;
    map.invalidateSize();
  }, [isMapInitialized, basemapMode]);

  const prevSelectedVillageRef = useRef<string | null>(null);

  // Sync Selected Village
  useEffect(() => {
    if (!mapRef.current || !selectedVillageId) return;

    const targetVillage = villages.find((v) => v.village_id === selectedVillageId);
    if (targetVillage && targetVillage.latitude && targetVillage.longitude) {
      if (prevSelectedVillageRef.current === selectedVillageId) return;
      prevSelectedVillageRef.current = selectedVillageId;

      const vRegion = getRegionForVillage(selectedVillageId);
      if (selectedRegion !== 'ALL' && selectedRegion !== vRegion) {
        setSelectedRegion(vRegion);
      }

      mapRef.current.flyTo([targetVillage.latitude, targetVillage.longitude], 12, {
        duration: 0.8,
      });
    }
  }, [selectedVillageId, villages]);

  // Render Village Markers
  useEffect(() => {
    if (!isMapInitialized) return;
    const layer = villageLayerRef.current;
    if (!layer) return;

    layer.clearLayers();
    if (!showVillages) return;

    filteredVillages.forEach((v) => {
      const isSelected = v.village_id === selectedVillageId;
      const riskColor = getRiskColorHex(v.risk_level);
      const vMeta = getStationMetadata(v.village_id);
      const score = Math.round(v.flash_flood_risk_score || 0);
      const slopeVal = v.slope ?? CANONICAL_VILLAGES_MAP[v.village_id]?.slope;

      const lsDetail = landslides.find((l) => l.village_id === v.village_id);
      const lsScore = v.landslide_risk_score ?? lsDetail?.landslide_risk_score;
      const lsLevel = v.landslide_risk_level ?? lsDetail?.risk_level;
      let landslideDisplay = 'Unavailable';
      if (lsLevel && lsScore != null) {
        landslideDisplay = `${lsLevel} (${Math.round(lsScore)}%)`;
      } else if (lsLevel) {
        landslideDisplay = `${lsLevel}`;
      } else if (lsScore != null) {
        landslideDisplay = `${Math.round(lsScore)}%`;
      }

      const riverFactor = v.factors?.find((f) => f.feature_key === 'river_water_level');
      let riverStageDisplay = 'Unavailable';
      if (riverFactor && riverFactor.raw_value != null) {
        riverStageDisplay = `${riverFactor.raw_value} ${riverFactor.unit || ''} (DEMO)`.trim();
      }

      const customIcon = L.divIcon({
        className: 'custom-village-icon',
        html: `
          <div class="relative flex items-center justify-center cursor-pointer group" style="transform: translate(-50%, -50%);">
            ${
              isSelected
                ? `<div class="absolute -inset-3 rounded-full border-2 border-[#FF7A18] animate-ping opacity-75"></div>
                   <div class="absolute -inset-1.5 rounded-full border-2 border-[#FFB703]"></div>`
                : ''
            }
            ${
              v.risk_level === 'CRITICAL'
                ? `<div class="absolute -inset-2 rounded-full bg-red-500/30 animate-pulse"></div>`
                : ''
            }
            <div
              class="w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-black font-mono text-white shadow-xl transition-transform duration-200 group-hover:scale-125"
              style="background-color: ${riskColor}; border: 2px solid ${isSelected ? '#FFB703' : '#ffffff'};"
            >
              #${vMeta.stationNumber.toString().padStart(2, '0')}
            </div>
            <div class="absolute top-8 left-1/2 -translate-x-1/2 bg-[#14181D] border border-white/15 px-2 py-0.5 rounded-lg text-[9px] font-mono font-bold text-white whitespace-nowrap shadow-xl pointer-events-none">
              ${v.village_name}
            </div>
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      const marker = L.marker([v.latitude, v.longitude], { icon: customIcon });

      marker.on('click', () => {
        onSelectVillage(v.village_id);
      });

      marker.bindPopup(`
        <div style="font-family: monospace; font-size: 11px; padding: 4px; color: #FFFFFF; min-width: 190px;">
          <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 4px; margin-bottom: 6px;">
            <strong style="color: #FFFFFF; font-size: 13px;">${v.village_name}</strong>
            <span style="background: ${riskColor}33; color: ${riskColor}; border: 1px solid ${riskColor}; padding: 1px 5px; border-radius: 6px; font-weight: bold; font-size: 10px;">
              ${v.risk_level} (${score}%)
            </span>
          </div>
          <div style="display: grid; gap: 3px; font-size: 11px; color: #9CA3AF;">
            <div>Region: <strong style="color: #FFFFFF;">${vMeta.region}</strong></div>
            <div>Elevation: <strong style="color: #FFFFFF;">${v.elevation != null ? `${v.elevation} m` : 'Unavailable'}</strong></div>
            <div>Slope: <strong style="color: #FFFFFF;">${slopeVal != null ? `${slopeVal}°` : 'Unavailable'}</strong></div>
            <div>River Stage: <strong style="color: #FFFFFF;">${riverStageDisplay}</strong></div>
            <div>Landslide Risk: <strong style="color: #FFFFFF;">${landslideDisplay}</strong></div>
            <div>Population: <strong style="color: #FFFFFF;">${v.population != null ? v.population.toLocaleString() : 'Unavailable'}</strong></div>
            <div>Exposed: <strong style="color: #EF4444;">${v.exposure?.population_exposed != null ? v.exposure.population_exposed.toLocaleString() : 'Unavailable'}</strong></div>
          </div>
          <button
            onclick="window.dispatchEvent(new CustomEvent('apada:select-station', { detail: '${v.village_id}' }))"
            style="margin-top: 8px; width: 100%; background: linear-gradient(to right, #FF7A18, #FFB703); color: #000000; border: none; padding: 5px 8px; border-radius: 8px; font-weight: 800; cursor: pointer;"
          >
            INSPECT STATION
          </button>
        </div>
      `, {
        className: 'dark-leaflet-popup',
      });

      layer.addLayer(marker);
    });
  }, [isMapInitialized, filteredVillages, selectedVillageId, showVillages, onSelectVillage, landslides]);

  // Global listener for Leaflet popup click
  useEffect(() => {
    const handleStationSelect = (e: any) => {
      if (e.detail) {
        onSelectVillage(e.detail);
      }
    };
    window.addEventListener('apada:select-station', handleStationSelect);
    return () => {
      window.removeEventListener('apada:select-station', handleStationSelect);
    };
  }, [onSelectVillage]);

  // Render Road Network Polylines
  useEffect(() => {
    if (!isMapInitialized) return;
    const layer = roadLayerRef.current;
    if (!layer) return;

    layer.clearLayers();
    if (!showRoads) return;

    filteredRoads.forEach((r) => {
      let color = '#10B981'; // EMERALD (Safe road)
      let dashArray = undefined;
      let opacity = 0.85;
      let weight = 3.5;

      if (r.status === 'DEGRADED') {
        color = '#F59E0B'; // AMBER
        dashArray = '6, 6';
      } else if (r.status === 'BLOCKED') {
        color = '#EF4444'; // RED
        dashArray = '4, 4';
        opacity = 0.95;
        weight = 4;
      }

      const polyline = L.polyline(r.coordinates as L.LatLngExpression[], {
        color,
        weight,
        opacity,
        dashArray,
      });

      polyline.bindTooltip(`
        <div style="font-family: monospace; font-size: 11px;">
          <strong>${r.name}</strong><br/>
          Hazard Status: <span style="color: ${color}; font-weight: bold;">MODELED ${r.status}</span><br/>
          Distance: ${r.distance_km} km
        </div>
      `, { sticky: true, className: 'dark-leaflet-tooltip' });

      layer.addLayer(polyline);
    });
  }, [isMapInitialized, filteredRoads, showRoads]);

  const [activeVillageShelterCandidates, setActiveVillageShelterCandidates] = useState<any[]>([]);
  const villagesRef = useRef(villages);
  const sheltersRef = useRef(shelters);

  useEffect(() => {
    villagesRef.current = villages;
    sheltersRef.current = shelters;
  }, [villages, shelters]);

  // Fetch or filter candidate shelters for the selected village only
  useEffect(() => {
    if (!selectedVillageId) {
      setActiveVillageShelterCandidates([]);
      return;
    }

    fetch(`/api/shelters/villages/${selectedVillageId}/candidates`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setActiveVillageShelterCandidates(data);
        } else {
          // Local Haversine fallback <= 15km
          const v = villagesRef.current.find((x) => x.village_id === selectedVillageId);
          if (v) {
            const local = sheltersRef.current.filter((s) => {
              const R = 6371.0;
              const dlat = (s.latitude - v.latitude) * (Math.PI / 180.0);
              const dlon = (s.longitude - v.longitude) * (Math.PI / 180.0);
              const a =
                Math.sin(dlat / 2.0) ** 2 +
                Math.cos(v.latitude * (Math.PI / 180.0)) *
                  Math.cos(s.latitude * (Math.PI / 180.0)) *
                  Math.sin(dlon / 2.0) ** 2;
              const dist = R * 2.0 * Math.atan2(Math.sqrt(a), Math.sqrt(1.0 - a));
              return dist <= 15.0;
            });
            setActiveVillageShelterCandidates(local);
          }
        }
      })
      .catch(() => {
        const v = villagesRef.current.find((x) => x.village_id === selectedVillageId);
        if (v) {
          const local = sheltersRef.current.filter((s) => {
            const R = 6371.0;
            const dlat = (s.latitude - v.latitude) * (Math.PI / 180.0);
            const dlon = (s.longitude - v.longitude) * (Math.PI / 180.0);
            const a =
              Math.sin(dlat / 2.0) ** 2 +
              Math.cos(v.latitude * (Math.PI / 180.0)) *
                Math.cos(s.latitude * (Math.PI / 180.0)) *
                Math.sin(dlon / 2.0) ** 2;
            const dist = R * 2.0 * Math.atan2(Math.sqrt(a), Math.sqrt(1.0 - a));
            return dist <= 15.0;
          });
          setActiveVillageShelterCandidates(local);
        }
      });
  }, [selectedVillageId]);

      // Render ALL registered shelters as persistent subtle markers (always visible)
  useEffect(() => {
    if (!isMapInitialized) return;
    const layer = allShelterLayerRef.current;
    if (!layer) return;
    layer.clearLayers();
    if (!showShelters) return;
    shelters.forEach((s: any) => {
      const sLat = s.latitude;
      const sLon = s.longitude;
      const sName = s.shelter_name || s.name;
      if (sLat == null || sLon == null) return;
            const allShelterIcon = L.divIcon({
        className: 'custom-all-shelter-icon',
        html: `
          <div style="transform: translate(-50%, -50%);" class="cursor-pointer group">
            <div style="width:22px;height:22px;border-radius:8px;background:#181D22;border:1.5px solid #FFB703;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(0,0,0,0.5);" class="group-hover:scale-125 transition-transform">
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#FFB703" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/></svg>
            </div>
          </div>
        `,
        iconSize: [22, 22],
        iconAnchor: [11, 11],
      });
      const marker = L.marker([sLat, sLon], { icon: allShelterIcon });
      const sType = s.shelter_type || 'Relief Shelter';
      const sState = s.state || '';
      const sDistrict = s.district || '';
      const sCap = s.total_capacity != null ? `${s.total_capacity} beds` : 'Not published';
      marker.bindPopup(
        `<div style="font-family: monospace; font-size: 11px; padding: 4px; color: #FFFFFF; min-width: 190px;">
          <div style="border-bottom: 1px solid rgba(255,255,255,0.15); padding-bottom: 4px; margin-bottom: 6px;">
            <strong style="color: #FFB703; font-size: 12px;">${sName}</strong>
          </div>
          <div style="display: grid; gap: 3px; font-size: 11px; color: #9CA3AF;">
            <div>Type: <strong style="color: #FFFFFF;">${sType}</strong></div>
            <div>Location: <strong style="color: #FFFFFF;">${sDistrict}${sDistrict && sState ? ', ' : ''}${sState}</strong></div>
            <div>Capacity: <strong style="color: #FFFFFF;">${sCap}</strong></div>
          </div>
        </div>`,
        { className: 'dark-leaflet-popup' }
      );
      layer.addLayer(marker);
    });
    }, [isMapInitialized, showShelters, shelters]);

  // Render Shelter Markers & Connecting Vector Lines for Selected Village Only
  useEffect(() => {
    if (!isMapInitialized) return;
    const layer = shelterLayerRef.current;
if (!layer) return;

    layer.clearLayers();
   if (!showShelters || !selectedVillageId) return;

    const targetVillage = villages.find((v) => v.village_id === selectedVillageId);

    activeVillageShelterCandidates.forEach((cand) => {
      const sLat = cand.latitude;
      const sLon = cand.longitude;
      const sName = cand.shelter_name || cand.name;
      const sId = cand.shelter_id || cand.id;
      const isDestination = activeRoute?.destination_shelter_id === sId;

      let straightDist = cand.straight_line_distance_km;
      if (straightDist == null && targetVillage) {
        const R = 6371.0;
        const dlat = (sLat - targetVillage.latitude) * (Math.PI / 180.0);
        const dlon = (sLon - targetVillage.longitude) * (Math.PI / 180.0);
        const a =
          Math.sin(dlat / 2.0) ** 2 +
          Math.cos(targetVillage.latitude * (Math.PI / 180.0)) *
            Math.cos(sLat * (Math.PI / 180.0)) *
            Math.sin(dlon / 2.0) ** 2;
        straightDist = Math.round(R * 2.0 * Math.atan2(Math.sqrt(a), Math.sqrt(1.0 - a)) * 10.0) / 10.0;
      }

      const routeDist = cand.route_distance_km;

      // Draw subtle connecting line from selected village to candidate shelter
      if (targetVillage && targetVillage.latitude && targetVillage.longitude) {
        const connLine = L.polyline(
          [
            [targetVillage.latitude, targetVillage.longitude],
            [sLat, sLon],
          ],
          {
            color: '#FFB703',
            weight: 1.5,
            dashArray: '4, 4',
            opacity: 0.5,
          }
        );
        layer.addLayer(connLine);
      }

      const shelterIcon = L.divIcon({
        className: 'custom-shelter-icon',
        html: `
          <div class="relative flex items-center justify-center cursor-pointer group" style="transform: translate(-50%, -50%);">
            ${
              isDestination
                ? `<div class="absolute -inset-3 rounded-xl border-2 border-emerald-400 animate-ping opacity-75"></div>`
                : ''
            }
            <div
              class="w-7 h-7 rounded-xl flex items-center justify-center shadow-xl transition-transform duration-200 group-hover:scale-125 ${
                isDestination
                  ? 'bg-emerald-500 border-2 border-white ring-2 ring-emerald-400 text-black'
                  : 'bg-[#181D22] border border-[#FFB703]/80 text-[#FFB703]'
              }"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/></svg>
            </div>
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      const marker = L.marker([sLat, sLon], { icon: shelterIcon });

      const capText = cand.total_capacity != null ? `${cand.total_capacity} beds` : 'Not published';
      const availText = cand.available_capacity != null ? `${cand.available_capacity} beds` : 'Not published';
      const routeText = routeDist != null ? `${routeDist.toFixed(1)} km` : 'Calculated on Evacuation Route';

      marker.bindPopup(
        `
        <div style="font-family: monospace; font-size: 11px; padding: 4px; color: #FFFFFF; min-width: 210px;">
          <div style="border-bottom: 1px solid rgba(255,255,255,0.15); padding-bottom: 4px; margin-bottom: 6px;">
            <strong style="color: #FFB703; font-size: 12px;">${sName}</strong>
          </div>
          <div style="display: grid; gap: 3px; font-size: 11px; color: #9CA3AF;">
            <div>Proximity: <strong style="color: #FFFFFF;">${straightDist != null ? `${straightDist} km` : 'Local Candidate'}</strong> from selected village</div>
            <div>Route Distance: <strong style="color: #38BDF8;">${routeText}</strong></div>
            <div>Capacity: <strong style="color: #FFFFFF;">${capText}</strong></div>
            <div>Available Beds: <strong style="color: #10B981;">${availText}</strong></div>
            <div>Verification: <strong style="color: #A7F3D0;">Government-Documented / Candidate</strong></div>
            <div>Source: <span style="color: #D1D5DB;">${cand.source || 'USDMA / DDMA Relief Catalog'}</span></div>
          </div>
        </div>
      `,
        { className: 'dark-leaflet-popup' }
      );

      layer.addLayer(marker);
    });
  }, [isMapInitialized, activeVillageShelterCandidates, showShelters, activeRoute, selectedVillageId, villages]);

  const prevActiveRouteRef = useRef<EvacuationRouteResult | null>(null);

  // Auto-zoom to evacuation route ONLY when a new activeRoute is generated
  useEffect(() => {
    if (!mapRef.current || !activeRoute) return;
    if (prevActiveRouteRef.current === activeRoute) return;
    prevActiveRouteRef.current = activeRoute;

    if (activeRoute.path_coordinates && activeRoute.path_coordinates.length > 0) {
      const coords = activeRoute.path_coordinates as L.LatLngExpression[];
      const routeLine = L.polyline(coords);
      mapRef.current.fitBounds(routeLine.getBounds(), { padding: [60, 60], maxZoom: 13 });
    }
  }, [activeRoute]);

  // Render Active Evacuation Route Polyline (Glowing Orange / Yellow)
  useEffect(() => {
    if (!isMapInitialized) return;
    const layer = routeLayerRef.current;
    if (!layer) return;

    layer.clearLayers();
    if (!showRoute || !activeRoute || !activeRoute.path_coordinates || activeRoute.path_coordinates.length === 0) return;

    if (selectedRegion !== 'ALL') {
      const originRegion = getRegionForVillage(activeRoute.origin_village_id);
      if (originRegion !== selectedRegion) {
        return;
      }
    }

    const coords = activeRoute.path_coordinates as L.LatLngExpression[];

    const glowLine = L.polyline(coords, {
      color: '#FF7A18',
      weight: 10,
      opacity: 0.45,
      lineCap: 'round',
      lineJoin: 'round',
    });

    const routeLine = L.polyline(coords, {
      color: '#FFB703',
      weight: 5,
      opacity: 0.95,
      lineCap: 'round',
      lineJoin: 'round',
    });

    routeLine.bindTooltip(`
      <div style="font-family: monospace; font-size: 11px;">
        <strong style="color: #FFB703;">SAFE EVACUATION PATHFINDER</strong><br/>
        Destination: ${activeRoute.destination_shelter_name}<br/>
        Distance: ${activeRoute.total_distance_km.toFixed(1)} km<br/>
        Transit: ${activeRoute.estimated_travel_time_mins.toFixed(1)} mins<br/>
        Safety Score: ${Math.round(activeRoute.route_safety_score > 1 ? activeRoute.route_safety_score : activeRoute.route_safety_score * 100)}%
      </div>
    `, { sticky: true, className: 'dark-leaflet-tooltip' });

    layer.addLayer(glowLine);
    layer.addLayer(routeLine);
  }, [isMapInitialized, activeRoute, showRoute, selectedRegion]);

  const handleSelectRegion = useCallback((region: RegionFilter) => {
    if (selectedRegion === region) return;
    setSelectedRegion(region);
    if (!mapRef.current) return;

    mapRef.current.flyToBounds(REGION_BOUNDS[region], {
      padding: region === 'ALL' ? [30, 30] : [50, 50],
      duration: 1.2,
      easeLinearity: 0.25,
      maxZoom: region === 'HIMACHAL' || region === 'KERALA' ? 13 : 11,
    });
  }, [selectedRegion]);

  const handleResetView = useCallback(() => {
    if (!mapRef.current) return;
    mapRef.current.flyToBounds(REGION_BOUNDS[selectedRegion], {
      padding: [40, 40],
      duration: 1.0,
      easeLinearity: 0.25,
    });
  }, [selectedRegion]);

  return (
    <div className="w-full h-full relative flex flex-col bg-[#08090B] font-sans select-none overflow-hidden rounded-2xl">
      {/* Top Map Control Bar */}
      <div className="bg-[#14181D]/90 border-b border-white/10 px-2.5 py-1.5 flex items-center justify-between gap-2 z-10 shadow-md font-mono text-xs backdrop-blur-md flex-shrink-0 overflow-x-auto no-scrollbar">
        {/* Region Filter Buttons */}
        <div className="flex items-center gap-1 bg-[#08090B] p-0.5 sm:p-1 rounded-xl border border-white/10 flex-shrink-0">
          <button
            onClick={() => handleSelectRegion('ALL')}
            className={`px-2 sm:px-2.5 py-1 rounded-lg text-[10px] sm:text-[11px] font-bold transition flex items-center gap-1 cursor-pointer flex-shrink-0 ${
              selectedRegion === 'ALL'
                ? 'bg-gradient-to-r from-[#FF7A18] to-[#FFB703] text-black font-extrabold shadow'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Compass className="w-3.5 h-3.5" />
            <span>ALL (15)</span>
          </button>

          <button
            onClick={() => handleSelectRegion('UTTARAKHAND')}
            className={`px-2 sm:px-2.5 py-1 rounded-lg text-[10px] sm:text-[11px] font-bold transition flex items-center gap-1 cursor-pointer flex-shrink-0 ${
              selectedRegion === 'UTTARAKHAND'
                ? 'bg-gradient-to-r from-[#FF7A18] to-[#FFB703] text-black font-extrabold shadow'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <span>UK (12)</span>
          </button>

          <button
            onClick={() => handleSelectRegion('HIMACHAL')}
            className={`px-2 sm:px-2.5 py-1 rounded-lg text-[10px] sm:text-[11px] font-bold transition flex items-center gap-1 cursor-pointer flex-shrink-0 ${
              selectedRegion === 'HIMACHAL'
                ? 'bg-gradient-to-r from-[#FF7A18] to-[#FFB703] text-black font-extrabold shadow'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <span>HP (1)</span>
          </button>

          <button
            onClick={() => handleSelectRegion('KERALA')}
            className={`px-2 sm:px-2.5 py-1 rounded-lg text-[10px] sm:text-[11px] font-bold transition flex items-center gap-1 cursor-pointer flex-shrink-0 ${
              selectedRegion === 'KERALA'
                ? 'bg-gradient-to-r from-[#FF7A18] to-[#FFB703] text-black font-extrabold shadow'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <span>KL (2)</span>
          </button>
        </div>

        {/* Basemap Switcher: TERRAIN | SATELLITE */}
        <div className="flex items-center gap-1 bg-[#08090B] p-0.5 sm:p-1 rounded-xl border border-white/10 shadow-inner flex-shrink-0">
          <button
            onClick={() => setBasemapMode('TERRAIN')}
            className={`px-2 sm:px-2.5 py-1 rounded-lg text-[10px] sm:text-[11px] font-bold transition flex items-center gap-1 cursor-pointer flex-shrink-0 ${
              basemapMode === 'TERRAIN'
                ? 'bg-gradient-to-r from-[#FF7A18] to-[#FFB703] text-black font-extrabold shadow'
                : 'text-gray-400 hover:text-white'
            }`}
            title="Switch to Topographic Mountain Terrain Basemap"
          >
            <Mountain className="w-3.5 h-3.5" />
            <span>TERRAIN</span>
          </button>

          <button
            onClick={() => setBasemapMode('SATELLITE')}
            className={`px-2 sm:px-2.5 py-1 rounded-lg text-[10px] sm:text-[11px] font-bold transition flex items-center gap-1 cursor-pointer flex-shrink-0 ${
              basemapMode === 'SATELLITE'
                ? 'bg-gradient-to-r from-[#FF7A18] to-[#FFB703] text-black font-extrabold shadow'
                : 'text-gray-400 hover:text-white'
            }`}
            title="Switch to High-Resolution Satellite Aerial Imagery"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>SATELLITE</span>
          </button>
        </div>

        {/* Layer Toggles & Reset Control */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <div className="hidden xl:flex items-center gap-2 text-[10px]">
            <label className="flex items-center gap-1 text-gray-400 hover:text-white cursor-pointer">
              <input
                type="checkbox"
                checked={showVillages}
                onChange={(e) => setShowVillages(e.target.checked)}
                className="accent-[#FF7A18] rounded cursor-pointer"
              />
              <span>Stations</span>
            </label>

            <label className="flex items-center gap-1 text-gray-400 hover:text-white cursor-pointer">
              <input
                type="checkbox"
                checked={showRoads}
                onChange={(e) => setShowRoads(e.target.checked)}
                className="accent-[#FF7A18] rounded cursor-pointer"
              />
              <span>Roads</span>
            </label>

            <label className="flex items-center gap-1 text-gray-400 hover:text-white cursor-pointer">
              <input
                type="checkbox"
                checked={showShelters}
                onChange={(e) => setShowShelters(e.target.checked)}
                className="accent-[#FF7A18] rounded cursor-pointer"
              />
              <span>Shelters</span>
            </label>

            {activeRoute && (
              <label className="flex items-center gap-1 text-[#FFB703] font-bold cursor-pointer">
                <input
                  type="checkbox"
                  checked={showRoute}
                  onChange={(e) => setShowRoute(e.target.checked)}
                  className="accent-[#FFB703] rounded cursor-pointer"
                />
                <span>Active Route</span>
              </label>
            )}
          </div>

          <button
            onClick={handleResetView}
            className="px-2 sm:px-2.5 py-1 bg-[#08090B] border border-white/10 hover:border-[#FF7A18] text-gray-400 hover:text-white rounded-xl text-[10px] sm:text-[11px] font-bold transition flex items-center gap-1 shadow-sm cursor-pointer flex-shrink-0"
            title="Fit map to active region bounds"
          >
            <RotateCcw className="w-3 h-3 text-[#FF7A18]" />
            <span>FIT BOUNDS</span>
          </button>

          <span className="hidden sm:flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-[10px] font-bold">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            GIS BASEMAP
          </span>
        </div>
      </div>

      {/* Leaflet Map Canvas Container */}
      <div className="flex-1 w-full h-full relative">
        <div ref={mapContainerRef} className="w-full h-full z-0 bg-[#0B0D10]" />

        {/* Region Information Pill - visible on desktop/tablet */}
        <div className="absolute top-3 left-3 z-[400] pointer-events-none hidden sm:block">
          <div className="bg-[#14181D]/90 border border-white/15 rounded-xl px-3 py-1.5 shadow-2xl backdrop-blur-md text-[11px] font-mono text-gray-300 flex items-center gap-2 pointer-events-auto">
            <MapPin className="w-3.5 h-3.5 text-[#FF7A18] flex-shrink-0" />
            <span>
              {selectedRegion === 'ALL' && 'National Monitored Watersheds (Uttarakhand, Himachal, Kerala)'}
              {selectedRegion === 'UTTARAKHAND' && 'Alaknanda & Mandakini Basins (Chamoli, Rudraprayag)'}
              {selectedRegion === 'HIMACHAL' && 'Beas River Gorge Catchment (Aut / Mandi Station)'}
              {selectedRegion === 'KERALA' && 'Iruvaipuzha Basin Multi-Slope Zone (Vythiri / Meppadi)'}
            </span>
          </div>
        </div>

        {/* Floating Bottom Legend - Collapsible on Mobile */}
        <div className="absolute bottom-3 right-3 z-[400]">
          {/* Mobile Toggle Button */}
          <button
            onClick={() => setIsLegendOpen(!isLegendOpen)}
            className="sm:hidden px-2.5 py-1 rounded-xl bg-[#14181D]/95 border border-white/20 text-[10px] font-mono font-bold text-[#FFB703] shadow-lg backdrop-blur-md flex items-center gap-1.5 cursor-pointer ml-auto mb-1"
          >
            <Layers className="w-3 h-3 text-[#FF7A18]" />
            <span>{isLegendOpen ? 'Hide Legend ▲' : 'Map Legend ▼'}</span>
          </button>

          {/* Legend Box */}
          <div className={`${isLegendOpen ? 'block' : 'hidden'} sm:block bg-[#14181D]/95 border border-white/15 rounded-2xl p-2.5 shadow-2xl backdrop-blur-md text-[10px] font-mono space-y-1.5 pointer-events-auto max-w-[260px]`}>
            <div className="flex items-center justify-between border-b border-white/10 pb-1 text-white font-bold">
              <span>GIS MAP LEGEND</span>
              <span className="text-gray-400">15 NODES</span>
            </div>

            <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-gray-400">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
                <span className="text-white">Critical Risk</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                <span>Mod/High Risk</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                <span>Low Risk</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded bg-[#181D22] border border-white" />
                <span>Relief Shelter</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-0.5 bg-emerald-500" />
                <span>Open Road</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-0.5 bg-red-500 border-dashed" />
                <span>Blocked Road</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GeospatialMonitoringMap;
