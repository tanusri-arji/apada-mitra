import React from 'react';
import { ImpactSummary } from '../types';
import { MapPin, AlertTriangle, Users, Gauge } from 'lucide-react';

interface Props {
  impact: ImpactSummary | null;
  loading: boolean;
}

export const MetricsBar: React.FC<Props> = ({ impact, loading }) => {
  const criticalAndHigh = impact
    ? impact.critical_villages_count + impact.high_villages_count
    : 0;

  return (
    <div className="bg-command-card/90 border-b border-command-border px-6 py-2.5 flex items-center justify-between font-mono text-xs shadow-inner">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 w-full">
        {/* Metric 1 */}
        <div className="flex items-center gap-3 bg-command-bg/60 p-2 rounded border border-command-border/60">
          <div className="p-2 rounded bg-cyan-500/10 text-cyan-400">
            <MapPin className="w-4 h-4" />
          </div>
          <div>
            <div className="text-command-muted uppercase text-[10px]">Villages Monitored</div>
            <div className="text-sm font-bold text-white">
              {loading ? '...' : impact?.total_villages || 0} Villages
            </div>
          </div>
        </div>

        {/* Metric 2 */}
        <div className="flex items-center gap-3 bg-command-bg/60 p-2 rounded border border-command-border/60">
          <div className="p-2 rounded bg-amber-500/10 text-amber-400">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div>
            <div className="text-command-muted uppercase text-[10px]">High/Critical Vulnerability</div>
            <div className="text-sm font-bold text-amber-400">
              {loading ? '...' : criticalAndHigh} Villages
            </div>
          </div>
        </div>

        {/* Metric 3 */}
        <div className="flex items-center gap-3 bg-command-bg/60 p-2 rounded border border-command-border/60">
          <div className="p-2 rounded bg-red-500/10 text-red-400">
            <Users className="w-4 h-4" />
          </div>
          <div>
            <div className="text-command-muted uppercase text-[10px]">Population Exposed</div>
            <div className="text-sm font-bold text-red-400">
              {loading ? '...' : impact?.total_population_exposed.toLocaleString() || 0} Residents
            </div>
          </div>
        </div>

        {/* Metric 4 */}
        <div className="flex items-center gap-3 bg-command-bg/60 p-2 rounded border border-command-border/60">
          <div className="p-2 rounded bg-emerald-500/10 text-emerald-400">
            <Gauge className="w-4 h-4" />
          </div>
          <div>
            <div className="text-command-muted uppercase text-[10px]">Average Confidence</div>
            <div className="text-sm font-bold text-emerald-400">
              {loading ? '...' : `${impact?.average_confidence}%`}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
