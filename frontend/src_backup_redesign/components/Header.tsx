import React from 'react';
import { Activity, ShieldAlert, Database, Sliders, LayoutDashboard, RotateCcw } from 'lucide-react';
import { ScenarioStateResponse, ReadinessResponse } from '../types';

interface Props {
  scenarioState: ScenarioStateResponse | null;
  readinessState?: ReadinessResponse | null;
  onScenarioChangeClick: () => void;
  onDemoReset: () => void;
  backendError: string | null;
  activeTab: 'COMMAND_CENTER' | 'WHAT_IF';
  onTabChange: (tab: 'COMMAND_CENTER' | 'WHAT_IF') => void;
  isSimulationActive?: boolean;
}

export const Header: React.FC<Props> = ({
  scenarioState,
  readinessState,
  onScenarioChangeClick,
  onDemoReset,
  backendError,
  activeTab,
  onTabChange,
  isSimulationActive = false,
}) => {
  const isDegraded = !!backendError || (readinessState ? !readinessState.ready : false);
  const readinessText = isDegraded ? 'DEGRADED — FALLBACK ACTIVE' : (readinessState?.status || 'SYSTEM READY');
  const readinessColor = !isDegraded ? 'text-emerald-400' : 'text-amber-400';

  return (
    <header className="h-16 bg-command-card border-b border-command-border px-6 flex items-center justify-between shadow-lg z-20 relative font-mono">
      {/* Brand Title & Navigation Tabs */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-command-accent/10 border border-command-accent/30 flex items-center justify-center text-command-accent">
            <ShieldAlert className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-lg text-white tracking-wide uppercase font-mono">
                APADA MITRA
              </h1>
              <span className="bg-command-accent/20 text-command-accent text-[10px] font-mono font-bold px-2 py-0.5 rounded border border-command-accent/40">
                SIH26192
              </span>
            </div>
            <p className="text-xs text-command-muted font-sans">
              Terrain-Aware Multi-Hazard Disaster Intelligence Platform
            </p>
          </div>
        </div>

        {/* View Switcher Navigation Tabs */}
        <div className="flex bg-command-bg border border-command-border p-1 rounded-lg">
          <button
            onClick={() => onTabChange('COMMAND_CENTER')}
            className={`px-3 py-1.5 rounded-md text-xs font-bold transition flex items-center gap-1.5 ${
              activeTab === 'COMMAND_CENTER'
                ? 'bg-command-accent text-black shadow'
                : 'text-command-muted hover:text-white hover:bg-command-panel'
            }`}
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            COMMAND CENTER
          </button>
          <button
            onClick={() => onTabChange('WHAT_IF')}
            className={`px-3 py-1.5 rounded-md text-xs font-bold transition flex items-center gap-1.5 ${
              activeTab === 'WHAT_IF'
                ? 'bg-command-accent text-black shadow'
                : 'text-command-muted hover:text-white hover:bg-command-panel'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            WHAT-IF SIMULATOR
          </button>
        </div>
      </div>

      {/* Center Readiness Check & Operational Status */}
      <div className="hidden xl:flex items-center gap-4 text-xs font-mono">
        {isSimulationActive && (
          <div className="flex items-center gap-2 bg-red-950/90 border border-red-500 text-red-200 px-3 py-1.5 rounded-full animate-pulse shadow-lg font-bold">
            <span className="w-2 h-2 rounded-full bg-red-400"></span>
            SIMULATION ACTIVE
          </div>
        )}

        <div className="flex items-center gap-2 bg-command-bg px-3 py-1.5 rounded-full border border-command-border">
          <Activity className={`w-3.5 h-3.5 ${backendError ? 'text-amber-400' : 'text-emerald-400'}`} />
          <span className="text-command-muted">Readiness:</span>
          <span className={`font-semibold ${readinessColor}`}>
            {readinessText}
          </span>
        </div>

        <div className="flex items-center gap-2 bg-command-bg px-3 py-1.5 rounded-full border border-command-border">
          <Database className="w-3.5 h-3.5 text-command-accent" />
          <span className="text-command-muted">Data Quality:</span>
          <span className="font-semibold text-command-accent">
            {scenarioState?.data_quality_status || 'OK'}
          </span>
        </div>
      </div>

      {/* Right Controls & Demo Mode Indicator */}
      <div className="flex items-center gap-3">
        <div className="hidden lg:flex items-center gap-1.5 bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs px-2.5 py-1 rounded font-mono" title="100% Offline Local Deterministic Dataset">
          <span className="w-2 h-2 rounded-full bg-amber-400"></span>
          DEMO MODE — SYNTHETIC LOCAL DATA
        </div>

        <button
          onClick={onScenarioChangeClick}
          className="bg-command-accent text-black font-semibold text-xs px-3.5 py-2 rounded-md hover:bg-command-accentHover transition flex items-center gap-2 shadow-md font-mono uppercase"
        >
          <span>Scenario:</span>
          <span className="underline decoration-black/40">
            {scenarioState?.scenario || 'HEAVY_RAIN'}
          </span>
        </button>

        <button
          onClick={onDemoReset}
          className="px-3 py-2 bg-command-bg border border-command-border hover:border-red-500/60 text-command-muted hover:text-white rounded-md hover:bg-command-panel transition flex items-center gap-1.5 font-mono text-xs"
          title="Reset scenario, route, selected village, and simulation to initial state"
        >
          <RotateCcw className="w-3.5 h-3.5 text-amber-400" />
          <span className="hidden sm:inline">RESET DEMO</span>
        </button>
      </div>
    </header>
  );
};

