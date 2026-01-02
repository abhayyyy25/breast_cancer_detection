/**
 * Enterprise Sidebar Component
 * Unified sidebar navigation for all roles
 */

import React from 'react';
import { useAuth } from '../../context/AuthContext';
import './EnterpriseSidebar.css';

const EnterpriseSidebar = ({ user, navigationItems }) => {
  const { logout } = useAuth();

  const getRoleDisplay = (role) => {
    const roleMap = {
      'super_admin': 'Super Admin',
      'organization_admin': 'Admin',
      'doctor': 'Doctor',
      'lab_tech': 'Lab Tech',
      'patient': 'Patient'
    };
    return roleMap[role] || role;
  };

  return (
    <aside className="eds-sidebar">
      <div className="eds-sidebar-header">
        <div className="eds-sidebar-brand">
          <div className="eds-sidebar-brand-text">
            Breast Cancer Detection
          </div>
          <div className="eds-sidebar-brand-version">Enterprise v2.0</div>
        </div>
      </div>

      <nav className="eds-sidebar-nav">
        {navigationItems && navigationItems.map((item) => (
          <button
            key={item.id}
            className={`eds-sidebar-nav-item ${item.active ? 'active' : ''}`}
            onClick={item.onClick}
            disabled={item.disabled}
          >
            <span className="eds-sidebar-nav-icon">{item.icon}</span>
            <span className="eds-sidebar-nav-label">{item.label}</span>
            {item.badge && (
              <span className="eds-sidebar-nav-badge">{item.badge}</span>
            )}
          </button>
        ))}
      </nav>

      <div className="eds-sidebar-footer">
        <div className="eds-sidebar-user">
          <div className="eds-sidebar-user-avatar">
            {user?.full_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
          </div>
          <div className="eds-sidebar-user-info">
            <div className="eds-sidebar-user-name">
              {user?.full_name || user?.email || 'User'}
            </div>
            <div className="eds-sidebar-user-role">
              {getRoleDisplay(user?.role)}
            </div>
          </div>
        </div>
        <button className="eds-sidebar-logout" onClick={logout}>
          Logout
        </button>
      </div>
    </aside>
  );
};

export default EnterpriseSidebar;

