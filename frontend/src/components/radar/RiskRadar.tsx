import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { fetchRiskOverview, fetchVillagesList } from '../../api/client';
import { RiskOverviewResponse, RiskLevel } from '../../types';
import { X, Radar } from 'lucide-react';

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
  
  const toggleButton = (
    <button
      onClick={() => setIsOpen(true)}
      className="fixed bottom-6 right-6 z-[999998] flex items-center gap-2 px-5 py-3 bg-[#020606]/90 backdrop-blur-xl border border-emerald-500/30 rounded-full text-emerald-400 font-mono text-xs hover:bg-emerald-950/50 transition-all shadow-[0_0_15px_rgba(16,185,129,0.2)]"
    >
      <Radar className={`w-5 h-5 ${loading ? 'animate-pulse' : ''}`} />
      <span className="font-bold tracking-wider">{loading ? 'SYNCING...' : 'COMMAND RADAR'}</span>
    </button>
  );

  const modalContent = isOpen ? (
    <div className="fixed inset-0 z-[999999] flex items-center justify-center bg-[#040909]/80 backdrop-blur-md">
      <div className="relative p-10 bg-[#020606] border border-emerald-500/20 rounded-[2.5rem] shadow-[0_0_80px_rgba(0,255,150,0.1)] flex flex-col items-center">
        
        <button 
          onClick={() => setIsOpen(false)}
          className="absolute top-6 right-6 text-emerald-700 hover:text-emerald-300 transition-colors bg-emerald-950/30 p-2 rounded-full"
        >
          <X className="w-6 h-6" />
        </button>

        <h3 className="text-emerald-400 font-mono font-bold text-xl mb-8 tracking-widest flex items-center gap-3">
          <Radar className="w-6 h-6 animate-pulse" />
          COMMAND CENTER SONAR
        </h3>

        <div className="relative w-[440px] h-[440px] flex items-center justify-center">
          
          {/* SVG Radar Grid and Sectors */}
          <svg width="440" height="440" viewBox="0 0 440 440" className="absolute inset-0">
            {/* Outer segmented ring */}
            {sectors.map((lvl, i) => {
              const color = lvl === 'critical' ? '#EF4444' : lvl === 'high' ? '#F97316' : lvl === 'moderate' ? '#EAB308' : '#10B981';
              const radius = 200;
              const circumference = 2 * Math.PI * radius;
              const dashLength = (40 / 360) * circumference;
              const gapLength = circumference - dashLength;

              return (
                <circle
                  key={i}
                  cx="220"
                  cy="220"
                  r={radius}
                  fill="none"
                  stroke={color}
                  strokeWidth="16"
                  strokeDasharray={`${dashLength} ${gapLength}`}
                  strokeDashoffset={-((circumference / 360) * (i * 45))}
                  className="transition-all duration-1000 ease-in-out"
                  style={{ transformOrigin: 'center', transform: 'rotate(-90deg)' }}
                />
              );
            })}

            {/* Inner concentric circles */}
            <circle cx="220" cy="220" r="150" fill="none" stroke="#10B981" strokeWidth="1.5" strokeOpacity="0.2" />
            <circle cx="220" cy="220" r="100" fill="none" stroke="#10B981" strokeWidth="1.5" strokeOpacity="0.2" />
            <circle cx="220" cy="220" r="50" fill="none" stroke="#10B981" strokeWidth="1.5" strokeOpacity="0.2" />
            
            {/* Crosshairs */}
            <line x1="220" y1="20" x2="220" y2="420" stroke="#10B981" strokeWidth="1" strokeOpacity="0.2" />
            <line x1="20" y1="220" x2="420" y2="220" stroke="#10B981" strokeWidth="1" strokeOpacity="0.2" />
          </svg>

          {/* Sweeping Cone */}
          <div
            className="absolute inset-[20px] rounded-full pointer-events-none overflow-hidden"
            style={{
              transform: `rotate(${sweepAngle}deg)`,
            }}
          >
            {/* Gradient Cone trailing the laser */}
            <div className="absolute inset-0" style={{
              background: `conic-gradient(from 0deg, transparent 0deg, transparent 270deg, rgba(16, 185, 129, 0.4) 360deg)`
            }} />
            {/* Laser Line */}
            <div className="absolute top-0 bottom-1/2 left-1/2 w-[2px] bg-emerald-400 shadow-[0_0_15px_#10B981]" style={{ transform: 'translateX(-50%)' }} />
          </div>

          {/* Sector Labels (Sector A, Sector B...) */}
          {sectors.map((_, i) => {
            const angle = i * 45 + 22.5;
            const rad = (angle - 90) * (Math.PI / 180);
            const x = 220 + 175 * Math.cos(rad);
            const y = 220 + 175 * Math.sin(rad);
            const textRot = angle > 90 && angle < 270 ? angle + 180 : angle;
            
            return (
              <div 
                key={`label-${i}`} 
                className="absolute text-[9px] font-mono font-bold text-emerald-500/70 uppercase"
                style={{ 
                  left: `${x}px`, 
                  top: `${y}px`, 
                  transform: `translate(-50%, -50%) rotate(${textRot}deg)`
                }}
              >
                Sector {String.fromCharCode(65 + i)}
              </div>
            );
          })}

          {/* Center Text Stats Box */}
          <div className="absolute flex flex-col items-center justify-center text-center z-10 bg-[#020606]/90 w-[110px] h-[110px] rounded-full border border-emerald-500/30 backdrop-blur-md shadow-[0_0_20px_rgba(0,0,0,0.8)]">
             <div className="text-emerald-500 font-mono text-[9px] tracking-widest uppercase opacity-80 mt-1">Villages</div>
             <div className="text-emerald-50 font-bold text-2xl">{total}</div>
             <div className="w-12 h-px bg-emerald-500/30 my-1"></div>
             <div className="text-red-400 font-mono text-[9px] tracking-widest uppercase opacity-90">High Risk</div>
             <div className="text-red-400 font-bold text-lg">{critical + high}</div>
          </div>
        </div>

        {/* Legend */}
        <div className="mt-10 flex items-center justify-center gap-6 text-[11px] font-mono text-gray-400 uppercase tracking-wider bg-black/60 px-8 py-3 rounded-full border border-emerald-900/40">
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-[#EF4444] inline-block shadow-[0_0_10px_#EF4444]"></span> Critical</div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-[#F97316] inline-block shadow-[0_0_10px_#F97316]"></span> High</div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-[#EAB308] inline-block shadow-[0_0_10px_#EAB308]"></span> Moderate</div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-[#10B981] inline-block shadow-[0_0_10px_#10B981]"></span> Low</div>
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
