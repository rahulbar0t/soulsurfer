import { Warning, Info, WarningCircle } from '@phosphor-icons/react';
import './SeverityBadge.css';

const SEVERITY_CONFIG = {
  low: {
    icon: Info,
    label: 'Low',
  },
  medium: {
    icon: Warning,
    label: 'Medium',
  },
  high: {
    icon: WarningCircle,
    label: 'High',
  },
};

export default function SeverityBadge({ severity }) {
  const config = SEVERITY_CONFIG[severity] || SEVERITY_CONFIG.low;
  const Icon = config.icon;

  return (
    <span className={`severity-badge severity-badge--${severity}`}>
      <Icon weight="fill" size={12} />
      {config.label}
    </span>
  );
}
