import React, { useState, useEffect } from 'react';
import {
  Search,
  RotateCcw,
  SlidersHorizontal,
  Maximize,
  Minimize,
  Menu,
} from 'lucide-react';
import { ScenarioStateResponse, ReadinessResponse, TopLevelView, VillageRiskDetail } from '../types';

interface Props {
  scenarioState: ScenarioStateResponse | null;
  readinessState?: ReadinessResponse | null;
  onScenarioChangeClick: () => void;
  onDemoReset: () => void;
  backendError: string | null;
  activeTab: TopLevelView;
  isSimulationActive?: boolean;
  villages?: VillageRiskDetail[];
  onSelectVillage?: (id: string) => void;
  onToggleMobileSidebar?: () => void;
}

export const Header: React.FC<Props> = ({
  scenarioState,
  readinessState,
  onScenarioChangeClick,
  onDemoReset,
  backendError,
  activeTab,
  isSimulationActive = false,
  villages = [],
  onSelectVillage,
  onToggleMobileSidebar,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const handleFsChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFsChange);
    return () => document.removeEventListener('fullscreenchange', handleFsChange);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      }
    }
  };

  const isDegraded = !!backendError || (readinessState ? !readinessState.ready : false);
  const readinessText = isDegraded ? 'DEGRADED' : 'ONLINE';
  const readinessDotColor = !isDegraded ? 'bg-emerald-500' : 'bg-amber-500';
  const readinessTextColor = !isDegraded ? 'text-emerald-400' : 'text-amber-400';

  const getPageInfo = (tab: TopLevelView) => {
    switch (tab) {
      case 'LIVE_MONITORING':
        return {
          title: 'LIVE MONITORING',
          subtitle: 'Real-time terrain and sensor intelligence',
        };
      case 'PREDICTION':
        return {
          title: 'PREDICTION',
          subtitle: 'Predictive hazard intelligence & causal attribution',
        };
      case 'EVACUATION_ACTION':
        return {
          title: 'EVACUATION & ACTION',
          subtitle: 'Decide, route, mobilize & incident action desk',
        };
      case 'VALIDATION_REPLAY':
        return {
          title: 'HISTORICAL CASE STUDIES',
          subtitle: 'Documented disaster events & reference scenario analysis',
        };
      default:
        return {
          title: 'COMMAND CENTER',
          subtitle: 'Real-time disaster intelligence',
        };
    }
  };

  const pageInfo = getPageInfo(activeTab);

  const searchResults = villages.filter(
    (v) =>
      v.village_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.village_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <header className="h-16 px-3 lg:px-6 bg-[#0E1115]/90 backdrop-blur-xl border-b border-white/10 flex items-center justify-between gap-2 sm:gap-4 z-30 font-sans flex-shrink-0 relative">
      {/* 1. Left Page Title, Subtitle & Mobile Menu Trigger */}
      <div className="flex items-center gap-2.5 min-w-0 flex-shrink-0">
        {onToggleMobileSidebar && (
          <button
            onClick={onToggleMobileSidebar}
            className="lg:hidden p-2 rounded-xl bg-[#14181D] hover:bg-[#1C2228] border border-white/10 text-gray-300 hover:text-[#FFB703] transition flex items-center justify-center cursor-pointer flex-shrink-0"
            aria-label="Toggle navigation menu"
          >
            <Menu className="w-5 h-5 text-[#FFB703]" />
          </button>
        )}
        <div className="flex-shrink-0 min-w-0">
          <h1 className="text-sm sm:text-base lg:text-lg font-black text-white tracking-wider uppercase font-mono leading-none truncate">
            {pageInfo.title}
          </h1>
          <p className="text-xs text-gray-400 font-sans tracking-normal mt-0.5 hidden sm:block truncate">
            {pageInfo.subtitle}
          </p>
        </div>
      </div>

      {/* 2. Center Glassmorphic Search Bar */}
      <div className="flex-1 max-w-lg relative hidden md:block">
        <div className="relative">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search villages, stations, incidents..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setShowSearchResults(e.target.value.length > 0);
            }}
            onFocus={() => setShowSearchResults(searchQuery.length > 0)}
            onBlur={() => setTimeout(() => setShowSearchResults(false), 200)}
            className="w-full bg-[#14181D]/90 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-gray-500 backdrop-blur-md focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]/50 transition shadow-inner font-mono"
          />
        </div>

        {/* Quick Search Dropdown Results */}
        {showSearchResults && searchResults.length > 0 && (
          <div className="absolute top-full mt-2 left-0 right-0 bg-[#14181D] border border-white/15 rounded-2xl p-2 shadow-2xl z-50 max-h-60 overflow-y-auto space-y-1 backdrop-blur-2xl">
            {searchResults.slice(0, 5).map((v) => (
              <button
                key={v.village_id}
                onMouseDown={() => {
                  if (onSelectVillage) onSelectVillage(v.village_id);
                  setSearchQuery('');
                  setShowSearchResults(false);
                }}
                className="w-full text-left p-2 rounded-xl hover:bg-white/10 transition flex items-center justify-between cursor-pointer font-mono text-xs"
              >
                <div>
                  <strong className="text-white block">{v.village_name}</strong>
                  <span className="text-[10px] text-gray-400">{v.village_id} • Elev: {v.elevation}m</span>
                </div>
                <span className="text-xs font-bold text-[#F97316]">
                  {Math.round(v.flash_flood_risk_score)}% ({v.risk_level})
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 3. Right Status Badges & Quick Action Controls */}
      <div className="flex items-center gap-1.5 sm:gap-2.5 text-xs font-mono flex-shrink-0">
        {isSimulationActive && (
          <div className="hidden lg:flex items-center gap-1.5 bg-red-500/15 border border-red-500/40 text-red-400 px-2.5 py-1.5 rounded-xl font-bold text-[11px] animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
            <span>SIMULATION ACTIVE</span>
          </div>
        )}

        {/* SYSTEM STATUS PILL (EMERALD) */}
        <div className="hidden md:flex items-center gap-2 bg-[#14181D] px-3 py-1.5 rounded-xl border border-white/10 text-[11px]">
          <span className={`w-2 h-2 rounded-full ${readinessDotColor} shadow-sm shadow-emerald-500/50`}></span>
          <span className="text-gray-400">SYSTEM:</span>
          <span className={`font-black ${readinessTextColor}`}>
            {readinessText}
          </span>
        </div>

        {/* SCENARIO SELECTOR BUTTON */}
        <button
          onClick={onScenarioChangeClick}
          className="bg-gradient-to-r from-[#FF7A18]/20 to-[#FFB703]/20 hover:from-[#FF7A18]/30 hover:to-[#FFB703]/30 text-[#FFB703] border border-[#FF7A18]/40 hover:border-[#FF7A18]/70 font-extrabold text-xs px-2.5 sm:px-3 py-1.5 rounded-xl transition flex items-center gap-1.5 sm:gap-2 shadow-sm font-mono uppercase tracking-wider cursor-pointer"
        >
          <SlidersHorizontal className="w-3.5 h-3.5 text-[#FF7A18]" />
          <span className="hidden xl:inline text-[10px] text-gray-400">SCENARIO:</span>
          <span className="text-white text-[10px] sm:text-xs">
            {scenarioState?.scenario || 'HEAVY_RAIN'}
          </span>
        </button>

        {/* RESET BUTTON */}
        <button
          onClick={onDemoReset}
          className="p-1.5 sm:px-2.5 sm:py-1.5 bg-[#14181D] hover:bg-[#1C2228] border border-white/10 hover:border-[#FF7A18]/50 text-gray-400 hover:text-white rounded-xl text-xs font-bold font-mono transition flex items-center gap-1.5 cursor-pointer"
          title="Reset application to initial state"
        >
          <RotateCcw className="w-3.5 h-3.5 text-gray-400" />
          <span className="hidden sm:inline">RESET</span>
        </button>

        {/* FULLSCREEN COMMAND CENTER TOGGLE BUTTON */}
        <button
          onClick={toggleFullscreen}
          className="p-1.5 sm:px-2.5 sm:py-1.5 bg-[#14181D] hover:bg-[#1C2228] border border-white/10 hover:border-[#FF7A18]/50 text-gray-300 hover:text-white rounded-xl text-xs font-bold font-mono transition flex items-center gap-1.5 cursor-pointer"
          title={isFullscreen ? "Exit Fullscreen (F11 / Esc)" : "Enter Fullscreen Command Center (F11)"}
        >
          {isFullscreen ? (
            <>
              <Minimize className="w-3.5 h-3.5 text-[#FFB703]" />
              <span className="hidden md:inline text-[11px]">EXIT FULL</span>
            </>
          ) : (
            <>
              <Maximize className="w-3.5 h-3.5 text-gray-400 hover:text-white" />
              <span className="hidden md:inline text-[11px]">FULLSCREEN</span>
            </>
          )}
        </button>
      </div>
    </header>
  );
};

export default Header;
