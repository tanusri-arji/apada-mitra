import React, { useState } from 'react';
import { VillageRiskDetail, RiskLevel, EvacuationPriority } from '../types';
import { RiskBadge } from './RiskBadge';
import {
  Search,
  Filter,
  Bell,
  Sliders,
  Layers,
  ChevronRight,
  Shield,
  AlertTriangle,
} from 'lucide-react';

interface Props {
  villages: VillageRiskDetail[];
  evacuationPriorities?: EvacuationPriority[];
  selectedVillageId: string | null;
  onSelectVillage: (id: string) => void;
  loading: boolean;
}

export const Sidebar: React.FC<Props> = ({
  villages,
  evacuationPriorities = [],
  selectedVillageId,
  onSelectVillage,
  loading,
}) => {
  const [search, setSearch] = useState('');
  const [filterLevel, setFilterLevel] = useState<RiskLevel | 'ALL'>('ALL');
  const [activeTab, setActiveTab] = useState<'VILLAGES' | 'RANKING' | 'FUTURE'>('VILLAGES');

  const filteredVillages = villages.filter((v) => {
    const matchesSearch = v.village_name.toLowerCase().includes(search.toLowerCase());
    const matchesLevel = filterLevel === 'ALL' || v.risk_level === filterLevel;
    return matchesSearch && matchesLevel;
  });

  return (
    <aside className="w-80 bg-command-card border-r border-command-border flex flex-col h-full z-10 font-sans">
      {/* Tab Switcher */}
      <div className="p-2 border-b border-command-border flex gap-1 bg-command-bg/50">
        <button
          onClick={() => setActiveTab('VILLAGES')}
          className={`flex-1 py-1.5 text-[11px] font-mono font-bold rounded transition flex items-center justify-center gap-1 ${
            activeTab === 'VILLAGES'
              ? 'bg-command-accent text-black shadow'
              : 'text-command-muted hover:text-white hover:bg-command-panel'
          }`}
        >
          <Layers className="w-3 h-3" />
          VILLAGES
        </button>
        <button
          onClick={() => setActiveTab('RANKING')}
          className={`flex-1 py-1.5 text-[11px] font-mono font-bold rounded transition flex items-center justify-center gap-1 ${
            activeTab === 'RANKING'
              ? 'bg-command-accent text-black shadow'
              : 'text-command-muted hover:text-white hover:bg-command-panel'
          }`}
        >
          <AlertTriangle className="w-3 h-3" />
          PRIORITY
        </button>
        <button
          onClick={() => setActiveTab('FUTURE')}
          className={`py-1.5 px-2 text-[11px] font-mono font-bold rounded transition flex items-center justify-center gap-1 ${
            activeTab === 'FUTURE'
              ? 'bg-command-accent text-black shadow'
              : 'text-command-muted hover:text-white hover:bg-command-panel'
          }`}
        >
          <Shield className="w-3 h-3" />
          ROADMAP
        </button>
      </div>

      {activeTab === 'VILLAGES' ? (
        <>
          {/* Search & Filter */}
          <div className="p-3 border-b border-command-border space-y-2">
            <div className="relative">
              <Search className="w-4 h-4 text-command-muted absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search village name..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-command-bg border border-command-border rounded-md pl-9 pr-3 py-1.5 text-xs text-white placeholder-command-muted focus:outline-none focus:border-command-accent font-mono"
              />
            </div>

            <div className="flex items-center gap-1 overflow-x-auto pb-1 text-[11px] font-mono">
              <Filter className="w-3 h-3 text-command-muted flex-shrink-0 ml-1" />
              {(['ALL', 'CRITICAL', 'HIGH', 'MODERATE', 'LOW'] as const).map((lvl) => (
                <button
                  key={lvl}
                  onClick={() => setFilterLevel(lvl)}
                  className={`px-2 py-0.5 rounded flex-shrink-0 transition ${
                    filterLevel === lvl
                      ? 'bg-command-accent/20 text-command-accent border border-command-accent/40 font-bold'
                      : 'text-command-muted hover:text-white hover:bg-command-panel'
                  }`}
                >
                  {lvl}
                </button>
              ))}
            </div>
          </div>

          {/* Villages List */}
          <div className="flex-1 overflow-y-auto divide-y divide-command-border/50">
            {loading ? (
              <div className="p-8 text-center text-xs text-command-muted font-mono animate-pulse">
                Loading watershed data...
              </div>
            ) : filteredVillages.length === 0 ? (
              <div className="p-8 text-center text-xs text-command-muted font-mono">
                No villages match filter criteria.
              </div>
            ) : (
              filteredVillages.map((v) => {
                const isSelected = selectedVillageId === v.village_id;

                return (
                  <div
                    key={v.village_id}
                    onClick={() => onSelectVillage(v.village_id)}
                    className={`p-3 cursor-pointer transition flex items-center justify-between group ${
                      isSelected
                        ? 'bg-command-accent/10 border-l-4 border-command-accent'
                        : 'hover:bg-command-panel/60'
                    }`}
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-xs text-white group-hover:text-command-accent transition">
                          {v.village_name}
                        </span>
                        <span className="text-[10px] text-command-muted font-mono">
                          {v.elevation}m
                        </span>
                      </div>
                      <div className="text-[11px] text-command-muted font-mono flex items-center gap-3">
                        <span>Pop: {v.population}</span>
                        <span>Exp: {v.exposure.population_exposed}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <div className="text-right font-mono">
                        <div className="text-sm font-bold text-white">
                          {Math.round(v.flash_flood_risk_score)}%
                        </div>
                        <RiskBadge level={v.risk_level} className="text-[9px] px-1.5 py-0" />
                      </div>
                      <ChevronRight
                        className={`w-4 h-4 text-command-muted group-hover:text-white transition ${
                          isSelected ? 'text-command-accent' : ''
                        }`}
                      />
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </>
      ) : activeTab === 'RANKING' ? (
        /* Evacuation Priority Ranking Tab */
        <div className="flex-1 overflow-y-auto divide-y divide-command-border/50 font-mono">
          <div className="p-3 bg-command-bg/90 border-b border-command-border text-[10px] text-command-muted space-y-1">
            <div className="font-bold text-white uppercase text-[11px] flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              Evacuation Priority Ranking
            </div>
            <p className="font-sans leading-tight">
              Calculated from weighted multi-hazard & exposure factors: Flood (35%), Landslide (25%), Exposed Pop (25%), Infrastructure (15%). Priority is not simply highest hazard score.
            </p>
          </div>

          {evacuationPriorities.map((p) => {
            const isSelected = selectedVillageId === p.village_id;

            return (
              <div
                key={p.village_id}
                onClick={() => onSelectVillage(p.village_id)}
                className={`p-3 cursor-pointer transition flex items-start justify-between group ${
                  isSelected
                    ? 'bg-command-accent/10 border-l-4 border-command-accent'
                    : 'hover:bg-command-panel/60'
                }`}
              >
                <div className="space-y-1.5 flex-1 pr-2">
                  <div className="flex items-center gap-2">
                    <span className="bg-command-accent text-black font-extrabold text-[10px] px-1.5 py-0.5 rounded">
                      #{p.rank}
                    </span>
                    <span className="font-bold text-xs text-white group-hover:text-command-accent transition">
                      {p.village_name}
                    </span>
                  </div>
                  <p className="text-[10px] text-amber-300 font-sans leading-tight">
                    {p.primary_urgency_reason}
                  </p>
                  <p className="text-[9px] text-command-muted font-mono bg-command-bg/60 p-1 rounded border border-command-border/40">
                    {p.factor_breakdown_summary}
                  </p>
                </div>

                <div className="text-right flex-shrink-0">
                  <div className="text-sm font-extrabold text-amber-400">
                    {p.evacuation_priority_score} pts
                  </div>
                  <RiskBadge level={p.priority_level} className="text-[9px] px-1.5 py-0" />
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Roadmap Panel */
        <div className="p-4 overflow-y-auto space-y-4 font-mono text-xs">
          <div className="bg-emerald-500/10 border border-emerald-500/30 p-3 rounded text-emerald-300 text-[11px] leading-relaxed">
            <strong>Day 2 Active:</strong> Evacuation Priority Engine, Landslide Susceptibility, Mountain Road Graph, Hazard-Aware Dijkstra Routing & Shelter Recommendation active.
          </div>

          <div className="space-y-2">
            <h3 className="text-command-muted text-[10px] uppercase font-bold tracking-wider">
              Planned Day 3+ Extensions
            </h3>

            {[
              { title: 'Multilingual Warning Broadcast', desc: 'Garhwali / Hindi / English citizen alerts', icon: Bell },
              { title: 'What-If Parameter Simulator', desc: 'Custom cloudburst & dam release sliders', icon: Sliders },
            ].map((f) => {
              const Icon = f.icon;
              return (
                <div
                  key={f.title}
                  className="p-3 bg-command-bg/40 border border-command-border/60 rounded opacity-60 flex items-start gap-3 relative overflow-hidden group cursor-not-allowed"
                >
                  <Icon className="w-4 h-4 text-command-muted mt-0.5" />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white text-xs">{f.title}</span>
                      <span className="bg-gray-800 text-gray-400 text-[9px] px-1.5 py-0.5 rounded border border-gray-700 font-sans">
                        Coming in Day 3
                      </span>
                    </div>
                    <p className="text-[11px] text-command-muted font-sans mt-0.5">{f.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Footer Info */}
      <div className="p-3 bg-command-bg border-t border-command-border text-[10px] text-command-muted font-mono flex items-center justify-between">
        <span>APADA MITRA v2.0</span>
        <span className="text-command-accent">DAY 2 VERTICAL SLICE</span>
      </div>
    </aside>
  );
};
