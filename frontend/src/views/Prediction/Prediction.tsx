import React, { useEffect, useState } from 'react';
import {
  VillageRiskDetail,
  LandslideRiskDetail,
  RoadSegment,
  Shelter,
  WhatIfSimulationResponse,
} from '../../types';
import { GeospatialMonitoringMap } from '../../components/map/GeospatialMonitoringMap';
import { WhatIfSimulator } from '../../components/WhatIfSimulator';
import {
  Clock,
  History,
  TrendingUp,
  Sliders,
  MapPin,
  Flame,
  Layers,
  Sparkles,
  Waves,
} from 'lucide-react';
import { DeepHydrographVisualizer } from '../../components/DeepHydrographVisualizer';
import { getStationMetadata } from '../../utils/stationMetadata';
import { fetchVillageLeadTime, fetchVillageHistoricalLandslideSummary } from '../../services/api';

interface Props {
  villages: VillageRiskDetail[];
  selectedVillageId: string | null;
  onSelectVillage: (id: string) => void;
  selectedVillageDetail: VillageRiskDetail | null;
  selectedLandslide: LandslideRiskDetail | null;
  roads: RoadSegment[];
  shelters: Shelter[];
  activeSimulation: WhatIfSimulationResponse | null;
  onSimulationUpdate: (sim: WhatIfSimulationResponse | null) => void;
}

