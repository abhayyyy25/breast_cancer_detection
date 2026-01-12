/**
 * Super Admin Dashboard - FULLY FUNCTIONAL
 * Global platform management with Organizations and Analytics views
 * Refactored with view switching and API integration
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getAdminStats, getAllTenants, createTenant, updateTenantStatus } from '../config/api';
import EnterpriseLayout from './common/EnterpriseLayout';
import EnterpriseTable from './common/EnterpriseTable';
import EnterpriseMetricTile from './common/EnterpriseMetricTile';
import LoadingSpinner from './LoadingSpinner';
import '../styles/enterpriseDesignSystem.css';
import './SuperAdminDashboard.css';

const SuperAdminDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  // State for view management
  const [currentView, setCurrentView] = useState('dashboard');
  
  // Data states
  const [stats, setStats] = useState(null);
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Modal states
  const [showOnboardModal, setShowOnboardModal] = useState(false);
  const [onboardData, setOnboardData] = useState({
    name: '',
    email: '',
    password: '',
    location: '',
    plan_type: 'trial'
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsData, tenantsData] = await Promise.all([
        getAdminStats(),
        getAllTenants()
      ]);
      setStats(statsData);
      setTenants(tenantsData);
    } catch (error) {
      console.error('Error fetching data:', error);
      alert('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleOnboardOrganization = async (e) => {
    e.preventDefault();
    
    if (onboardData.password.length < 6) {
      alert('Password must be at least 6 characters');
      return;
    }

    try {
      await createTenant(onboardData);
      alert('Organization onboarded successfully!');
      setShowOnboardModal(false);
      setOnboardData({
        name: '',
        email: '',
        password: '',
        location: '',
        plan_type: 'trial'
      });
      fetchData();
    } catch (error) {
      console.error('Error onboarding:', error);
      alert('Failed to onboard organization: ' + error.message);
    }
  };

  const handleToggleStatus = async (tenantId, currentStatus) => {
    const newStatus = currentStatus === 'active' ? 'suspended' : 'active';
    
    if (!window.confirm(`Are you sure you want to ${newStatus === 'suspended' ? 'suspend' : 'activate'} this organization?`)) {
      return;
    }

    try {
      await updateTenantStatus(tenantId, newStatus);
      alert(`Organization ${newStatus === 'suspended' ? 'suspended' : 'activated'} successfully`);
      fetchData();
    } catch (error) {
      console.error('Error updating status:', error);
      alert('Failed to update status: ' + error.message);
    }
  };

  // Navigation items with click handlers
  const navigationItems = [
    { 
      id: 'dashboard', 
      label: 'Dashboard', 
      icon: '📊', 
      active: currentView === 'dashboard',
      onClick: () => setCurrentView('dashboard')
    },
    { 
      id: 'organizations', 
      label: 'Organizations', 
      icon: '🏥', 
      active: currentView === 'organizations',
      onClick: () => setCurrentView('organizations')
    },
    { 
      id: 'analytics', 
      label: 'Analytics', 
      icon: '📈', 
      active: currentView === 'analytics',
      onClick: () => setCurrentView('analytics')
    },
  ];

  // Table columns for organizations
  const tenantColumns = [
    {
      header: 'Organization',
      accessor: 'name',
      render: (row) => (
        <div>
          <div style={{ fontWeight: 500, color: 'var(--eds-color-text-primary)' }}>
            {row.name}
          </div>
          <div className="eds-text-small" style={{ marginTop: '4px' }}>
            {row.organization_type?.replace('_', ' ') || 'Hospital'}
          </div>
        </div>
      ),
    },
    {
      header: 'Status',
      accessor: 'subscription_status',
      width: '120px',
      render: (row) => {
        const statusMap = {
          'active': 'success',
          'trial': 'warning',
          'suspended': 'error'
        };
        return (
          <span className={`eds-badge eds-badge-${statusMap[row.subscription_status] || 'neutral'}`}>
            {row.subscription_status}
          </span>
        );
      },
    },
    {
      header: 'Usage',
      accessor: 'current_month_scans',
      width: '140px',
      render: (row) => (
        <div className="eds-text-mono">
          {row.current_month_scans || 0} / {row.monthly_scan_limit || 100}
        </div>
      ),
    },
    {
      header: 'Total Scans',
      accessor: 'total_scans_processed',
      width: '120px',
      render: (row) => (
        <div className="eds-text-mono">{row.total_scans_processed || 0}</div>
      ),
    },
    {
      header: 'Location',
      accessor: 'city',
      width: '180px',
      render: (row) => (
        <div className="eds-text-small">
          {row.city || 'N/A'}, {row.state || 'N/A'}
        </div>
      ),
    },
    {
      header: 'Contact',
      accessor: 'contact_email',
      render: (row) => (
        <div className="eds-text-small">
          {row.contact_email}
        </div>
      ),
    },
    {
      header: 'Actions',
      accessor: 'id',
      width: '200px',
      render: (row) => (
        <div style={{ display: 'flex', gap: 'var(--eds-space-2)' }}>
          <button
            className="eds-button eds-button-sm eds-button-secondary"
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/superadmin/organization/${row.id}`);
            }}
          >
            View
          </button>
          <button
            className={`eds-button eds-button-sm ${row.subscription_status === 'active' ? 'eds-button-danger' : 'eds-button-primary'}`}
            onClick={(e) => {
              e.stopPropagation();
              handleToggleStatus(row.id, row.subscription_status);
            }}
          >
            {row.subscription_status === 'active' ? 'Suspend' : 'Activate'}
          </button>
        </div>
      ),
    },
  ];

  if (loading) {
    return <LoadingSpinner message="Loading Super Admin Dashboard..." />;
  }

  // ============================================================================
  // DASHBOARD VIEW
  // ============================================================================
  const renderDashboardView = () => (
    <>
      {/* Metrics */}
      {stats && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 'var(--eds-space-4)',
          marginBottom: 'var(--eds-space-8)'
        }}>
          <EnterpriseMetricTile
            label="Total Organizations"
            value={stats.total_tenants}
            subtitle={`${stats.active_tenants_count} active`}
          />
          <EnterpriseMetricTile
            label="Total Users"
            value={stats.total_users}
            subtitle="Across all tenants"
          />
          <EnterpriseMetricTile
            label="Total Scans"
            value={stats.total_scans}
            subtitle="Platform-wide"
          />
          <EnterpriseMetricTile
            label="Active Tenants"
            value={stats.active_tenants_count}
            subtitle="Currently active"
          />
        </div>
      )}

      {/* Recent Organizations */}
      <div className="eds-card">
        <div className="eds-card-header">
          <h3 className="eds-card-title">Recent Organizations</h3>
        </div>
        <div style={{ marginTop: 'var(--eds-space-4)' }}>
          <EnterpriseTable
            columns={tenantColumns}
            data={tenants.slice(0, 5)}
            emptyMessage="No organizations found"
          />
        </div>
      </div>
    </>
  );

  // ============================================================================
  // ORGANIZATIONS VIEW
  // ============================================================================
  const renderOrganizationsView = () => (
    <div className="eds-card">
      <div className="eds-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 className="eds-card-title">All Organizations</h3>
        <button
          className="eds-button eds-button-primary"
          onClick={() => setShowOnboardModal(true)}
        >
          ➕ Onboard Organization
        </button>
      </div>
      <div style={{ marginTop: 'var(--eds-space-4)' }}>
        <EnterpriseTable
          columns={tenantColumns}
          data={tenants}
          emptyMessage="No organizations found. Click 'Onboard Organization' to add one."
        />
      </div>
    </div>
  );

  // ============================================================================
  // ANALYTICS VIEW
  // ============================================================================
  const renderAnalyticsView = () => (
    <>
      {/* Summary Cards */}
      {stats && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 'var(--eds-space-4)',
          marginBottom: 'var(--eds-space-8)'
        }}>
          <EnterpriseMetricTile
            label="Total Tenants"
            value={stats.total_tenants}
            subtitle="All organizations"
          />
          <EnterpriseMetricTile
            label="Total Scans"
            value={stats.total_scans}
            subtitle="Platform-wide"
          />
          <EnterpriseMetricTile
            label="Active Tenants"
            value={stats.active_tenants_count}
            subtitle="Currently active"
          />
          <EnterpriseMetricTile
            label="Total Users"
            value={stats.total_users}
            subtitle="All roles"
          />
        </div>
      )}

      {/* Charts Section */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--eds-space-6)', marginBottom: 'var(--eds-space-6)' }}>
        {/* Scans per Month Chart */}
        <div className="eds-card">
          <div className="eds-card-header">
            <h3 className="eds-card-title">📈 Scans Per Month (Last 6 Months)</h3>
          </div>
          <div style={{ padding: 'var(--eds-space-6)' }}>
            {stats && stats.monthly_scans && stats.monthly_scans.length > 0 ? (
              <div style={{ width: '100%' }}>
                {stats.monthly_scans.map((item, index) => (
                  <div key={index} style={{ marginBottom: 'var(--eds-space-3)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--eds-space-1)' }}>
                      <span className="eds-text-small">{item.month}</span>
                      <span className="eds-text-small" style={{ fontWeight: 600 }}>{item.scans} scans</span>
                    </div>
                    <div style={{ 
                      width: '100%', 
                      height: '8px', 
                      background: 'var(--eds-color-border)', 
                      borderRadius: '4px',
                      overflow: 'hidden'
                    }}>
                      <div style={{ 
                        width: `${Math.min((item.scans / 250) * 100, 100)}%`, 
                        height: '100%', 
                        background: 'var(--eds-color-primary)',
                        transition: 'width 0.3s ease'
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="eds-text-muted">No scan data available</p>
            )}
          </div>
        </div>

        {/* Prediction Distribution Chart */}
        <div className="eds-card">
          <div className="eds-card-header">
            <h3 className="eds-card-title">🎯 Prediction Distribution</h3>
          </div>
          <div style={{ padding: 'var(--eds-space-6)' }}>
            {stats && stats.prediction_distribution ? (
              <div style={{ width: '100%' }}>
                {stats.prediction_distribution.map((item, index) => {
                  const total = stats.prediction_distribution.reduce((sum, d) => sum + d.value, 0);
                  const percentage = total > 0 ? ((item.value / total) * 100).toFixed(1) : 0;
                  const color = item.label === 'Benign' ? '#10b981' : '#ef4444';
                  
                  return (
                    <div key={index} style={{ marginBottom: 'var(--eds-space-4)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--eds-space-1)' }}>
                        <span className="eds-text-small">{item.label}</span>
                        <span className="eds-text-small" style={{ fontWeight: 600 }}>{item.value} ({percentage}%)</span>
                      </div>
                      <div style={{ 
                        width: '100%', 
                        height: '12px', 
                        background: 'var(--eds-color-border)', 
                        borderRadius: '6px',
                        overflow: 'hidden'
                      }}>
                        <div style={{ 
                          width: `${percentage}%`, 
                          height: '100%', 
                          background: color,
                          transition: 'width 0.3s ease'
                        }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="eds-text-muted">No prediction data available</p>
            )}
          </div>
        </div>
      </div>

      {/* Platform Health */}
      <div className="eds-card">
        <div className="eds-card-header">
          <h3 className="eds-card-title">🏥 Platform Health Overview</h3>
        </div>
        <div style={{ padding: 'var(--eds-space-6)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--eds-space-6)' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '48px', marginBottom: 'var(--eds-space-2)' }}>✅</div>
              <div style={{ fontSize: 'var(--eds-font-size-2xl)', fontWeight: 700, color: 'var(--eds-color-success)' }}>
                {stats?.active_tenants_count || 0}
              </div>
              <div className="eds-text-small" style={{ marginTop: 'var(--eds-space-1)' }}>Active Organizations</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '48px', marginBottom: 'var(--eds-space-2)' }}>⏳</div>
              <div style={{ fontSize: 'var(--eds-font-size-2xl)', fontWeight: 700, color: 'var(--eds-color-warning)' }}>
                {tenants.filter(t => t.subscription_status === 'trial').length}
              </div>
              <div className="eds-text-small" style={{ marginTop: 'var(--eds-space-1)' }}>Trial Organizations</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '48px', marginBottom: 'var(--eds-space-2)' }}>⛔</div>
              <div style={{ fontSize: 'var(--eds-font-size-2xl)', fontWeight: 700, color: 'var(--eds-color-error)' }}>
                {tenants.filter(t => t.subscription_status === 'suspended').length}
              </div>
              <div className="eds-text-small" style={{ marginTop: 'var(--eds-space-1)' }}>Suspended</div>
            </div>
          </div>
        </div>
      </div>
    </>
  );

  // ============================================================================
  // ONBOARD MODAL
  // ============================================================================
  const renderOnboardModal = () => (
    <div className="eds-modal-overlay" onClick={() => setShowOnboardModal(false)}>
      <div className="eds-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '500px' }}>
        <div className="eds-modal-header">
          <h2 className="eds-modal-title">Onboard New Organization</h2>
          <button
            className="eds-modal-close"
            onClick={() => setShowOnboardModal(false)}
          >
            ×
          </button>
        </div>

        <form onSubmit={handleOnboardOrganization}>
          <div className="eds-modal-body">
            <div className="eds-form-group">
              <label className="eds-form-label">Organization Name *</label>
              <input
                className="eds-form-input"
                type="text"
                value={onboardData.name}
                onChange={(e) => setOnboardData({ ...onboardData, name: e.target.value })}
                placeholder="e.g., Apollo Hospitals"
                required
              />
            </div>

            <div className="eds-form-group">
              <label className="eds-form-label">Admin Email *</label>
              <input
                className="eds-form-input"
                type="email"
                value={onboardData.email}
                onChange={(e) => setOnboardData({ ...onboardData, email: e.target.value })}
                placeholder="admin@hospital.com"
                required
              />
            </div>

            <div className="eds-form-group">
              <label className="eds-form-label">Admin Password *</label>
              <input
                className="eds-form-input"
                type="password"
                value={onboardData.password}
                onChange={(e) => setOnboardData({ ...onboardData, password: e.target.value })}
                placeholder="Min 6 characters"
                minLength={6}
                required
              />
              <span className="eds-form-hint">Minimum 6 characters</span>
            </div>

            <div className="eds-form-group">
              <label className="eds-form-label">Location *</label>
              <input
                className="eds-form-input"
                type="text"
                value={onboardData.location}
                onChange={(e) => setOnboardData({ ...onboardData, location: e.target.value })}
                placeholder="City, State"
                required
              />
              <span className="eds-form-hint">Format: City, State (e.g., Mumbai, Maharashtra)</span>
            </div>

            <div className="eds-form-group">
              <label className="eds-form-label">Plan Type *</label>
              <select
                className="eds-form-select"
                value={onboardData.plan_type}
                onChange={(e) => setOnboardData({ ...onboardData, plan_type: e.target.value })}
              >
                <option value="trial">Trial (100 scans/month)</option>
                <option value="active">Active (500 scans/month)</option>
                <option value="premium">Premium (Unlimited)</option>
              </select>
            </div>
          </div>

          <div className="eds-modal-footer">
            <button
              type="button"
              className="eds-button eds-button-secondary"
              onClick={() => setShowOnboardModal(false)}
            >
              Cancel
            </button>
            <button type="submit" className="eds-button eds-button-primary">
              Onboard Organization
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  // ============================================================================
  // MAIN RENDER
  // ============================================================================
  return (
    <EnterpriseLayout
      user={user}
      pageTitle="Super Admin - Platform Management"
      navigationItems={navigationItems}
    >
      {/* Render current view */}
      {currentView === 'dashboard' && renderDashboardView()}
      {currentView === 'organizations' && renderOrganizationsView()}
      {currentView === 'analytics' && renderAnalyticsView()}

      {/* Onboard Modal */}
      {showOnboardModal && renderOnboardModal()}
    </EnterpriseLayout>
  );
};

export default SuperAdminDashboard;
