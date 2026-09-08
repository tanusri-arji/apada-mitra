import React from 'react';
import { RiskLevel } from '../types';
import { getRiskBadgeClasses, getRiskEmoji } from '../utils/riskColors';

interface Props {
  level: RiskLevel;
  className?: string;
  showEmoji?: boolean;
}

export const RiskBadge: React.FC<Props> = ({ level, className = '', showEmoji = true }) => {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs tracking-wider border font-mono ${getRiskBadgeClasses(
        level
      )} ${className}`}
    >
      {showEmoji && <span className="text-[10px] leading-none">{getRiskEmoji(level)}</span>}
      <span>{level}</span>
    </span>
  );
};
