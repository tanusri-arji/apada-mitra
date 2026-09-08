import React, { useState } from 'react';
import { VillageRiskDetail, RiskLevel, EvacuationPriority, TopLevelView } from '../types';
import { RiskBadge } from './RiskBadge';
import { getRiskColorHex } from '../utils/riskColors';
import {
  Brain,
  Navigation,
  FileCheck,
  Shield,
  Search,
  Filter,
  CheckCircle2,
  Sparkles,
  LayoutDashboard,
} from 'lucide-react';

interface Props {
  activeTab: TopLevelView;
  onTabChange: (tab: TopLevelView) => void;
  villages: VillageRiskDetail[];
  evacuationPriorities?: EvacuationPriority[];
  selectedVillageId: string | null;
  onSelectVillage: (id: string) => void;
  loading: boolean;
}

export const Sidebar: React.FC<Props> = ({
  activeTab,
  onTabChange,
  villages,
  selectedVillageId,
  onSelectVillage,
}) => {
  const [search, setSearch] = useState('');
  const [filterLevel, setFilterLevel] = useState<RiskLevel | 'ALL'>('ALL');
  const [sidebarTab, setSidebarTab] = useState<'NAV' | 'VILLAGES'>('NAV');

  const navItems: {
    id: TopLevelView;
    step: string;
    label: string;
    subtitle: string;
    icon: any;
    badge?: string;
  }[] = [
    {
      id: 'LIVE_MONITORING',
      step: '01',
      label: 'LIVE MONITORING',
      subtitle: 'Live Telemetry & GIS Streams',
      icon: LayoutDashboard,
    },
    {
      id: 'PREDICTION',
      step: '02',
      label: 'PREDICTION',
      subtitle: 'Risk Drivers & What-If Sandbox',
      icon: Brain,
    },
    {
      id: 'EVACUATION_ACTION',
      step: '03',
      label: 'EVACUATION',
      subtitle: 'Pathfinder & Response Desk',
      icon: Navigation,
    },
    {
      id: 'VALIDATION_REPLAY',
      step: '04',
      label: 'VALIDATION',
      subtitle: 'Historical Case Studies',
      icon: FileCheck,
      badge: 'CASE STUDY',
    },
  ];

  const filteredVillages = villages.filter((v) => {
    const matchesSearch = v.village_name.toLowerCase().includes(search.toLowerCase()) || v.village_id.toLowerCase().includes(search.toLowerCase());
    const matchesLevel = filterLevel === 'ALL' || v.risk_level === filterLevel;
    return matchesSearch && matchesLevel;
  });

  const totalCount = villages.length;

  return (
    <aside className="w-[260px] min-w-[250px] max-w-[270px] bg-[#0E1115]/95 backdrop-blur-xl border-r border-white/10 flex flex-col h-full z-40 font-sans shadow-2xl flex-shrink-0 select-none">
      {/* 1. App Brand & Identity Header */}
      <div className="p-4 border-b border-white/10 bg-[#14181D]/60 flex items-center gap-3 flex-shrink-0">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#FF7A18] to-[#FFB703] p-0.5 flex items-center justify-center shadow-lg shadow-orange-500/20 flex-shrink-0">
          <div className="w-full h-full bg-[#0E1115] rounded-[10px] flex items-center justify-center">
            <Shield className="w-5 h-5 text-[#FFB703]" />
          </div>
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-1.5">
            <h1 className="text-sm font-black text-white tracking-wider uppercase font-mono truncate">
              APADA MITRA
            </h1>
            <span className="bg-white/10 text-white/90 text-[9px] font-mono px-1 py-0.2 rounded font-extrabold">
              v2.0
            </span>
          </div>
          <p className="text-[10px] text-gray-400 font-mono tracking-wide uppercase truncate mt-0.5">
            DISASTER INTELLIGENCE
          </p>
        </div>
      </div>

      {/* 2. Top Nav Mode Switcher (Phases vs Monitored Stations) */}
      <div className="px-3 pt-3 pb-1 border-b border-white/10 flex gap-1.5 bg-[#08090B]/50 flex-shrink-0">
        <button
          onClick={() => setSidebarTab('NAV')}
          className={`flex-1 py-1.5 text-[11px] font-mono font-bold rounded-lg transition flex items-center justify-center gap-1.5 uppercase tracking-wider cursor-pointer ${
            sidebarTab === 'NAV'
              ? 'bg-gradient-to-r from-[#FF7A18] to-[#FFB703] text-black font-extrabold shadow-md shadow-orange-500/20'
              : 'text-gray-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>PHASES</span>
        </button>
        <button
          onClick={() => setSidebarTab('VILLAGES')}
          className={`flex-1 py-1.5 text-[11px] font-mono font-bold rounded-lg transition flex items-center justify-center gap-1.5 uppercase tracking-wider cursor-pointer ${
            sidebarTab === 'VILLAGES'
              ? 'bg-gradient-to-r from-[#FF7A18] to-[#FFB703] text-black font-extrabold shadow-md shadow-orange-500/20'
              : 'text-gray-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <span>NODES ({totalCount})</span>
        </button>
      </div>

      {/* 3. Middle Scrollable Area */}
      {sidebarTab === 'NAV' ? (
        <div className="flex-1 p-3 space-y-2 overflow-y-auto">
          <div className="px-2 pt-1 pb-1">
            <span className="text-[10px] font-mono font-extrabold text-gray-500 uppercase tracking-widest">
              LIVE MONITORING
            </span>
          </div>

          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full text-left p-3 rounded-2xl transition-all duration-200 flex items-center justify-between group cursor-pointer relative ${
                  isActive
                    ? 'bg-gradient-to-r from-[#FF7A18] to-[#FFB703] text-black font-extrabold shadow-lg shadow-orange-500/25 scale-[1.02]'
                    : 'bg-[#14181D]/60 hover:bg-[#181D22] text-gray-300 hover:text-white border border-white/5 hover:border-white/10'
                }`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 transition ${
                      isActive
                        ? 'bg-black/20 text-black'
                        : 'bg-white/5 text-gray-400 group-hover:text-white group-hover:bg-white/10'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono text-xs font-bold tracking-wider truncate">
                        {item.label}
                      </span>
                    </div>
                    <span
                      className={`text-[10px] font-sans block truncate leading-tight ${
                        isActive ? 'text-black/80 font-medium' : 'text-gray-400'
                      }`}
                    >
                      {item.subtitle}
                    </span>
                  </div>
                </div>

                {item.badge && (
                  <span
                    className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-black flex-shrink-0 ${
                      isActive
                        ? 'bg-black/20 text-black'
                        : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}

          {/* Quick Active Station Preview Card in Nav Mode */}
          <div className="mt-4 p-3 bg-[#14181D] border border-white/10 rounded-2xl space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono font-bold text-gray-400 uppercase">
                SELECTED NODE
              </span>
              <span className="text-[9px] font-mono font-bold text-[#FFB703] bg-[#FF7A18]/10 border border-[#FF7A18]/30 px-1.5 py-0.2 rounded">
                ACTIVE
              </span>
            </div>
            {selectedVillageId ? (
              <div>
                <div className="text-xs font-bold text-white flex items-center justify-between">
                  <span>{villages.find((v) => v.village_id === selectedVillageId)?.village_name || selectedVillageId}</span>
                  <span className="text-[10px] font-mono text-gray-400 font-bold">
                    {villages.find((v) => v.village_id === selectedVillageId)?.elevation}m
                  </span>
                </div>
                <div className="flex items-center justify-between text-[10px] font-mono text-gray-400 mt-1">
                  <span>Risk: <strong className="text-[#F97316]">{Math.round(villages.find((v) => v.village_id === selectedVillageId)?.flash_flood_risk_score || 0)}%</strong></span>
                  <span>Pop: <strong className="text-white">{villages.find((v) => v.village_id === selectedVillageId)?.population.toLocaleString()}</strong></span>
                </div>
              </div>
            ) : (
              <span className="text-[11px] text-gray-500 font-sans">No station selected.</span>
            )}
          </div>
        </div>
      ) : (
        /* Village Selector Queue */
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Search Input */}
          <div className="p-3 border-b border-white/10 space-y-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search village name..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-[#14181D] border border-white/10 rounded-xl pl-8 pr-2.5 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-[#FF7A18] font-mono"
              />
            </div>

            {/* Filter Pills */}
            <div className="flex items-center gap-1 overflow-x-auto pb-0.5 text-[9px] font-mono">
              <Filter className="w-3 h-3 text-gray-500 flex-shrink-0" />
              {['ALL', 'CRITICAL', 'HIGH', 'MODERATE', 'LOW'].map((lvl) => (
                <button
                  key={lvl}
                  onClick={() => setFilterLevel(lvl as any)}
                  className={`px-1.5 py-0.5 rounded font-bold transition flex-shrink-0 cursor-pointer ${
                    filterLevel === lvl
                      ? 'bg-[#FF7A18]/20 text-[#FFB703] border border-[#FF7A18]/50'
                      : 'text-gray-400 hover:text-white border border-white/5'
                  }`}
                >
                  {lvl}
                </button>
              ))}
            </div>
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto divide-y divide-white/5">
            {filteredVillages.map((v) => {
              const isSelected = selectedVillageId === v.village_id;
              const riskColor = getRiskColorHex(v.risk_level);

              return (
                <div
                  key={v.village_id}
                  onClick={() => onSelectVillage(v.village_id)}
                  className={`p-2.5 cursor-pointer transition-all flex items-center justify-between group ${
                    isSelected
                      ? 'bg-[#FF7A18]/15 border-l-4 border-l-[#FF7A18] text-white shadow-inner'
                      : 'hover:bg-[#181D22] border-l-4 border-l-transparent text-gray-300'
                  }`}
                >
                  <div className="min-w-0 pr-2">
                    <div className="flex items-center gap-1.5">
                      <span className="font-bold text-xs text-white truncate max-w-[120px]">
                        {v.village_name}
                      </span>
                      <span className="text-[9px] text-gray-500 font-mono">
                        {v.elevation}m
                      </span>
                    </div>
                    <div className="text-[10px] text-gray-400 font-mono mt-0.5 flex items-center gap-2">
                      <span>POP <strong className="text-white">{v.population.toLocaleString()}</strong></span>
                      <span>EXP <strong className="text-red-400">{v.exposure.population_exposed.toLocaleString()}</strong></span>
                    </div>
                  </div>

                  <div className="text-right flex-shrink-0 font-mono">
                    <div className="text-xs font-black" style={{ color: riskColor }}>
                      {Math.round(v.flash_flood_risk_score)}%
                    </div>
                    <RiskBadge level={v.risk_level} className="text-[8px] px-1 py-0 mt-0.5" />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 4. Bottom System Status (Required Emerald Status) */}
      <div className="p-3.5 bg-[#08090B] border-t border-white/10 flex-shrink-0 font-mono">
        <div className="flex items-center justify-between text-[10px] text-gray-400 mb-1.5">
          <span className="font-bold uppercase tracking-wider">SYSTEM STATUS</span>
          <span className="text-gray-500 font-mono text-[9px]">SIH26192</span>
        </div>

        <div className="bg-[#14181D] border border-white/10 rounded-xl p-2.5 space-y-1.5 shadow-inner">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
              </span>
              <span className="text-xs font-black text-emerald-400 uppercase tracking-wider">
                ● LIVE
              </span>
            </div>
            <span className="text-[10px] font-bold text-white bg-white/5 border border-white/10 px-1.5 py-0.2 rounded">
              15/15 NODES
            </span>
          </div>

          <div className="flex items-center justify-between text-[10px] text-gray-400 pt-1 border-t border-white/5">
            <span className="flex items-center gap-1 text-emerald-400 font-bold">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              DATA HEALTHY
            </span>
            <span className="text-gray-500 text-[9px]">Copernicus DEM</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