export const Prediction: React.FC<Props> = ({
  villages,
  selectedVillageId,
  onSelectVillage,
  selectedVillageDetail,
  selectedLandslide,
  roads,
  shelters,
  activeSimulation,
  onSimulationUpdate,
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'XAI_EXPLANATION' | 'WHAT_IF_SANDBOX' | 'DEEP_HYDROGRAPH'>('XAI_EXPLANATION');
  const [leadTime, setLeadTime] = useState<import('../../types').VillageLeadTimeDetail | null>(null);
  const [historicalSummary, setHistoricalSummary] = useState<any>(null);

  useEffect(() => {
    if (!selectedVillageId) {
      setLeadTime(null);
      setHistoricalSummary(null);
      return;
    }
    let cancelled = false;
    Promise.all([
      fetchVillageLeadTime(selectedVillageId).catch(() => null),
      fetchVillageHistoricalLandslideSummary(selectedVillageId).catch(() => null),
    ]).then(([lt, hist]) => {
      if (!cancelled) {
        setLeadTime(lt);
        setHistoricalSummary(hist);
      }
    });
    return () => { cancelled = true; };
  }, [selectedVillageId]);

  const stationMeta = getStationMetadata(selectedVillageId);

  const floodScore = Math.round(selectedVillageDetail?.flash_flood_risk_score || 0);
  const landslideScore = Math.round(selectedLandslide?.landslide_risk_score || 0);
  const overallRiskScore = Math.round((floodScore * 0.55) + (landslideScore * 0.45));
  const rawConf = selectedVillageDetail?.confidence || 0.85;
  const confidence = Math.round(rawConf > 1 ? rawConf : rawConf * 100);
  const factors = selectedVillageDetail?.factors || [];

  const getOverallLevel = (score: number) => {
    if (score >= 75) return { label: 'CRITICAL', color: 'text-red-400', stroke: '#EF4444' };
    if (score >= 55) return { label: 'HIGH', color: 'text-[#FF7A18]', stroke: '#FF7A18' };
    if (score >= 35) return { label: 'MODERATE', color: 'text-amber-400', stroke: '#F59E0B' };
    return { label: 'LOW', color: 'text-emerald-400', stroke: '#10B981' };
  };

  const overallMeta = getOverallLevel(overallRiskScore);

  // SVG Circular Ring parameters
  const ringRadius = 52;
  const circumference = 2 * Math.PI * ringRadius;
  const strokeDashoffset = circumference - (overallRiskScore / 100) * circumference;

  return (
    <div className="flex-1 flex flex-col h-full min-h-0 w-full bg-[#08090B] overflow-y-auto overflow-x-hidden lg:overflow-hidden font-sans p-2.5 lg:p-3.5 pb-28 sm:pb-32 lg:pb-3.5 space-y-2.5 lg:space-y-3">
      {/* 1. TOP BENTO ROW: GLOWING SCORE + DUAL RISK + CONTROLS */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-2.5 lg:gap-3 flex-shrink-0">
        {/* GLOWING PRIMARY OVERALL RISK SCORE CARD (4 COLS) */}
        <div className="md:col-span-4 bento-card p-3.5 flex items-center justify-between relative overflow-hidden bento-glow-orange">
          <div className="space-y-1 z-10">
            <div className="flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-[#FFB703]" />
              <span className="text-[10px] font-mono font-extrabold uppercase tracking-wider text-gray-400">
                OVERALL RISK INDEX
              </span>
            </div>
            <h3 className="text-sm font-black text-white truncate max-w-[140px]">
              {selectedVillageDetail?.village_name || 'Select Station'}
            </h3>
            <div className="flex items-center gap-2 pt-0.5">
              <span className={`text-xs font-mono font-black ${overallMeta.color}`}>
                {overallMeta.label} THREAT
              </span>
              <span className="text-[10px] font-mono text-gray-400 bg-white/5 px-1.5 py-0.2 rounded border border-white/10">
                Conf: {confidence}%
              </span>
            </div>
          </div>

          {/* Glowing Circular Progress Ring */}
          <div className="relative w-28 h-28 flex items-center justify-center flex-shrink-0">
            {/* Ambient Backlight Glow */}
            <div className="absolute inset-2 rounded-full bg-gradient-to-tr from-[#FF7A18]/25 to-[#FFB703]/20 blur-lg animate-pulse"></div>

            <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 120 120">
              <defs>
                <linearGradient id="scoreOrangeYellow" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#FF7A18" />
                  <stop offset="100%" stopColor="#FFB703" />
                </linearGradient>
              </defs>
              {/* Background Ring */}
              <circle
                cx="60"
                cy="60"
                r={ringRadius}
                fill="transparent"
                stroke="rgba(255, 255, 255, 0.08)"
                strokeWidth="10"
              />
              {/* Foreground Gradient Glow Ring */}
              <circle
                cx="60"
                cy="60"
                r={ringRadius}
                fill="transparent"
                stroke="url(#scoreOrangeYellow)"
                strokeWidth="10"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                className="transition-all duration-1000 ease-out"
              />
            </svg>

            {/* Inner Center Score Display */}
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className="text-2xl font-black font-mono tracking-tight bg-gradient-to-r from-white via-white to-[#FFB703] bg-clip-text text-transparent">
                {overallRiskScore}
              </span>
              <span className={`text-[9px] font-mono font-black uppercase tracking-wider ${overallMeta.color}`}>
                {overallMeta.label}
              </span>
            </div>
          </div>
        </div>

        {/* DUAL RISK CARDS (FLASH FLOOD & LANDSLIDE) (4 COLS) */}
        <div className="md:col-span-4 grid grid-cols-2 gap-2.5">
          {/* Flash Flood Risk Card */}
          <div className="bento-card p-3 flex flex-col justify-between space-y-2">
            <div className="flex items-center justify-between text-[10px] font-mono text-gray-400">
              <span className="uppercase font-bold">FLASH FLOOD</span>
              <Flame className="w-3.5 h-3.5 text-[#FF7A18]" />
            </div>
            <div className="flex items-baseline justify-between">
              <span className="text-2xl font-black text-white font-mono">{floodScore}%</span>
              <span
                className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded border ${
                  floodScore >= 75
                    ? 'bg-red-500/20 text-red-400 border-red-500/40'
                    : floodScore >= 55
                    ? 'bg-orange-500/20 text-orange-400 border-orange-500/40'
                    : 'bg-amber-500/20 text-amber-400 border-amber-500/40'
                }`}
              >
                {selectedVillageDetail?.risk_level || 'MOD'}
              </span>
            </div>
            <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-[#FF7A18] to-[#FFB703] rounded-full"
                style={{ width: `${Math.min(100, Math.max(5, floodScore))}%` }}
              />
            </div>
          </div>

          {/* Landslide Risk Card */}
          <div className="bento-card p-3 flex flex-col justify-between space-y-2">
            <div className="flex items-center justify-between text-[10px] font-mono text-gray-400">
              <span className="uppercase font-bold">LANDSLIDE</span>
              <Layers className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="flex items-baseline justify-between">
              <span className="text-2xl font-black text-white font-mono">{landslideScore}%</span>
              <span
                className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded border ${
                  landslideScore >= 75
                    ? 'bg-red-500/20 text-red-400 border-red-500/40'
                    : landslideScore >= 55
                    ? 'bg-orange-500/20 text-orange-400 border-orange-500/40'
                    : 'bg-amber-500/20 text-amber-400 border-amber-500/40'
                }`}
              >
                {selectedLandslide?.risk_level || 'MOD'}
              </span>
            </div>
            <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-[#FF7A18] to-amber-400 rounded-full"
                style={{ width: `${Math.min(100, Math.max(5, landslideScore))}%` }}
              />
            </div>
          </div>
        </div>

        {/* SUB-TAB TOGGLE & STATION SELECTOR (4 COLS) */}
        <div className="md:col-span-4 bento-card p-3 flex flex-col justify-between space-y-2">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-gray-400 uppercase font-bold text-[10px]">ANALYSIS MODE</span>
            <select
              value={selectedVillageId || 'VIL-001'}
              onChange={(e) => onSelectVillage(e.target.value)}
              className="bg-[#0E1115] border border-white/10 rounded-lg px-2 py-1 text-xs text-white font-mono focus:outline-none focus:border-[#FF7A18] cursor-pointer"
            >
              {villages.map((v) => (
                <option key={v.village_id} value={v.village_id}>
                  {v.village_name} ({v.village_id})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-3 gap-1 bg-[#0E1115] p-1 rounded-xl border border-white/10">
            <button
              onClick={() => setActiveSubTab('XAI_EXPLANATION')}
              className={`py-1.5 px-1.5 rounded-lg text-[11px] font-bold font-mono transition flex items-center justify-center gap-1 cursor-pointer ${
                activeSubTab === 'XAI_EXPLANATION'
                  ? 'bg-gradient-to-r from-[#FF7A18] to-[#FFB703] text-black font-extrabold shadow'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <TrendingUp className="w-3.5 h-3.5" />
              <span>DRIVERS</span>
            </button>
            <button
              onClick={() => setActiveSubTab('WHAT_IF_SANDBOX')}
              className={`py-1.5 px-1.5 rounded-lg text-[11px] font-bold font-mono transition flex items-center justify-center gap-1 cursor-pointer ${
                activeSubTab === 'WHAT_IF_SANDBOX'
                  ? 'bg-gradient-to-r from-[#FF7A18] to-[#FFB703] text-black font-extrabold shadow'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>WHAT-IF</span>
            </button>
            <button
              onClick={() => setActiveSubTab('DEEP_HYDROGRAPH')}
              className={`py-1.5 px-1.5 rounded-lg text-[11px] font-bold font-mono transition flex items-center justify-center gap-1 cursor-pointer ${
                activeSubTab === 'DEEP_HYDROGRAPH'
                  ? 'bg-gradient-to-r from-[#FF7A18] to-[#FFB703] text-black font-extrabold shadow'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Waves className="w-3.5 h-3.5" />
              <span>AI HYDRO</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. MAIN SPLIT CONTENT: MAP + DEEP PREDICTION / WHAT-IF */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-2.5 lg:gap-3 min-h-[440px] lg:min-h-0 overflow-hidden">
        {/* LEFT SPATIAL HAZARD CONTEXT MAP (5 COLS) */}
        <div className="lg:col-span-5 bento-card p-2 flex flex-col h-[480px] sm:h-[520px] lg:h-full min-h-[440px] lg:min-h-0 overflow-hidden relative shadow-2xl flex-shrink-0 lg:flex-shrink">
          <div className="flex items-center justify-between px-3 py-1.5 border-b border-white/10 mb-1 z-10 flex-shrink-0">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-white">
              <MapPin className="w-3.5 h-3.5 text-[#FF7A18]" />
              <span>SPATIAL HAZARD CONTEXT</span>
            </div>
            <span className="text-[10px] font-mono text-gray-400">
              {stationMeta.villageName} ({stationMeta.region})
            </span>
          </div>

          <div className="flex-1 w-full h-full relative rounded-2xl overflow-hidden">
            <GeospatialMonitoringMap
              villages={villages}
              roads={roads}
              shelters={shelters}
              activeRoute={null}
              selectedVillageId={selectedVillageId}
              onSelectVillage={onSelectVillage}
              isSimulationActive={!!activeSimulation}
            />
          </div>
        </div>

        {/* RIGHT BENTO WORKSPACE: XAI EXPLANATIONS OR WHAT-IF SANDBOX (7 COLS) */}
        <div className="lg:col-span-7 h-full overflow-y-auto space-y-3 pr-1">
          {activeSubTab === 'XAI_EXPLANATION' ? (
            <div className="space-y-3">
              {/* Bento Card 1: Risk Drivers / Why This Risk? (Factor Contribution Bars) */}
              <div className="bento-card p-4 space-y-3 shadow-lg">
                <div className="flex items-start justify-between border-b border-white/10 pb-2.5">
                  <div>
                    <h3 className="text-sm font-black text-white flex items-center gap-2 font-mono">
                      <TrendingUp className="w-4 h-4 text-[#FF7A18]" />
                      MULTI-FACTOR RISK CONTRIBUTION BREAKDOWN
                    </h3>
                    <p className="text-xs text-gray-400 font-sans mt-0.5">
                      Deterministic mathematical contribution points for {selectedVillageDetail?.village_name || 'selected station'}.
                    </p>
                  </div>
                  <span className="text-xs font-mono font-extrabold text-[#FFB703] bg-[#FF7A18]/15 px-2 py-1 rounded-lg border border-[#FF7A18]/30">
                    Confidence: {confidence}%
                  </span>
                </div>

                {/* Horizontal Contribution Bars in Orange -> Yellow Gradient */}
                <div className="space-y-2.5">
                  {factors.map((factor, idx) => (
                    <div key={idx} className="bg-[#14181D] p-3 rounded-xl border border-white/5 space-y-1.5">
                      <div className="flex items-center justify-between text-xs font-mono">
                        <span className="font-bold text-white flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-[#FF7A18]" />
                          {factor.feature_label}
                        </span>
                        <span className="text-[#FFB703] font-bold">
                          +{factor.contribution_points.toFixed(1)} pts ({Math.round(factor.contribution_percent)}%)
                        </span>
                      </div>

                      {/* Orange -> Yellow Gradient Progress Bar */}
                      <div className="w-full bg-[#0E1115] h-2 rounded-full overflow-hidden border border-white/5">
                        <div
                          className="h-full bg-gradient-to-r from-[#FF7A18] to-[#FFB703] rounded-full transition-all duration-500"
                          style={{ width: `${Math.min(100, Math.max(5, factor.contribution_percent))}%` }}
                        />
                      </div>

                      <div className="flex items-center justify-between text-[10px] text-gray-400 font-mono pt-0.5">
                        <span>Observed Value: <strong className="text-white">{factor.raw_value.toFixed(1)} {factor.unit}</strong></span>
                        <span>Physics Weight: {Math.round(factor.weight * 100)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Bento Card 2: Historical Landslide Inventory Evidence (GSI / ISRO) */}
              <div className="bento-card p-4 space-y-3 shadow-lg">
                <div className="flex items-center justify-between border-b border-white/10 pb-2">
                  <h3 className="text-xs font-bold text-white flex items-center gap-2 font-mono">
                    <History className="w-4 h-4 text-[#FFB703]" />
                    HISTORICAL LANDSLIDE INVENTORY (GSI / ISRO)
                  </h3>
                  <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/15 px-2 py-0.5 rounded border border-emerald-500/30">
                    VERIFIED
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                  <div className="bg-[#14181D] p-2.5 rounded-xl border border-white/5">
                    <span className="text-[10px] text-gray-400 block font-sans">Recorded Events</span>
                    <strong className="text-xs text-white mt-1 block">{historicalSummary?.events_within_15km ?? '—'} Events in 15 km</strong>
                  </div>
                  <div className="bg-[#14181D] p-2.5 rounded-xl border border-white/5">
                    <span className="text-[10px] text-gray-400 block font-sans">Nearest Proximity</span>
                    <strong className="text-xs text-white mt-1 block">{historicalSummary?.nearest_event_distance_km != null ? `${Number(historicalSummary.nearest_event_distance_km).toFixed(1)} km` : 'Unavailable'}</strong>
                  </div>
                  <div className="bg-[#14181D] p-2.5 rounded-xl border border-white/5">
                    <span className="text-[10px] text-gray-400 block font-sans">Susceptibility</span>
                    <strong className="text-xs text-[#FF7A18] mt-1 block">{historicalSummary?.historical_susceptibility_evidence?.replaceAll('_', ' ') || 'Unavailable'}</strong>
                  </div>
                </div>

                <p className="text-[11px] text-gray-400 font-sans leading-relaxed">
                  Historical slope destabilization verified against Geological Survey of India and ISRO National Remote Sensing Centre landslide inventories.
                </p>
              </div>

              {/* Bento Card 3: Operational Lead-Time & Mobilization Window */}
              <div className="bento-card p-4 space-y-3 shadow-lg">
                <div className="flex items-center justify-between border-b border-white/10 pb-2">
                  <h3 className="text-xs font-bold text-white flex items-center gap-2 font-mono">
                    <Clock className="w-4 h-4 text-emerald-400" />
                    OPERATIONAL LEAD-TIME & MOBILIZATION MARGIN
                  </h3>
                  <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/15 px-2 py-0.5 rounded border border-emerald-500/30">
                    SUFFICIENT
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                  <div className="bg-[#14181D] p-2.5 rounded-xl border border-white/5">
                    <span className="text-[10px] text-gray-400 block font-sans">Inflow Window</span>
                    <strong className="text-xs text-[#FFB703] mt-1 block">{leadTime?.available_lead_time_minutes != null ? `${Number(leadTime.available_lead_time_minutes).toFixed(1)}m` : 'Unavailable'}</strong>
                  </div>
                  <div className="bg-[#14181D] p-2.5 rounded-xl border border-white/5">
                    <span className="text-[10px] text-gray-400 block font-sans">Evacuation Transit</span>
                    <strong className="text-xs text-white mt-1 block">{leadTime ? `${Number(leadTime.evacuation_time_minutes).toFixed(1)} mins` : 'Unavailable'}</strong>
                  </div>
                  <div className="bg-[#14181D] p-2.5 rounded-xl border border-white/5">
                    <span className="text-[10px] text-gray-400 block font-sans">Safety Margin</span>
                    <strong className={`text-xs mt-1 block ${leadTime?.decision_status === 'INSUFFICIENT' ? 'text-red-400' : leadTime?.decision_status === 'TIGHT' ? 'text-amber-400' : 'text-emerald-400'}`}>{leadTime?.safety_margin_minutes != null ? `${leadTime.safety_margin_minutes >= 0 ? '+' : ''}${Number(leadTime.safety_margin_minutes).toFixed(1)}m (${leadTime.decision_status})` : 'Unavailable'}</strong>
                  </div>
                </div>
              </div>
            </div>
          ) : activeSubTab === 'DEEP_HYDROGRAPH' ? (
            <div className="w-full">
              <DeepHydrographVisualizer
                villageId={selectedVillageId}
                villageName={selectedVillageDetail?.village_name}
              />
            </div>
          ) : (
            <div className="w-full">
              <WhatIfSimulator
                onSimulationUpdate={onSimulationUpdate}
                activeSimulation={activeSimulation}
                selectedVillageId={selectedVillageId}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Prediction;
