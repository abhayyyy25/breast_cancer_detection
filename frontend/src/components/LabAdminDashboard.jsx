/**
 * Lab Admin Dashboard - PATH Labs Management
 * Simplified for Phase 1: Lab staff and patient management only
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContextSaaS';
import { useTheme } from '../context/ThemeContext';
import './LabAdminDashboard.css';

const LabAdminDashboard = () => {
  const { axiosInstance } = useAuth();
  const { colors } = useTheme();
  const [dashboardData, setDashboardData] = useState(null);
  const [users, setUsers] = useState([]);
  const [patients, setPatients] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [showCreateUserModal, setShowCreateUserModal] = useState(false);
  const [newUser, setNewUser] = useState({
    email: '',
    full_name: '',
    phone: '',
    department: 'Pathology',
  });
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchDashboardData();
    fetchUsers();
    fetchPatients();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axiosInstance.get('/hospital-admin/dashboard');
      setDashboardData(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axiosInstance.get('/hospital-admin/users?role=lab_tech');
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const fetchPatients = async () => {
    try {
      const response = await axiosInstance.get('/hospital-admin/patients');
      setPatients(response.data);
    } catch (error) {
      console.error('Error fetching patients:', error);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      const userData = {
        ...newUser,
        role: 'lab_tech'
      };
      const response = await axiosInstance.post('/hospital-admin/users', userData);
      
      // Show generated credentials
      alert(
        `Lab Technician Created Successfully!\n\n` +
        `Username: ${response.data.username}\n` +
        `Password: ${response.data.password}\n\n` +
        `⚠️ Please save these credentials securely.\n` +
        `Password won't be shown again!`
      );
      
      setShowCreateUserModal(false);
      setNewUser({
        email: '',
        full_name: '',
        phone: '',
        department: 'Pathology',
      });
      fetchUsers();
      fetchDashboardData();
    } catch (error) {
      console.error('Error creating user:', error);
      alert('Failed to create user: ' + (error.response?.data?.detail || 'Unknown error'));
    }
  };

  const handleDeactivateUser = async (userId, userName) => {
    if (window.confirm(`Are you sure you want to deactivate ${userName}?`)) {
      try {
        await axiosInstance.delete(`/hospital-admin/users/${userId}`);
        fetchUsers();
        fetchDashboardData();
      } catch (error) {
        console.error('Error deactivating user:', error);
        alert('Failed to deactivate user');
      }
    }
  };

  const filteredPatients = patients.filter(
    (patient) =>
      patient.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      patient.mrn.toLowerCase().includes(searchQuery.toLowerCase()) ||
      patient.phone.includes(searchQuery)
  );

  if (loading) {
    return (
      <div className="lab-admin-dashboard">
        <div className="loading-spinner">Loading Lab Dashboard...</div>
      </div>
    );
  }

  return (
    <div className="lab-admin-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div>
          <h1>🔬 {dashboardData?.tenant_name || 'PATH Lab'} - Admin Panel</h1>
          <p>Manage lab technicians and patient records</p>
        </div>
        <button className="btn-add-user" onClick={() => setShowCreateUserModal(true)}>
          + Add Lab Technician
        </button>
      </div>

      {/* Statistics Cards */}
      {dashboardData && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon" style={{ background: colors.primary }}>
              🔬
            </div>
            <div className="stat-content">
              <h3>{dashboardData.total_lab_techs}</h3>
              <p>Lab Technicians</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: colors.secondary }}>
              👥
            </div>
            <div className="stat-content">
              <h3>{dashboardData.total_patients}</h3>
              <p>Registered Patients</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: colors.accent }}>
              📊
            </div>
            <div className="stat-content">
              <h3>{dashboardData.total_scans}</h3>
              <p>Total Scans</p>
              <span className="stat-detail">{dashboardData.scans_today} today</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: colors.info }}>
              📈
            </div>
            <div className="stat-content">
              <h3>{dashboardData.scans_this_month}</h3>
              <p>This Month</p>
              <span className="stat-detail">
                {dashboardData.scan_limit_usage_percentage.toFixed(0)}% of limit
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Usage Meter */}
      {dashboardData && (
        <div className="usage-meter">
          <div className="usage-header">
            <h3>📊 Monthly Scan Usage</h3>
            <span className="usage-text">
              {dashboardData.scans_this_month} / {dashboardData.monthly_scan_limit} scans
            </span>
          </div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{
                width: `${Math.min(dashboardData.scan_limit_usage_percentage, 100)}%`,
                background:
                  dashboardData.scan_limit_usage_percentage > 90
                    ? colors.error
                    : dashboardData.scan_limit_usage_percentage > 75
                    ? colors.warning
                    : colors.success,
              }}
            />
          </div>
          <p className="usage-percentage">
            {dashboardData.scan_limit_usage_percentage.toFixed(1)}% used
          </p>
        </div>
      )}

      {/* Tabs */}
      <div className="tabs-container">
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            📋 Overview
          </button>
          <button
            className={`tab ${activeTab === 'technicians' ? 'active' : ''}`}
            onClick={() => setActiveTab('technicians')}
          >
            🔬 Lab Technicians ({users.length})
          </button>
          <button
            className={`tab ${activeTab === 'patients' ? 'active' : ''}`}
            onClick={() => setActiveTab('patients')}
          >
            👥 Patient Records ({patients.length})
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {/* Overview Tab */}
        {activeTab === 'overview' && dashboardData && (
          <div className="overview-tab">
            <div className="section">
              <h2>Recent Scans</h2>
              {dashboardData.recent_scans.length === 0 ? (
                <p className="empty-state">No scans yet</p>
              ) : (
                <div className="scans-list">
                  {dashboardData.recent_scans.slice(0, 5).map((scan) => (
                    <div key={scan.id} className="scan-item">
                      <div className="scan-info">
                        <span className="scan-number">{scan.scan_number}</span>
                        <span className="scan-date">
                          {new Date(scan.scan_date).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="scan-result">
                        {scan.prediction && (
                          <span
                            className={`prediction-badge ${scan.prediction}`}
                            style={{
                              background:
                                scan.prediction === 'benign'
                                  ? `${colors.benign}20`
                                  : `${colors.malignant}20`,
                              color:
                                scan.prediction === 'benign'
                                  ? colors.benign
                                  : colors.malignant,
                            }}
                          >
                            {scan.prediction}
                          </span>
                        )}
                        <span className={`status-badge ${scan.status}`}>
                          {scan.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="section">
              <h2>Active Lab Technicians</h2>
              {dashboardData.active_users.length === 0 ? (
                <p className="empty-state">No active technicians</p>
              ) : (
                <div className="users-grid">
                  {dashboardData.active_users.slice(0, 6).map((u) => (
                    <div key={u.id} className="user-card-mini">
                      <div className="user-avatar">{u.full_name.charAt(0)}</div>
                      <div className="user-info-mini">
                        <h4>{u.full_name}</h4>
                        <p>{u.department || 'Lab Tech'}</p>
                        {u.last_login && (
                          <span className="last-active">
                            Last: {new Date(u.last_login).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Technicians Tab */}
        {activeTab === 'technicians' && (
          <div className="technicians-tab">
            <div className="users-list-card">
              {users.length === 0 ? (
                <div className="empty-state-large">
                  <div className="empty-icon">🔬</div>
                  <h3>No Lab Technicians Yet</h3>
                  <p>Click "Add Lab Technician" to add your first team member</p>
                </div>
              ) : (
                <div className="users-grid-large">
                  {users.map((user) => (
                    <div key={user.id} className="user-card">
                      <div className="user-card-header">
                        <div className="user-avatar-large">{user.full_name.charAt(0)}</div>
                        <div className="user-info">
                          <h3>{user.full_name}</h3>
                          <p className="user-username">@{user.username}</p>
                        </div>
                        <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>

                      <div className="user-details">
                        <div className="detail-row">
                          <span className="detail-label">📧 Email:</span>
                          <span className="detail-value">{user.email}</span>
                        </div>
                        {user.phone && (
                          <div className="detail-row">
                            <span className="detail-label">📞 Phone:</span>
                            <span className="detail-value">{user.phone}</span>
                          </div>
                        )}
                        <div className="detail-row">
                          <span className="detail-label">🏢 Department:</span>
                          <span className="detail-value">{user.department || 'Pathology'}</span>
                        </div>
                        {user.last_login && (
                          <div className="detail-row">
                            <span className="detail-label">🕒 Last Login:</span>
                            <span className="detail-value">
                              {new Date(user.last_login).toLocaleString()}
                            </span>
                          </div>
                        )}
                      </div>

                      <div className="user-actions">
                        <button
                          className="btn-deactivate"
                          onClick={() => handleDeactivateUser(user.id, user.full_name)}
                        >
                          Deactivate
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Patients Tab */}
        {activeTab === 'patients' && (
          <div className="patients-tab">
            <div className="search-bar">
              <input
                type="text"
                placeholder="🔍 Search patients by name, MRN, or phone..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
            </div>

            <div className="patients-list-card">
              {filteredPatients.length === 0 ? (
                <div className="empty-state-large">
                  <div className="empty-icon">👥</div>
                  <h3>{searchQuery ? 'No Patients Found' : 'No Patients Registered'}</h3>
                  <p>
                    {searchQuery
                      ? 'Try adjusting your search query'
                      : 'Patients will be registered when scans are performed'}
                  </p>
                </div>
              ) : (
                <div className="patients-grid">
                  {filteredPatients.map((patient) => (
                    <div key={patient.id} className="patient-card">
                      <div className="patient-header">
                        <div className="patient-avatar">{patient.full_name.charAt(0)}</div>
                        <div className="patient-info">
                          <h3>{patient.full_name}</h3>
                          <span className="patient-mrn">MRN: {patient.mrn}</span>
                        </div>
                      </div>

                      <div className="patient-details">
                        <div className="detail-item">
                          <span className="icon">🎂</span>
                          <span>
                            {new Date(patient.date_of_birth).toLocaleDateString()} (
                            {patient.gender})
                          </span>
                        </div>
                        <div className="detail-item">
                          <span className="icon">📞</span>
                          <span>{patient.phone}</span>
                        </div>
                        {patient.last_visit_date && (
                          <div className="detail-item">
                            <span className="icon">📅</span>
                            <span>
                              Last Visit: {new Date(patient.last_visit_date).toLocaleDateString()}
                            </span>
                          </div>
                        )}
                      </div>

                      <button className="btn-view-patient">View Details</button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Create User Modal */}
      {showCreateUserModal && (
        <div className="modal-overlay" onClick={() => setShowCreateUserModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>➕ Add Lab Technician</h2>
              <button className="close-button" onClick={() => setShowCreateUserModal(false)}>
                ×
              </button>
            </div>

            <form onSubmit={handleCreateUser} className="user-form">
              <div className="form-group">
                <label>Full Name *</label>
                <input
                  type="text"
                  value={newUser.full_name}
                  onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                  placeholder="Enter full name"
                  required
                />
              </div>

              <div className="form-group">
                <label>Email *</label>
                <input
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  placeholder="email@example.com"
                  required
                />
              </div>

              <div className="form-group">
                <label>Phone</label>
                <input
                  type="tel"
                  value={newUser.phone}
                  onChange={(e) => setNewUser({ ...newUser, phone: e.target.value })}
                  placeholder="+91-XXX-XXX-XXXX"
                />
              </div>

              <div className="form-group">
                <label>Department</label>
                <select
                  value={newUser.department}
                  onChange={(e) => setNewUser({ ...newUser, department: e.target.value })}
                >
                  <option value="Pathology">Pathology</option>
                  <option value="Imaging">Imaging</option>
                  <option value="Laboratory">Laboratory</option>
                  <option value="Radiology">Radiology</option>
                </select>
              </div>

              <div className="info-box">
                <strong>ℹ️ Note:</strong> System will automatically generate secure login
                credentials (username & password) for the new technician.
              </div>

              <div className="form-actions">
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => setShowCreateUserModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-submit">
                  Create Lab Technician
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default LabAdminDashboard;

