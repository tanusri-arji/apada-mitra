import { RiskLevel, DecisionStatus } from '../types';

export function getRiskColorHex(level: RiskLevel): string {
  switch (level) {
    case 'CRITICAL':
      return '#EF4444'; // Red
    case 'HIGH':
      return '#F97316'; // Orange
    case 'MODERATE':
      return '#F59E0B'; // Amber
    case 'LOW':
      return '#10B981'; // Green
    default:
      return '#6B7280';
  }
}

export function getRiskBadgeClasses(level: RiskLevel): string {
  switch (level) {
    case 'CRITICAL':
      return 'bg-red-500/20 text-red-400 border-red-500/40';
    case 'HIGH':
      return 'bg-orange-500/20 text-orange-400 border-orange-500/40';
    case 'MODERATE':
      return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
    case 'LOW':
      return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
    default:
      return 'bg-gray-500/20 text-gray-400 border-gray-500/40';
  }
}

export function getDecisionBadgeClasses(status: DecisionStatus): string {
  switch (status) {
    case 'EVACUATION_READINESS':
      return 'bg-red-950/60 text-red-300 border-red-600/60 animate-pulse';
    case 'PREPARE':
      return 'bg-amber-950/60 text-amber-300 border-amber-600/60';
    case 'MONITOR':
      return 'bg-emerald-950/60 text-emerald-300 border-emerald-600/60';
    default:
      return 'bg-gray-800 text-gray-300 border-gray-700';
  }
}

export function getDecisionStatusLabel(status: DecisionStatus): string {
  switch (status) {
    case 'EVACUATION_READINESS':
      return 'EVACUATION READINESS';
    case 'PREPARE':
      return 'PREPARE & STANDBY';
    case 'MONITOR':
      return 'ROUTINE MONITORING';
    default:
      return status;
  }
}
