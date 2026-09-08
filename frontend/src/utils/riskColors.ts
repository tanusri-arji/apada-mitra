import { RiskLevel, DecisionStatus } from '../types';

export function getRiskColorHex(level: RiskLevel): string {
  switch (level) {
    case 'CRITICAL':
      return '#EF4444'; // Red
    case 'HIGH':
      return '#F97316'; // Orange
    case 'MODERATE':
      return '#F59E0B'; // Amber / Gold
    case 'LOW':
      return '#10B981'; // Emerald Green / Safe
    default:
      return '#9CA3AF'; // Muted Gray
  }
}

export function getRiskEmoji(level: RiskLevel): string {
  switch (level) {
    case 'CRITICAL':
      return '🔴';
    case 'HIGH':
      return '🟠';
    case 'MODERATE':
      return '🟡';
    case 'LOW':
      return '🟢';
    default:
      return '⚪';
  }
}

export function getRiskBadgeClasses(level: RiskLevel): string {
  switch (level) {
    case 'CRITICAL':
      return 'bg-red-500/20 text-red-400 border-red-500/40 font-black shadow-sm shadow-red-950/50';
    case 'HIGH':
      return 'bg-orange-500/20 text-orange-400 border-orange-500/40 font-bold';
    case 'MODERATE':
      return 'bg-amber-500/20 text-amber-400 border-amber-500/40 font-bold';
    case 'LOW':
      return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40 font-bold';
    default:
      return 'bg-gray-500/20 text-gray-400 border-gray-500/40';
  }
}

export function getDecisionBadgeClasses(status: DecisionStatus): string {
  switch (status) {
    case 'EVACUATION_READINESS':
      return 'bg-red-950/80 text-red-300 border-red-500/80 animate-pulse shadow-lg font-black';
    case 'PREPARE':
      return 'bg-amber-950/80 text-amber-300 border-amber-500/80 font-bold';
    case 'MONITOR':
      return 'bg-emerald-950/80 text-emerald-300 border-emerald-500/80 font-bold';
    default:
      return 'bg-[#14181D] text-gray-300 border-white/10';
  }
}

export function getDecisionStatusLabel(status: DecisionStatus): string {
  switch (status) {
    case 'EVACUATION_READINESS':
      return 'IMMEDIATE EVACUATION PREPARATION';
    case 'PREPARE':
      return 'PREPARE & STANDBY FOR EVACUATION';
    case 'MONITOR':
      return 'ROUTINE DISASTER MONITORING';
    default:
      return status;
  }
}
