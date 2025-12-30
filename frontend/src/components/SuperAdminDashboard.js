/**
 * Super Admin Dashboard
 * Global platform management and tenant overview
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import LoadingSpinner from './LoadingSpinner';
import LogoutButton from './LogoutButton';
import './SuperAdminDashboard.css';

// API Base URL - uses environment variable for production, falls back to localhost for development
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001/api';

// Default color scheme
const colors = {
  primary: '#9C2B6D',
  secondary: '#6B21A8',
  accent: '#D946A6',
  success: '#10B981',
  error: '#DC2626',
  warning: '#F59E0B',
  info: '#3B82F6'
};

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
      const response = await fetch(`http://localhost:8001/api${url}`, {
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
      const response = await fetch(`http://localhost:8001/api${url}`, {
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
    
    // Validate password length
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
      // Simple success notification
      alert('✅ Organization created successfully!');
    } catch (error) {
      console.error('Error creating tenant:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      alert('Failed to create organization:\n\n' + errorMsg);
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

  if (loading) {
    return <LoadingSpinner message="Loading Super Admin Dashboard..." />;
  }

  return (
    <div className="super-admin-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div>
          <h1>🌐 Super Admin Dashboard</h1>
          <p>Global platform management and tenant overview</p>
        </div>
        <div className="header-actions">
          <button
            className="btn-create-tenant"
            onClick={() => setShowCreateTenantModal(true)}
          >
            + Onboard New Organization
          </button>
          <LogoutButton variant="sidebar" />
        </div>
      </div>

      {/* Statistics Cards */}
      {dashboardData && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon" style={{ background: colors.primary }}>
              🏥
            </div>
            <div className="stat-content">
              <h3>{dashboardData.total_tenants}</h3>
              <p>Total Organizations</p>
              <span className="stat-detail">
                {dashboardData.active_tenants} active
              </span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: colors.secondary }}>
              👥
            </div>
            <div className="stat-content">
              <h3>{dashboardData.total_users}</h3>
              <p>Total Users</p>
              <span className="stat-detail">Across all tenants</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: colors.accent }}>
              🔬
            </div>
            <div className="stat-content">
              <h3>{dashboardData.total_scans_processed}</h3>
              <p>Total Scans</p>
              <span className="stat-detail">
                {dashboardData.scans_today} today
              </span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: colors.info }}>
              📊
            </div>
            <div className="stat-content">
              <h3>{dashboardData.total_patients}</h3>
              <p>Total Patients</p>
              <span className="stat-detail">System-wide</span>
            </div>
          </div>
        </div>
      )}

      {/* Tenant Breakdown */}
      {dashboardData && (
        <div className="tenant-breakdown">
          <h2>Organization Status</h2>
          <div className="breakdown-grid">
            <div className="breakdown-item">
              <div className="breakdown-label">Active</div>
              <div className="breakdown-value" style={{ color: colors.success }}>
                {dashboardData.active_tenants}
              </div>
            </div>
            <div className="breakdown-item">
              <div className="breakdown-label">Trial</div>
              <div className="breakdown-value" style={{ color: colors.warning }}>
                {dashboardData.trial_tenants}
              </div>
            </div>
            <div className="breakdown-item">
              <div className="breakdown-label">Suspended</div>
              <div className="breakdown-value" style={{ color: colors.error }}>
                {dashboardData.suspended_tenants}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tenants List */}
      <div className="tenants-section">
        <h2>All Organizations</h2>
        <div className="tenants-list">
          {tenants.map((tenant) => (
            <div key={tenant.id} className="tenant-card">
              <div className="tenant-card-grid">
                <div className="tenant-avatar">
                  {tenant.name?.charAt(0)}
                </div>
                <div className="tenant-card-main">
                  <div className="tenant-header">
                    <div className="tenant-info">
                      <h3>{tenant.name}</h3>
                      <span className={`org-type ${tenant.organization_type}`}>
                        {tenant.organization_type.replace('_', ' ')}
                      </span>
                    </div>
                    <span className={`status-badge ${tenant.subscription_status}`}>
                      {tenant.subscription_status}
                    </span>
                  </div>

                  <div className="tenant-stats">
                    <div className="tenant-stat">
                      <span className="stat-label">Scans:</span>
                      <span className="stat-value">
                        {tenant.current_month_scans} / {tenant.monthly_scan_limit}
                      </span>
                    </div>
                    <div className="tenant-stat">
                      <span className="stat-label">Total Scans:</span>
                      <span className="stat-value">{tenant.total_scans_processed}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="tenant-contact">
                <p>📧 {tenant.contact_email}</p>
                {tenant.contact_phone && <p>📞 {tenant.contact_phone}</p>}
                <p>📍 {tenant.city}, {tenant.state}</p>
              </div>

              <div className="tenant-actions">
                <button 
                  className="btn-view-details"
                  onClick={() => navigate(`/superadmin/organization/${tenant.id}`)}
                >
                  View Details
                </button>
                <button
                  className={`btn-toggle-status ${tenant.is_active ? 'deactivate' : 'activate'}`}
                  onClick={() => handleToggleTenantStatus(tenant.id, tenant.is_active)}
                >
                  {tenant.is_active ? 'Suspend' : 'Activate'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Create Tenant Modal */}
      {showCreateTenantModal && (
        <div className="modal-overlay" onClick={() => setShowCreateTenantModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Onboard New Organization</h2>
              <button
                className="close-button"
                onClick={() => setShowCreateTenantModal(false)}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleCreateTenant} className="tenant-form">
              <div className="form-group">
                <label>Organization Name *</label>
                <input
                  type="text"
                  value={newTenant.name}
                  onChange={(e) =>
                    setNewTenant({ ...newTenant, name: e.target.value })
                  }
                  placeholder="e.g., Apollo Hospitals"
                  required
                />
              </div>

              <div className="form-group">
                <label>Organization Type *</label>
                <select
                  value={newTenant.organization_type}
                  onChange={(e) =>
                    setNewTenant({ ...newTenant, organization_type: e.target.value })
                  }
                >
                  <option value="hospital">Hospital</option>
                  <option value="pathology_lab">Pathology Lab</option>
                  <option value="diagnostic_center">Diagnostic Center</option>
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Contact Email *</label>
                  <input
                    type="email"
                    value={newTenant.contact_email}
                    onChange={(e) =>
                      setNewTenant({ ...newTenant, contact_email: e.target.value })
                    }
                    placeholder="contact@hospital.com"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Contact Phone</label>
                  <input
                    type="tel"
                    value={newTenant.contact_phone}
                    onChange={(e) =>
                      setNewTenant({ ...newTenant, contact_phone: e.target.value })
                    }
                    placeholder="+91-xxx-xxx-xxxx"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>City</label>
                  <input
                    type="text"
                    value={newTenant.city}
                    onChange={(e) =>
                      setNewTenant({ ...newTenant, city: e.target.value })
                    }
                    placeholder="New Delhi"
                  />
                </div>

                <div className="form-group">
                  <label>State</label>
                  <input
                    type="text"
                    value={newTenant.state}
                    onChange={(e) =>
                      setNewTenant({ ...newTenant, state: e.target.value })
                    }
                    placeholder="Delhi"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Monthly Scan Limit</label>
                <input
                  type="number"
                  value={newTenant.monthly_scan_limit}
                  onChange={(e) =>
                    setNewTenant({
                      ...newTenant,
                      monthly_scan_limit: parseInt(e.target.value),
                    })
                  }
                  min="10"
                  max="10000"
                />
              </div>

              {/* Admin Credentials Section */}
              <div style={{ 
                borderTop: '2px solid #e2e8f0', 
                marginTop: '1.5rem', 
                paddingTop: '1.5rem' 
              }}>
                <h3 style={{ 
                  fontSize: '1rem', 
                  fontWeight: '600', 
                  marginBottom: '1rem',
                  color: '#475569'
                }}>
                  👤 Organization Admin Credentials
                </h3>

                <div className="form-group">
                  <label>Admin Full Name *</label>
                  <input
                    type="text"
                    value={newTenant.admin_full_name}
                    onChange={(e) =>
                      setNewTenant({ ...newTenant, admin_full_name: e.target.value })
                    }
                    placeholder="John Doe"
                    required
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Admin Username *</label>
                    <input
                      type="text"
                      value={newTenant.admin_username}
                      onChange={(e) =>
                        setNewTenant({ ...newTenant, admin_username: e.target.value })
                      }
                      placeholder="admin_username"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Admin Password *</label>
                    <div style={{ position: 'relative' }}>
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={newTenant.admin_password}
                        onChange={(e) =>
                          setNewTenant({ ...newTenant, admin_password: e.target.value })
                        }
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
                          fontSize: '1.2rem',
                          color: '#64748b',
                          padding: '0',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}
                        title={showPassword ? 'Hide password' : 'Show password'}
                      >
                        {showPassword ? '👁️' : '👁️‍🗨️'}
                      </button>
                    </div>
                    <small style={{ color: '#64748b', fontSize: '0.75rem' }}>
                      Minimum 6 characters
                    </small>
                  </div>
                </div>
              </div>

              <div className="form-actions">
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => setShowCreateTenantModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-submit">
                  Create Organization
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SuperAdminDashboard;

