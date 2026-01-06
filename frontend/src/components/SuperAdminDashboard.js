/**
 * Super Admin Dashboard
 * Global platform management and tenant overview
 * Refactored with Enterprise Design System
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import EnterpriseLayout from './common/EnterpriseLayout';
import EnterpriseTable from './common/EnterpriseTable';
import EnterpriseMetricTile from './common/EnterpriseMetricTile';
import LoadingSpinner from './LoadingSpinner';
import '../styles/enterpriseDesignSystem.css';
import './SuperAdminDashboard.css';

// API Base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const SuperAdminDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  // Create axios-like instance using fetch
  const axiosInstance = {
    get: async (url) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}${url}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return { data: await response.json() };
    },
    post: async (url, data) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}${url}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return { data: await response.json() };
    },
    put: async (url, data) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api${url}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return { data: await response.json() };
    },
    delete: async (url) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api${url}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return { data: await response.json() };
    }
  };

  const [dashboardData, setDashboardData] = useState(null);
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateTenantModal, setShowCreateTenantModal] = useState(false);
  const [newTenant, setNewTenant] = useState({
    name: '',
    organization_type: 'hospital',
    contact_email: '',
    contact_phone: '',
    city: '',
    state: '',
    monthly_scan_limit: 100,
    admin_full_name: '',
    admin_username: '',
    admin_password: '',
  });
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    fetchDashboardData();
    fetchTenants();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axiosInstance.get('/super-admin/dashboard');
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const fetchTenants = async () => {
    try {
      const response = await axiosInstance.get('/super-admin/tenants');
      setTenants(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching tenants:', error);
      setLoading(false);
    }
  };

  const handleCreateTenant = async (e) => {
    e.preventDefault();

    if (newTenant.admin_password.length < 6) {
      alert('Password must be at least 6 characters long');
      return;
    }

    try {
      await axiosInstance.post('/super-admin/tenants', newTenant);
      setShowCreateTenantModal(false);
      setNewTenant({
        name: '',
        organization_type: 'hospital',
        contact_email: '',
        contact_phone: '',
        city: '',
        state: '',
        monthly_scan_limit: 100,
        admin_full_name: '',
        admin_username: '',
        admin_password: '',
      });
      setShowPassword(false);
      fetchTenants();
      fetchDashboardData();
      alert('Organization created successfully');
    } catch (error) {
      console.error('Error creating tenant:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      alert('Failed to create organization: ' + errorMsg);
    }
  };

  const handleToggleTenantStatus = async (tenantId, currentStatus) => {
    try {
      await axiosInstance.put(`/super-admin/tenants/${tenantId}`, {
        is_active: !currentStatus,
      });
      fetchTenants();
      fetchDashboardData();
    } catch (error) {
      console.error('Error updating tenant status:', error);
    }
  };

  const navigationItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '■', active: true, onClick: () => { } },
    { id: 'organizations', label: 'Organizations', icon: '⬒', onClick: () => { } },
    { id: 'analytics', label: 'Analytics', icon: '▦', onClick: () => { } },
  ];

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
            {row.organization_type.replace('_', ' ')}
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
      header: 'Scans Used',
      accessor: 'current_month_scans',
      width: '140px',
      render: (row) => (
        <div className="eds-text-mono">
          {row.current_month_scans} / {row.monthly_scan_limit}
        </div>
      ),
    },
    {
      header: 'Total Scans',
      accessor: 'total_scans_processed',
      width: '120px',
      render: (row) => (
        <div className="eds-text-mono">{row.total_scans_processed}</div>
      ),
    },
    {
      header: 'Location',
      accessor: 'city',
      width: '180px',
      render: (row) => (
        <div className="eds-text-small">
          {row.city}, {row.state}
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
            className={`eds-button eds-button-sm ${row.is_active ? 'eds-button-danger' : 'eds-button-primary'}`}
            onClick={(e) => {
              e.stopPropagation();
              handleToggleTenantStatus(row.id, row.is_active);
            }}
          >
            {row.is_active ? 'Suspend' : 'Activate'}
          </button>
        </div>
      ),
    },
  ];

  if (loading) {
    return <LoadingSpinner message="Loading Super Admin Dashboard..." />;
  }

  return (
    <EnterpriseLayout
      user={user}
      pageTitle="Platform Management"
      navigationItems={navigationItems}
    >
      {/* Metrics */}
      {dashboardData && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 'var(--eds-space-4)',
          marginBottom: 'var(--eds-space-8)'
        }}>
          <EnterpriseMetricTile
            label="Total Organizations"
            value={dashboardData.total_tenants}
            subtitle={`${dashboardData.active_tenants} active`}
          />
          <EnterpriseMetricTile
            label="Total Users"
            value={dashboardData.total_users}
            subtitle="Across all tenants"
          />
          <EnterpriseMetricTile
            label="Total Scans"
            value={dashboardData.total_scans_processed}
            subtitle={`${dashboardData.scans_today} today`}
          />
          <EnterpriseMetricTile
            label="Total Patients"
            value={dashboardData.total_patients}
            subtitle="System-wide"
          />
        </div>
      )}

      {/* Organization Status Summary */}
      {dashboardData && (
        <div className="eds-card" style={{ marginBottom: 'var(--eds-space-8)' }}>
          <div className="eds-card-header">
            <h3 className="eds-card-title">Organization Status</h3>
          </div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: 'var(--eds-space-6)',
            marginTop: 'var(--eds-space-4)'
          }}>
            <div>
              <div className="eds-text-small">Active</div>
              <div style={{ fontSize: 'var(--eds-font-size-2xl)', fontWeight: 600, color: 'var(--eds-color-success)', marginTop: 'var(--eds-space-2)' }}>
                {dashboardData.active_tenants}
              </div>
            </div>
            <div>
              <div className="eds-text-small">Trial</div>
              <div style={{ fontSize: 'var(--eds-font-size-2xl)', fontWeight: 600, color: 'var(--eds-color-warning)', marginTop: 'var(--eds-space-2)' }}>
                {dashboardData.trial_tenants}
              </div>
            </div>
            <div>
              <div className="eds-text-small">Suspended</div>
              <div style={{ fontSize: 'var(--eds-font-size-2xl)', fontWeight: 600, color: 'var(--eds-color-error)', marginTop: 'var(--eds-space-2)' }}>
                {dashboardData.suspended_tenants}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Organizations Table */}
      <div className="eds-card">
        <div className="eds-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 className="eds-card-title">All Organizations</h3>
          <button
            className="eds-button eds-button-primary"
            onClick={() => setShowCreateTenantModal(true)}
          >
            Onboard Organization
          </button>
        </div>
        <div style={{ marginTop: 'var(--eds-space-4)' }}>
          <EnterpriseTable
            columns={tenantColumns}
            data={tenants}
            emptyMessage="No organizations found"
          />
        </div>
      </div>

      {/* Create Tenant Modal */}
      {showCreateTenantModal && (
        <div className="eds-modal-overlay" onClick={() => setShowCreateTenantModal(false)}>
          <div className="eds-modal" onClick={(e) => e.stopPropagation()}>
            <div className="eds-modal-header">
              <h2 className="eds-modal-title">Onboard New Organization</h2>
              <button
                className="eds-modal-close"
                onClick={() => setShowCreateTenantModal(false)}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleCreateTenant}>
              <div className="eds-modal-body">
                <div className="eds-form-group">
                  <label className="eds-form-label">Organization Name *</label>
                  <input
                    className="eds-form-input"
                    type="text"
                    value={newTenant.name}
                    onChange={(e) => setNewTenant({ ...newTenant, name: e.target.value })}
                    placeholder="e.g., Apollo Hospitals"
                    required
                  />
                </div>

                <div className="eds-form-group">
                  <label className="eds-form-label">Organization Type *</label>
                  <select
                    className="eds-form-select"
                    value={newTenant.organization_type}
                    onChange={(e) => setNewTenant({ ...newTenant, organization_type: e.target.value })}
                  >
                    <option value="hospital">Hospital</option>
                    <option value="pathology_lab">Pathology Lab</option>
                    <option value="diagnostic_center">Diagnostic Center</option>
                  </select>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--eds-space-4)' }}>
                  <div className="eds-form-group">
                    <label className="eds-form-label">Contact Email *</label>
                    <input
                      className="eds-form-input"
                      type="email"
                      value={newTenant.contact_email}
                      onChange={(e) => setNewTenant({ ...newTenant, contact_email: e.target.value })}
                      placeholder="contact@hospital.com"
                      required
                    />
                  </div>

                  <div className="eds-form-group">
                    <label className="eds-form-label">Contact Phone</label>
                    <input
                      className="eds-form-input"
                      type="tel"
                      value={newTenant.contact_phone}
                      onChange={(e) => setNewTenant({ ...newTenant, contact_phone: e.target.value })}
                      placeholder="+91-xxx-xxx-xxxx"
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--eds-space-4)' }}>
                  <div className="eds-form-group">
                    <label className="eds-form-label">City</label>
                    <input
                      className="eds-form-input"
                      type="text"
                      value={newTenant.city}
                      onChange={(e) => setNewTenant({ ...newTenant, city: e.target.value })}
                      placeholder="New Delhi"
                    />
                  </div>

                  <div className="eds-form-group">
                    <label className="eds-form-label">State</label>
                    <input
                      className="eds-form-input"
                      type="text"
                      value={newTenant.state}
                      onChange={(e) => setNewTenant({ ...newTenant, state: e.target.value })}
                      placeholder="Delhi"
                    />
                  </div>
                </div>

                <div className="eds-form-group">
                  <label className="eds-form-label">Monthly Scan Limit</label>
                  <input
                    className="eds-form-input"
                    type="number"
                    value={newTenant.monthly_scan_limit}
                    onChange={(e) => setNewTenant({ ...newTenant, monthly_scan_limit: parseInt(e.target.value) })}
                    min="10"
                    max="10000"
                  />
                </div>

                <div style={{
                  borderTop: '1px solid var(--eds-color-border)',
                  marginTop: 'var(--eds-space-6)',
                  paddingTop: 'var(--eds-space-6)'
                }}>
                  <h4 style={{ fontSize: 'var(--eds-font-size-md)', fontWeight: 600, marginBottom: 'var(--eds-space-4)' }}>
                    Organization Admin Credentials
                  </h4>

                  <div className="eds-form-group">
                    <label className="eds-form-label">Admin Full Name *</label>
                    <input
                      className="eds-form-input"
                      type="text"
                      value={newTenant.admin_full_name}
                      onChange={(e) => setNewTenant({ ...newTenant, admin_full_name: e.target.value })}
                      placeholder="John Doe"
                      required
                    />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--eds-space-4)' }}>
                    <div className="eds-form-group">
                      <label className="eds-form-label">Admin Username *</label>
                      <input
                        className="eds-form-input"
                        type="text"
                        value={newTenant.admin_username}
                        onChange={(e) => setNewTenant({ ...newTenant, admin_username: e.target.value })}
                        placeholder="admin_username"
                        required
                      />
                    </div>

                    <div className="eds-form-group">
                      <label className="eds-form-label">Admin Password *</label>
                      <div style={{ position: 'relative' }}>
                        <input
                          className="eds-form-input"
                          type={showPassword ? 'text' : 'password'}
                          value={newTenant.admin_password}
                          onChange={(e) => setNewTenant({ ...newTenant, admin_password: e.target.value })}
                          placeholder="Min 6 characters"
                          required
                          minLength={6}
                          style={{ paddingRight: '40px' }}
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          style={{
                            position: 'absolute',
                            right: '10px',
                            top: '50%',
                            transform: 'translateY(-50%)',
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            color: 'var(--eds-color-text-muted)'
                          }}
                        >
                          {showPassword ? 'Hide' : 'Show'}
                        </button>
                      </div>
                      <span className="eds-form-hint">Minimum 6 characters</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="eds-modal-footer">
                <button
                  type="button"
                  className="eds-button eds-button-secondary"
                  onClick={() => setShowCreateTenantModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="eds-button eds-button-primary">
                  Create Organization
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </EnterpriseLayout>
  );
};

export default SuperAdminDashboard;
