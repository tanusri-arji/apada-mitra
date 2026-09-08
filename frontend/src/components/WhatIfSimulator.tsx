import React, { useState, useEffect, useCallback } from 'react';
import {
  WhatIfSimulationInput,
  WhatIfSimulationResponse,
} from '../types';
import { runWhatIfSimulation } from '../api/client';
import {
  Sliders,
  Play,
  RotateCcw,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Globe,
  Copy,
  Check,
  CloudRain,
  TrendingUp,
  Droplets,
  Waves,
} from 'lucide-react';

interface Props {
  onSimulationUpdate: (sim: WhatIfSimulationResponse | null) => void;
  activeSimulation: WhatIfSimulationResponse | null;
  selectedVillageId?: string | null;
}

export const WhatIfSimulator: React.FC<Props> = ({
  onSimulationUpdate,
  activeSimulation,
  selectedVillageId,
}) => {
  const [activePreset, setActivePreset] = useState<'NORMAL' | 'HEAVY' | 'EXTREME' | 'CUSTOM'>('HEAVY');
  const [rainfall, setRainfall] = useState<number>(55.0);
  const [forecast, setForecast] = useState<number>(120.0);
  const [soilSat, setSoilSat] = useState<number>(75.0);
  const [riverLevel, setRiverLevel] = useState<number>(5.8);

  const [loading, setLoading] = useState(false);
  const [lang, setLang] = useState<'english' | 'hindi' | 'garhwali' | 'kumaoni' | 'nepali'>('english');
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeSimulation = useCallback(
    async (
      rf: number,
      fc: number,
      ss: number,
      rl: number,
      vId?: string | null
    ) => {
      try {
        setLoading(true);
        setError(null);
        const input: WhatIfSimulationInput = {
          current_rainfall_mm_hr: Number(rf),
          forecast_rainfall_24h_mm: Number(fc),
          soil_saturation_pct: Number(ss),
          river_level_m: Number(rl),
          selected_village_id: vId || selectedVillageId || 'VIL-001',
        };

        const result = await runWhatIfSimulation(input);
        onSimulationUpdate(result);
      } catch (err: any) {
        console.error('Simulation execution failed:', err);
        setError(err.message || 'Simulation execution failed. Please check network connectivity or backend status.');
      } finally {
        setLoading(false);
      }
    },
    [selectedVillageId, onSimulationUpdate]
  );

  useEffect(() => {
    if (!activeSimulation) {
      executeSimulation(rainfall, forecast, soilSat, riverLevel, selectedVillageId);
    }
  }, []);

  const applyPreset = (preset: 'NORMAL' | 'HEAVY' | 'EXTREME') => {
    setActivePreset(preset);
    let newRf = 55.0;
    let newFc = 120.0;
    let newSs = 75.0;
    let newRl = 5.8;

    if (preset === 'NORMAL') {
      newRf = 10.0;
      newFc = 25.0;
      newSs = 35.0;
      newRl = 2.1;
    } else if (preset === 'HEAVY') {
      newRf = 55.0;
      newFc = 120.0;
      newSs = 75.0;
      newRl = 5.8;
    } else if (preset === 'EXTREME') {
      newRf = 135.0;
      newFc = 320.0;
      newSs = 95.0;
      newRl = 10.4;
    }

    setRainfall(newRf);
    setForecast(newFc);
    setSoilSat(newSs);
    setRiverLevel(newRl);

    executeSimulation(newRf, newFc, newSs, newRl, selectedVillageId);
  };

  const handleRunSimulation = () => {
    executeSimulation(rainfall, forecast, soilSat, riverLevel, selectedVillageId);
  };

  const handleReset = () => {
    onSimulationUpdate(null);
    applyPreset('HEAVY');
    setError(null);
  };

  const comp = activeSimulation?.comparison_summary;
  const alert = activeSimulation?.operator_alert;

  const handleCopyAlert = () => {
    if (alert?.translations[lang]) {
      navigator.clipboard.writeText(alert.translations[lang]);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bento-card p-4 lg:p-5 flex flex-col space-y-4 font-sans select-text">
      {/* 1. Header */}
      <div className="flex items-center justify-between border-b border-white/10 pb-3 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#FF7A18] to-[#FFB703] p-0.5 flex items-center justify-center shadow-lg shadow-orange-500/20 flex-shrink-0">
            <div className="w-full h-full bg-[#14181D] rounded-[10px] flex items-center justify-center">
              <Sliders className="w-5 h-5 text-[#FFB703]" />
            </div>
          </div>
          <div>
            <h2 className="text-sm font-black uppercase tracking-wider text-white font-mono flex items-center gap-2">
              SCENARIO SIMULATOR & WHAT-IF SANDBOX
            </h2>
            <p className="text-xs text-gray-400 font-sans mt-0.5">
              Simulate hydro-meteorological loading across all 15 watershed nodes.
            </p>
          </div>
        </div>

        <span
          className={`text-[10px] font-mono font-black px-2.5 py-1 rounded-xl border uppercase tracking-wider ${
            activeSimulation
              ? 'bg-gradient-to-r from-[#FF7A18]/20 to-[#FFB703]/20 text-[#FFB703] border-[#FF7A18]/50 animate-pulse'
              : 'bg-white/5 text-gray-400 border-white/10'
          }`}
        >
          {activeSimulation ? 'SIMULATION ACTIVE' : 'STANDBY'}
        </span>
      </div>

      {/* 2. Scenario Presets Selection */}
      <div className="space-y-2">
        <span className="text-[10px] text-gray-400 uppercase font-mono font-extrabold tracking-wider block">
          SCENARIO PRESETS
        </span>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 font-mono">
          {[
            { id: 'NORMAL', label: 'NORMAL', desc: 'Baseline weather', color: 'emerald' },
            { id: 'HEAVY', label: 'HEAVY RAIN', desc: 'Monsoon downpour', color: 'amber' },
            { id: 'EXTREME', label: 'CLOUDBURST', desc: 'Extreme flash surge', color: 'red' },
            { id: 'CUSTOM', label: 'CUSTOM', desc: 'Custom parameters', color: 'neutral' },
          ].map((p) => {
            const isSelected = activePreset === p.id;
            return (
              <button
                key={p.id}
                onClick={() => p.id !== 'CUSTOM' && applyPreset(p.id as any)}
                disabled={p.id === 'CUSTOM'}
                className={`p-3 rounded-2xl border text-left transition flex flex-col justify-between cursor-pointer ${
                  isSelected
                    ? p.color === 'emerald'
                      ? 'bg-emerald-500/20 border-emerald-500 text-white shadow-lg shadow-emerald-500/10'
                      : p.color === 'amber'
                      ? 'bg-amber-500/20 border-amber-500 text-white shadow-lg shadow-amber-500/10'
                      : p.color === 'red'
                      ? 'bg-red-500/20 border-red-500 text-white shadow-lg shadow-red-500/10'
                      : 'bg-white/10 border-white/30 text-white'
                    : 'bg-[#14181D] border-white/10 hover:border-white/20 text-gray-400'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-xs font-black uppercase ${
                    isSelected
                      ? p.color === 'emerald' ? 'text-emerald-400' : p.color === 'amber' ? 'text-amber-400' : p.color === 'red' ? 'text-red-400' : 'text-white'
                      : 'text-white'
                  }`}>
                    {p.label}
                  </span>
                  {isSelected && (
                    <span className="w-2 h-2 rounded-full bg-[#FF7A18] animate-ping" />
                  )}
                </div>
                <span className="text-[10px] text-gray-400 font-sans mt-1">
                  {p.desc}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Environmental Sliders Panel */}
      <div className="bg-[#14181D] border border-white/10 p-4 rounded-2xl space-y-4 shadow-inner font-mono">
        <div className="flex items-center justify-between border-b border-white/10 pb-2">
          <span className="text-[10px] text-gray-400 uppercase font-extrabold tracking-wider flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-[#FF7A18]" />
            ENVIRONMENTAL STRESS PARAMETERS
          </span>
          <span className="text-[10px] text-[#FFB703] font-bold">PHYSICS INPUTS</span>
        </div>

        {/* Rainfall Intensity Slider */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="text-white font-bold flex items-center gap-1.5">
              <CloudRain className="w-3.5 h-3.5 text-[#FF7A18]" />
              Rainfall Intensity
            </span>
            <span className="text-[#FF7A18] font-black">{rainfall} mm/h</span>
          </div>
          <input
            type="range"
            min="0"
            max="200"
            step="1"
            value={rainfall}
            onChange={(e) => {
              setRainfall(parseFloat(e.target.value));
              setActivePreset('CUSTOM');
            }}
            className="w-full accent-[#FF7A18] bg-[#0E1115] rounded-lg cursor-pointer h-2"
          />
          <div className="flex justify-between text-[9px] text-gray-500">
            <span>0 mm/h</span>
            <span>100 mm/h</span>
            <span>200 mm/h</span>
          </div>
        </div>

        {/* 24h Accumulation Forecast Slider */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="text-white font-bold flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5 text-[#FFB703]" />
              24h Accumulation Forecast
            </span>
            <span className="text-[#FFB703] font-black">{forecast} mm</span>
          </div>
          <input
            type="range"
            min="0"
            max="500"
            step="5"
            value={forecast}
            onChange={(e) => {
              setForecast(parseFloat(e.target.value));
              setActivePreset('CUSTOM');
            }}
            className="w-full accent-[#FFB703] bg-[#0E1115] rounded-lg cursor-pointer h-2"
          />
          <div className="flex justify-between text-[9px] text-gray-500">
            <span>0 mm</span>
            <span>250 mm</span>
            <span>500 mm</span>
          </div>
        </div>

        {/* Soil Saturation Slider */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="text-white font-bold flex items-center gap-1.5">
              <Droplets className="w-3.5 h-3.5 text-amber-400" />
              Soil Saturation Index
            </span>
            <span className="text-amber-400 font-black">{soilSat}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            step="1"
            value={soilSat}
            onChange={(e) => {
              setSoilSat(parseFloat(e.target.value));
              setActivePreset('CUSTOM');
            }}
            className="w-full accent-amber-400 bg-[#0E1115] rounded-lg cursor-pointer h-2"
          />
          <div className="flex justify-between text-[9px] text-gray-500">
            <span>DRY (0%)</span>
            <span>SATURATED (100%)</span>
          </div>
        </div>

        {/* River Water Level Slider */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="text-white font-bold flex items-center gap-1.5">
              <Waves className="w-3.5 h-3.5 text-red-400" />
              River Gauge Water Level
            </span>
            <span className="text-red-400 font-black">{riverLevel} m</span>
          </div>
          <input
            type="range"
            min="0"
            max="15"
            step="0.1"
            value={riverLevel}
            onChange={(e) => {
              setRiverLevel(parseFloat(e.target.value));
              setActivePreset('CUSTOM');
            }}
            className="w-full accent-red-400 bg-[#0E1115] rounded-lg cursor-pointer h-2"
          />
          <div className="flex justify-between text-[9px] text-gray-500">
            <span>NORMAL (2.0m)</span>
            <span>DANGER (15.0m)</span>
          </div>
        </div>
      </div>

      {/* 4. Run Action Button */}
      <div className="space-y-1.5">
        <button
          disabled={loading}
          onClick={handleRunSimulation}
          className="w-full bg-gradient-to-r from-[#FF7A18] to-[#FFB703] hover:from-[#FF7A18]/90 hover:to-[#FFB703]/90 text-black font-black py-3 rounded-xl transition flex items-center justify-center gap-2 shadow-xl shadow-orange-500/20 uppercase tracking-wider text-xs font-mono cursor-pointer"
        >
          <Play className="w-4 h-4 fill-black" />
          {loading ? 'SIMULATING CASCADE...' : 'RUN WHAT-IF SIMULATION'}
        </button>

        {error && (
          <div className="p-2.5 bg-red-500/15 border border-red-500/30 rounded-xl text-red-400 text-xs font-mono">
            {error}
          </div>
        )}
      </div>

      {/* 5. Before vs After Delta Bento Cards */}
      {comp && (
        <div className="space-y-3 pt-3 border-t border-white/10 font-mono">
          <div className="flex items-center justify-between">
            <span className="text-xs font-black text-white uppercase tracking-wider flex items-center gap-1.5">
              BEFORE → AFTER IMPACT COMPARISON
            </span>
            <span className="bg-[#FF7A18]/15 text-[#FFB703] border border-[#FF7A18]/30 text-[9px] font-black px-2 py-0.5 rounded-lg uppercase">
              DELTA LIVE
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {[
              { data: comp.avg_flood_risk, label: 'Avg Flood Risk' },
              { data: comp.avg_landslide_risk, label: 'Avg Landslide Risk' },
              { data: comp.critical_villages_count, label: 'High/Critical Nodes' },
              { data: comp.total_population_exposed, label: 'Exposed Population' },
              { data: comp.blocked_roads_count, label: 'Blocked Roads' },
              { data: comp.shelter_shortfall_count, label: 'Shelter Shortfall' },
            ].map(({ data: m, label }) => {
              if (!m) return null;
              const isIncrease = m.delta > 0;
              const isDecrease = m.delta < 0;

              return (
                <div
                  key={label}
                  className="p-3 bg-[#14181D] border border-white/10 rounded-2xl space-y-1.5 shadow-sm"
                >
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-bold text-white uppercase tracking-wider">{label}</span>
                    <span
                      className={`text-xs font-black flex items-center gap-0.5 px-1.5 py-0.2 rounded-lg ${
                        isIncrease
                          ? 'bg-red-500/20 text-red-400 border border-red-500/40'
                          : isDecrease
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                          : 'bg-white/5 text-gray-400 border border-white/10'
                      }`}
                    >
                      {isIncrease ? (
                        <ArrowUpRight className="w-3.5 h-3.5 text-red-400" />
                      ) : isDecrease ? (
                        <ArrowDownRight className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Minus className="w-3.5 h-3.5 text-gray-400" />
                      )}
                      {m.delta > 0 ? `+${m.delta}` : m.delta} {m.unit}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-[#0E1115] p-2 rounded-xl border border-white/5">
                      <span className="text-[9px] text-gray-400 uppercase block font-bold">Baseline</span>
                      <span className="text-xs font-black text-gray-300">{m.current_val} {m.unit}</span>
                    </div>

                    <div className="bg-[#0E1115] p-2 rounded-xl border border-white/5">
                      <span className="text-[9px] text-gray-400 uppercase block font-bold">Simulated</span>
                      <span className="text-xs font-black text-white">{m.simulated_val} {m.unit}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 6. Multilingual Alert Box */}
      {alert && (
        <div className="space-y-3 pt-3 border-t border-white/10 font-mono">
          <div className="flex items-center justify-between">
            <span className="text-xs font-black text-white uppercase tracking-wider flex items-center gap-1.5">
              <Globe className="w-4 h-4 text-[#FF7A18]" />
              SIMULATION OPERATOR ALERT
            </span>

            {/* Language Switcher */}
            <div className="flex bg-[#0E1115] p-0.5 rounded-xl border border-white/10 text-[10px]">
              {['english', 'hindi', 'garhwali', 'kumaoni', 'nepali'].map((l) => (
                <button
                  key={l}
                  onClick={() => setLang(l as any)}
                  className={`px-2 py-0.5 rounded-lg transition font-bold ${
                    lang === l
                      ? 'bg-[#FF7A18] text-black font-extrabold'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {l.substring(0, 2).toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div className="p-3.5 bg-red-500/15 border border-red-500/30 rounded-2xl space-y-2.5 text-xs shadow-xl">
            <div className="flex items-center justify-between border-b border-red-500/20 pb-1.5">
              <span className="font-black text-red-400 uppercase text-xs">
                ⚠️ {alert.village_name} ({alert.risk_level})
              </span>
              <span className="text-white font-black text-sm">{Math.round(alert.risk_score)}%</span>
            </div>

            <div className="bg-[#0E1115] p-2.5 rounded-xl border border-white/10 text-[11px] leading-relaxed text-white font-sans whitespace-pre-wrap">
              {alert.translations[lang]}
            </div>

            <div className="flex items-center justify-between pt-1">
              <button
                onClick={handleCopyAlert}
                className="flex items-center gap-1.5 px-3 py-1 bg-[#14181D] hover:bg-[#1C2228] border border-white/10 text-[#FFB703] rounded-xl text-[10px] font-bold transition cursor-pointer"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-[#FF7A18]" />}
                {copied ? 'COPIED!' : 'COPY ALERT'}
              </button>

              <span className="text-[9px] text-amber-400 font-bold uppercase tracking-wider">
                SIMULATION ALERT — OFFLINE DEMO
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Reset */}
      {activeSimulation && (
        <button
          onClick={handleReset}
          className="w-full py-2 px-4 bg-[#14181D] border border-white/10 text-gray-400 hover:text-white rounded-xl hover:bg-[#1C2228] transition flex items-center justify-center gap-2 text-xs font-bold font-mono uppercase tracking-wider cursor-pointer"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          RESET SIMULATION
        </button>
      )}
    </div>
  );
};

export default WhatIfSimulator;
