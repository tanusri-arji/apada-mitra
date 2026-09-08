import React from 'react';
import { ScenarioType } from '../types';
import { CloudRain, Zap, Sun, X, Check } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  currentScenario: ScenarioType;
  onSelectScenario: (scenario: ScenarioType) => void;
  loading: boolean;
}

export const ScenarioControl: React.FC<Props> = ({
  isOpen,
  onClose,
  currentScenario,
  onSelectScenario,
  loading,
}) => {
  if (!isOpen) return null;

  const scenarios: { type: ScenarioType; title: string; desc: string; icon: any; color: string }[] = [
    {
      type: 'NORMAL',
      title: 'NORMAL WEATHER',
      desc: 'Baseline clear to seasonal drizzle (2-12 mm/h). Minimal flash flood threat.',
      icon: Sun,
      color: 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10',
    },
    {
      type: 'HEAVY_RAIN',
      title: 'HEAVY MONSOON DOWNPOUR',
      desc: 'Sustained monsoon rain (35-65 mm/h). Significant mountain runoff and rising rivers.',
      icon: CloudRain,
      color: 'text-amber-400 border-amber-500/40 bg-amber-500/10',
    },
    {
      type: 'EXTREME_RAIN',
      title: 'EXTREME CLOUDBURST EVENT',
      desc: 'Upper watershed cloudburst (75-110 mm/h). Severe flash flood emergency and debris flows.',
      icon: Zap,
      color: 'text-red-400 border-red-500/40 bg-red-500/10',
    },
  ];

  return (
    <div className="fixed inset-0 bg-black/85 backdrop-blur-md flex items-center justify-center z-50 p-4 font-sans">
      <div className="bg-[#14181D] border border-white/10 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden font-mono">
        <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-[#0E1115]">
          <div className="flex items-center gap-2.5">
            <CloudRain className="w-5 h-5 text-[#FF7A18]" />
            <h2 className="text-sm font-black text-white uppercase tracking-wider">
              Select Hydro-Meteorological Scenario
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-white/10 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-3.5">
          <p className="text-xs text-gray-400 mb-2 font-sans leading-relaxed">
            Changing scenario triggers real-time multi-hazard risk engine recalculation for all 15 watershed villages.
          </p>

          {scenarios.map((s) => {
            const Icon = s.icon;
            const isSelected = currentScenario === s.type;

            return (
              <button
                key={s.type}
                disabled={loading}
                onClick={() => {
                  onSelectScenario(s.type);
                  onClose();
                }}
                className={`w-full text-left p-4 rounded-xl border transition flex items-start gap-4 cursor-pointer ${
                  isSelected
                    ? 'border-[#FF7A18] bg-[#FF7A18]/15 shadow-xl ring-1 ring-[#FF7A18]/40'
                    : 'border-white/10 hover:border-white/20 bg-[#0E1115]/60'
                }`}
              >
                <div className={`p-2.5 rounded-xl border ${s.color}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-black text-white uppercase tracking-wider">
                      {s.title}
                    </span>
                    {isSelected && (
                      <span className="flex items-center gap-1 text-[10px] text-black font-black bg-gradient-to-r from-[#FF7A18] to-[#FFB703] px-2 py-0.5 rounded shadow">
                        <Check className="w-3 h-3 text-black stroke-[3]" /> ACTIVE
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-400 mt-1 font-sans leading-relaxed">
                    {s.desc}
                  </p>
                </div>
              </button>
            );
          })}
        </div>

        <div className="px-6 py-3 bg-[#0E1115] border-t border-white/10 text-[11px] text-gray-400 flex items-center justify-between font-mono">
          <span>Backend Calculation: Real-Time</span>
          <span className="text-amber-400 font-bold">DEMO SYNTHETIC DATASET</span>
        </div>
      </div>
    </div>
  );
};

export default ScenarioControl;
