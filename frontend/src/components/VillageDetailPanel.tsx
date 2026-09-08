import React from 'react';
import {
  VillageRiskDetail,
  LandslideRiskDetail,
  EvacuationPriority,
  ShelterRecommendationResult,
} from '../types';
import { RiskBadge } from './RiskBadge';
import {
  getDecisionBadgeClasses,
  getDecisionStatusLabel,
  getRiskColorHex,
} from '../utils/riskColors';
import {
  Users,
  BarChart3,
  X,
  Compass,
  AlertTriangle,
  Navigation,
  Zap,
  Send,
  CheckCircle2,
  XCircle,
  Building2,
  CloudRain,
  RefreshCw,
  ShieldAlert,
} from 'lucide-react';
import { fetchIMDWarningsForVillage } from '../api/client';
import { IMDVillageWarningResponse } from '../types';



interface Props {
  village: VillageRiskDetail | null;
  landslideDetail?: LandslideRiskDetail | null;
  priorityDetail?: EvacuationPriority | null;
  shelterRecommendation?: ShelterRecommendationResult | null;
  dataMode?: string | null;
  onRefreshVillage?: (villageId: string) => Promise<void>;
  onCalculateRoute?: () => void;
  routeLoading?: boolean;
  onOpenSmsModal?: () => void;
  onClose: () => void;
}

