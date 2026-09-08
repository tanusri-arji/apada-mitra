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
    <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-command-card border border-command-border rounded-xl w-full max-w-lg shadow-2xl overflow-hidden font-mono">
        <div className="px-6 py-4 border-b border-command-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CloudRain className="w-5 h-5 text-command-accent" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Select Hydro-Meteorological Scenario
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-command-muted hover:text-white p-1 rounded-lg hover:bg-command-bg transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-3">
          <p className="text-xs text-command-muted mb-2 font-sans">
            Changing scenario forces backend risk engine recalculation for all 15 watershed villages.
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
                className={`w-full text-left p-4 rounded-lg border transition flex items-start gap-4 ${
                  isSelected
                    ? 'border-command-accent bg-command-accent/10 shadow-lg'
                    : 'border-command-border hover:border-command-muted bg-command-bg/40'
                }`}
              >
                <div className={`p-2.5 rounded-lg border ${s.color}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white uppercase tracking-wide">
                      {s.title}
                    </span>
                    {isSelected && (
                      <span className="flex items-center gap-1 text-[10px] text-command-accent font-semibold bg-command-accent/20 px-2 py-0.5 rounded border border-command-accent/40">
                        <Check className="w-3 h-3" /> ACTIVE
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-command-muted mt-1 font-sans leading-relaxed">
                    {s.desc}
                  </p>
                </div>
              </button>
            );
          })}
        </div>

        <div className="px-6 py-3 bg-command-bg border-t border-command-border text-[11px] text-command-muted flex items-center justify-between">
          <span>Backend Server Calculation: Real-Time</span>
          <span className="text-amber-400">DEMO SYNTHETIC MODEL</span>
        </div>
      </div>
    </div>
  );
};
