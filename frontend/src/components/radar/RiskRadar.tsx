import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { fetchRiskOverview, fetchVillagesList } from '../../api/client';
import { RiskOverviewResponse, RiskLevel } from '../../types';
import { Activity } from 'lucide-react';

const SECTOR_COUNT = 8;

const levelOrder: RiskLevel[] = ['LOW', 'MODERATE', 'HIGH', 'CRITICAL'];

export const RiskRadar: React.FC = () => {
  const [overview, setOverview] = useState<RiskOverviewResponse | null>(null);
  const [villageCount, setVillageCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [sweepAngle, setSweepAngle] = useState(0);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [riskRes, vList] = await Promise.all([
        fetchRiskOverview().catch(() => null),
        fetchVillagesList().catch(() => []),
      ]);
      if (riskRes) setOverview(riskRes);
      if (vList) setVillageCount(vList.length);
    } catch (err) {
      console.error('Radar load error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, [loadData]);

  useEffect(() => {
    const id = setInterval(() => {
      setSweepAngle((a) => (a + 3) % 360);
    }, 50);
    return () => clearInterval(id);
  }, []);

  if (loading) {
    const loadingNode = (
      <div className="fixed bottom-6 right-6 z-[999999] p-4 text-xs text-gray-500 font-mono bg-black/50 rounded-xl border border-cyan-400/30 shadow-2xl">
        Loading Risk Radar…
      </div>
    );
    return typeof document !== 'undefined' ? createPortal(loadingNode, document.body) : null;
  }

  const impact = overview?.impact_summary ?? null;
  const total = impact?.total_villages ?? villageCount ?? 0;

  const sectors = Array(SECTOR_COUNT).fill('low');
  let lowCount = 0;
  (overview?.villages_risk ?? []).forEach((v, idx) => {
    const i = idx % SECTOR_COUNT;
    if (levelOrder.indexOf(v.risk_level) >= 3) {
      sectors[i] = 'critical';
    } else if (levelOrder.indexOf(v.risk_level) >= 2) {
      sectors[i] = 'high';
    } else if (levelOrder.indexOf(v.risk_level) >= 1) {
      sectors[i] = 'moderate';
    } else {
      lowCount++;
    }
  });

  const critical = impact?.critical_villages_count ?? 0;
  const high = impact?.high_villages_count ?? 0;
  const moderate = impact?.moderate_villages_count ?? 0;
  const _low = lowCount;

  const content = (
    <aside className="fixed bottom-6 right-6 w-[220px] h-[220px] z-[999999]">
      <div className="relative w-full h-full">
        {/* Radar Sweep */}
        <div className="absolute inset-0 rounded-full border-2 border-cyan-400/40 shadow-cyan-400/20 shadow-[0_0_12px_4px_rgba(0,255,255,0.1)] overflow-hidden"></div>
        <div
          className="absolute inset-0 rounded-full pointer-events-none"
          style={{
            transform: `rotate(${sweepAngle}deg)`,
            background: `conic-gradient(
              0deg,
              rgba(0, 255, 255, 0.12) 0deg,
              transparent 45deg,
              transparent 360deg
            )`,
          }}
        />
        {sectors.map((lvl, i) => {
          const color = lvl === 'critical' ? 'bg-red-500' : lvl === 'high' ? 'bg-amber-400' : lvl === 'moderate' ? 'bg-yellow-400' : 'bg-emerald-400';
          return (
            <div
              key={i}
              className={`absolute w-2 h-2 rounded-full ${color} border border-white/30`}
              style={{
                left: '50%',
                top: '50%',
                transform: `rotate(${(360 / SECTOR_COUNT) * i}deg) translate(40px)`,
                transformOrigin: '0 0',
              }}
            />
          );
        })}

        {/* Center Label */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center">
          <div className="text-cyan-300 font-black text-xs font-mono">Risk Radar</div>
          <div className="text-gray-400 text-[10px] mt-0.5">Live</div>
        </div>

        {/* Stats Grid Around */}
        <div className="absolute top-1 left-1/2 -translate-x-1/2 text-center text-[8px] font-mono text-gray-300">
          {critical} CRIT
        </div>
        <div className="absolute top-1/2 left-0.5 -translate-y-1/2 text-center text-[8px] font-mono text-gray-300">
          {high} HIGH
        </div>
        <div className="absolute top-1/2 right-0.5 -translate-y-1/2 text-center text-[8px] font-mono text-gray-300">
          {moderate} MED
        </div>
        <div className="absolute bottom-1 left-1/2 -translate-x-1/2 text-center text-[8px] font-mono text-gray-300">
          {_low} LOW ({total} total)
        </div>

        {/* Mini HUD Counter */}
        <div className="absolute bottom-2 right-2 flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-black/50 border border-cyan-400/30 text-cyan-300 font-mono text-[9px]">
          <Activity className="w-2.5 h-2.5 animate-pulse" />
          Live
        </div>
      </div>
    </aside>
  );

  return typeof document !== 'undefined' ? createPortal(content, document.body) : null;
};
