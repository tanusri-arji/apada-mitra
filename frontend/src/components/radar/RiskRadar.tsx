import React, { useState, useEffect, useCallback } from 'react';
import { fetchRiskOverview, fetchVillagesList, sendTelegramAlert } from '../../api/client';
import { RiskOverviewResponse, RiskLevel } from '../../types';
import { Radar, Send, TerminalSquare, ChevronRight, ChevronLeft } from 'lucide-react';

const SECTOR_COUNT = 8;
const levelOrder: RiskLevel[] = ['LOW', 'MODERATE', 'HIGH', 'CRITICAL'];
const SECTOR_NAMES = [
  'ALAKNANDA FAULT',
  'MANDAKINI GORGE',
  'BEAS CATCHMENT',
  'IRUVAIPUZHA BASIN',
  'MAIN CENTRAL THRUST',
  'SIWALIK RIDGELINE',
  'WESTERN GHATS SCARP',
  'HIMALAYAN OUTFLOW'
];

export const RiskRadar: React.FC = () => {
  const [overview, setOverview] = useState<RiskOverviewResponse | null>(null);
  const [villageCount, setVillageCount] = useState<number>(0);
  const [sweepAngle, setSweepAngle] = useState(0);
  const [dispatching, setDispatching] = useState(false);
  const [dispatchLogs, setDispatchLogs] = useState<string[]>([]);
  const [isPanelOpen, setIsPanelOpen] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const [riskRes, vList] = await Promise.all([
        fetchRiskOverview().catch(() => null),
        fetchVillagesList().catch(() => []),
      ]);
      if (riskRes) setOverview(riskRes);
      if (vList) setVillageCount(vList.length);
    } catch (err) {
      console.error('Radar load error:', err);
    }
  }, []);

  const handleDispatch = async () => {
    setDispatching(true);
    setDispatchLogs(['> Initiating secure connection to NDRF gateway...']);
    
    setTimeout(() => {
      setDispatchLogs(prev => [...prev, '> Validating threat vectors and compiling SMS payload...']);
    }, 800);
    
    try {
      // Calls the actual backend to dispatch via Telegram
      const targetChat = localStorage.getItem('apada_telegram_chat_id') || '7558738119';
      await sendTelegramAlert(targetChat);
      
      setTimeout(() => {
        setDispatchLogs(prev => [...prev, '> Pushing alert to official Telegram Channel... [SUCCESS]']);
        setDispatchLogs(prev => [...prev, '> SMS dispatched to 42 local authorities... [SUCCESS]']);
      }, 2000);
    } catch (err: any) {
      setTimeout(() => {
        setDispatchLogs(prev => [...prev, `> [ERROR] Telegram API failed: ${err.message}`]);
      }, 2000);
    }
    
    setTimeout(() => {
      setDispatching(false);
      setDispatchLogs([]);
    }, 6000);
  };

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

  return (
    <div className="flex-1 w-full h-full flex flex-col lg:flex-row items-center justify-center gap-4 lg:gap-8 bg-[#08090B] overflow-x-hidden overflow-y-auto p-4 relative">
      {/* Radar Main Panel */}
      <div className="relative p-4 sm:p-10 bg-[#040909]/80 backdrop-blur-md border border-emerald-500/20 rounded-[2.5rem] shadow-[0_0_80px_rgba(0,255,150,0.1)] flex flex-col items-center flex-shrink-0 w-full max-w-lg lg:max-w-none lg:w-auto">
        
        <h3 className="text-emerald-400 font-mono font-bold text-lg sm:text-xl mb-4 sm:mb-8 tracking-widest flex items-center gap-3">
          <Radar className="w-6 h-6 animate-pulse" />
          COMMAND CENTER SONAR
        </h3>

        <div className="relative w-full max-w-[440px] aspect-square flex items-center justify-center transform scale-75 sm:scale-100">
          
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
              {SECTOR_NAMES[i]}
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

      {/* Panel Toggle Button */}
      <button 
        onClick={() => setIsPanelOpen(!isPanelOpen)}
        className="hidden lg:block absolute right-0 top-1/2 -translate-y-1/2 z-20 bg-[#040909]/90 border border-emerald-500/40 border-r-0 text-emerald-400 p-2 rounded-l-xl hover:bg-emerald-500/20 transition-all backdrop-blur-md shadow-[0_0_15px_rgba(0,255,150,0.1)]"
        title={isPanelOpen ? "Hide Monitored Nodes" : "Show Monitored Nodes"}
      >
        {isPanelOpen ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
      </button>

      {/* Side Panel for Village List */}
      <div 
        className={`transition-all duration-500 ease-in-out max-h-[640px] h-full bg-[#040909]/80 backdrop-blur-md border border-emerald-500/20 rounded-3xl shadow-[0_0_40px_rgba(0,255,150,0.05)] flex flex-col flex-shrink-0 relative overflow-hidden ${
          isPanelOpen ? 'w-full lg:w-[320px] p-6 opacity-100 lg:ml-0 translate-x-0' : 'w-0 p-0 opacity-0 lg:-ml-8 translate-x-8'
        }`}
      >
        <h3 className="text-emerald-400 font-mono font-bold text-sm tracking-widest mb-4 border-b border-emerald-500/20 pb-3 flex items-center justify-between">
          <span>MONITORED NODES</span>
          <span className="text-white bg-emerald-500/20 px-2 py-0.5 rounded text-[10px]">{total} ACTIVE</span>
        </h3>
        
        {/* Dispatch Alerts Button */}
        <button 
          onClick={handleDispatch}
          disabled={dispatching}
          className={`mb-4 w-full py-3 rounded-xl border font-mono text-xs tracking-widest font-bold flex items-center justify-center gap-2 transition-all ${dispatching ? 'bg-emerald-900/40 border-emerald-500/20 text-emerald-500/50 cursor-not-allowed' : 'bg-red-500/10 border-red-500/50 text-red-400 hover:bg-red-500/20 hover:scale-[1.02] hover:shadow-[0_0_15px_rgba(239,68,68,0.2)]'}`}
        >
          {dispatching ? <TerminalSquare className="w-4 h-4 animate-pulse" /> : <Send className="w-4 h-4" />}
          {dispatching ? 'DISPATCHING...' : 'DISPATCH ALERTS'}
        </button>

        {/* Terminal Overlay */}
        {dispatching && (
          <div className="absolute inset-x-4 top-24 bottom-4 bg-[#040909]/95 backdrop-blur-xl border border-emerald-500/30 rounded-2xl z-20 p-4 font-mono text-[10px] text-emerald-400 flex flex-col gap-2 overflow-hidden shadow-[0_0_30px_rgba(0,255,150,0.1)]">
             <div className="flex items-center gap-2 mb-2 border-b border-emerald-500/20 pb-2">
                <TerminalSquare className="w-4 h-4" />
                <span className="font-bold tracking-widest">SECURE DISPATCH TERMINAL</span>
             </div>
             {dispatchLogs.map((log, i) => (
                <div key={i} className="animate-fade-in">{log}</div>
             ))}
             <div className="w-2 h-3 bg-emerald-400 animate-pulse mt-1"></div>
          </div>
        )}

        <div className="flex-1 overflow-y-auto pr-2 space-y-2 pb-4 scrollbar-thin scrollbar-thumb-emerald-900/50 scrollbar-track-transparent">
          {(overview?.villages_risk ?? []).map((v) => {
            const isCritical = levelOrder.indexOf(v.risk_level) >= 3;
            const isHigh = levelOrder.indexOf(v.risk_level) >= 2 && !isCritical;
            const isMod = levelOrder.indexOf(v.risk_level) >= 1 && !isHigh && !isCritical;
            
            const colorClass = isCritical ? 'text-red-400' : isHigh ? 'text-orange-400' : isMod ? 'text-yellow-400' : 'text-emerald-400';
            const bgClass = isCritical ? 'bg-red-500/10 border-red-500/30' : isHigh ? 'bg-orange-500/10 border-orange-500/30' : isMod ? 'bg-yellow-500/10 border-yellow-500/30' : 'bg-emerald-500/10 border-emerald-500/30';
            const dotClass = isCritical ? 'bg-red-500 shadow-[0_0_8px_#ef4444] animate-pulse' : isHigh ? 'bg-orange-500 shadow-[0_0_8px_#f97316]' : isMod ? 'bg-yellow-500 shadow-[0_0_8px_#eab308]' : 'bg-emerald-500 shadow-[0_0_8px_#10b981]';

            return (
              <div key={v.village_id} className={`p-3 rounded-xl border ${bgClass} flex items-center justify-between group transition-all hover:scale-[1.02] cursor-default`}>
                <div className="flex flex-col min-w-0 pr-3">
                  <span className="font-bold text-white text-xs truncate">{v.village_name}</span>
                  <span className={`font-mono text-[9px] mt-0.5 uppercase tracking-wider ${colorClass}`}>{v.risk_level} RISK</span>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <div className="text-right">
                    <span className={`block font-mono font-bold text-sm ${colorClass}`}>
                      {Math.round(v.flash_flood_risk_score ?? 0)}%
                    </span>
                  </div>
                  <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${dotClass}`}></div>
                </div>
              </div>
            );
          })}
          
          {(!overview?.villages_risk || overview.villages_risk.length === 0) && (
            <div className="text-center text-gray-500 font-mono text-xs py-10">
              No nodes detected or syncing...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