export const VillageDetailPanel: React.FC<Props> = ({
  village,
  landslideDetail,
  priorityDetail,
  shelterRecommendation,
  dataMode,
  onRefreshVillage,
  onCalculateRoute,
  routeLoading,
  onOpenSmsModal,
  onClose,
}) => {
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const [refreshMessage, setRefreshMessage] = React.useState<{ text: string; success: boolean } | null>(null);
  const [imdData, setImdData] = React.useState<IMDVillageWarningResponse | null>(null);

  React.useEffect(() => {
    if (village?.village_id) {
      fetchIMDWarningsForVillage(village.village_id)
        .then((data) => setImdData(data))
        .catch((err) => {
          console.warn('IMD warning fetch skipped:', err);
          setImdData(null);
        });
    }
  }, [village?.village_id]);

  // Empty State: No Village Selected
  if (!village) {
    return (
      <aside className="w-[25%] min-w-[300px] max-w-[380px] bg-earth-surface/95 border-l border-earth-border p-6 flex flex-col items-center justify-center text-center font-mono z-20 shadow-2xl flex-shrink-0">
        <div className="w-14 h-14 rounded-full bg-earth-olive/15 border border-earth-olive/40 flex items-center justify-center mb-4 shadow-inner">
          <Compass className="w-7 h-7 text-earth-olive animate-pulse" />
        </div>
        <h3 className="text-xs font-extrabold text-earth-primary uppercase tracking-widest mb-1.5">
          NO LOCATION SELECTED
        </h3>
        <p className="text-[11px] text-earth-secondary font-sans max-w-xs leading-relaxed">
          Select any village from the <strong className="text-earth-cream">Map</strong> or <strong className="text-earth-cream">Incident Priority Queue</strong> to view real-time risk intelligence, XAI factor contributions, impact assessment, and evacuation routes.
        </p>
      </aside>
    );
  }

  const floodRisk = Math.round(village.flash_flood_risk_score);
  const lsRisk = landslideDetail ? Math.round(landslideDetail.landslide_risk_score) : 0;
  const floodRiskColor = getRiskColorHex(village.risk_level);
  const lsRiskColor = landslideDetail ? getRiskColorHex(landslideDetail.risk_level) : '#6B7280';
  
  const isFloodDominant = floodRisk >= lsRisk;

  const recShelter = shelterRecommendation?.recommended_shelter;
  const route = shelterRecommendation?.route;

  // Shelter Occupancy Stats
  const totalCapacity = recShelter?.total_capacity || 100;
  const availCapacity = recShelter?.available_capacity || 45;
  const occupiedCapacity = totalCapacity - availCapacity;
  const projectedEvacuees = Math.min(village.exposure.population_exposed, 60);
  const projectedOccupancy = occupiedCapacity + projectedEvacuees;
  const isOverflow = projectedOccupancy > totalCapacity;

  // Feature 1 & 2: Extract rainfall and soil moisture values from factors
  const rainfallFactor = village.factors?.find((f) => f.feature_key === 'current_rainfall');
  const forecastFactor = village.factors?.find((f) => f.feature_key === 'forecast_rainfall');
  const soilMoistureFactor = village.factors?.find((f) => f.feature_key === 'soil_saturation');

  const currentRainfallVal = rainfallFactor?.raw_value;
  const forecastRainfallVal = forecastFactor?.raw_value;
  const soilMoistureVal = soilMoistureFactor?.raw_value;

  // Compute Data Source & Live Status
  const getLiveStatusInfo = () => {
    if (!dataMode || dataMode.includes('LIVE API') || dataMode.includes('LIVE')) {
      return {
        status: 'LIVE_EXTERNAL_API',
        label: 'LIVE',
        source: 'Open-Meteo Weather API',
        colorClass: 'bg-earth-forest/30 border-earth-safe/80 text-earth-safe',
        isLive: true,
      };
    }
    if (dataMode.includes('CACHED')) {
      return {
        status: 'CACHED',
        label: 'CACHED',
        source: 'Open-Meteo Weather API (Cached)',
        colorClass: 'bg-earth-warning/20 border-earth-warning/80 text-earth-warning',
        isLive: false,
      };
    }
    return {
      status: 'OFFLINE_DEMO',
      label: 'OFFLINE DEMO',
      source: 'SIH Synthetic Dataset',
      colorClass: 'bg-earth-elevated border-earth-border text-earth-secondary',
      isLive: false,
    };
  };
  const liveStatus = getLiveStatusInfo();

  const handleRefreshClick = async () => {
    if (!village || isRefreshing) return;
    try {
      setIsRefreshing(true);
      setRefreshMessage(null);
      if (onRefreshVillage) {
        await onRefreshVillage(village.village_id);
      }
      setRefreshMessage({ text: 'Data refreshed from API', success: true });
    } catch (err: any) {
      setRefreshMessage({ text: err.message || 'Refresh failed', success: false });
    } finally {
      setIsRefreshing(false);
      setTimeout(() => setRefreshMessage(null), 3000);
    }
  };

  return (
    <aside className="w-[25%] min-w-[300px] max-w-[380px] bg-earth-surface/95 border-l border-earth-border flex flex-col h-full z-20 font-sans shadow-2xl flex-shrink-0 overflow-y-auto select-text">
      {/* 1. SELECTED LOCATION HEADER */}
      <div className="p-3 border-b border-earth-border bg-earth-bg/90 flex items-start justify-between sticky top-0 backdrop-blur-md z-30 font-mono">
        <div>
          <span className="text-[9px] text-earth-secondary uppercase font-bold tracking-widest block mb-0.5">
            SELECTED LOCATION
          </span>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-extrabold text-earth-primary tracking-wide uppercase">
              {village.village_name}
            </h2>
            <RiskBadge level={village.risk_level} className="text-[9px] px-1.5 py-0" />
          </div>
          <p className="text-[10px] text-earth-secondary mt-0.5 font-mono">
            {village.elevation.toLocaleString()} m • {village.village_id}
          </p>
        </div>
        <button
          onClick={onClose}
          title="Close Panel"
          className="text-earth-secondary hover:text-earth-primary p-1 rounded hover:bg-earth-elevated transition"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="p-3.5 space-y-4 font-mono text-xs">
        {/* Sensor Telemetry Degraded Alert if missing features */}
        {village.missing_features.length > 0 && (
          <div className="p-2.5 bg-earth-warning/10 border border-earth-warning/30 rounded-lg text-earth-warning text-[10px] flex items-start gap-2 shadow-sm">
            <AlertTriangle className="w-4 h-4 text-earth-warning flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-earth-warning font-bold block">SENSOR TELEMETRY DEGRADED</strong>
              Missing inputs ({village.missing_features.join(', ')}). Model confidence reduced to {village.confidence}%.
            </div>
          </div>
        )}

        {/* LIVE ENVIRONMENT DATA SECTION (FEATURE 1) */}
        <div className="space-y-2 border-b border-earth-border/60 pb-3 font-mono">
          <div className="flex items-center justify-between text-[9px] uppercase font-extrabold tracking-wider">
            <span className="flex items-center gap-1 text-earth-cream">
              <CloudRain className="w-3.5 h-3.5 text-earth-olive" />
              LIVE ENVIRONMENT DATA
            </span>
            <button
              onClick={handleRefreshClick}
              disabled={isRefreshing}
              title="Refresh Live Data"
              className="flex items-center gap-1 text-[8px] bg-earth-elevated hover:bg-earth-border text-earth-cream border border-earth-border px-2 py-0.5 rounded transition cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3 h-3 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span>{isRefreshing ? 'REFRESHING...' : 'REFRESH LIVE DATA'}</span>
            </button>
          </div>

          {refreshMessage && (
            <div
              className={`p-1.5 rounded text-[9px] text-center font-bold border ${
                refreshMessage.success
                  ? 'bg-earth-forest/40 border-earth-safe/60 text-earth-safe'
                  : 'bg-earth-critical/20 border-earth-critical/60 text-earth-critical'
              }`}
            >
              {refreshMessage.text}
            </div>
          )}

          <div className="bg-earth-bg/95 border border-earth-border rounded-lg p-2.5 space-y-2 shadow-sm">
            {/* Data Source & Status */}
            <div className="flex items-center justify-between border-b border-earth-border/50 pb-1.5 text-[10px]">
              <div className="flex items-center gap-1.5 truncate max-w-[200px]">
                <span className="text-earth-secondary font-bold">SOURCE:</span>
                <span className="text-earth-primary font-extrabold truncate">{liveStatus.source}</span>
              </div>
              <span className={`text-[8px] font-extrabold px-1.5 py-0.5 rounded border uppercase flex-shrink-0 ${liveStatus.colorClass}`}>
                {liveStatus.status}
              </span>
            </div>

            {/* Fallback warning if live unavailable */}
            {!liveStatus.isLive && (
              <div className="p-1.5 bg-earth-warning/10 border border-earth-warning/30 rounded text-[9px] text-earth-warning text-center font-bold">
                LIVE DATA UNAVAILABLE — Using fallback/demo data
              </div>
            )}

            {/* Live Environment Metrics Display (Feature 1 & 2) */}
            <div className="grid grid-cols-3 gap-1.5 text-[10px]">
              {/* Current Rainfall */}
              <div className="bg-earth-surface/90 border border-earth-olive/40 p-1.5 rounded-md space-y-0.5">
                <span className="text-[7.5px] text-earth-secondary uppercase font-bold block truncate">RAINFALL</span>
                <div className="text-sm font-extrabold text-earth-cream flex items-baseline gap-0.5">
                  <span>{currentRainfallVal !== undefined && currentRainfallVal !== null ? currentRainfallVal.toFixed(1) : '0.0'}</span>
                  <span className="text-[8px] text-earth-olive font-normal">mm/h</span>
                </div>
              </div>

              {/* Soil Moisture (Feature 2) */}
              <div className="bg-earth-surface/90 border border-earth-safe/40 p-1.5 rounded-md space-y-0.5">
                <span className="text-[7.5px] text-earth-secondary uppercase font-bold block truncate">SOIL MOISTURE</span>
                <div className="text-sm font-extrabold text-earth-safe flex items-baseline gap-0.5">
                  <span>{soilMoistureVal !== undefined && soilMoistureVal !== null ? soilMoistureVal.toFixed(1) : '0.0'}</span>
                  <span className="text-[8px] text-earth-safe font-normal">%</span>
                </div>
              </div>

              {/* 24h Forecast */}
              <div className="bg-earth-surface/90 border border-earth-border p-1.5 rounded-md space-y-0.5">
                <span className="text-[7.5px] text-earth-secondary uppercase font-bold block truncate">24H FORECAST</span>
                <div className="text-sm font-extrabold text-earth-primary flex items-baseline gap-0.5">
                  <span>{forecastRainfallVal !== undefined && forecastRainfallVal !== null ? forecastRainfallVal.toFixed(1) : '0.0'}</span>
                  <span className="text-[8px] text-earth-secondary font-normal">mm</span>
                </div>
              </div>
            </div>

            {/* Last Updated Timestamp */}
            <div className="flex items-center justify-between text-[8px] text-earth-secondary border-t border-earth-border/40 pt-1.5">
              <span>LAST UPDATED:</span>
              <span className="text-earth-primary font-mono font-bold">
                {village.last_updated ? new Date(village.last_updated).toLocaleTimeString() : 'JUST NOW'}
              </span>
            </div>
          </div>

          {/* SIMULATION SCENARIO SEPARATION BOX */}
          <div className="flex items-center justify-between text-[8.5px] bg-earth-surface/60 border border-earth-border/50 px-2 py-1 rounded text-earth-secondary">
            <span>ACTIVE SIMULATION SCENARIO:</span>
            <span className="text-earth-warning font-extrabold uppercase">{village.scenario}</span>
          </div>
        </div>

        {/* SECTION 1 — RISK OVERVIEW */}
        <div className="space-y-1.5 border-b border-earth-border/60 pb-3">
          <div className="flex items-center justify-between text-[9px] text-earth-secondary uppercase font-extrabold tracking-wider">
            <span>RISK OVERVIEW</span>
            <span className="text-earth-olive font-bold">CONFIDENCE: {village.confidence}%</span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {/* Flood Risk */}
            <div
              className={`bg-earth-elevated border rounded-lg p-2.5 space-y-1 shadow-sm transition ${
                isFloodDominant ? 'border-earth-olive/80 ring-1 ring-earth-olive/30' : 'border-earth-border'
              }`}
            >
              <span className="text-[9px] text-earth-secondary uppercase font-bold tracking-wider block">
                FLOOD RISK
              </span>
              <div className="text-2xl font-extrabold tracking-tight" style={{ color: floodRiskColor }}>
                {floodRisk}%
              </div>
              <RiskBadge level={village.risk_level} className="text-[8px] px-1 py-0" />
            </div>

            {/* Landslide Risk */}
            <div
              className={`bg-earth-elevated border rounded-lg p-2.5 space-y-1 shadow-sm transition ${
                !isFloodDominant ? 'border-earth-olive/80 ring-1 ring-earth-olive/30' : 'border-earth-border'
              }`}
            >
              <span className="text-[9px] text-earth-secondary uppercase font-bold tracking-wider block">
                LANDSLIDE RISK
              </span>
              <div className="text-2xl font-extrabold tracking-tight" style={{ color: lsRiskColor }}>
                {lsRisk}%
              </div>
              {landslideDetail ? (
                <RiskBadge level={landslideDetail.risk_level} className="text-[8px] px-1 py-0" />
              ) : (
                <span className="text-[8px] text-earth-secondary uppercase">MODERATE</span>
              )}
            </div>
          </div>
        </div>

        {/* SECTION 2 — PRIMARY RISK DRIVERS */}
        <div className="space-y-2 border-b border-earth-border/60 pb-3">
          <div className="flex items-center justify-between text-[9px] text-earth-secondary uppercase font-extrabold tracking-wider">
            <span className="flex items-center gap-1.5 text-earth-primary">
              <BarChart3 className="w-3.5 h-3.5 text-earth-olive" />
              PRIMARY RISK DRIVERS
            </span>
            <span className="text-[8px] text-earth-secondary tracking-tight">CONTRIBUTING FACTORS</span>
          </div>

          {village.factors && village.factors.length > 0 ? (
            <>
              {(() => {
                const sortedFactors = [...village.factors].sort((a, b) => b.contribution_points - a.contribution_points);
                const topDrivers = sortedFactors.slice(0, 3);

                return (
                  <>
                    <div className="bg-earth-bg/95 border border-earth-border rounded-lg p-2 space-y-1 font-mono shadow-sm">
                      <span className="text-[8px] font-extrabold text-earth-olive uppercase tracking-widest block border-b border-earth-border/40 pb-0.5">
                        TOP CONTRIBUTING FACTORS
                      </span>
                      <div className="space-y-1 pt-0.5">
                        {topDrivers.map((f, idx) => {
                          const impactLevel = f.normalized_value >= 0.7 ? 'HIGH' : f.normalized_value >= 0.4 ? 'MODERATE' : 'LOW';
                          const badgeColor =
                            impactLevel === 'HIGH'
                              ? 'text-earth-critical bg-earth-critical/15 border-earth-critical/40'
                              : 'text-earth-warning bg-earth-warning/15 border-earth-warning/40';

                          return (
                            <div key={f.feature_key} className="flex items-center justify-between text-[10px]">
                              <div className="flex items-center gap-1.5 truncate max-w-[190px]">
                                <span className="text-[9px] font-bold text-earth-secondary/70">0{idx + 1}</span>
                                <span className="font-extrabold text-earth-primary truncate uppercase">{f.feature_label}</span>
                              </div>
                              <span className={`text-[8px] font-bold px-1.5 py-0.2 rounded border uppercase ${badgeColor}`}>
                                +{f.contribution_points} PTS ({impactLevel})
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    <div className="space-y-1.5 font-mono">
                      {sortedFactors.map((f, idx) => {
                        const isTopDriver = idx === 0;
                        const impactLevel = f.normalized_value >= 0.7 ? 'HIGH' : f.normalized_value >= 0.4 ? 'MODERATE' : 'LOW';
                        const impactColorClass =
                          impactLevel === 'HIGH'
                            ? 'text-earth-critical'
                            : impactLevel === 'MODERATE'
                            ? 'text-earth-warning'
                            : 'text-earth-safe';
                        const barBgClass =
                          impactLevel === 'HIGH'
                            ? 'bg-earth-critical'
                            : impactLevel === 'MODERATE'
                            ? 'bg-earth-warning'
                            : 'bg-earth-safe';

                        return (
                          <div
                            key={f.feature_key}
                            className={`bg-earth-bg/90 border p-2 rounded-lg space-y-1 shadow-sm transition-all duration-300 ${
                              isTopDriver
                                ? 'border-earth-olive/80 ring-1 ring-earth-olive/30'
                                : 'border-earth-border hover:border-earth-olive/40'
                            }`}
                          >
                            <div className="flex items-center justify-between text-[10px]">
                              <div className="flex items-center gap-1.5">
                                <span className="font-extrabold text-earth-primary uppercase">{f.feature_label}</span>
                                {f.raw_value !== undefined && f.raw_value !== null && (
                                  <span className="text-[9px] text-earth-secondary font-normal">
                                    ({f.raw_value} {f.unit})
                                  </span>
                                )}
                              </div>
                              <span className={`font-extrabold text-[9px] ${impactColorClass}`}>
                                +{f.contribution_points} PTS
                              </span>
                            </div>

                            <div className="w-full bg-earth-surface rounded-full h-1.5 overflow-hidden border border-earth-border/50">
                              <div
                                className={`h-full transition-all duration-500 rounded-full ${barBgClass}`}
                                style={{ width: `${Math.min(100, Math.max(8, f.normalized_value * 100))}%` }}
                              ></div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </>
                );
              })()}
            </>
          ) : (
            <div className="p-3 bg-earth-bg/60 border border-earth-border/60 rounded-lg text-center text-[10px] text-earth-secondary font-mono">
              RISK DRIVER DATA UNAVAILABLE
            </div>
          )}
        </div>

        {/* SECTION 2B — OFFICIAL REGIONAL WARNING (IMD / NDMA CAP) */}
        <div className="space-y-2 border-b border-earth-border/60 pb-3">
          <div className="flex items-center justify-between text-[9px] text-earth-secondary uppercase font-extrabold tracking-wider">
            <span className="flex items-center gap-1.5 text-earth-primary">
              <ShieldAlert className="w-3.5 h-3.5 text-earth-warning" />
              OFFICIAL REGIONAL WARNING
            </span>
            <span className="text-[8px] font-mono px-1.5 py-0.5 rounded border border-earth-border/80 bg-earth-elevated text-earth-cream">
              {imdData?.data_state === 'REAL_LIVE_OFFICIAL'
                ? 'REAL LIVE OFFICIAL'
                : imdData?.data_state === 'CACHED_OFFICIAL'
                ? 'CACHED OFFICIAL'
                : 'IMD FEED ACTIVE'}
            </span>
          </div>

          <div className="bg-earth-bg/95 border border-earth-border rounded-lg p-2.5 space-y-1.5 font-mono shadow-sm">
            <div className="flex items-center justify-between border-b border-earth-border/40 pb-1 text-[9px]">
              <span className="text-earth-secondary uppercase font-bold">
                SOURCE: <strong className="text-earth-primary">IMD/NDMA CAP</strong>
              </span>
              <span className="text-earth-cream uppercase font-bold">
                DISTRICT: {village.district || 'CHAMOLI'}
              </span>
            </div>

            {imdData?.has_active_warning && imdData.warnings.length > 0 ? (
              <div className="space-y-1.5">
                {imdData.warnings.slice(0, 2).map((w, idx) => (
                  <div key={idx} className="bg-earth-elevated/90 border border-earth-warning/40 rounded p-2 space-y-1">
                    <div className="flex items-center justify-between text-[9px]">
                      <span className="text-earth-warning font-extrabold uppercase">
                        {w.event || 'WEATHER WARNING'}
                      </span>
                      <span className="bg-earth-warning/20 text-earth-warning text-[8px] font-extrabold px-1 rounded border border-earth-warning/40">
                        {w.severity?.toUpperCase() || 'SEVERE'}
                      </span>
                    </div>
                    {w.headline && (
                      <p className="text-[9.5px] text-earth-primary font-sans font-medium leading-tight">
                        {w.headline}
                      </p>
                    )}
                    {w.instruction && (
                      <p className="text-[8.5px] text-earth-cream font-sans leading-tight border-t border-earth-border/30 pt-1">
                        👉 {w.instruction.slice(0, 140)}...
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-1.5 bg-earth-elevated/40 border border-earth-border/30 rounded text-center text-[8.5px] text-earth-secondary">
                NO ACTIVE IMD WARNING FOR {village.district?.toUpperCase() || 'CHAMOLI'} DISTRICT
              </div>
            )}

            <p className="text-[7.5px] text-earth-secondary font-sans leading-tight pt-0.5 border-t border-earth-border/30">
              ℹ️ Official IMD/NDMA warning at district level. APADA MITRA combines this with 30m terrain physics for village risk assessment.
            </p>
          </div>
        </div>

        {/* SECTION 3 — IMPACT ASSESSMENT */}
        <div className="space-y-1.5 border-b border-earth-border/60 pb-3">
          <div className="flex items-center justify-between text-[9px] text-earth-secondary uppercase font-extrabold tracking-wider">
            <span className="flex items-center gap-1 text-earth-primary">
              <Users className="w-3.5 h-3.5 text-earth-olive" />
              IMPACT ASSESSMENT
            </span>
            <span className="text-earth-cream font-mono text-[9px]">EXPOSURE SCORE: {village.exposure.exposure_score}/100</span>
          </div>

          <div className="grid grid-cols-2 gap-2 font-mono">
            <div className="bg-earth-bg/90 border border-earth-border p-2 rounded-lg space-y-0.5">
              <span className="text-[8px] text-earth-secondary uppercase font-bold block">POPULATION</span>
              <span className="text-sm font-extrabold text-earth-primary block">
                {village.population.toLocaleString()}
              </span>
              <span className="text-[8px] text-earth-critical font-bold block">
                EXPOSED: {village.exposure.population_exposed.toLocaleString()}
              </span>
            </div>

            <div className="bg-earth-bg/90 border border-earth-border p-2 rounded-lg space-y-0.5">
              <span className="text-[8px] text-earth-secondary uppercase font-bold block">CRITICAL INFRASTRUCTURE</span>
              <span className="text-sm font-extrabold text-earth-warning block">
                {village.exposure.infrastructure.bridges_and_roads} LOCATIONS
              </span>
              <span className="text-[8px] text-earth-secondary block">ROADS & BRIDGES AT RISK</span>
            </div>
          </div>
        </div>

        {/* SECTION 4 — EVACUATION PRIORITY */}
        <div className="space-y-1.5 border-b border-earth-border/60 pb-3">
          <div className="flex items-center justify-between text-[9px] text-earth-secondary uppercase font-extrabold tracking-wider">
            <span className="flex items-center gap-1 text-earth-primary">
              <Zap className="w-3.5 h-3.5 text-earth-warning" />
              EVACUATION PRIORITY
            </span>
            {priorityDetail && (
              <span className="bg-earth-olive text-black font-extrabold text-[9px] px-1.5 py-0.5 rounded shadow">
                RANK #{priorityDetail.rank} / 15
              </span>
            )}
          </div>

          {priorityDetail ? (
            <div className="bg-earth-bg/90 border border-earth-border rounded-lg p-2.5 space-y-1.5 shadow-sm">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-earth-secondary text-[10px] uppercase font-bold">PRIORITY SCORE:</span>
                <span className="text-earth-warning font-extrabold text-sm">{priorityDetail.evacuation_priority_score} / 100 PTS</span>
              </div>

              <div className="text-[10px] text-earth-cream font-sans leading-tight bg-earth-surface p-2 rounded border border-earth-border font-mono">
                <strong className="block text-earth-warning uppercase text-[9px] mb-0.5">Urgency Reason:</strong>
                {priorityDetail.primary_urgency_reason}
              </div>
            </div>
          ) : (
            <div className="bg-earth-bg/60 p-2 rounded text-[10px] text-earth-secondary">
              Evacuation priority score calculating...
            </div>
          )}
        </div>

        {/* SECTION 5 — RECOMMENDED ACTION */}
        <div className="space-y-1.5 border-b border-earth-border/60 pb-3">
          <div className="text-[9px] text-earth-secondary uppercase font-extrabold tracking-wider">
            RECOMMENDED ACTION
          </div>

          <div
            className={`p-2.5 rounded-lg border text-xs font-mono font-extrabold text-center uppercase tracking-wider shadow-md ${getDecisionBadgeClasses(
              village.decision_status
            )}`}
          >
            {getDecisionStatusLabel(village.decision_status)}
          </div>
        </div>

        {/* SECTION 6 — SAFEST ROUTE */}
        <div className="space-y-2 border-b border-earth-border/60 pb-3">
          <div className="flex items-center justify-between text-[9px] text-earth-secondary uppercase font-extrabold tracking-wider">
            <span className="flex items-center gap-1.5 text-earth-primary">
              <Navigation className="w-3.5 h-3.5 text-earth-olive" />
              SAFEST ROUTE
            </span>
            {routeLoading ? (
              <span className="bg-earth-olive/20 text-earth-cream text-[8px] font-bold px-1.5 py-0.5 rounded border border-earth-olive/40 animate-pulse">
                COMPUTING...
              </span>
            ) : shelterRecommendation ? (
              <span className="bg-earth-safe/20 text-earth-safe text-[8px] font-bold px-1.5 py-0.5 rounded border border-earth-safe/40">
                ACTIVE
              </span>
            ) : (
              <span className="bg-earth-warning/20 text-earth-warning text-[8px] font-bold px-1.5 py-0.5 rounded border border-earth-warning/40">
                NOT CALCULATED
              </span>
            )}
          </div>

          {!shelterRecommendation ? (
            <div className="bg-earth-bg/90 border border-earth-border rounded-lg p-3 space-y-2 text-center">
              <p className="text-[10px] text-earth-secondary leading-relaxed font-sans">
                Hazard-aware Dijkstra router computes safest evacuation path avoiding blocked mountain roads.
              </p>
              <button
                disabled={routeLoading}
                onClick={onCalculateRoute}
                className="w-full bg-earth-olive hover:bg-earth-olive/90 text-black font-extrabold text-xs py-2 rounded-lg transition flex items-center justify-center gap-2 shadow-md uppercase tracking-wider font-mono cursor-pointer disabled:opacity-50"
              >
                <Navigation className="w-3.5 h-3.5" />
                {routeLoading ? 'COMPUTING SAFEST ROUTE...' : 'CALCULATE SAFEST ROUTE'}
              </button>
            </div>
          ) : (
            <div className="space-y-2 font-mono text-[11px]">
              <div className="bg-earth-elevated border border-earth-safe/60 rounded-lg p-2.5 space-y-2 shadow-md">
                <div className="flex items-center justify-between border-b border-earth-border pb-1.5">
                  <span className="text-[10px] font-extrabold text-earth-safe uppercase flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-earth-safe" />
                    RECOMMENDED SAFEST PATH
                  </span>
                  <span className="bg-earth-safe/20 text-earth-safe text-[9px] font-extrabold px-1.5 py-0.5 rounded border border-earth-safe/40">
                    SAFETY: {route?.route_safety_score}%
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-1.5 text-[10px] bg-earth-bg/90 p-2 rounded border border-earth-border">
                  <div>DISTANCE: <strong className="text-earth-primary font-extrabold">{route?.total_distance_km} km</strong></div>
                  <div>ETA: <strong className="text-earth-primary font-extrabold">{route?.estimated_travel_time_mins} mins</strong></div>
                </div>

                <div className="text-[8px] text-earth-secondary space-y-0.5 pt-1 border-t border-earth-border/40 uppercase">
                  <div className="flex items-center gap-1 text-earth-safe font-bold">
                    <span>✓ HAZARDOUS ROADS AVOIDED</span>
                  </div>
                </div>
              </div>

              {/* REJECTED SHORTEST ROUTE CARD */}
              <div className="bg-earth-critical/15 border border-earth-critical/50 rounded-lg p-2 space-y-1 shadow-sm">
                <div className="flex items-center justify-between border-b border-earth-critical/40 pb-0.5">
                  <span className="text-[9.5px] font-extrabold text-earth-critical uppercase flex items-center gap-1">
                    <XCircle className="w-3.5 h-3.5 text-earth-critical" />
                    REJECTED SHORTEST ROUTE
                  </span>
                  <span className="bg-earth-critical/20 text-earth-critical text-[8px] font-bold px-1 py-0.2 rounded border border-earth-critical/40">
                    BLOCKED
                  </span>
                </div>
                <div className="text-[8.5px] text-earth-cream font-mono">
                  SHORTEST ROUTE AVOIDED DUE TO ROAD BLOCKAGE
                </div>
              </div>
            </div>
          )}
        </div>

        {/* SECTION 7 — RECOMMENDED SHELTER */}
        <div className="space-y-2 border-b border-earth-border/60 pb-3">
          <div className="flex items-center justify-between text-[9px] text-earth-secondary uppercase font-extrabold tracking-wider">
            <span className="flex items-center gap-1.5 text-earth-primary">
              <Building2 className="w-3.5 h-3.5 text-earth-olive" />
              RECOMMENDED SHELTER
            </span>
            {recShelter && (
              <span className={`text-[8px] font-extrabold px-1.5 py-0.5 rounded border uppercase ${isOverflow ? 'bg-earth-critical/25 border-earth-critical text-earth-critical' : 'bg-earth-forest/40 border-earth-safe text-earth-safe'}`}>
                {isOverflow ? 'OVERFLOW' : 'AVAILABLE'}
              </span>
            )}
          </div>

          {!recShelter ? (
            <div className="bg-earth-bg/60 p-2.5 rounded-lg text-center text-[10px] text-earth-secondary font-mono border border-earth-border">
              Calculate route to view recommended relief shelter capacity.
            </div>
          ) : (
            <div className="space-y-2 font-mono text-[11px]">
              <div className="bg-earth-elevated border border-earth-border rounded-lg p-2.5 space-y-2 shadow-md">
                <div className="flex items-center justify-between border-b border-earth-border/50 pb-1">
                  <span className="text-[11px] font-extrabold text-earth-primary uppercase truncate max-w-[190px]">
                    {recShelter.name} ({recShelter.elevation}m)
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-1.5 text-[10px] bg-earth-bg/90 p-2 rounded border border-earth-border">
                  <div>CAPACITY: <strong className="text-earth-primary font-extrabold">{totalCapacity} beds</strong></div>
                  <div>OCCUPIED: <strong className="text-earth-primary font-extrabold">{occupiedCapacity} beds</strong></div>
                  <div>AVAILABLE: <strong className="text-earth-safe font-extrabold">{availCapacity} beds</strong></div>
                  <div>DEMAND: <strong className="text-earth-warning font-extrabold">+{village.exposure.population_exposed} residents</strong></div>
                </div>

                <div className="space-y-1 pt-0.5">
                  <div className="flex justify-between text-[8px] text-earth-secondary uppercase">
                    <span>UTILIZATION</span>
                    <span className={isOverflow ? 'text-earth-critical font-bold' : 'text-earth-safe font-bold'}>
                      {Math.round((occupiedCapacity / totalCapacity) * 100)}%
                    </span>
                  </div>
                  <div className="w-full bg-earth-surface rounded-full h-2 overflow-hidden border border-earth-border/60">
                    <div
                      className={`h-full transition-all duration-500 rounded-full ${
                        isOverflow
                          ? 'bg-earth-critical'
                          : occupiedCapacity / totalCapacity > 0.8
                          ? 'bg-earth-warning'
                          : 'bg-earth-safe'
                      }`}
                      style={{ width: `${Math.min(100, Math.max(10, (occupiedCapacity / totalCapacity) * 100))}%` }}
                    ></div>
                  </div>
                </div>

                {isOverflow ? (
                  <div className="p-1.5 bg-earth-critical/20 border border-earth-critical/60 rounded text-[8.5px] text-earth-cream font-mono font-bold">
                    ⚠️ OVERFLOW SHORTFALL: +{projectedOccupancy - totalCapacity} RESIDENTS EXCEED AVAILABLE BEDS
                  </div>
                ) : (
                  <div className="p-1.5 bg-earth-forest/30 border border-earth-safe/40 rounded text-[8.5px] text-earth-safe font-mono">
                    ✓ CAPACITY SUFFICIENT: {availCapacity} BEDS AVAILABLE
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* SECTION 8 — EMERGENCY SMS */}
        <div className="space-y-1.5 pt-1">
          <div className="text-[9px] text-earth-secondary uppercase font-extrabold tracking-wider">
            EMERGENCY SMS
          </div>

          {onOpenSmsModal && (
            <button
              onClick={onOpenSmsModal}
              className="w-full bg-earth-olive hover:bg-earth-olive/90 text-black font-extrabold text-xs py-2.5 rounded-lg transition flex items-center justify-center gap-2 shadow-md uppercase tracking-wider font-mono cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              <span>DISPATCH EMERGENCY SMS (SIMULATION)</span>
            </button>
          )}
        </div>

        {/* Footer Data Provenance */}
        <div className="pt-2 border-t border-earth-border/60 font-mono text-[9px]">
          <div className="flex items-center justify-between text-earth-secondary uppercase font-bold text-[8px] tracking-wider mb-0.5">
            <span>DATA PROVENANCE</span>
            <span className="text-earth-cream font-bold">SYNTHETIC WATERSHED</span>
          </div>
          <p className="text-[8px] text-earth-secondary font-sans text-center leading-tight">
            Real-time multi-hazard exposure & Dijkstra router simulation connected to active backend APIs.
          </p>
        </div>
      </div>
    </aside>
  );
};

