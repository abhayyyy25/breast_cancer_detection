/**
 * Enterprise Layout Component
 * Unified layout structure for all dashboards
 */

import React from 'react';
import EnterpriseSidebar from './EnterpriseSidebar';
import EnterpriseHeader from './EnterpriseHeader';
import './EnterpriseLayout.css';

const EnterpriseLayout = ({ children, user, pageTitle, navigationItems }) => {
  return (
    <div className="eds-layout">
      <EnterpriseSidebar user={user} navigationItems={navigationItems} />
      <div className="eds-layout-main">
        <EnterpriseHeader pageTitle={pageTitle} user={user} />
        <main className="eds-layout-content">
          <div className="eds-layout-content-inner">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default EnterpriseLayout;

