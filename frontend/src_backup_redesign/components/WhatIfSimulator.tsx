import React, { useState } from 'react';
import {
  WhatIfSimulationInput,
  WhatIfSimulationResponse,
} from '../types';
import { runWhatIfSimulation } from '../api/client';
import {
  Sliders,
  Play,
  RotateCcw,
  AlertTriangle,
  Flame,
  Shield,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Globe,
  Layers,
  Zap,
  Navigation,
  Tent,
} from 'lucide-react';

interface Props {
  onSimulationUpdate: (sim: WhatIfSimulationResponse | null) => void;
  activeSimulation: WhatIfSimulationResponse | null;
}

export const WhatIfSimulator: React.FC<Props> = ({
  onSimulationUpdate,
  activeSimulation,
}) => {
  const [rainfall, setRainfall] = useState<number>(55.0);
  const [forecast, setForecast] = useState<number>(120.0);
  const [soilSat, setSoilSat] = useState<number>(75.0);
  const [riverLevel, setRiverLevel] = useState<number>(5.8);

  const [loading, setLoading] = useState(false);
  const [lang, setLang] = useState<'english' | 'hindi' | 'telugu'>('english');
  const [error, setError] = useState<string | null>(null);

  const applyPreset = (preset: 'NORMAL' | 'HEAVY' | 'EXTREME') => {
    if (preset === 'NORMAL') {
      setRainfall(10.0);
      setForecast(25.0);
      setSoilSat(35.0);
      setRiverLevel(2.1);
    } else if (preset === 'HEAVY') {
      setRainfall(55.0);
      setForecast(120.0);
      setSoilSat(75.0);
      setRiverLevel(5.8);
    } else if (preset === 'EXTREME') {
      setRainfall(135.0);
      setForecast(320.0);
      setSoilSat(95.0);
      setRiverLevel(10.4);
    }
  };

  const handleRunSimulation = async () => {
    try {
      setLoading(true);
      setError(null);
      const input: WhatIfSimulationInput = {
        current_rainfall_mm_hr: Number(rainfall),
        forecast_rainfall_24h_mm: Number(forecast),
        soil_saturation_pct: Number(soilSat),
        river_level_m: Number(riverLevel),
        selected_village_id: 'VIL-011',
      };

      const result = await runWhatIfSimulation(input);
      onSimulationUpdate(result);
    } catch (err: any) {
      console.error('Simulation execution failed:', err);
      setError(err.message || 'Simulation execution failed');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    onSimulationUpdate(null);
    applyPreset('HEAVY');
    setError(null);
  };

  const comp = activeSimulation?.comparison_summary;
  const alert = activeSimulation?.operator_alert;

  return (
    <div className="w-96 bg-command-card border-l border-command-border flex flex-col h-full z-10 font-sans shadow-2xl overflow-y-auto">
      {/* Header */}
      <div className="p-4 border-b border-command-border bg-command-bg/80 sticky top-0 backdrop-blur-md z-10 font-mono">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-command-accent">
            <Sliders className="w-5 h-5 text-command-accent" />
            <h2 className="text-sm font-bold uppercase tracking-wider text-white">
              What-If Simulator
            </h2>
          </div>
          <span className="bg-command-accent/20 text-command-accent border border-command-accent/40 text-[9px] font-bold px-2 py-0.5 rounded uppercase">
            DEMO SIMULATOR
          </span>
        </div>
        <div className="text-[10px] text-amber-300 font-mono mt-1 bg-amber-500/10 p-1.5 rounded border border-amber-500/30 flex items-center gap-1">
          <AlertTriangle className="w-3 h-3 text-amber-400 flex-shrink-0" />
          <span>WHAT-IF SIMULATION — SYNTHETIC DEMO INPUT</span>
        </div>
      </div>

      <div className="p-5 space-y-6 font-mono text-xs">
        {/* Preset Selector */}
        <div className="space-y-2">
          <label className="text-[10px] text-command-muted uppercase font-bold tracking-wider block">
            Simulation Presets
          </label>
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => applyPreset('NORMAL')}
              className="py-1.5 px-2 bg-command-bg border border-command-border hover:border-emerald-500 rounded text-[11px] font-bold text-emerald-400 hover:bg-command-panel transition uppercase"
            >
              NORMAL
            </button>
            <button
              onClick={() => applyPreset('HEAVY')}
              className="py-1.5 px-2 bg-command-bg border border-command-border hover:border-amber-500 rounded text-[11px] font-bold text-amber-400 hover:bg-command-panel transition uppercase"
            >
              HEAVY RAIN
            </button>
            <button
              onClick={() => applyPreset('EXTREME')}
              className="py-1.5 px-2 bg-command-bg border border-command-border hover:border-red-500 rounded text-[11px] font-bold text-red-400 hover:bg-command-panel transition uppercase"
            >
              CLOUDBURST
            </button>
          </div>
        </div>

        {/* Input Parameters Controls */}
        <div className="bg-command-panel/70 border border-command-border p-4 rounded-xl space-y-4">
          {/* Current Rainfall Slider */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-white">Rainfall Intensity</span>
              <span className="text-command-accent font-bold">{rainfall} mm/hr</span>
            </div>
            <input
              type="range"
              min="0"
              max="200"
              step="1"
              value={rainfall}
              onChange={(e) => setRainfall(parseFloat(e.target.value))}
              className="w-full accent-command-accent bg-command-bg rounded cursor-pointer"
            />
            <div className="flex justify-between text-[9px] text-command-muted">
              <span>0 mm/h (Dry)</span>
              <span>100 mm/h (Cloudburst)</span>
              <span>200 mm/h (Extreme)</span>
            </div>
          </div>

          {/* 24h Forecast Slider */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-white">24h Forecast Rainfall</span>
              <span className="text-cyan-400 font-bold">{forecast} mm</span>
            </div>
            <input
              type="range"
              min="0"
              max="500"
              step="5"
              value={forecast}
              onChange={(e) => setForecast(parseFloat(e.target.value))}
              className="w-full accent-cyan-400 bg-command-bg rounded cursor-pointer"
            />
          </div>

          {/* Soil Saturation Slider */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-white">Soil Saturation</span>
              <span className="text-amber-400 font-bold">{soilSat}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="1"
              value={soilSat}
              onChange={(e) => setSoilSat(parseFloat(e.target.value))}
              className="w-full accent-amber-400 bg-command-bg rounded cursor-pointer"
            />
          </div>

          {/* River Stage Level Slider */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-white">River Stage Level</span>
              <span className="text-red-400 font-bold">{riverLevel} meters</span>
            </div>
            <input
              type="range"
              min="0"
              max="15"
              step="0.1"
              value={riverLevel}
              onChange={(e) => setRiverLevel(parseFloat(e.target.value))}
              className="w-full accent-red-400 bg-command-bg rounded cursor-pointer"
            />
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex gap-2">
          <button
            disabled={loading}
            onClick={handleRunSimulation}
            className="flex-1 bg-command-accent text-black font-extrabold py-2.5 rounded-lg hover:bg-command-accentHover transition flex items-center justify-center gap-2 shadow-lg uppercase tracking-wider"
          >
            <Play className="w-4 h-4 fill-black" />
            {loading ? 'Simulating Cascade...' : 'Run Simulation'}
          </button>

          {activeSimulation && (
            <button
              onClick={handleReset}
              className="px-3 bg-command-bg border border-command-border text-command-muted hover:text-white rounded-lg hover:bg-command-panel transition flex items-center justify-center"
              title="Reset to current scenario"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          )}
        </div>

        {error && (
          <div className="p-3 bg-red-950/80 border border-red-500 text-red-200 rounded text-xs">
            {error}
          </div>
        )}

        {/* Cascade Visualizer Chain */}
        <div className="space-y-2 pt-2 border-t border-command-border/50">
          <span className="text-[10px] text-command-muted uppercase font-bold tracking-wider block">
            Disaster Cascade Chain
          </span>
          <div className="grid grid-cols-3 gap-1.5 text-[9px] text-center font-mono">
            {[
              { name: 'RAINFALL', icon: Flame },
              { name: 'TERRAIN', icon: Layers },
              { name: 'FLOOD', icon: Activity },
              { name: 'LANDSLIDE', icon: Shield },
              { name: 'EXPOSURE', icon: AlertTriangle },
              { name: 'PRIORITY', icon: Zap },
              { name: 'ROADS', icon: Sliders },
              { name: 'ROUTE', icon: Navigation },
              { name: 'SHELTER', icon: Tent },
            ].map((node) => {
              const Icon = node.icon;
              return (
                <div
                  key={node.name}
                  className={`p-1.5 rounded border flex flex-col items-center gap-1 transition ${
                    activeSimulation
                      ? 'bg-command-accent/10 border-command-accent/50 text-white shadow-sm animate-pulse-glow'
                      : 'bg-command-bg/40 border-command-border/50 text-command-muted'
                  }`}
                >
                  <Icon className="w-3 h-3 text-command-accent" />
                  <span>{node.name}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Before / After Comparison Grid */}
        {comp && (
          <div className="space-y-3 pt-2 border-t border-command-border">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                Before / After Comparison
              </span>
              <span className="text-[10px] text-command-accent font-bold">
                DELTA ANALYSIS
              </span>
            </div>

            <div className="space-y-2">
              {[
                comp.avg_flood_risk,
                comp.avg_landslide_risk,
                comp.critical_villages_count,
                comp.total_population_exposed,
                comp.blocked_roads_count,
                comp.shelter_shortfall_count,
              ].map((m) => {
                const isIncrease = m.delta > 0;
                const isDecrease = m.delta < 0;

                return (
                  <div
                    key={m.name}
                    className="p-2.5 bg-command-panel/80 border border-command-border/80 rounded-lg flex items-center justify-between"
                  >
                    <div className="space-y-0.5">
                      <span className="text-[11px] font-bold text-white block">{m.name}</span>
                      <span className="text-[10px] text-command-muted">
                        Current: {m.current_val} {m.unit} → Sim: {m.simulated_val} {m.unit}
                      </span>
                    </div>

                    <div className="text-right flex items-center gap-1">
                      <span
                        className={`text-sm font-extrabold flex items-center ${
                          isIncrease
                            ? 'text-red-400'
                            : isDecrease
                            ? 'text-emerald-400'
                            : 'text-command-muted'
                        }`}
                      >
                        {isIncrease ? (
                          <ArrowUpRight className="w-4 h-4 text-red-400" />
                        ) : isDecrease ? (
                          <ArrowDownRight className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <Minus className="w-3.5 h-3.5 text-command-muted" />
                        )}
                        {m.delta > 0 ? `+${m.delta}` : m.delta}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Capacity Shortfall Warning */}
        {activeSimulation?.shelter_shortfall_warning && (
          <div className="p-3 bg-red-950/90 border border-red-500 rounded-lg text-red-200 text-xs space-y-1 font-mono shadow-xl">
            <div className="font-bold uppercase text-red-400 flex items-center gap-1">
              <AlertTriangle className="w-4 h-4 text-red-400 animate-pulse" />
              Capacity Shortfall Warning
            </div>
            <p className="text-[11px] leading-tight font-sans">
              {activeSimulation.shelter_shortfall_warning}
            </p>
          </div>
        )}

        {/* Multilingual Emergency Operator Decision Alert */}
        {alert && (
          <div className="space-y-3 pt-2 border-t border-command-border">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <Globe className="w-4 h-4 text-command-accent" />
                Operator Emergency Alert
              </span>

              {/* Language Selector Tabs */}
              <div className="flex bg-command-bg p-0.5 rounded border border-command-border text-[10px]">
                <button
                  onClick={() => setLang('english')}
                  className={`px-2 py-0.5 rounded transition ${
                    lang === 'english'
                      ? 'bg-command-accent text-black font-bold'
                      : 'text-command-muted hover:text-white'
                  }`}
                >
                  EN
                </button>
                <button
                  onClick={() => setLang('hindi')}
                  className={`px-2 py-0.5 rounded transition ${
                    lang === 'hindi'
                      ? 'bg-command-accent text-black font-bold'
                      : 'text-command-muted hover:text-white'
                  }`}
                >
                  हिन्दी
                </button>
                <button
                  onClick={() => setLang('telugu')}
                  className={`px-2 py-0.5 rounded transition ${
                    lang === 'telugu'
                      ? 'bg-command-accent text-black font-bold'
                      : 'text-command-muted hover:text-white'
                  }`}
                >
                  తెలుగు
                </button>
              </div>
            </div>

            <div className="p-3.5 bg-red-950/40 border border-red-500/50 rounded-xl space-y-2.5 font-mono text-xs">
              <div className="flex items-center justify-between border-b border-red-500/30 pb-2">
                <span className="font-bold text-red-400 uppercase text-xs">
                  ⚠️ {alert.village_name} ({alert.risk_level})
                </span>
                <span className="text-red-300 font-extrabold">{round(alert.risk_score)}%</span>
              </div>

              {/* Translated Alert Box */}
              <div className="bg-command-bg/80 p-2.5 rounded border border-command-border text-[11px] leading-relaxed text-white font-sans">
                {alert.translations[lang]}
              </div>

              <div className="space-y-1 text-[11px] text-command-muted font-sans">
                <div><strong>Recommended Action:</strong> {alert.recommended_action}</div>
                <div><strong>Target Shelter:</strong> <span className="text-emerald-400 font-bold">{alert.shelter_name}</span></div>
                <div><strong>Avoid Roads:</strong> <span className="text-amber-400">{alert.roads_to_avoid.join(', ')}</span></div>
              </div>

              <div className="text-[9px] text-command-muted font-mono text-center pt-1 border-t border-command-border/30">
                OPERATOR DECISION-SUPPORT ALERT — DEMO TRANSLATION
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

function round(val: number): number {
  return Math.round(val);
}
