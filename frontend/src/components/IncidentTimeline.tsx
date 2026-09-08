import React from 'react';
import {
  Activity,
  CloudRain,
  Waves,
  Mountain,
  ShieldAlert,
  Navigation,
  Building2,
  Send,
} from 'lucide-react';

interface Props {
  activeScenario: string;
  selectedVillageName?: string;
  onOpenSmsModal?: () => void;
}

export const IncidentTimeline: React.FC<Props> = ({
  activeScenario,
  selectedVillageName,
  onOpenSmsModal,
}) => {
  const isExtreme = activeScenario === 'EXTREME_RAIN';
  const isHeavy = activeScenario === 'HEAVY_RAIN' || isExtreme;

  const steps = [
    {
      id: 1,
      num: '01',
      title: 'NORMAL',
      sub: 'BASELINE',
      icon: Activity,
      active: true,
      current: activeScenario === 'NORMAL',
      color: 'border-earth-safe/50 bg-earth-forest/30 text-earth-safe',
      lineActive: true,
    },
    {
      id: 2,
      num: '02',
      title: 'RAINFALL',
      sub: isExtreme ? '>75mm/h' : isHeavy ? '>35mm/h' : 'DRIZZLE',
      icon: CloudRain,
      active: isHeavy,
      current: activeScenario === 'HEAVY_RAIN',
      color: isExtreme
        ? 'border-earth-critical/60 bg-earth-critical/20 text-earth-critical'
        : isHeavy
        ? 'border-earth-olive/60 bg-earth-forest/20 text-earth-cream'
        : 'border-earth-border/60 bg-earth-bg/50 text-earth-secondary',
      lineActive: isHeavy,
    },
    {
      id: 3,
      num: '03',
      title: 'FLOOD',
      sub: isExtreme ? 'CRITICAL RUNOFF' : isHeavy ? 'HIGH RUNOFF' : 'NORMAL STAGE',
      icon: Waves,
      active: isHeavy,
      current: false,
      color: isExtreme
        ? 'border-earth-critical/60 bg-earth-critical/20 text-earth-critical'
        : isHeavy
        ? 'border-earth-warning/60 bg-earth-warning/20 text-earth-warning'
        : 'border-earth-border/60 bg-earth-bg/50 text-earth-secondary',
      lineActive: isHeavy,
    },
    {
      id: 4,
      num: '04',
      title: 'LANDSLIDE',
      sub: isExtreme ? 'HIGH THREAT' : isHeavy ? 'MODERATE' : 'STABLE',
      icon: Mountain,
      active: isHeavy,
      current: false,
      color: isExtreme
        ? 'border-earth-orange/60 bg-earth-orange/20 text-earth-orange'
        : isHeavy
        ? 'border-earth-orange/50 bg-earth-orange/15 text-earth-orange'
        : 'border-earth-border/60 bg-earth-bg/50 text-earth-secondary',
      lineActive: isHeavy,
    },
    {
      id: 5,
      num: '05',
      title: 'ROAD',
      sub: isExtreme ? 'BLOCKED' : 'PASSABLE',
      icon: ShieldAlert,
      active: isExtreme,
      current: isExtreme,
      color: isExtreme
        ? 'border-earth-critical/70 bg-earth-critical/30 text-earth-critical ring-1 ring-earth-critical/40'
        : 'border-earth-warning/40 bg-earth-bg/60 text-earth-warning',
      lineActive: true,
    },
    {
      id: 6,
      num: '06',
      title: 'ROUTE',
      sub: 'DIJKSTRA',
      icon: Navigation,
      active: true,
      current: false,
      color: 'border-earth-olive/60 bg-earth-forest/20 text-earth-cream',
      lineActive: true,
    },
    {
      id: 7,
      num: '07',
      title: 'SHELTER',
      sub: 'CAPACITY OK',
      icon: Building2,
      active: true,
      current: false,
      color: 'border-earth-safe/60 bg-earth-forest/30 text-earth-safe',
      lineActive: true,
    },
    {
      id: 8,
      num: '08',
      title: 'ALERT',
      sub: 'SMS READY',
      icon: Send,
      active: true,
      current: false,
      color: 'border-earth-olive/60 bg-earth-forest/20 text-earth-cream',
      actionable: true,
      lineActive: false,
    },
  ];

  return (
    <div className="bg-earth-surface/95 border-b border-earth-border px-4 py-1.5 font-mono z-20 shadow-md h-12 flex items-center flex-shrink-0 relative overflow-hidden">
      <div className="flex items-center justify-between gap-3 overflow-x-auto w-full scrollbar-none relative z-10">
        {/* LEFT: Section Identifier */}
        <div className="flex items-center gap-2 flex-shrink-0 pr-3 border-r border-earth-border/60">
          <span className="w-2 h-2 rounded-full bg-earth-olive animate-pulse"></span>
          <div className="leading-tight">
            <div className="text-earth-primary font-extrabold text-[10px] tracking-wider uppercase font-mono">
              INCIDENT CASCADE
            </div>
            <div className="text-[8px] text-earth-secondary uppercase tracking-widest font-mono">
              LIVE OPERATIONAL FLOW
            </div>
          </div>
        </div>

        {/* CENTER: Rail Nodes with Connecting Progress Line */}
        <div className="flex items-center gap-1.5 flex-1 min-w-max justify-between relative px-2">
          {/* Continuous Rail Line Background */}
          <div className="absolute left-6 right-6 top-1/2 -translate-y-1/2 h-[2px] bg-earth-border/60 -z-10"></div>

          {steps.map((step, idx) => {
            const Icon = step.icon;
            const isLast = idx === steps.length - 1;

            return (
              <div key={step.id} className="flex items-center gap-1.5 relative">
                {/* Stage Node Item */}
                <div
                  onClick={() => {
                    if (step.actionable && onOpenSmsModal) {
                      onOpenSmsModal();
                    }
                  }}
                  className={`px-2 py-0.5 rounded-md border transition-all duration-300 flex items-center gap-1.5 ${
                    step.actionable ? 'cursor-pointer hover:border-earth-olive hover:scale-105 shadow' : ''
                  } ${step.current ? 'ring-1 ring-earth-olive shadow-lg scale-105' : ''} ${step.color}`}
                  title={`${step.num} ${step.title}: ${step.sub}`}
                >
                  <span className="text-[8px] font-bold text-earth-secondary/80 leading-none">
                    {step.num}
                  </span>
                  <Icon className="w-3 h-3 flex-shrink-0" />
                  <div className="leading-none">
                    <span className="font-extrabold tracking-wider uppercase text-[10px]">
                      {step.title}
                    </span>
                    <span className="text-[8px] text-earth-secondary font-sans font-medium block leading-none mt-0.5">
                      {step.sub}
                    </span>
                  </div>
                </div>

                {/* Connector Arrow Line */}
                {!isLast && (
                  <div
                    className={`h-[2px] w-3 flex-shrink-0 transition-colors duration-300 ${
                      step.lineActive ? 'bg-earth-olive/60' : 'bg-earth-border/50'
                    }`}
                  ></div>
                )}
              </div>
            );
          })}
        </div>

        {/* RIGHT: Active Scenario Indicator / Alert Action */}
        <div className="flex items-center gap-2 flex-shrink-0 pl-2 border-l border-earth-border/60">
          <div className="hidden lg:flex items-center gap-1.5 bg-earth-bg/80 px-2 py-0.5 rounded border border-earth-border text-[9px] font-mono font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-earth-olive animate-pulse"></span>
            <span className="text-earth-secondary uppercase">{activeScenario.replace('_', ' ')}</span>
          </div>

          {selectedVillageName && onOpenSmsModal && (
            <button
              onClick={onOpenSmsModal}
              className="bg-earth-olive hover:bg-earth-olive/90 text-black text-[9px] font-extrabold px-2.5 py-0.5 rounded transition flex items-center gap-1 uppercase shadow"
            >
              <Send className="w-2.5 h-2.5" />
              <span>ALERT ({selectedVillageName})</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
