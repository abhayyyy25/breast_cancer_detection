/**
 * Enterprise Metric Tile Component
 * Compact metric display (not colorful cards)
 */

import React from 'react';
import './EnterpriseMetricTile.css';

const EnterpriseMetricTile = ({ label, value, subtitle, trend }) => {
  return (
    <div className="eds-metric-tile">
      <div className="eds-metric-label">{label}</div>
      <div className="eds-metric-value">
        {value}
        {trend && (
          <span className={`eds-metric-trend ${trend.direction}`}>
            {trend.direction === 'up' ? '↑' : '↓'} {trend.value}
          </span>
        )}
      </div>
      {subtitle && <div className="eds-metric-subtitle">{subtitle}</div>}
    </div>
  );
};

export default EnterpriseMetricTile;

