import React, { useState, useEffect } from 'react';
import {
  VillageRiskDetail,
  EvacuationPriority,
  RoadSegment,
  Shelter,
  ShelterRecommendationResult,
  VillageLeadTimeDetail,
} from '../../types';
import { fetchVillageLeadTime } from '../../api/client';
import { GeospatialMonitoringMap } from '../../components/map/GeospatialMonitoringMap';
import {
  Navigation,
  Building2,
  Radio,
  AlertOctagon,
  CheckCircle2,
  Compass,
  ArrowUpRight,
  Check,
  Send,
  Shield,
} from 'lucide-react';
import { getStationMetadata } from '../../utils/stationMetadata';

interface Props {
  villages: VillageRiskDetail[];
  selectedVillageId: string | null;
  onSelectVillage: (id: string) => void;
  selectedVillageDetail: VillageRiskDetail | null;
  priorities: EvacuationPriority[];
  roads: RoadSegment[];
  shelters: Shelter[];
  shelterRec: ShelterRecommendationResult | null;
  onCalculateRoute: () => void;
  routeLoading: boolean;
  onOpenSmsModal: () => void;
}

type OperationalActionStatus = 'STANDBY' | 'ACKNOWLEDGED' | 'ESCALATED' | 'RESOLVED';

export const Response: React.FC<Props> = ({
  villages,
  selectedVillageId,
  onSelectVillage,
  selectedVillageDetail,
  priorities,
  roads,
  shelters,
  shelterRec,
  onCalculateRoute,
  routeLoading,
  onOpenSmsModal,
}) => {
  const [operationalStatus, setOperationalStatus] = useState<Record<string, OperationalActionStatus>>({});
  const [leadTimeDetail, setLeadTimeDetail] = useState<VillageLeadTimeDetail | null>(null);
  const [actionLog, setActionLog] = useState<{ id: number; time: string; village: string; status: string }[]>([]);

  const currentVillageId = selectedVillageId || 'VIL-001';
  const currentStatus = operationalStatus[currentVillageId] || 'STANDBY';

  useEffect(() => {
    let isMounted = true;
    if (!currentVillageId) {
      setLeadTimeDetail(null);
      return;
    }
    fetchVillageLeadTime(currentVillageId)
      .then((data) => {
        if (isMounted) setLeadTimeDetail(data);
      })
      .catch(() => {
        if (isMounted) setLeadTimeDetail(null);
      });
    return () => {
      isMounted = false;
    };
  }, [currentVillageId]);

  const updateStatus = (status: OperationalActionStatus) => {
    setOperationalStatus((prev) => ({
      ...prev,
      [currentVillageId]: status,
    }));
    setActionLog((prev) => [
      ...prev,
      {
        id: Date.now(),
        time: new Date().toLocaleTimeString(),
        village: selectedVillageDetail?.village_name || currentVillageId,
        status,
      },
    ]);
  };

  const selectedPriority = selectedVillageId ? priorities.find((p) => p.village_id === selectedVillageId) || null : null;
  const stationMeta = getStationMetadata(selectedVillageId);

  const blockedRoads = roads.filter((r) => r.status === 'BLOCKED');
  const degradedRoads = roads.filter((r) => r.status === 'DEGRADED');
  const safeRoads = roads.filter((r) => r.status === 'OPEN');

  const activeRoute = shelterRec?.route || null;
  const recommendedShelter = shelterRec?.recommended_shelter || null;
  const alternativeShelters = recommendedShelter ? shelters.filter((s) => s.id !== recommendedShelter.id) : shelters;

  // Operational metrics
  const availableLeadTime = leadTimeDetail?.available_lead_time_minutes ?? null;
  const travelTime = activeRoute?.estimated_travel_time_mins ?? null;
  const safetyMargin =
    travelTime != null && availableLeadTime != null
      ? availableLeadTime - travelTime
      : (leadTimeDetail?.safety_margin_minutes ?? null);
  const routeDistance = activeRoute?.total_distance_km ?? null;
  const routeSafety = activeRoute
    ? Math.round(activeRoute.route_safety_score > 1 ? activeRoute.route_safety_score : activeRoute.route_safety_score * 100)
    : null;
  const rawSuit = recommendedShelter?.accessibility_score ?? null;
  const shelterSuitability = rawSuit != null ? Math.round(rawSuit > 1 ? rawSuit : rawSuit * 100) : null;

  return (
    <div className="flex-1 flex flex-col h-full bg-[#08090B] overflow-hidden font-sans p-3 lg:p-4 space-y-3">
      {/* 1. TOP OPERATIONAL STATUS STRIP */}
      <div className="bento-card px-4 py-2.5 flex items-center justify-between text-xs font-mono flex-shrink-0 shadow-lg">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Navigation className="w-4 h-4 text-[#FF7A18]" />
            <span className="text-white font-black tracking-wider uppercase">
              EVACUATION PATHFINDER & INCIDENT ACTION DESK
            </span>
          </div>
          <div className="hidden lg:flex items-center gap-3 text-gray-400 text-[11px]">
            <span>Routing: <strong className="text-white">Hazard-Impedance Dijkstra</strong></span>
            <span>•</span>
            <span>Protocol: <strong className="text-[#FFB703]">Bypass Hazard → Configured Shelter Baseline</strong></span>
          </div>
        </div>

        {/* Action Trigger & Station Selector */}
        <div className="flex items-center gap-3">
          <select
            value={selectedVillageId || 'VIL-001'}
            onChange={(e) => onSelectVillage(e.target.value)}
            className="bg-[#0E1115] border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-[#FF7A18] cursor-pointer"
          >
            {villages.map((v) => (
              <option key={v.village_id} value={v.village_id}>
                {v.village_name} (Rank #{priorities.find((p) => p.village_id === v.village_id)?.rank || '-'})
              </option>
            ))}
          </select>

          {/* GENERATE ALERT BUTTON (ORANGE -> YELLOW GRADIENT) */}
          <button
            onClick={onOpenSmsModal}
            className="bg-gradient-to-r from-[#FF7A18] to-[#FFB703] hover:from-[#FF7A18]/90 hover:to-[#FFB703]/90 text-black font-black px-3.5 py-1.5 rounded-xl transition flex items-center gap-2 shadow-lg shadow-orange-500/20 text-xs font-mono animate-pulse cursor-pointer"
          >
            <Radio className="w-4 h-4" />
            <span>GENERATE ALERT</span>
          </button>
        </div>
      </div>

      {/* 2. MAIN BENTO GRID: 60% EVACUATION MAP + 40% ACTION STACK */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-3 min-h-0 overflow-hidden">
        {/* LARGE EVACUATION MAP BENTO (APPROX 60% / 7 COLUMNS) */}
        <div className="lg:col-span-7 bento-card p-2 flex flex-col h-full overflow-hidden relative shadow-2xl">
          <div className="flex items-center justify-between px-3 py-1.5 border-b border-white/10 mb-1 z-10 flex-shrink-0">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-white">
              <Compass className="w-3.5 h-3.5 text-[#FF7A18]" />
              <span>DYNAMIC HAZARD-BYPASSING ROUTE MAP</span>
            </div>

            <div className="flex items-center gap-2 text-[10px] font-mono text-gray-400">
              <span className="text-emerald-400 font-bold">● Safe Path</span>
              <span>•</span>
              <span className="text-red-400 font-bold">● Blocked Road</span>
            </div>
          </div>

          <div className="flex-1 w-full h-full relative rounded-2xl overflow-hidden">
            <GeospatialMonitoringMap
              villages={villages}
              roads={roads}
              shelters={shelters}
              activeRoute={activeRoute}
              selectedVillageId={selectedVillageId}
              onSelectVillage={onSelectVillage}
              isSimulationActive={false}
            />
          </div>
        </div>

        {/* RIGHT SIDE BENTO ACTION & SHELTER STACK (5 COLUMNS) */}
        <div className="lg:col-span-5 h-full overflow-y-auto space-y-3 pr-1">
          {/* Bento Card 1: Target Node Summary */}
          <div className="bento-card p-4 space-y-3 shadow-lg">
            <div className="flex items-start justify-between border-b border-white/10 pb-2.5">
              <div>
                <span className="text-[10px] text-gray-400 uppercase font-mono font-bold block">
                  AFFECTED TARGET NODE
                </span>
                <h3 className="text-base font-black text-white mt-0.5">
                  {selectedVillageDetail?.village_name || 'Select Origin'}
                </h3>
                <span className="text-[11px] text-gray-400 font-sans block mt-0.5">
                  {stationMeta.region} • Dialect: {stationMeta.primaryLanguage}
                </span>
              </div>

              <span className="text-[10px] font-mono font-black bg-[#FF7A18]/15 text-[#FFB703] px-2.5 py-1 rounded-xl border border-[#FF7A18]/40">
                Evac Priority {selectedPriority?.rank != null ? `#${selectedPriority.rank}` : 'N/A'}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="bg-[#14181D] p-2 rounded-xl border border-white/5">
                <span className="text-[10px] text-gray-400 block font-sans">Total Population</span>
                <strong className="text-white text-sm">
                  {selectedVillageDetail?.population != null ? selectedVillageDetail.population.toLocaleString() : 'Unavailable'}
                </strong>
              </div>
              <div className="bg-[#14181D] p-2 rounded-xl border border-white/5">
                <span className="text-[10px] text-gray-400 block font-sans">Exposed Headcount</span>
                <strong className="text-red-400 text-sm">
                  {selectedVillageDetail?.exposure?.population_exposed != null
                    ? selectedVillageDetail.exposure.population_exposed.toLocaleString()
                    : 'Unavailable'}
                </strong>
              </div>
            </div>
          </div>

          {/* Bento Card 2: Responder Action Desk with Strict Hierarchy */}
          <div className="bento-card p-4 space-y-3 shadow-lg">
            <div className="flex items-center justify-between border-b border-white/10 pb-2">
              <span className="text-xs font-black text-white uppercase font-mono tracking-wider flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-[#FF7A18]" />
                RESPONDER ACTION DESK
              </span>
              <span
                className={`text-[9px] font-mono font-black px-2 py-0.5 rounded-lg border ${
                  currentStatus === 'RESOLVED'
                    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
                    : currentStatus === 'ESCALATED'
                    ? 'bg-amber-500/20 text-amber-400 border-amber-500/40'
                    : currentStatus === 'ACKNOWLEDGED'
                    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
                    : 'bg-white/5 text-gray-400 border-white/10'
                }`}
              >
                STATUS: {currentStatus}
              </span>
            </div>

            {/* 4 Action Buttons with Hierarchical Styling */}
            <div className="grid grid-cols-2 gap-2 font-mono">
              {/* GENERATE ALERT: ORANGE -> YELLOW GRADIENT */}
              <button
                onClick={onOpenSmsModal}
                className="bg-gradient-to-r from-[#FF7A18] to-[#FFB703] hover:from-[#FF7A18]/90 hover:to-[#FFB703]/90 text-black font-black py-2.5 px-3 rounded-xl transition flex items-center justify-center gap-1.5 shadow-md text-xs cursor-pointer"
              >
                <Send className="w-3.5 h-3.5" />
                <span>GENERATE ALERT</span>
              </button>

              {/* ACKNOWLEDGE: EMERALD */}
              <button
                onClick={() => updateStatus('ACKNOWLEDGED')}
                className={`py-2.5 px-3 rounded-xl font-bold transition flex items-center justify-center gap-1.5 text-xs border cursor-pointer ${
                  currentStatus === 'ACKNOWLEDGED'
                    ? 'bg-emerald-500 text-black font-black shadow-lg shadow-emerald-500/20'
                    : 'bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 border-emerald-500/30'
                }`}
              >
                <Check className="w-3.5 h-3.5" />
                <span>ACKNOWLEDGE</span>
              </button>

              {/* ESCALATE: AMBER */}
              <button
                onClick={() => updateStatus('ESCALATED')}
                className={`py-2.5 px-3 rounded-xl font-bold transition flex items-center justify-center gap-1.5 text-xs border cursor-pointer ${
                  currentStatus === 'ESCALATED'
                    ? 'bg-amber-500 text-black font-black shadow-lg shadow-amber-500/20'
                    : 'bg-amber-500/15 hover:bg-amber-500/25 text-amber-400 border-amber-500/30'
                }`}
              >
                <ArrowUpRight className="w-3.5 h-3.5" />
                <span>ESCALATE</span>
              </button>

              {/* RESOLVE: EMERALD */}
              <button
                onClick={() => updateStatus('RESOLVED')}
                className={`py-2.5 px-3 rounded-xl font-bold transition flex items-center justify-center gap-1.5 text-xs border cursor-pointer ${
                  currentStatus === 'RESOLVED'
                    ? 'bg-emerald-500 text-black font-black shadow-lg shadow-emerald-500/20'
                    : 'bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 border-emerald-500/30'
                }`}
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>RESOLVE</span>
              </button>
            </div>

            {/* Calculate Evacuation Route Button */}
            <button
              disabled={routeLoading}
              onClick={onCalculateRoute}
              className="w-full bg-[#181D22] hover:bg-[#1C2228] text-white border border-white/10 hover:border-[#FF7A18]/50 font-black py-2.5 rounded-xl transition flex items-center justify-center gap-2 shadow text-xs font-mono uppercase tracking-wider cursor-pointer"
            >
              <Compass className="w-4 h-4 text-[#FF7A18]" />
              {routeLoading ? 'COMPUTING SAFE ROUTE...' : 'COMPUTE EVACUATION ROUTE'}
            </button>

            <div className="bento-card p-3 space-y-2 shadow-lg">
              <span className="text-[10px] text-gray-400 uppercase font-mono font-bold block border-b border-white/10 pb-2">
                ACTION LOG
              </span>
              {actionLog.length > 0 ? (
                <div className="space-y-1.5">
                  {actionLog.slice(-5).reverse().map((entry) => (
                    <div key={entry.id} className="flex items-center justify-between gap-2 text-[10px] font-mono">
                      <span className="text-gray-500 flex-shrink-0">{entry.time}</span>
                      <span className="text-gray-300 truncate">{entry.village}</span>
                      <span
                        className={`font-bold flex-shrink-0 ${
                          entry.status === 'ESCALATED' ? 'text-amber-400' : 'text-emerald-400'
                        }`}
                      >
                        {entry.status}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <span className="text-xs text-gray-500 font-sans">No actions logged yet</span>
              )}
            </div>
          </div>

          {/* Bento Card 3: Operational Time Margins (Lead Time, Transit Time, Safety Margin) */}
          <div className="bento-card p-4 space-y-2 shadow-lg">
            <span className="text-[10px] text-gray-400 uppercase font-mono font-bold block">
              OPERATIONAL TIME MARGINS
            </span>
            <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono">
              <div className="bg-[#14181D] p-2.5 rounded-xl border border-white/5">
                <span className="text-[10px] text-gray-400 block font-sans">Lead Time</span>
                <strong className="text-[#FFB703] text-sm">{availableLeadTime != null ? `${availableLeadTime.toFixed(0)}m` : 'Unavailable'}</strong>
              </div>
              <div className="bg-[#14181D] p-2.5 rounded-xl border border-white/5">
                <span className="text-[10px] text-gray-400 block font-sans">Travel Time</span>
                <strong className="text-white text-sm">{travelTime != null ? `${travelTime.toFixed(1)}m` : 'Unavailable'}</strong>
              </div>
              <div className="bg-[#14181D] p-2.5 rounded-xl border border-white/5">
                <span className="text-[10px] text-gray-400 block font-sans">Safety Margin</span>
                <strong className="text-emerald-400 text-sm">{safetyMargin != null ? `${safetyMargin >= 0 ? '+' : ''}${safetyMargin.toFixed(0)}m` : 'Unavailable'}</strong>
              </div>
            </div>
          </div>

          {/* Bento Card 4: Computed Safe Route Details */}
          {activeRoute && (
            <div className="bento-card p-4 space-y-3 bento-glow-emerald font-mono">
              <div className="flex items-center justify-between text-xs font-black text-emerald-400 border-b border-emerald-500/20 pb-2">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  SAFE PATHFINDER COMPUTED
                </span>
                <span>Safety: {routeSafety}%</span>
              </div>

              <div className="space-y-1.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Destination:</span>
                  <strong className="text-white">{activeRoute.destination_shelter_name}</strong>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Distance:</span>
                  <strong className="text-emerald-400">{routeDistance != null ? `${routeDistance.toFixed(1)} km` : 'Unavailable'}</strong>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Estimated Transit:</span>
                  <strong className="text-[#FFB703]">{travelTime != null ? `${travelTime.toFixed(1)} mins` : 'Unavailable'}</strong>
                </div>
              </div>

              {activeRoute.hazards_encountered.length > 0 && (
                <div className="p-2.5 bg-red-500/15 border border-red-500/30 rounded-xl text-[11px] text-white flex items-start gap-2">
                  <AlertOctagon className="w-3.5 h-3.5 text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-red-400 block">Bypassed Blocked Segments:</strong>
                    <span>{activeRoute.hazards_encountered.join(', ')}</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Bento Card 5: Recommended Shelter & Alternatives */}
          <div className="bento-card p-4 space-y-3 shadow-lg font-mono">
            <div className="flex items-center justify-between border-b border-white/10 pb-2">
              <span className="text-xs font-bold text-white uppercase flex items-center gap-1.5">
                <Building2 className="w-3.5 h-3.5 text-[#FFB703]" />
                RECOMMENDED RELIEF SHELTER
              </span>
              <span className="text-[10px] text-emerald-400 bg-emerald-500/15 px-2 py-0.5 rounded-lg border border-emerald-500/30 font-bold">
                Suitability: {shelterSuitability != null ? `${shelterSuitability}%` : 'N/A'}
              </span>
            </div>

            {recommendedShelter ? (
              <div className="bg-[#14181D] p-3 rounded-xl border border-white/5 space-y-1.5 text-xs">
                <div className="flex items-center justify-between">
                  <strong className="text-white font-bold truncate max-w-[240px]">{recommendedShelter.name}</strong>
                  <span className="text-[10px] text-gray-400 font-mono">
                    {recommendedShelter.total_capacity != null ? `Cap: ${recommendedShelter.total_capacity}` : 'Capacity: Not published'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-gray-400">
                  <span>Occupancy: {recommendedShelter.current_occupancy != null ? recommendedShelter.current_occupancy : 'Not published'}</span>
                  <span className="text-emerald-400 font-bold">
                    Available: {recommendedShelter.available_capacity != null ? recommendedShelter.available_capacity : 'Not published'}
                  </span>
                </div>
              </div>
            ) : (
              <div className="bg-[#14181D] p-3 rounded-xl border border-white/5 text-xs text-gray-400 text-center">
                No recommended shelter computed. Click &quot;COMPUTE EVACUATION ROUTE&quot; above.
              </div>
            )}

            {/* Alternative Candidate Shelters */}
            {alternativeShelters.length > 0 && (
              <div className="space-y-1.5 pt-1">
                <span className="text-[10px] text-gray-400 uppercase font-bold block">ALTERNATIVE SHELTER CANDIDATES</span>
                <div className="space-y-1 max-h-28 overflow-y-auto">
                  {alternativeShelters.slice(0, 3).map((alt) => (
                    <div key={alt.id} className="bg-[#14181D] p-2 rounded-lg border border-white/5 flex items-center justify-between text-[10px]">
                      <span className="text-gray-300 truncate max-w-[200px]">{alt.name}</span>
                      <span className="text-gray-400">
                        {alt.total_capacity != null ? `Cap ${alt.total_capacity}` : 'Not published'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Bento Card 6: Road Network Live Impedance Status */}
          <div className="bento-card p-4 space-y-2 shadow-lg font-mono text-xs">
            <span className="text-[10px] text-gray-400 uppercase font-bold block">
              WATERSHED ROAD NETWORK STATUS
            </span>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="bg-[#14181D] p-2.5 rounded-xl border border-white/5">
                <span className="text-[10px] text-gray-400 block font-sans">Safe/Open</span>
                <strong className="text-emerald-400 text-sm font-black">{safeRoads.length}</strong>
              </div>
              <div className="bg-[#14181D] p-2.5 rounded-xl border border-white/5">
                <span className="text-[10px] text-gray-400 block font-sans">Degraded</span>
                <strong className="text-amber-400 text-sm font-black">{degradedRoads.length}</strong>
              </div>
              <div className="bg-[#14181D] p-2.5 rounded-xl border border-white/5">
                <span className="text-[10px] text-gray-400 block font-sans">Blocked</span>
                <strong className="text-red-400 text-sm font-black">{blockedRoads.length}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Response;
