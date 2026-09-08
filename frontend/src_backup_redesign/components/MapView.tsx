import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import { VillageRiskDetail, RoadSegment, Shelter, EvacuationRouteResult } from '../types';
import { getRiskColorHex } from '../utils/riskColors';
import { Layers, ShieldCheck } from 'lucide-react';

interface Props {
  villages: VillageRiskDetail[];
  roads?: RoadSegment[];
  shelters?: Shelter[];
  activeRoute?: EvacuationRouteResult | null;
  selectedVillageId: string | null;
  onSelectVillage: (id: string) => void;
  isSimulationActive?: boolean;
}

// Custom Leaflet DivIcon generator for dark emergency command center
function createCustomRiskIcon(village: VillageRiskDetail, isSelected: boolean) {
  const color = getRiskColorHex(village.risk_level);
  const isCritical = village.risk_level === 'CRITICAL';
  const isHigh = village.risk_level === 'HIGH';

  const pulseClass = isCritical
    ? 'animate-pulse-critical'
    : isHigh
    ? 'animate-ping opacity-30'
    : '';

  const scaleClass = isSelected ? 'scale-125 z-50 ring-2 ring-white' : '';

  const htmlStr = `
    <div class="relative flex items-center justify-center cursor-pointer transition-all duration-300 ${scaleClass}">
      ${
        isCritical || isHigh
          ? `<div class="absolute w-8 h-8 rounded-full ${pulseClass}" style="background-color: ${color};"></div>`
          : ''
      }
      <div class="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-mono font-bold text-black shadow-lg border border-white/80" style="background-color: ${color}; shadow: 0 0 12px ${color};">
        ${Math.round(village.flash_flood_risk_score)}
      </div>
    </div>
  `;

  return L.divIcon({
    html: htmlStr,
    className: 'custom-leaflet-marker',
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

function createShelterIcon() {
  const htmlStr = `
    <div class="relative flex items-center justify-center cursor-pointer">
      <div class="w-7 h-7 rounded-lg bg-command-accent text-black font-bold flex items-center justify-center text-xs shadow-xl border-2 border-white">
        🎪
      </div>
    </div>
  `;
  return L.divIcon({
    html: htmlStr,
    className: 'custom-shelter-marker',
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

// Controller component to handle map re-centering when village is selected
const MapRecenter: React.FC<{ selectedVillage: VillageRiskDetail | null }> = ({
  selectedVillage,
}) => {
  const map = useMap();
  useEffect(() => {
    if (selectedVillage) {
      map.flyTo([selectedVillage.latitude, selectedVillage.longitude], 12, {
        duration: 1.2,
      });
    }
  }, [selectedVillage, map]);
  return null;
};

const TileErrorWatcher: React.FC<{ setHasTileError: (val: boolean) => void }> = ({
  setHasTileError,
}) => {
  const map = useMap();
  useEffect(() => {
    const handleTileError = () => {
      setHasTileError(true);
    };
    const handleWindowError = (e: Event) => {
      const target = e.target as HTMLElement;
      if (target && target.tagName === 'IMG' && target.classList.contains('leaflet-tile')) {
        setHasTileError(true);
      }
    };

    map.on('tileerror', handleTileError);
    window.addEventListener('error', handleWindowError, true);

    if (!navigator.onLine) {
      setHasTileError(true);
    }
    const handleOffline = () => setHasTileError(true);
    window.addEventListener('offline', handleOffline);

    return () => {
      map.off('tileerror', handleTileError);
      window.removeEventListener('error', handleWindowError, true);
      window.removeEventListener('offline', handleOffline);
    };
  }, [map, setHasTileError]);
  return null;
};

export const MapView: React.FC<Props> = ({
  villages,
  roads = [],
  shelters = [],
  activeRoute = null,
  selectedVillageId,
  onSelectVillage,
}) => {
  const [hasTileError, setHasTileError] = React.useState(false);
  // Center of Alaknanda / Mandakini valley dataset (approx 30.45 N, 79.25 E)
  const centerLat = 30.45;
  const centerLng = 79.25;

  const selectedVillage = villages.find((v) => v.village_id === selectedVillageId) || null;

  return (
    <div className="relative w-full h-full bg-command-bg overflow-hidden">
      {hasTileError && (
        <div className="absolute top-4 left-4 z-20 bg-amber-950/90 border border-amber-500/80 text-amber-200 text-xs px-3 py-1.5 rounded-md backdrop-blur-md font-mono flex items-center gap-2 shadow-xl">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping"></span>
          <span>Basemap Tile Fallback Active — DEMO MAP SCENARIO</span>
        </div>
      )}

      <MapContainer
        center={[centerLat, centerLng]}
        zoom={10}
        scrollWheelZoom={true}
        className="w-full h-full dark-tiles z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          eventHandlers={{
            tileerror: () => setHasTileError(true),
          }}
        />

        <TileErrorWatcher setHasTileError={setHasTileError} />
        <MapRecenter selectedVillage={selectedVillage} />

        {/* Mountain Road Network Graph Overlay */}
        {roads.map((road) => {
          let color = '#10B981'; // OPEN (green)
          let dashArray = undefined;
          let weight = 3;
          let opacity = 0.5;

          if (road.status === 'DEGRADED') {
            color = '#F59E0B'; // DEGRADED (amber)
            dashArray = '6, 6';
            opacity = 0.7;
          } else if (road.status === 'BLOCKED') {
            color = '#EF4444'; // BLOCKED (red)
            dashArray = '4, 8';
            weight = 4;
            opacity = 0.85;
          }

          const positions = road.coordinates.map((c) => [c[0], c[1]] as [number, number]);

          return (
            <Polyline
              key={road.id}
              positions={positions}
              pathOptions={{ color, weight, dashArray, opacity }}
            >
              <Popup>
                <div className="font-mono text-xs p-1 space-y-1">
                  <div className="font-bold text-white">{road.name}</div>
                  <div>Status: <strong className={road.status === 'BLOCKED' ? 'text-red-400' : road.status === 'DEGRADED' ? 'text-amber-400' : 'text-emerald-400'}>{road.status}</strong></div>
                  <div>Distance: {road.distance_km} km</div>
                  <div>Flood Exposure: {road.flood_exposure}% | Landslide Exposure: {road.landslide_exposure}%</div>
                </div>
              </Popup>
            </Polyline>
          );
        })}

        {/* Highlighted Active Evacuation Route Polyline */}
        {activeRoute && activeRoute.path_coordinates.length > 0 && (
          <Polyline
            positions={activeRoute.path_coordinates.map((c) => [c[0], c[1]] as [number, number])}
            pathOptions={{
              color: '#06B6D4',
              weight: 6,
              opacity: 0.95,
            }}
          />
        )}

        {/* Relief Shelter Markers */}
        {shelters.map((shelter) => (
          <Marker
            key={shelter.id}
            position={[shelter.latitude, shelter.longitude]}
            icon={createShelterIcon()}
          >
            <Popup>
              <div className="font-mono text-xs p-1 space-y-1.5">
                <div className="flex items-center gap-1.5 text-command-accent font-bold text-sm">
                  <ShieldCheck className="w-4 h-4 text-command-accent" />
                  {shelter.name}
                </div>
                <div className="text-[11px] text-command-muted">Elevation: {shelter.elevation}m</div>
                <div className="grid grid-cols-2 gap-2 text-[11px] border-t border-command-border/50 pt-1">
                  <div>Capacity: <strong className="text-white">{shelter.total_capacity}</strong></div>
                  <div>Available: <strong className="text-emerald-400 font-bold">{shelter.available_capacity} beds</strong></div>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Village Markers */}
        {villages.map((v) => {
          const isSelected = v.village_id === selectedVillageId;
          const icon = createCustomRiskIcon(v, isSelected);

          return (
            <Marker
              key={v.village_id}
              position={[v.latitude, v.longitude]}
              icon={icon}
              eventHandlers={{
                click: () => onSelectVillage(v.village_id),
              }}
            >
              <Popup>
                <div className="font-mono text-xs p-1 space-y-2">
                  <div className="flex items-center justify-between border-b border-command-border pb-1">
                    <span className="font-bold text-white text-sm">{v.village_name}</span>
                    <span
                      className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase"
                      style={{
                        backgroundColor: `${getRiskColorHex(v.risk_level)}20`,
                        color: getRiskColorHex(v.risk_level),
                        border: `1px solid ${getRiskColorHex(v.risk_level)}50`,
                      }}
                    >
                      {v.risk_level}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[11px] text-command-muted">
                    <div>Risk Score: <strong className="text-white">{Math.round(v.flash_flood_risk_score)}%</strong></div>
                    <div>Confidence: <strong className="text-white">{v.confidence}%</strong></div>
                    <div>Exposed Pop: <strong className="text-white">{v.exposure.population_exposed}</strong></div>
                    <div>Elevation: <strong className="text-white">{v.elevation}m</strong></div>
                  </div>

                  <button
                    onClick={() => onSelectVillage(v.village_id)}
                    className="w-full mt-2 bg-command-accent text-black font-bold py-1 rounded hover:bg-command-accentHover transition text-[11px] uppercase tracking-wider"
                  >
                    View Intelligence Panel
                  </button>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {/* Map Overlay Legend */}
      <div className="absolute bottom-4 left-4 z-10 bg-command-card/90 backdrop-blur-md border border-command-border p-3 rounded-lg shadow-xl font-mono text-xs">
        <div className="flex items-center gap-2 text-command-muted text-[10px] uppercase font-bold mb-2">
          <Layers className="w-3.5 h-3.5 text-command-accent" />
          <span>Multimodal Command Center Legend</span>
        </div>

        <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[11px]">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-risk-critical animate-pulse"></span>
            <span className="text-white">CRITICAL (75-100%)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-risk-high"></span>
            <span className="text-white">HIGH (50-74%)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-0.5 bg-emerald-500"></span>
            <span className="text-emerald-400">Open Road</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-0.5 bg-red-500 border-b border-dashed border-red-500"></span>
            <span className="text-red-400">Blocked Road</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs">🎪</span>
            <span className="text-command-accent font-bold">Relief Shelter</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-1 bg-cyan-400"></span>
            <span className="text-cyan-300 font-bold">Safest Route</span>
          </div>
        </div>
      </div>
    </div>
  );
};
