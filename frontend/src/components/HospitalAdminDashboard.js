/**
 * Hospital Admin Dashboard
 * Organization-level management for staff and patients
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import LoadingSpinner from './LoadingSpinner';
import LogoutButton from './LogoutButton';
import './HospitalAdminDashboard.css';

// Default color scheme
const colors = {
  primary: '#9C2B6D',
  secondary: '#6B21A8',
  accent: '#D946A6',
  success: '#10B981',
  error: '#DC2626',
  warning: '#F59E0B',
  info: '#3B82F6',
  benign: '#10B981',
  malignant: '#DC2626'
};

const HospitalAdminDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
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
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        const error = new Error(`HTTP ${response.status}`);
        error.response = { data: errorData, status: response.status };
        throw error;
      }
      return { data: await response.json() };
    },
    post: async (url, data) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8001/api${url}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        const error = new Error(`HTTP ${response.status}`);
        error.response = { data: errorData, status: response.status };
        throw error;
      }
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
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        const error = new Error(`HTTP ${response.status}`);
        error.response = { data: errorData, status: response.status };
        throw error;
      }
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
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        const error = new Error(`HTTP ${response.status}`);
        error.response = { data: errorData, status: response.status };
        throw error;
      }
      return { data: await response.json() };
    }
  };
  const [dashboardData, setDashboardData] = useState(null);
  const [users, setUsers] = useState([]);
  const [patients, setPatients] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [showCreateStaffModal, setShowCreateStaffModal] = useState(false);
  const [newStaff, setNewStaff] = useState({
    email: '',
    full_name: '',
    role: 'doctor',
    phone: '',
    license_number: '',
    department: '',
    specialization: '',
    username: '',
    password: '',
  });
  const [showStaffPassword, setShowStaffPassword] = useState(false);

  useEffect(() => {
    fetchDashboardData();
    fetchUsers();
    fetchPatients();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
      const response = await axiosInstance.get('/hospital-admin/users');
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

  const handleCreateStaff = async (e) => {
    e.preventDefault();
    
    // Validate password length
    if (newStaff.password.length < 6) {
      alert('Password must be at least 6 characters long');
      return;
    }
    
    console.log('📤 Sending staff creation request with data:', JSON.stringify(newStaff, null, 2));
    
    try {
      const response = await axiosInstance.post('/hospital-admin/staff', newStaff);
      
      console.log('✅ Staff created successfully:', response.data);
      
      setShowCreateStaffModal(false);
      fetchUsers();
      fetchDashboardData();
      
      // Simple success notification
      alert(`✅ Staff member "${newStaff.full_name}" created successfully!`);
      
      // Reset form
      setNewStaff({
        email: '',
        full_name: '',
        role: 'doctor',
        phone: '',
        license_number: '',
        department: '',
        specialization: '',
        username: '',
        password: '',
      });
      setShowStaffPassword(false);
    } catch (error) {
      console.error('❌ Error creating staff member:', error);
      console.error('Server Error Details:', error.response?.data || error.message);
      console.error('Response Status:', error.response?.status);
      console.error('Full Error Object:', error);
      
      // Show detailed error message
      const errorMessage = error.response?.data?.detail 
        || (error.response?.data?.message)
        || (typeof error.response?.data === 'string' ? error.response?.data : null)
        || error.message 
        || 'Unknown error';
      
      alert(`Failed to create staff member:\n\n${errorMessage}`);
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

  if (loading) {
    return <LoadingSpinner message="Loading Hospital Admin Dashboard..." />;
  }

  return (
    <div className="hospital-admin-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div>
          <h1>🏥 {dashboardData?.tenant_name || 'Hospital'} Admin</h1>
          <p>Manage staff, patients, and organization operations</p>
        </div>
        <div className="header-actions">
          <button className="btn-add-user" onClick={() => setShowCreateStaffModal(true)}>
            👨‍⚕️ Register Staff
          </button>
          <LogoutButton variant="sidebar" />
        </div>
      </div>

      {/* Statistics Cards */}
      {dashboardData && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon" style={{ background: colors.primary }}>
              👨‍⚕️
            </div>
            <div className="stat-content">
              <h3>{dashboardData.total_doctors}</h3>
              <p>Doctors</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: colors.secondary }}>
              🔬
            </div>
            <div className="stat-content">
              <h3>{dashboardData.total_lab_techs}</h3>
              <p>Lab Technicians</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: colors.accent }}>
              👥
            </div>
            <div className="stat-content">
              <h3>{dashboardData.total_patients}</h3>
              <p>Patients</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: colors.info }}>
              📊
            </div>
            <div className="stat-content">
              <h3>{dashboardData.total_scans}</h3>
              <p>Total Scans</p>
              <span className="stat-detail">{dashboardData.scans_today} today</span>
            </div>
          </div>
        </div>
      )}

      {/* Usage Meter */}
      {dashboardData && (
        <div className="usage-meter">
          <div className="usage-header">
            <h3>Monthly Scan Usage</h3>
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
            Overview
          </button>
          <button
            className={`tab ${activeTab === 'staff' ? 'active' : ''}`}
            onClick={() => setActiveTab('staff')}
          >
            Staff ({users.filter((u) => u.role !== 'patient').length})
          </button>
          <button
            className={`tab ${activeTab === 'patients' ? 'active' : ''}`}
            onClick={() => setActiveTab('patients')}
          >
            Patients ({patients.length})
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'overview' && dashboardData && (
          <div className="overview-tab">
            <div className="section">
              <h2>Recent Scans</h2>
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
            </div>

            <div className="section">
              <h2>Active Staff</h2>
              <div className="users-grid">
                {dashboardData.active_users.slice(0, 6).map((u) => (
                  <div key={u.id} className="user-card-mini">
                    <div className="user-avatar">{u.full_name.charAt(0)}</div>
                    <div className="user-info-mini">
                      <h4>{u.full_name}</h4>
                      <p>{u.role.replace('_', ' ')}</p>
                      {u.department && <span>{u.department}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'staff' && (
          <div className="staff-tab">
            <div className="users-table">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Role</th>
                    <th>Department</th>
                    <th>License #</th>
                    <th>Email</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users
                    .filter((u) => u.role !== 'patient')
                    .map((u) => (
                      <tr key={u.id}>
                        <td>
                          <div className="user-cell">
                            <div className="user-avatar-small">
                              {u.full_name.charAt(0)}
                            </div>
                            <span>{u.full_name}</span>
                          </div>
                        </td>
                        <td>
                          <span className="role-badge">{u.role.replace('_', ' ')}</span>
                        </td>
                        <td>{u.department || '-'}</td>
                        <td>{u.license_number || '-'}</td>
                        <td>{u.email}</td>
                        <td>
                          <span className={`status-dot ${u.is_active ? 'active' : 'inactive'}`}>
                            {u.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td>
                          <button
                            className="btn-action"
                            onClick={() => handleDeactivateUser(u.id, u.full_name)}
                          >
                            Deactivate
                          </button>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'patients' && (
          <div className="patients-tab">
            <div className="patients-table">
              <table>
                <thead>
                  <tr>
                    <th>MRN</th>
                    <th>Name</th>
                    <th>Gender</th>
                    <th>DOB</th>
                    <th>Phone</th>
                    <th>Last Visit</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {patients.map((p) => (
                    <tr key={p.id}>
                      <td>
                        <span className="mrn-badge">{p.mrn}</span>
                      </td>
                      <td>{p.full_name}</td>
                      <td>{p.gender}</td>
                      <td>{new Date(p.date_of_birth).toLocaleDateString()}</td>
                      <td>{p.phone}</td>
                      <td>
                        {p.last_visit_date
                          ? new Date(p.last_visit_date).toLocaleDateString()
                          : 'Never'}
                      </td>
                      <td>
                        <button 
                          className="btn-action"
                          onClick={() => navigate(`/admin/patient/${p.id}`)}
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Register Staff Modal - Admin can ONLY register Doctors & Lab Techs */}
      {showCreateStaffModal && (
        <div className="modal-overlay" onClick={() => setShowCreateStaffModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>👨‍⚕️ Register Staff Member</h2>
              <button className="close-button" onClick={() => setShowCreateStaffModal(false)}>
                ×
              </button>
            </div>
            <form onSubmit={handleCreateStaff} className="user-form">
              <div className="form-group">
                <label>Full Name *</label>
                <input
                  type="text"
                  value={newStaff.full_name}
                  onChange={(e) => setNewStaff({ ...newStaff, full_name: e.target.value })}
                  required
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Email *</label>
                  <input
                    type="email"
                    value={newStaff.email}
                    onChange={(e) => setNewStaff({ ...newStaff, email: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Phone</label>
                  <input
                    type="tel"
                    value={newStaff.phone}
                    onChange={(e) => setNewStaff({ ...newStaff, phone: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Role *</label>
                  <select
                    value={newStaff.role}
                    onChange={(e) => setNewStaff({ ...newStaff, role: e.target.value })}
                  >
                    <option value="doctor">Doctor</option>
                    <option value="lab_tech">Lab Technician</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Department</label>
                  <input
                    type="text"
                    value={newStaff.department}
                    onChange={(e) => setNewStaff({ ...newStaff, department: e.target.value })}
                    placeholder="e.g., Radiology, Oncology"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>License Number</label>
                  <input
                    type="text"
                    value={newStaff.license_number}
                    onChange={(e) => setNewStaff({ ...newStaff, license_number: e.target.value })}
                    placeholder="Medical license #"
                  />
                </div>
                <div className="form-group">
                  <label>Specialization</label>
                  <input
                    type="text"
                    value={newStaff.specialization}
                    onChange={(e) => setNewStaff({ ...newStaff, specialization: e.target.value })}
                    placeholder="e.g., Breast Cancer Specialist"
                  />
                </div>
              </div>

              {/* Login Credentials Section */}
              <div style={{ 
                borderTop: '2px solid #e2e8f0', 
                marginTop: '1.5rem', 
                paddingTop: '1.5rem' 
              }}>
                <h3 style={{ 
                  fontSize: '0.95rem', 
                  fontWeight: '600', 
                  marginBottom: '1rem',
                  color: '#475569'
                }}>
                  🔐 Login Credentials
                </h3>

                <div className="form-row">
                  <div className="form-group">
                    <label>Username *</label>
                    <input
                      type="text"
                      value={newStaff.username}
                      onChange={(e) => setNewStaff({ ...newStaff, username: e.target.value })}
                      placeholder="username"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Password *</label>
                    <div style={{ position: 'relative' }}>
                      <input
                        type={showStaffPassword ? 'text' : 'password'}
                        value={newStaff.password}
                        onChange={(e) => setNewStaff({ ...newStaff, password: e.target.value })}
                        placeholder="Min 6 characters"
                        required
                        minLength={6}
                        style={{ paddingRight: '40px' }}
                      />
                      <button
                        type="button"
                        onClick={() => setShowStaffPassword(!showStaffPassword)}
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
                        title={showStaffPassword ? 'Hide password' : 'Show password'}
                      >
                        {showStaffPassword ? '👁️' : '👁️‍🗨️'}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="form-actions">
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => setShowCreateStaffModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-submit">
                  Register Staff
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      {/* Note: Admins can ONLY register Staff (Doctors & Lab Techs).
          Patient registration is done by Doctors in their dashboard. */}
    </div>
  );
};

export default HospitalAdminDashboard;

