/**
 * Organization Details Page
 * Shows complete organization information, statistics, and users
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import LoadingSpinner from './LoadingSpinner';
import './OrganizationDetails.css';

const OrganizationDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [organization, setOrganization] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  // Create axios-like instance using fetch
  const axiosInstance = {
    get: async (url) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8001/api${url}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return { data: await response.json() };
    }
  };

  useEffect(() => {
    fetchOrganizationDetails();
    fetchOrganizationStats();
  }, [id]);

  const fetchOrganizationDetails = async () => {
    try {
      const response = await axiosInstance.get(`/super-admin/tenants/${id}`);
      setOrganization(response.data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching organization details:', err);
      setError('Failed to load organization details');
      setLoading(false);
    }
  };

  const fetchOrganizationStats = async () => {
    try {
      const response = await axiosInstance.get(`/super-admin/tenants/${id}/stats`);
      setStats(response.data);
    } catch (err) {
      console.error('Error fetching organization stats:', err);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading organization details..." />;
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>❌ {error}</h2>
        <button onClick={() => navigate(-1)}>← Go Back</button>
      </div>
    );
  }

  if (!organization) {
    return (
      <div className="error-container">
        <h2>❌ Organization not found</h2>
        <button onClick={() => navigate(-1)}>← Go Back</button>
      </div>
    );
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return '#10B981';
      case 'trial':
        return '#F59E0B';
      case 'suspended':
        return '#DC2626';
      default:
        return '#6B7280';
    }
  };

  return (
    <div className="organization-details-container">
      {/* Header */}
      <div className="details-header">
        <button className="btn-back" onClick={() => navigate(-1)}>
          ← Back to Dashboard
        </button>
        <h1>Organization Details</h1>
      </div>

      {/* Organization Info Card */}
      <div className="organization-info-card">
        <div className="organization-avatar-large">
          {organization.name.charAt(0)}
        </div>
        <div className="organization-header-info">
          <h2>{organization.name}</h2>
          <p className="organization-type">{organization.organization_type.replace('_', ' ')}</p>
          <div className="organization-status">
            <span 
              className="status-badge" 
              style={{ backgroundColor: getStatusColor(organization.subscription_status) }}
            >
              {organization.subscription_status}
            </span>
            <span className={`active-badge ${organization.is_active ? 'active' : 'inactive'}`}>
              {organization.is_active ? '✓ Active' : '✗ Inactive'}
            </span>
          </div>
          <div className="organization-quick-info">
            <span>📧 {organization.contact_email}</span>
            {organization.contact_phone && <span>📞 {organization.contact_phone}</span>}
            <span>📍 {organization.city}, {organization.state}</span>
            <span>🗓️ Joined: {new Date(organization.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">👥</div>
            <div className="stat-content">
              <h3>{stats.total_users}</h3>
              <p>Total Users</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🏥</div>
            <div className="stat-content">
              <h3>{stats.total_patients}</h3>
              <p>Total Patients</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🔬</div>
            <div className="stat-content">
              <h3>{stats.total_scans}</h3>
              <p>Total Scans</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <h3>{stats.scans_this_month}</h3>
              <p>Scans This Month</p>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="details-tabs">
        <button
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={activeTab === 'subscription' ? 'active' : ''}
          onClick={() => setActiveTab('subscription')}
        >
          Subscription
        </button>
        <button
          className={activeTab === 'contact' ? 'active' : ''}
          onClick={() => setActiveTab('contact')}
        >
          Contact Info
        </button>
      </div>

      {/* Tab Content */}
      <div className="details-content">
        {activeTab === 'overview' && (
          <div className="overview-section">
            <div className="info-grid">
              <div className="info-item">
                <label>Organization Name:</label>
                <span>{organization.name}</span>
              </div>
              <div className="info-item">
                <label>Organization Type:</label>
                <span>{organization.organization_type.replace('_', ' ')}</span>
              </div>
              <div className="info-item">
                <label>Status:</label>
                <span style={{ color: getStatusColor(organization.subscription_status) }}>
                  {organization.subscription_status}
                </span>
              </div>
              <div className="info-item">
                <label>Is Active:</label>
                <span>{organization.is_active ? 'Yes' : 'No'}</span>
              </div>
              <div className="info-item">
                <label>Created At:</label>
                <span>{new Date(organization.created_at).toLocaleString()}</span>
              </div>
              <div className="info-item">
                <label>City:</label>
                <span>{organization.city}</span>
              </div>
              <div className="info-item">
                <label>State:</label>
                <span>{organization.state}</span>
              </div>
              <div className="info-item">
                <label>Total Scans Processed:</label>
                <span>{organization.total_scans_processed || 0}</span>
              </div>
            </div>

            {stats && (
              <div className="staff-info">
                <h3>Staff Overview</h3>
                <div className="staff-stats">
                  <div className="staff-stat">
                    <span className="label">Active Doctors:</span>
                    <span className="value">{stats.active_doctors}</span>
                  </div>
                  <div className="staff-stat">
                    <span className="label">Active Lab Technicians:</span>
                    <span className="value">{stats.active_lab_techs}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'subscription' && (
          <div className="subscription-section">
            <div className="info-grid">
              <div className="info-item">
                <label>Subscription Plan:</label>
                <span>{organization.subscription_plan || 'Free'}</span>
              </div>
              <div className="info-item">
                <label>Subscription Status:</label>
                <span style={{ color: getStatusColor(organization.subscription_status) }}>
                  {organization.subscription_status}
                </span>
              </div>
              <div className="info-item">
                <label>Monthly Scan Limit:</label>
                <span>{organization.monthly_scan_limit}</span>
              </div>
              <div className="info-item">
                <label>Current Month Scans:</label>
                <span>{organization.current_month_scans || 0}</span>
              </div>
              {organization.trial_ends_at && (
                <div className="info-item">
                  <label>Trial Ends:</label>
                  <span>{new Date(organization.trial_ends_at).toLocaleDateString()}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'contact' && (
          <div className="contact-section">
            <div className="info-grid">
              <div className="info-item">
                <label>Contact Email:</label>
                <span>{organization.contact_email}</span>
              </div>
              <div className="info-item">
                <label>Contact Phone:</label>
                <span>{organization.contact_phone || 'Not provided'}</span>
              </div>
              <div className="info-item">
                <label>Address:</label>
                <span>{organization.address || 'Not provided'}</span>
              </div>
              <div className="info-item">
                <label>City:</label>
                <span>{organization.city}</span>
              </div>
              <div className="info-item">
                <label>State:</label>
                <span>{organization.state}</span>
              </div>
              <div className="info-item">
                <label>Postal Code:</label>
                <span>{organization.postal_code || 'Not provided'}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OrganizationDetails;

