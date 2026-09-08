import React from 'react';
import { RiskLevel } from '../types';
import { getRiskBadgeClasses } from '../utils/riskColors';

interface Props {
  level: RiskLevel;
  className?: string;
}

export const RiskBadge: React.FC<Props> = ({ level, className = '' }) => {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-semibold uppercase tracking-wider border ${getRiskBadgeClasses(
        level
      )} ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
      {level}
    </span>
  );
};
