import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { fetchRiskOverview, fetchVillagesList } from '../../api/client';
import { RiskOverviewResponse, RiskLevel } from '../../types';
import { Activity, X } from 'lucide-react';

const SECTOR_COUNT = 8;

const levelOrder: RiskLevel[] = ['LOW', 'MODERATE', 'HIGH', 'CRITICAL'];

export const RiskRadar: React.FC = () => {
  const [overview, setOverview] = useState<RiskOverviewResponse | null>(null);
  const [villageCount, setVillageCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [sweepAngle, setSweepAngle] = useState(0);
  const [isOpen, setIsOpen] = useState(false);

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

  const toggleButton = (
    <button
      onClick={() => setIsOpen(true)}
      className="fixed bottom-6 right-6 z-[999998] flex items-center gap-2 px-4 py-2 bg-[#0E1115]/90 backdrop-blur-xl border border-cyan-400/30 rounded-full text-cyan-300 font-mono text-xs hover:bg-cyan-950 transition-colors shadow-lg shadow-cyan-900/20"
    >
      <Activity className={`w-4 h-4 ${loading ? 'animate-pulse' : ''}`} />
      <span>{loading ? 'SYNCING...' : 'RISK RADAR'}</span>
    </button>
  );

  const modalContent = isOpen ? (
    <div className="fixed inset-0 z-[999999] flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="relative p-10 bg-[#08090B] border border-cyan-400/20 rounded-2xl shadow-2xl flex flex-col items-center">
        
        <button 
          onClick={() => setIsOpen(false)}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <h3 className="text-cyan-300 font-mono font-bold text-lg mb-8 tracking-widest flex items-center gap-2">
          <Activity className="w-5 h-5" />
          LIVE RISK RADAR
        </h3>

        <div className="relative w-[280px] h-[280px]">
          <div className="absolute inset-0 rounded-full border-2 border-cyan-400/40 shadow-[0_0_20px_rgba(0,255,255,0.15)] overflow-hidden"></div>
          <div
            className="absolute inset-0 rounded-full pointer-events-none"
            style={{
              transform: `rotate(${sweepAngle}deg)`,
              background: `conic-gradient(
                0deg,
                rgba(0, 255, 255, 0.15) 0deg,
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
                className={`absolute w-3 h-3 rounded-full ${color} border border-white/30`}
                style={{
                  left: '50%',
                  top: '50%',
                  transform: `rotate(${(360 / SECTOR_COUNT) * i}deg) translate(70px)`,
                  transformOrigin: '0 0',
                }}
              />
            );
          })}

          <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-center text-[11px] font-mono text-gray-300 whitespace-nowrap">
            {critical} CRITICAL
          </div>
          <div className="absolute top-1/2 -left-12 -translate-y-1/2 text-center text-[11px] font-mono text-gray-300">
            {high} HIGH
          </div>
          <div className="absolute top-1/2 -right-14 -translate-y-1/2 text-center text-[11px] font-mono text-gray-300">
            {moderate} MOD
          </div>
          <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-center text-[11px] font-mono text-gray-300 whitespace-nowrap">
            {_low} LOW (of {total})
          </div>
        </div>
        
        <div className="mt-8 flex items-center justify-center gap-4 text-[10px] font-mono text-gray-400">
          <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500 inline-block"></span> CRIT</div>
          <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-400 inline-block"></span> HIGH</div>
          <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-400 inline-block"></span> MOD</div>
          <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-400 inline-block"></span> LOW</div>
        </div>
      </div>
    </div>
  ) : null;

  return typeof document !== 'undefined' ? createPortal(
    <>
      {!isOpen && toggleButton}
      {modalContent}
    </>,
    document.body
  ) : null;
};
