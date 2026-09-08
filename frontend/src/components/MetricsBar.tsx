import React from 'react';
import { ImpactSummary, RoadSegment, Shelter } from '../types';
import { Users, AlertTriangle, ShieldCheck, ShieldAlert, Building2, Clock } from 'lucide-react';

interface Props {
  impact: ImpactSummary | null;
  roads?: RoadSegment[];
  shelters?: Shelter[];
  loading: boolean;
}

export const MetricsBar: React.FC<Props> = ({ impact, roads = [], shelters = [], loading }) => {
  const criticalAndHigh = impact
    ? impact.critical_villages_count + impact.high_villages_count
    : 0;

  const blockedRoadsCount = roads.filter((r) => r.status === 'BLOCKED').length;
  const availableSheltersCount = shelters.filter((s) => s.available_capacity > 0).length;

  // Check if lead_time exists in impact summary or backend data (do NOT create fake lead time)
  const leadTimeVal = (impact as any)?.lead_time_mins || (impact as any)?.lead_time;

  return (
    <div className="bg-earth-surface/95 border-b border-earth-border px-4 py-1 flex items-center justify-between font-mono shadow-md z-20 h-12 flex-shrink-0">
      <div className="flex items-center gap-3 w-full">
        {/* Left Section Label */}
        <div className="hidden 2xl:flex flex-col pr-3 border-r border-earth-border/60 flex-shrink-0 leading-tight">
          <span className="text-[10px] font-extrabold text-earth-primary uppercase font-mono tracking-wider">
            SITUATION SNAPSHOT
          </span>
          <span className="text-[8px] text-earth-secondary uppercase tracking-widest font-mono">
            OPERATIONAL METRICS
          </span>
        </div>

        <div className="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-6 gap-2 flex-1 w-full">
          {/* 1. POPULATION EXPOSED */}
          <div className="bg-earth-critical/15 px-2.5 py-1 rounded-md border border-earth-critical/40 flex items-center justify-between shadow-sm">
            <div className="space-y-0.5">
              <div className="text-[8.5px] text-earth-critical uppercase font-bold tracking-wider flex items-center gap-1">
                <Users className="w-3 h-3 text-earth-critical flex-shrink-0" />
                <span>POPULATION EXPOSED</span>
              </div>
              <div className="text-base lg:text-lg font-extrabold text-earth-critical leading-none tracking-tight">
                {loading ? '...' : impact?.total_population_exposed.toLocaleString() || 0}
              </div>
            </div>
            <span className="text-[7.5px] bg-earth-critical/20 text-earth-critical font-extrabold px-1 py-0.2 rounded border border-earth-critical/40 uppercase hidden xl:inline">
              AT RISK
            </span>
          </div>

          {/* 2. HIGH / CRITICAL VILLAGES */}
          <div className="bg-earth-bg/80 px-2.5 py-1 rounded-md border border-earth-border border-l-2 border-l-earth-warning flex items-center justify-between shadow-sm">
            <div className="space-y-0.5">
              <div className="text-[8.5px] text-earth-warning uppercase font-bold tracking-wider flex items-center gap-1">
                <AlertTriangle className="w-3 h-3 text-earth-warning flex-shrink-0" />
                <span>HIGH / CRITICAL</span>
              </div>
              <div className="text-base lg:text-lg font-extrabold text-earth-warning leading-none tracking-tight">
                {loading ? '...' : `${criticalAndHigh} / ${impact?.total_villages || 15}`}
              </div>
            </div>
            <span className="text-[7.5px] bg-earth-warning/15 text-earth-warning font-bold px-1 py-0.2 rounded border border-earth-warning/30 uppercase hidden xl:inline">
              PRIORITY
            </span>
          </div>

          {/* 3. AVERAGE RISK / CONFIDENCE */}
          <div className="bg-earth-bg/80 px-2.5 py-1 rounded-md border border-earth-border flex items-center justify-between shadow-sm">
            <div className="space-y-0.5">
              <div className="text-[8.5px] text-earth-secondary uppercase font-bold tracking-wider flex items-center gap-1">
                <ShieldCheck className="w-3 h-3 text-earth-safe flex-shrink-0" />
                <span>AVG RISK / CONFIDENCE</span>
              </div>
              <div className="text-base lg:text-lg font-extrabold text-earth-safe leading-none tracking-tight">
                {loading ? '...' : `${impact?.average_risk_score || 64}% / ${impact?.average_confidence || 95}%`}
              </div>
            </div>
            <span className="text-[7.5px] bg-earth-safe/15 text-earth-safe font-bold px-1 py-0.2 rounded border border-earth-safe/30 uppercase hidden xl:inline">
              HIGH CONF
            </span>
          </div>

          {/* 4. ROADS BLOCKED */}
          <div className="bg-earth-bg/80 px-2.5 py-1 rounded-md border border-earth-border border-l-2 border-l-earth-critical flex items-center justify-between shadow-sm">
            <div className="space-y-0.5">
              <div className="text-[8.5px] text-earth-secondary uppercase font-bold tracking-wider flex items-center gap-1">
                <ShieldAlert className="w-3 h-3 text-earth-critical flex-shrink-0" />
                <span>ROADS BLOCKED</span>
              </div>
              <div className="text-base lg:text-lg font-extrabold text-earth-critical leading-none tracking-tight">
                {loading ? '...' : `${blockedRoadsCount} SEGMENTS`}
              </div>
            </div>
            <span className="text-[7.5px] bg-earth-critical/15 text-earth-critical font-bold px-1 py-0.2 rounded border border-earth-critical/30 uppercase hidden xl:inline">
              IMPEDIMENT
            </span>
          </div>

          {/* 5. SHELTERS AVAILABLE */}
          <div className="bg-earth-bg/80 px-2.5 py-1 rounded-md border border-earth-border flex items-center justify-between shadow-sm">
            <div className="space-y-0.5">
              <div className="text-[8.5px] text-earth-secondary uppercase font-bold tracking-wider flex items-center gap-1">
                <Building2 className="w-3 h-3 text-earth-olive flex-shrink-0" />
                <span>SHELTERS AVAILABLE</span>
              </div>
              <div className="text-base lg:text-lg font-extrabold text-earth-primary leading-none tracking-tight">
                {loading ? '...' : `${availableSheltersCount} / ${shelters.length || 4}`}
              </div>
            </div>
            <span className="text-[7.5px] bg-earth-olive/15 text-earth-cream font-bold px-1 py-0.2 rounded border border-earth-olive/30 uppercase hidden xl:inline">
              READY
            </span>
          </div>

          {/* 6. LEAD TIME (rendered ONLY if actual value exists) */}
          {leadTimeVal !== undefined && (
            <div className="bg-earth-bg/80 px-2.5 py-1 rounded-md border border-earth-border flex items-center justify-between shadow-sm">
              <div className="space-y-0.5">
                <div className="text-[8.5px] text-earth-cream uppercase font-bold tracking-wider flex items-center gap-1">
                  <Clock className="w-3 h-3 text-earth-olive flex-shrink-0" />
                  <span>EARLY LEAD TIME</span>
                </div>
                <div className="text-base lg:text-lg font-extrabold text-earth-cream leading-none tracking-tight">
                  {leadTimeVal} mins
                </div>
              </div>
              <span className="text-[7.5px] bg-earth-olive/15 text-earth-cream font-bold px-1 py-0.2 rounded border border-earth-olive/30 uppercase hidden xl:inline">
                PRE-ALERT
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

