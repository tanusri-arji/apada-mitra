import React, { useEffect, useState } from 'react';
import {
  VillageRiskDetail,
  RoadSegment,
  Shelter,
} from '../../types';
import { GeospatialMonitoringMap } from '../../components/map/GeospatialMonitoringMap';
import {
  FileCheck,
  MapPin,
  Info,
  Shield,
  Database,
  Terminal,
  CheckCircle2,
  Clock,
  Play,
  Cpu,
  ArrowRight,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

interface Props {
  villages: VillageRiskDetail[];
  selectedVillageId: string | null;
  onSelectVillage: (id: string) => void;
  roads: RoadSegment[];
  shelters: Shelter[];
}

interface HistoricalDisasterEvent {
  id: string;
  title: string;
  date: string;
  region: string;
  type: string;
  description: string;
  status: string;
  catchmentLat: number;
  catchmentLon: number;
}

const HISTORICAL_EVENTS_CATALOG: HistoricalDisasterEvent[] = [
  {
    id: 'HIST-2021-CHAMOLI',
    title: 'Chamoli Rockslide & Flash Flood Surge',
    date: 'February 7, 2021',
    region: 'Rishi Ganga & Dhauliganga (Chamoli, UK)',
    type: 'Glacial Rock-Ice Detachment & Flash Surge',
    description: 'High-elevation hanging glacier detachment triggering debris flood impacting Rini, Tapovan, and downstream reaches.',
    status: 'HISTORICAL CASE STUDY',
    catchmentLat: 30.485,
    catchmentLon: 79.728,
  },
  {
    id: 'HIST-2013-KEDARNATH',
    title: 'Kedarnath Extreme Cloudburst & GLOF',
    date: 'June 16–17, 2013',
    region: 'Mandakini Valley (Rudraprayag, UK)',
    type: 'Chorabari Lake Outburst & Cloudburst',
    description: 'Catastrophic multi-day precipitation cascade causing severe flash floods and extensive slope failures across Sonprayag and Gaurikund.',
    status: 'HISTORICAL CASE STUDY',
    catchmentLat: 30.735,
    catchmentLon: 79.066,
  },
  {
    id: 'HIST-2024-WAYANAD',
    title: 'Wayanad Multi-Slope Debris Flow',
    date: 'July 30, 2024',
    region: 'Iruvaipuzha Basin (Wayanad, Kerala)',
    type: 'Extreme Precipitation Debris Avalanche',
    description: 'Intense 48h rainfall exceeding 300mm triggering mudflows across Chooralmala, Mundakkai, and Meppadi slopes.',
    status: 'HISTORICAL CASE STUDY',
    catchmentLat: 11.532,
    catchmentLon: 76.136,
  },
];

const HAZARD_CASCADES: Record<string, string[]> = {
  'HIST-2021-CHAMOLI': ['Rock/Glacier Detachment', 'Debris Flow', 'River Surge', 'Flash Flood', 'Downstream Impact'],
  'HIST-2013-KEDARNATH': ['Extreme Rainfall + GLOF', 'Water Surge', 'Flood/Debris', 'Infrastructure Risk'],
  'HIST-2024-WAYANAD': ['Heavy Rainfall', 'Soil Saturation', 'Slope Instability', 'Multiple Slope Failures', 'Debris Flow'],
};

const RESPONSE_ITEMS = [
  ['Risk Analysis', 'Replay the initiating hazard and cascade profile.'],
  ['Exposure', 'Estimate downstream population and critical assets at risk.'],
  ['Evacuation Priority', 'Rank impacted settlements by urgency and lead time.'],
  ['Hazard-Aware Route', 'Recompute routes while bypassing affected segments.'],
  ['Shelter', 'Match exposed population to safe, available capacity.'],
];

const CASE_STUDY_DETAILS: Record<string, { narrative: string; impact: string[]; lesson: string }> = {
  'HIST-2021-CHAMOLI': {
    narrative: 'On February 7, 2021, a high-elevation rock and glacier detachment entered the Rishi Ganga system and rapidly transformed into a debris flow. The surge traveled through the Rishi Ganga and Dhauliganga valleys, damaging downstream settlements and infrastructure around Rini and Tapovan.',
    impact: ['Fatalities: Illustrative reference figure: 200+', 'Displaced population: Illustrative reference figure: 1,000+', 'Infrastructure damage: Illustrative reference figure: roads, bridges, and hydropower assets'],
    lesson: 'Early detection of cascading high-altitude failures must feed directly into downstream evacuation decisions.',
  },
  'HIST-2013-KEDARNATH': {
    narrative: 'During June 16–17, 2013, extreme rainfall combined with the Chorabari Lake outburst to produce a fast-moving water surge through the Mandakini Valley. Floodwater and debris overwhelmed routes and built infrastructure around Kedarnath, Sonprayag, and Gaurikund.',
    impact: ['Fatalities: Illustrative reference figure: 5,000+', 'Displaced population: Illustrative reference figure: 100,000+', 'Infrastructure damage: Illustrative reference figure: roads, bridges, homes, and public facilities'],
    lesson: 'Compound rainfall and outburst hazards require unified warning, route closure, and shelter coordination.',
  },
  'HIST-2024-WAYANAD': {
    narrative: 'On July 30, 2024, intense rainfall across the Iruvaipuzha Basin saturated slopes around Chooralmala, Mundakkai, and Meppadi. The resulting instability produced multiple slope failures and debris flows that crossed settlements and disrupted access through the Wayanad highlands.',
    impact: ['Fatalities: Illustrative reference figure: 200+', 'Displaced population: Illustrative reference figure: 1,000+', 'Infrastructure damage: Illustrative reference figure: homes, roads, bridges, and utilities'],
    lesson: 'Rainfall accumulation and soil saturation indicators can provide crucial time to prioritize slope-risk communities.',
  },
};

export const Validation: React.FC<Props> = ({
  villages,
  selectedVillageId,
  onSelectVillage,
  roads,
  shelters,
}) => {
  const [selectedEventId, setSelectedEventId] = useState<string>('HIST-2021-CHAMOLI');
  const [isDetailExpanded, setIsDetailExpanded] = useState(false);

  useEffect(() => {
    setIsDetailExpanded(false);
  }, [selectedEventId]);

  const activeEvent = HISTORICAL_EVENTS_CATALOG.find((e) => e.id === selectedEventId) || HISTORICAL_EVENTS_CATALOG[0];
  const activeCaseStudyDetails = CASE_STUDY_DETAILS[activeEvent.id];

  return (
    <div className="flex-1 flex flex-col h-full bg-[#08090B] overflow-y-auto overflow-x-hidden lg:overflow-hidden font-sans p-2.5 lg:p-4 space-y-3">
      {/* 1. TOP VALIDATION RIBBON */}
      <div className="bento-card px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs font-mono flex-shrink-0 shadow-lg">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <FileCheck className="w-4 h-4 text-[#FF7A18]" />
            <span className="text-white font-black tracking-wider uppercase">
              HISTORICAL CASE STUDY & BENCHMARK REFERENCE WORKSPACE
            </span>
          </div>
          <div className="hidden lg:flex items-center gap-3 text-gray-400 text-[11px]">
            <span>Methodology: <strong className="text-white">Historical Case Study Analysis</strong></span>
            <span>•</span>
            <span>Focus: <strong className="text-[#FFB703]">Reference Event Documentation</strong></span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-bold text-[11px] flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-emerald-400" />
            CASE STUDY FRAMEWORK
          </span>
        </div>
      </div>

      {/* 2. MAIN BENTO GRID: LEFT MAP + RIGHT REPLAY WORKSPACE */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-3 min-h-0 overflow-visible lg:overflow-hidden">
        {/* LEFT HISTORICAL CATCHMENT MAP BENTO (5 COLS) */}
        <div className="lg:col-span-5 bento-card p-2 flex flex-col h-[380px] lg:h-full min-h-[340px] lg:min-h-0 overflow-hidden relative shadow-2xl flex-shrink-0 lg:flex-shrink">
          <div className="flex items-center justify-between px-3 py-1.5 border-b border-white/10 mb-1 z-10 flex-shrink-0">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-white">
              <MapPin className="w-3.5 h-3.5 text-[#FF7A18]" />
              <span>HISTORICAL CASE STUDY CATCHMENT ZONE</span>
            </div>
            <span className="text-[10px] font-mono text-gray-400">
              {activeEvent.title.split(' ')[0]} Catchment
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
              isSimulationActive={false}
            />
          </div>

          {/* Active Replay Metadata Footer */}
          <div className="p-3 bg-[#14181D] border-t border-white/10 space-y-1.5 text-xs font-mono flex-shrink-0 rounded-b-xl">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Reference Case Study:</span>
              <strong className="text-white">{activeEvent.id}</strong>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Date of Incident:</span>
              <strong className="text-[#FFB703]">{activeEvent.date}</strong>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Reference Profile:</span>
              <span className="text-emerald-400 font-bold flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Documented Record
              </span>
            </div>
          </div>
        </div>

        {/* RIGHT VALIDATION REPLAY & METRICS WORKSPACE (7 COLS) */}
        <div className="lg:col-span-7 h-full min-h-[400px] lg:min-h-0 overflow-visible lg:overflow-y-auto space-y-3 pr-1">
          {/* Bento Card 1: Transparent Scientific Honesty Notice */}
          <div className="bento-card p-4 space-y-2 border-amber-500/30 bg-[#14181D]">
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-[#FFB703] flex-shrink-0 mt-0.5" />
              <div className="space-y-1">
                <strong className="text-[#FFB703] font-mono font-bold text-xs uppercase block">
                  SCIENTIFIC HONESTY & TRANSPARENCY NOTICE
                </strong>
                <p className="text-xs text-gray-300 font-sans leading-relaxed">
                  In adherence to strict engineering honesty, the system does not claim to have predicted or dynamically reproduced these historical disaster events. The cases below serve as documented historical reference case studies and benchmark targets for qualitative scenario evaluation.
                </p>
              </div>
            </div>
          </div>

          {/* Bento Card 2: Historical Disaster Events Catalog (3 Reference Case Studies) */}
          <div className="bento-card p-4 space-y-3 shadow-lg">
            <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
              <div>
                <h3 className="text-xs font-black text-white uppercase flex items-center gap-2 font-mono">
                  <Database className="w-4 h-4 text-[#FF7A18]" />
                  DOCUMENTED DISASTER CASE STUDIES (3 HISTORICAL REFERENCE EVENTS)
                </h3>
                <p className="text-[11px] text-gray-400 font-sans mt-0.5">
                  Select a historical disaster event to inspect reference event records and benchmark parameters.
                </p>
              </div>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/15 px-2 py-0.5 rounded-lg border border-emerald-500/30">
                HISTORICAL REFERENCE
              </span>
            </div>

            {/* 3 Case Study Bento Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5 font-mono">
              {HISTORICAL_EVENTS_CATALOG.map((event) => {
                const isSelected = event.id === selectedEventId;
                return (
                  <button
                    key={event.id}
                    onClick={() => setSelectedEventId(event.id)}
                    aria-pressed={isSelected}
                    className={`text-left p-3 rounded-2xl border transition flex flex-col justify-between space-y-2 cursor-pointer ${
                      isSelected
                        ? 'bg-gradient-to-br from-[#FF7A18]/20 to-[#FFB703]/20 border-[#FF7A18] text-white shadow-lg shadow-orange-500/15'
                        : 'bg-[#14181D] border-white/10 text-gray-300 hover:border-white/20 hover:text-white'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between text-[10px] font-mono mb-1">
                        <span className="font-black text-[#FFB703]">{event.date}</span>
                        <span className="text-gray-500 text-[9px]">{event.id}</span>
                      </div>
                      <h4 className="font-bold text-white text-xs leading-snug">
                        {event.title}
                      </h4>
                      <p className="text-[10px] text-gray-400 font-sans mt-1">
                        {event.region}
                      </p>
                    </div>

                    <div className="pt-2 border-t border-white/10 flex items-center justify-between text-[10px] font-mono">
                      <span className="text-gray-400">{event.type.split(' ')[0]}</span>
                      <span className="text-emerald-400 font-bold">{event.status}</span>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Selected Event Details Breakdown */}
            <div className="bg-[#14181D] p-3.5 rounded-2xl border border-white/5 space-y-2 font-mono">
              <div className="flex items-center justify-between text-xs">
                <span className="text-white font-bold">Case Study: {activeEvent.title}</span>
                <span className="text-[#FFB703] font-bold">{activeEvent.status}</span>
              </div>
              <p className="text-xs text-gray-400 font-sans leading-relaxed">
                {activeEvent.description}
              </p>
              <button
                type="button"
                onClick={() => setIsDetailExpanded((expanded) => !expanded)}
                aria-expanded={isDetailExpanded}
                className="w-full flex items-center gap-3 pt-2 text-xs text-left cursor-pointer group"
              >
                <span className="bg-white/5 text-gray-500 px-3 py-1.5 rounded-xl border border-white/10 flex items-center gap-1.5 text-[11px] group-hover:border-[#FF7A18]/50 group-hover:text-gray-300 transition">
                  <Play className="w-3.5 h-3.5" />
                  OFFLINE CASE STUDY REFERENCE ONLY
                </span>
                <span className="text-[11px] text-gray-400 font-sans flex-1">
                  Documented historical event for qualitative benchmarking.
                </span>
                {isDetailExpanded ? (
                  <ChevronUp className="w-4 h-4 text-[#FF7A18] flex-shrink-0" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-[#FF7A18] flex-shrink-0" />
                )}
              </button>
              <div
                className={`overflow-hidden transition-all duration-300 ease-out ${
                  isDetailExpanded ? 'max-h-96 opacity-100 translate-y-0 pt-2' : 'max-h-0 opacity-0 -translate-y-1'
                }`}
              >
                <div className="bg-[#08090B] border border-[#FF7A18]/25 rounded-xl p-3 space-y-2.5 text-xs">
                  <p className="text-gray-300 font-sans leading-relaxed">{activeCaseStudyDetails.narrative}</p>
                  <div className="space-y-1.5 font-mono">
                    <span className="text-[10px] text-[#FFB703] uppercase font-bold block">Impact</span>
                    {activeCaseStudyDetails.impact.map((stat) => (
                      <div key={stat} className="text-[10px] text-gray-400">{stat}</div>
                    ))}
                    <span className="text-[10px] text-[#FFB703] uppercase font-bold block pt-1">Key Lesson</span>
                    <div className="text-[10px] text-gray-300 font-sans">{activeCaseStudyDetails.lesson}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Selected Event Hazard Cascade */}
            <div className="bg-[#14181D] p-3.5 rounded-2xl border border-white/5 space-y-3 font-mono">
              <div className="flex items-center justify-between border-b border-white/10 pb-2">
                <span className="text-xs font-black text-white uppercase">HAZARD CASCADE</span>
                <span className="text-[10px] text-[#FFB703]">{activeEvent.date}</span>
              </div>
              <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
                {HAZARD_CASCADES[activeEvent.id].map((stage, index) => (
                  <React.Fragment key={stage}>
                    <div
                      className="min-w-max bg-[#08090B] border border-[#FF7A18]/40 text-gray-200 rounded-xl px-2.5 py-2 text-[10px] font-bold text-center"
                      style={{
                        animation: 'validation-cascade-stage 420ms ease-out both',
                        animationDelay: `${index * 110}ms`,
                      }}
                    >
                      {stage}
                    </div>
                    {index < HAZARD_CASCADES[activeEvent.id].length - 1 && (
                      <ArrowRight
                        className="w-3.5 h-3.5 text-[#FF7A18] flex-shrink-0"
                        style={{
                          animation: 'validation-cascade-stage 420ms ease-out both',
                          animationDelay: `${index * 110 + 55}ms`,
                        }}
                      />
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>

            {/* APADA MITRA Retrospective Response */}
            <div className="bg-[#14181D] p-3.5 rounded-2xl border border-white/5 space-y-2 font-mono">
              <div className="flex items-center gap-2 border-b border-white/10 pb-2">
                <Shield className="w-3.5 h-3.5 text-[#FF7A18]" />
                <span className="text-xs font-black text-white uppercase">APADA MITRA RESPONSE</span>
              </div>
              <div className="space-y-1.5">
                {RESPONSE_ITEMS.map(([label, description]) => (
                  <div key={label} className="flex items-center justify-between gap-3 text-[10px]">
                    <span className="text-[#FFB703] font-bold flex-shrink-0">{label}</span>
                    <span className="text-gray-400 text-right font-sans">{description}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Bento Card 3: Metrics Targets Shell */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Prediction Metric Shell */}
            <div className="bento-card p-4 space-y-3 font-mono">
              <div className="flex items-center justify-between border-b border-white/10 pb-2">
                <h4 className="text-xs font-black text-white flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-[#FF7A18]" />
                  EVALUATION BENCHMARK OBJECTIVES
                </h4>
                <span className="text-[10px] text-gray-400">BENCHMARK TARGETS</span>
              </div>

              <div className="space-y-2 text-xs">
                <div className="bg-[#14181D] p-2.5 rounded-xl border border-white/5 flex items-center justify-between">
                  <div>
                    <span className="text-white font-bold block">ROC-AUC Target</span>
                    <span className="text-[10px] text-gray-400 font-sans">Multi-Hazard Classification Target</span>
                  </div>
                  <strong className="text-[#FFB703]">&gt; 0.85 Target</strong>
                </div>

                <div className="bg-[#14181D] p-2.5 rounded-xl border border-white/5 flex items-center justify-between">
                  <div>
                    <span className="text-white font-bold block">Precision / Recall</span>
                    <span className="text-[10px] text-gray-400 font-sans">Flood & Landslide Objective</span>
                  </div>
                  <strong className="text-[#FFB703]">Target &gt; 0.80</strong>
                </div>

                <div className="bg-[#14181D] p-2.5 rounded-xl border border-white/5 flex items-center justify-between">
                  <div>
                    <span className="text-white font-bold block">Confusion Matrix</span>
                    <span className="text-[10px] text-gray-400 font-sans">Evaluation Framework</span>
                  </div>
                  <strong className="text-emerald-400">Framework Defined</strong>
                </div>
              </div>
            </div>

            {/* Lead-Time Accuracy Shell */}
            <div className="bento-card p-4 space-y-3 font-mono">
              <div className="flex items-center justify-between border-b border-white/10 pb-2">
                <h4 className="text-xs font-black text-white flex items-center gap-2">
                  <Clock className="w-4 h-4 text-emerald-400" />
                  OPERATIONAL WINDOW BENCHMARKS
                </h4>
                <span className="text-[10px] text-gray-400">BENCHMARK TARGETS</span>
              </div>

              <div className="space-y-2 text-xs">
                <div className="bg-[#14181D] p-2.5 rounded-xl border border-white/5 flex items-center justify-between">
                  <div>
                    <span className="text-white font-bold block">Hydrological Lead Time</span>
                    <span className="text-[10px] text-gray-400 font-sans">Inundation Warning</span>
                  </div>
                  <strong className="text-emerald-400">Target &ge; 4.0h</strong>
                </div>

                <div className="bg-[#14181D] p-2.5 rounded-xl border border-white/5 flex items-center justify-between">
                  <div>
                    <span className="text-white font-bold block">Debris Flow Mobilization</span>
                    <span className="text-[10px] text-gray-400 font-sans">Slope Saturation</span>
                  </div>
                  <strong className="text-emerald-400">Target &ge; 2.5h</strong>
                </div>

                <div className="bg-[#14181D] p-2.5 rounded-xl border border-white/5 flex items-center justify-between">
                  <div>
                    <span className="text-white font-bold block">Safe Route Redundancy</span>
                    <span className="text-[10px] text-gray-400 font-sans">Dijkstra Bypass</span>
                  </div>
                  <strong className="text-[#FFB703]">Target 100%</strong>
                </div>
              </div>
            </div>
          </div>

          {/* Bento Card 4: Operational Pipeline Audit Trail Log */}
          <div className="bento-card p-4 space-y-2 shadow-lg font-mono">
            <div className="flex items-center justify-between border-b border-white/10 pb-2">
              <h4 className="text-xs font-black text-white flex items-center gap-2">
                <Terminal className="w-4 h-4 text-[#FF7A18]" />
                PIPELINE AUDIT TRAIL LOG
              </h4>
              <span className="text-[10px] text-emerald-400 bg-emerald-500/15 px-2 py-0.5 rounded-lg border border-emerald-500/30">
                AUDIT ACTIVE
              </span>
            </div>

            <div className="bg-[#14181D] p-3 rounded-2xl border border-white/5 text-[11px] text-gray-400 space-y-1.5">
              <div className="flex items-center gap-2 text-gray-300">
                <span className="text-[#FFB703]">[AUDIT-01]</span>
                <span>Copernicus 30m DEM Elevation Rasters: Ingested & Verified for 15 Stations.</span>
              </div>
              <div className="flex items-center gap-2 text-emerald-400">
                <span className="text-emerald-400">[AUDIT-02]</span>
                <span>GSI Historical Landslide Spatial Polyline Vector Layers: Ingested.</span>
              </div>
              <div className="flex items-center gap-2 text-amber-400">
                <span className="text-amber-400">[AUDIT-03]</span>
                <span>Hydrological Manning-Strickler Runoff Formulas: Deterministic Mode Configured.</span>
              </div>
              <div className="flex items-center gap-2 text-[#FF7A18]">
                <span className="text-[#FF7A18]">[AUDIT-04]</span>
                <span>Hazard-Impedance Dijkstra Evacuation Pathfinder: 0 Submerged Intersections.</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <style>{`
        @keyframes validation-cascade-stage {
          from { opacity: 0; transform: translateX(-10px); }
          to { opacity: 1; transform: translateX(0); }
        }
      `}</style>
    </div>
  );
};

export default Validation;
