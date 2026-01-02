/**
 * Enterprise Header Component
 * Unified top header for all dashboards
 */

import React from 'react';
import './EnterpriseHeader.css';

const EnterpriseHeader = ({ pageTitle, user, actions }) => {
  return (
    <header className="eds-header">
      <div className="eds-header-content">
        <div className="eds-header-left">
          <h1 className="eds-header-title">{pageTitle}</h1>
        </div>
        <div className="eds-header-right">
          {actions && actions.map((action, index) => (
            <button
              key={index}
              className={`eds-button ${action.variant || 'eds-button-secondary'}`}
              onClick={action.onClick}
              disabled={action.disabled}
            >
              {action.label}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
};

export default EnterpriseHeader;

