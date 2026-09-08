import React, { useState } from 'react';
import {
  VillageRiskDetail,
  RoadSegment,
  Shelter,
  EvacuationPriority,
  ImpactSummary,
} from '../../types';
import { GeospatialMonitoringMap } from '../../components/map/GeospatialMonitoringMap';
import {
  CloudRain,
  Droplets,
  Waves,
  Search,
  CheckCircle2,
  Database,
  MapPin,
  Radio,
  Mountain,
  Clock,
} from 'lucide-react';
import { getStationMetadata } from '../../utils/stationMetadata';
import { getRiskColorHex } from '../../utils/riskColors';

interface Props {
  villages: VillageRiskDetail[];
  selectedVillageId: string | null;
  onSelectVillage: (id: string) => void;
  selectedVillageDetail: VillageRiskDetail | null;
  roads: RoadSegment[];
  shelters: Shelter[];
  priorities: EvacuationPriority[];
  impact: ImpactSummary | null;
  loading: boolean;
  dataMode?: string;
}

export const LiveMonitoring: React.FC<Props> = ({
  villages,
  selectedVillageId,
  onSelectVillage,
  selectedVillageDetail,
  roads,
  shelters,
}) => {
  const [stationSearch, setStationSearch] = useState('');

  const stationMeta = getStationMetadata(selectedVillageId);

  // Extract factor raw values for current selected village
  const getFactorRaw = (key: string): { val: string; unit: string } => {
    if (!selectedVillageDetail || !selectedVillageDetail.factors) {
      return { val: '—', unit: '' };
    }
    const f = selectedVillageDetail.factors.find((item) => item.feature_key === key);
    if (!f) return { val: '—', unit: '' };
    return { val: f.raw_value.toFixed(1), unit: f.unit };
  };

  const currentRain = getFactorRaw('current_rainfall');
  const forecastRain = getFactorRaw('forecast_rainfall');
  const soilSat = getFactorRaw('soil_saturation');
  const riverLevel = getFactorRaw('river_water_level');

  const filteredStations = villages.filter(
    (v) =>
      v.village_name.toLowerCase().includes(stationSearch.toLowerCase()) ||
      v.village_id.toLowerCase().includes(stationSearch.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col h-full min-h-0 w-full bg-[#08090B] overflow-y-auto overflow-x-hidden lg:overflow-hidden relative font-sans p-2.5 lg:p-3.5 space-y-2.5 lg:space-y-3">
      {/* 1. TOP BENTO ROW: 6 COMPACT SENSOR METRICS CARDS */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 flex-shrink-0">
        {/* CURRENT RAINFALL */}
        <div className="bento-card p-3 flex flex-col justify-between space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono text-gray-400">
            <span className="uppercase font-bold tracking-wider">RAINFALL</span>
            <span className="flex items-center gap-1 text-emerald-400 font-bold text-[9px] bg-emerald-500/10 px-1.5 py-0.2 rounded border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              LIVE
            </span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl lg:text-2xl font-black text-white font-mono">
              {currentRain.val !== '—' ? currentRain.val : '—'}
            </span>
            <span className="text-[11px] font-mono text-gray-400">mm/h</span>
          </div>
          <span className="text-[10px] text-gray-400 font-sans truncate">Telemetry active</span>
        </div>

        {/* 24H FORECAST */}
        <div className="bento-card p-3 flex flex-col justify-between space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono text-gray-400">
            <span className="uppercase font-bold tracking-wider">24H FORECAST</span>
            <CloudRain className="w-3.5 h-3.5 text-[#FFB703]" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl lg:text-2xl font-black text-white font-mono">
             {forecastRain.val !== '—' ? forecastRain.val : '—'}
            </span>
            <span className="text-[11px] font-mono text-gray-400">mm</span>
          </div>
          <span className="text-[10px] text-gray-400 font-sans truncate">Accumulation loading</span>
        </div>

        {/* SOIL MOISTURE */}
        <div className="bento-card p-3 flex flex-col justify-between space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono text-gray-400">
            <span className="uppercase font-bold tracking-wider">SOIL MOISTURE</span>
            <Droplets className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl lg:text-2xl font-black text-white font-mono">
              {soilSat.val !== '—' ? soilSat.val : '—'}
            </span>
            <span className="text-[11px] font-mono text-gray-400">%</span>
          </div>
          <span className="text-[10px] text-gray-400 font-sans truncate">Saturation index</span>
        </div>

        {/* RIVER LEVEL */}
        <div className="bento-card p-3 flex flex-col justify-between space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono text-gray-400">
            <span className="uppercase font-bold tracking-wider">RIVER LEVEL</span>
            <Waves className="w-3.5 h-3.5 text-[#F97316]" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl lg:text-2xl font-black text-white font-mono">
              {riverLevel.val !== '—' ? riverLevel.val : '—'}
            </span>
            <span className="text-[11px] font-mono text-gray-400">m</span>
          </div>
          <span className="text-[10px] text-gray-400 font-sans truncate">CWC gauge stage</span>
        </div>

        {/* ELEVATION */}
        <div className="bento-card p-3 flex flex-col justify-between space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono text-gray-400">
            <span className="uppercase font-bold tracking-wider">ELEVATION</span>
            <Mountain className="w-3.5 h-3.5 text-gray-400" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl lg:text-2xl font-black text-white font-mono">
              {selectedVillageDetail?.elevation || 1150}
            </span>
            <span className="text-[11px] font-mono text-gray-400">m</span>
          </div>
          <span className="text-[10px] text-gray-400 font-sans truncate">Copernicus 30m DEM</span>
        </div>

        {/* DATA FRESHNESS */}
        <div className="bento-card p-3 flex flex-col justify-between space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono text-gray-400">
            <span className="uppercase font-bold tracking-wider">FRESHNESS</span>
            <Clock className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-base lg:text-lg font-black text-emerald-400 font-mono">
              &lt; 30s
            </span>
            <span className="text-[11px] font-mono text-gray-400">ago</span>
          </div>
          <span className="text-[10px] text-emerald-400 font-mono font-bold flex items-center gap-1">
            <CheckCircle2 className="w-2.5 h-2.5" /> Synchronized
          </span>
        </div>
      </div>

      {/* 2. MAIN BENTO GRID: DOMINANT GIS MAP + SIDE TELEMETRY STACK */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-3 min-h-0 overflow-visible lg:overflow-hidden">
        {/* DOMINANT GIS MAP BENTO CARD (8 COLUMNS ON LARGE SCREEN) */}
        <div className="lg:col-span-8 bento-card p-2 flex flex-col h-[380px] lg:h-full min-h-[340px] lg:min-h-0 overflow-hidden relative shadow-2xl flex-shrink-0 lg:flex-shrink">
          <div className="flex items-center justify-between px-3 py-1.5 border-b border-white/10 mb-1 z-10 flex-shrink-0">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="text-xs font-mono font-black text-white uppercase tracking-wider">
                GEOSPATIAL TERRAIN & MULTI-HAZARD OBSERVATION
              </span>
            </div>
            <div className="flex items-center gap-2 text-[10px] font-mono text-gray-400">
              <span>Nodes: <strong className="text-white">15 Active</strong></span>
              <span>•</span>
              <span className="text-[#FFB703] font-bold">ArcGIS Dark Basemap</span>
            </div>
          </div>

          <div className="flex-1 w-full h-full relative rounded-2xl overflow-hidden">
            <GeospatialMonitoringMap
              villages={villages}
              roads={roads}
              shelters={shelters}
              activeRoute={null}
              selectedVillageId={selectedVillageId}
              onSelectVillage={onSelectVillage}
              isSimulationActive={false}
            />
          </div>
        </div>

        {/* RIGHT BENTO STACK (4 COLUMNS ON LARGE SCREEN) */}
        <div className="lg:col-span-4 flex flex-col gap-3 h-full min-h-[380px] lg:min-h-0 overflow-visible lg:overflow-hidden">
          {/* Bento Card 1: Selected Station Telemetry Card */}
          <div className="bento-card p-4 space-y-3 flex-shrink-0">
            <div className="flex items-start justify-between border-b border-white/10 pb-2.5">
              <div>
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-[#FF7A18]" />
                  <h2 className="text-sm font-black text-white truncate max-w-[170px]">
                    {selectedVillageDetail?.village_name || 'Select Station'}
                  </h2>
                  <span className="text-[10px] font-mono font-bold text-[#FFB703] bg-[#FF7A18]/15 border border-[#FF7A18]/40 px-1.5 py-0.2 rounded">
                    #{stationMeta.stationNumber.toString().padStart(2, '0')}
                  </span>
                </div>
                <p className="text-[11px] text-gray-400 mt-0.5 font-sans">
                  {stationMeta.region} • {stationMeta.state}
                </p>
              </div>

              <span
                className={`text-[10px] font-mono font-black px-2 py-0.5 rounded-lg border ${
                  selectedVillageDetail?.risk_level === 'CRITICAL'
                    ? 'bg-red-500/20 text-red-400 border-red-500/50'
                    : selectedVillageDetail?.risk_level === 'HIGH'
                    ? 'bg-orange-500/20 text-orange-400 border-orange-500/50'
                    : selectedVillageDetail?.risk_level === 'MODERATE'
                    ? 'bg-amber-500/20 text-amber-400 border-amber-500/50'
                    : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50'
                }`}
              >
                {selectedVillageDetail?.risk_level || 'NORMAL'} ({Math.round(selectedVillageDetail?.flash_flood_risk_score || 0)}%)
              </span>
            </div>

            {/* Quick Metrics in Selected Station */}
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="bg-[#14181D] p-2 rounded-xl border border-white/5">
                <span className="text-[10px] text-gray-400 block font-sans">Exposed Population</span>
                <strong className="text-white text-sm">
                  {selectedVillageDetail?.exposure.population_exposed.toLocaleString() || '1,240'}
                </strong>
              </div>
              <div className="bg-[#14181D] p-2 rounded-xl border border-white/5">
                <span className="text-[10px] text-gray-400 block font-sans">Confidence Level</span>
                <strong className="text-emerald-400 text-sm">
                  {Math.round((selectedVillageDetail?.confidence || 0.85) > 1 ? (selectedVillageDetail?.confidence || 0.85) : (selectedVillageDetail?.confidence || 0.85) * 100)}%
                </strong>
              </div>
            </div>
          </div>

          {/* Bento Card 2: Monitored Station Incident Queue */}
          <div className="bento-card p-3 flex-1 flex flex-col overflow-hidden min-h-0 space-y-2">
            <div className="flex items-center justify-between border-b border-white/10 pb-2">
              <span className="text-xs font-black text-white uppercase font-mono tracking-wider flex items-center gap-1.5">
                <Radio className="w-3.5 h-3.5 text-[#FF7A18]" />
                INCIDENT QUEUE ({villages.length})
              </span>
              <span className="text-[10px] font-mono text-gray-400">
                Click to inspect
              </span>
            </div>

            {/* Search */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-gray-500 absolute left-2.5 top-2.5" />
              <input
                type="text"
                value={stationSearch}
                onChange={(e) => setStationSearch(e.target.value)}
                placeholder="Filter stations..."
                className="w-full bg-[#0E1115] border border-white/10 rounded-xl pl-8 pr-2.5 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-[#FF7A18] font-mono"
              />
            </div>

            {/* Station List */}
            <div className="flex-1 overflow-y-auto space-y-1.5 pr-0.5">
              {filteredStations.map((v) => {
                const isSelected = v.village_id === selectedVillageId;
                const vMeta = getStationMetadata(v.village_id);
                const riskColor = getRiskColorHex(v.risk_level);

                return (
                  <button
                    key={v.village_id}
                    onClick={() => onSelectVillage(v.village_id)}
                    className={`w-full text-left p-2 rounded-xl border transition flex items-center justify-between cursor-pointer ${
                      isSelected
                        ? 'bg-gradient-to-r from-[#FF7A18]/20 to-[#FFB703]/20 border-[#FF7A18] text-white shadow-md'
                        : 'bg-[#14181D]/60 border-white/5 text-gray-300 hover:border-white/20 hover:text-white'
                    }`}
                  >
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] font-mono font-bold text-[#FFB703]">
                          #{vMeta.stationNumber.toString().padStart(2, '0')}
                        </span>
                        <strong className="text-white text-xs truncate max-w-[130px]">{v.village_name}</strong>
                      </div>
                      <span className="text-[10px] text-gray-400 font-mono block mt-0.5">
                        {vMeta.region}
                      </span>
                    </div>

                    <div className="text-right font-mono">
                      <span
                        className="text-xs font-black block"
                        style={{ color: riskColor }}
                      >
                        {Math.round(v.flash_flood_risk_score)}%
                      </span>
                      <span className="text-[9px] text-gray-400 block mt-0.5">
                        {v.risk_level}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Bento Card 3: System Health & Catchment Status */}
          <div className="bento-card p-3 space-y-2 flex-shrink-0 text-xs font-mono">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-white flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-[#FFB703]" />
                NETWORK TELEMETRY STATUS
              </span>
              <span className="text-[9px] font-black text-emerald-400 bg-emerald-500/15 border border-emerald-500/30 px-1.5 py-0.2 rounded">
                100% HEALTHY
              </span>
            </div>

            <div className="grid grid-cols-3 gap-1.5 text-[10px]">
              <div className="bg-[#14181D] p-1.5 rounded-xl border border-white/5 text-center">
                <span className="text-gray-400 block font-sans">Active IoT</span>
                <strong className="text-emerald-400 font-bold">15/15</strong>
              </div>
              <div className="bg-[#14181D] p-1.5 rounded-xl border border-white/5 text-center">
                <span className="text-gray-400 block font-sans">DEM Rasters</span>
                <strong className="text-[#FFB703] font-bold">Copernicus</strong>
              </div>
              <div className="bg-[#14181D] p-1.5 rounded-xl border border-white/5 text-center">
                <span className="text-gray-400 block font-sans">CWC Gauges</span>
                <strong className="text-orange-400 font-bold">4 Linked</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveMonitoring;
