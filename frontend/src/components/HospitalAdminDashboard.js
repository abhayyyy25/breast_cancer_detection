/**
 * Hospital Admin Dashboard
 * Organization-level management for staff and patients
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
import './HospitalAdminDashboard.css';

// API Base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const HospitalAdminDashboard = () => {
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
      const response = await fetch(`${API_BASE_URL}${url}`, {
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
      const response = await fetch(`${API_BASE_URL}${url}`, {
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
      const response = await fetch(`${API_BASE_URL}${url}`, {
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

    if (newStaff.password.length < 6) {
      alert('Password must be at least 6 characters long');
      return;
    }

    try {
      const response = await axiosInstance.post('/hospital-admin/staff', newStaff);
      console.log('Staff created successfully:', response.data);

      setShowCreateStaffModal(false);
      fetchUsers();
      fetchDashboardData();

      alert(`Staff member "${newStaff.full_name}" created successfully`);

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
      console.error('Error creating staff member:', error);
      const errorMessage = error.response?.data?.detail
        || (error.response?.data?.message)
        || (typeof error.response?.data === 'string' ? error.response?.data : null)
        || error.message
        || 'Unknown error';
      alert(`Failed to create staff member: ${errorMessage}`);
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

  const navigationItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '■', active: activeTab === 'overview', onClick: () => setActiveTab('overview') },
    { id: 'staff', label: 'Staff', icon: '⬒', active: activeTab === 'staff', onClick: () => setActiveTab('staff'), badge: users.filter((u) => u.role !== 'patient').length },
    { id: 'patients', label: 'Patients', icon: '▦', active: activeTab === 'patients', onClick: () => setActiveTab('patients'), badge: patients.length },
  ];

  const staffColumns = [
    {
      header: 'Name',
      accessor: 'full_name',
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--eds-space-2)' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            background: 'var(--eds-color-primary)',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 'var(--eds-font-size-sm)',
            fontWeight: 600
          }}>
            {row.full_name.charAt(0)}
          </div>
          <span style={{ fontWeight: 500 }}>{row.full_name}</span>
        </div>
      ),
    },
    {
      header: 'Role',
      accessor: 'role',
      width: '120px',
      render: (row) => (
        <span className="eds-badge eds-badge-neutral">
          {row.role.replace('_', ' ')}
        </span>
      ),
    },
    {
      header: 'Department',
      accessor: 'department',
      width: '150px',
      render: (row) => <span className="eds-text-small">{row.department || '-'}</span>,
    },
    {
      header: 'License #',
      accessor: 'license_number',
      width: '150px',
      render: (row) => <span className="eds-text-mono">{row.license_number || '-'}</span>,
    },
    {
      header: 'Email',
      accessor: 'email',
      render: (row) => <span className="eds-text-small">{row.email}</span>,
    },
    {
      header: 'Status',
      accessor: 'is_active',
      width: '100px',
      render: (row) => (
        <span className={`eds-badge ${row.is_active ? 'eds-badge-success' : 'eds-badge-error'}`}>
          {row.is_active ? 'Active' : 'Inactive'}
        </span>
      ),
    },
    {
      header: 'Actions',
      accessor: 'id',
      width: '120px',
      render: (row) => (
        <button
          className="eds-button eds-button-sm eds-button-danger"
          onClick={(e) => {
            e.stopPropagation();
            handleDeactivateUser(row.id, row.full_name);
          }}
        >
          Deactivate
        </button>
      ),
    },
  ];

  const patientColumns = [
    {
      header: 'MRN',
      accessor: 'mrn',
      width: '120px',
      render: (row) => <span className="eds-text-mono" style={{ fontWeight: 600 }}>{row.mrn}</span>,
    },
    {
      header: 'Name',
      accessor: 'full_name',
      render: (row) => <span style={{ fontWeight: 500 }}>{row.full_name}</span>,
    },
    {
      header: 'Gender',
      accessor: 'gender',
      width: '100px',
    },
    {
      header: 'DOB',
      accessor: 'date_of_birth',
      width: '120px',
      render: (row) => <span className="eds-text-small">{new Date(row.date_of_birth).toLocaleDateString()}</span>,
    },
    {
      header: 'Phone',
      accessor: 'phone',
      width: '150px',
      render: (row) => <span className="eds-text-small">{row.phone}</span>,
    },
    {
      header: 'Last Visit',
      accessor: 'last_visit_date',
      width: '120px',
      render: (row) => (
        <span className="eds-text-small">
          {row.last_visit_date ? new Date(row.last_visit_date).toLocaleDateString() : 'Never'}
        </span>
      ),
    },
    {
      header: 'Actions',
      accessor: 'id',
      width: '100px',
      render: (row) => (
        <button
          className="eds-button eds-button-sm eds-button-secondary"
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/admin/patient/${row.id}`);
          }}
        >
          View
        </button>
      ),
    },
  ];

  if (loading) {
    return <LoadingSpinner message="Loading Hospital Admin Dashboard..." />;
  }

  return (
    <EnterpriseLayout
      user={user}
      pageTitle={dashboardData?.tenant_name || 'Hospital Administration'}
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
            label="Doctors"
            value={dashboardData.total_doctors}
          />
          <EnterpriseMetricTile
            label="Lab Technicians"
            value={dashboardData.total_lab_techs}
          />
          <EnterpriseMetricTile
            label="Patients"
            value={dashboardData.total_patients}
          />
          <EnterpriseMetricTile
            label="Total Scans"
            value={dashboardData.total_scans}
            subtitle={`${dashboardData.scans_today} today`}
          />
        </div>
      )}

      {/* Usage Meter */}
      {dashboardData && (
        <div className="eds-card" style={{ marginBottom: 'var(--eds-space-8)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--eds-space-4)' }}>
            <h3 className="eds-card-title">Monthly Scan Usage</h3>
            <span className="eds-text-mono">
              {dashboardData.scans_this_month} / {dashboardData.monthly_scan_limit}
            </span>
          </div>
          <div style={{
            width: '100%',
            height: '8px',
            background: 'var(--eds-color-surface-raised)',
            borderRadius: '4px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${Math.min(dashboardData.scan_limit_usage_percentage, 100)}%`,
              height: '100%',
              background: dashboardData.scan_limit_usage_percentage > 90
                ? 'var(--eds-color-error)'
                : dashboardData.scan_limit_usage_percentage > 75
                  ? 'var(--eds-color-warning)'
                  : 'var(--eds-color-success)',
              transition: 'width var(--eds-transition-base)'
            }} />
          </div>
          <div className="eds-text-small" style={{ marginTop: 'var(--eds-space-2)' }}>
            {dashboardData.scan_limit_usage_percentage.toFixed(1)}% used
          </div>
        </div>
      )}

      {/* Tab Content */}
      {activeTab === 'overview' && dashboardData && (
        <div>
          <div className="eds-card" style={{ marginBottom: 'var(--eds-space-6)' }}>
            <div className="eds-card-header">
              <h3 className="eds-card-title">Recent Scans</h3>
            </div>
            <div style={{ marginTop: 'var(--eds-space-4)' }}>
              <EnterpriseTable
                columns={[
                  { header: 'Scan #', accessor: 'scan_number', width: '140px', render: (row) => <span className="eds-text-mono">{row.scan_number}</span> },
                  { header: 'Date', accessor: 'scan_date', width: '120px', render: (row) => <span className="eds-text-small">{new Date(row.scan_date).toLocaleDateString()}</span> },
                  { header: 'Prediction', accessor: 'prediction', width: '120px', render: (row) => row.prediction ? <span className={`eds-badge ${row.prediction === 'benign' ? 'eds-badge-success' : 'eds-badge-error'}`}>{row.prediction}</span> : <span className="eds-text-muted">Pending</span> },
                  { header: 'Status', accessor: 'status', width: '120px', render: (row) => <span className="eds-badge eds-badge-neutral">{row.status}</span> },
                ]}
                data={dashboardData.recent_scans.slice(0, 5)}
                emptyMessage="No recent scans"
              />
            </div>
          </div>

          <div className="eds-card">
            <div className="eds-card-header">
              <h3 className="eds-card-title">Active Staff</h3>
            </div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
              gap: 'var(--eds-space-4)',
              marginTop: 'var(--eds-space-4)'
            }}>
              {dashboardData.active_users.slice(0, 6).map((u) => (
                <div key={u.id} style={{
                  padding: 'var(--eds-space-4)',
                  background: 'var(--eds-color-surface-raised)',
                  border: '1px solid var(--eds-color-border)',
                  borderRadius: 'var(--eds-radius-md)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--eds-space-3)'
                }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    background: 'var(--eds-color-primary)',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 'var(--eds-font-size-md)',
                    fontWeight: 600,
                    flexShrink: 0
                  }}>
                    {u.full_name.charAt(0)}
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontWeight: 500, fontSize: 'var(--eds-font-size-sm)' }}>{u.full_name}</div>
                    <div className="eds-text-small">{u.role.replace('_', ' ')}</div>
                    {u.department && <div className="eds-text-small" style={{ color: 'var(--eds-color-text-muted)' }}>{u.department}</div>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'staff' && (
        <div className="eds-card">
          <div className="eds-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 className="eds-card-title">Staff Members</h3>
            <button
              className="eds-button eds-button-primary"
              onClick={() => setShowCreateStaffModal(true)}
            >
              Register Staff
            </button>
          </div>
          <div style={{ marginTop: 'var(--eds-space-4)' }}>
            <EnterpriseTable
              columns={staffColumns}
              data={users.filter((u) => u.role !== 'patient')}
              emptyMessage="No staff members found"
            />
          </div>
        </div>
      )}

      {activeTab === 'patients' && (
        <div className="eds-card">
          <div className="eds-card-header">
            <h3 className="eds-card-title">Patients</h3>
          </div>
          <div style={{ marginTop: 'var(--eds-space-4)' }}>
            <EnterpriseTable
              columns={patientColumns}
              data={patients}
              emptyMessage="No patients found"
            />
          </div>
        </div>
      )}

      {/* Register Staff Modal */}
      {showCreateStaffModal && (
        <div className="eds-modal-overlay" onClick={() => setShowCreateStaffModal(false)}>
          <div className="eds-modal" onClick={(e) => e.stopPropagation()}>
            <div className="eds-modal-header">
              <h2 className="eds-modal-title">Register Staff Member</h2>
              <button className="eds-modal-close" onClick={() => setShowCreateStaffModal(false)}>
                ×
              </button>
            </div>
            <form onSubmit={handleCreateStaff}>
              <div className="eds-modal-body">
                <div className="eds-form-group">
                  <label className="eds-form-label">Full Name *</label>
                  <input
                    className="eds-form-input"
                    type="text"
                    value={newStaff.full_name}
                    onChange={(e) => setNewStaff({ ...newStaff, full_name: e.target.value })}
                    required
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--eds-space-4)' }}>
                  <div className="eds-form-group">
                    <label className="eds-form-label">Email *</label>
                    <input
                      className="eds-form-input"
                      type="email"
                      value={newStaff.email}
                      onChange={(e) => setNewStaff({ ...newStaff, email: e.target.value })}
                      required
                    />
                  </div>
                  <div className="eds-form-group">
                    <label className="eds-form-label">Phone</label>
                    <input
                      className="eds-form-input"
                      type="tel"
                      value={newStaff.phone}
                      onChange={(e) => setNewStaff({ ...newStaff, phone: e.target.value })}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--eds-space-4)' }}>
                  <div className="eds-form-group">
                    <label className="eds-form-label">Role *</label>
                    <select
                      className="eds-form-select"
                      value={newStaff.role}
                      onChange={(e) => setNewStaff({ ...newStaff, role: e.target.value })}
                    >
                      <option value="doctor">Doctor</option>
                      <option value="lab_tech">Lab Technician</option>
                    </select>
                  </div>
                  <div className="eds-form-group">
                    <label className="eds-form-label">Department</label>
                    <input
                      className="eds-form-input"
                      type="text"
                      value={newStaff.department}
                      onChange={(e) => setNewStaff({ ...newStaff, department: e.target.value })}
                      placeholder="e.g., Radiology, Oncology"
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--eds-space-4)' }}>
                  <div className="eds-form-group">
                    <label className="eds-form-label">License Number</label>
                    <input
                      className="eds-form-input"
                      type="text"
                      value={newStaff.license_number}
                      onChange={(e) => setNewStaff({ ...newStaff, license_number: e.target.value })}
                      placeholder="Medical license #"
                    />
                  </div>
                  <div className="eds-form-group">
                    <label className="eds-form-label">Specialization</label>
                    <input
                      className="eds-form-input"
                      type="text"
                      value={newStaff.specialization}
                      onChange={(e) => setNewStaff({ ...newStaff, specialization: e.target.value })}
                      placeholder="e.g., Breast Cancer Specialist"
                    />
                  </div>
                </div>

                <div style={{
                  borderTop: '1px solid var(--eds-color-border)',
                  marginTop: 'var(--eds-space-6)',
                  paddingTop: 'var(--eds-space-6)'
                }}>
                  <h4 style={{ fontSize: 'var(--eds-font-size-md)', fontWeight: 600, marginBottom: 'var(--eds-space-4)' }}>
                    Login Credentials
                  </h4>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--eds-space-4)' }}>
                    <div className="eds-form-group">
                      <label className="eds-form-label">Username *</label>
                      <input
                        className="eds-form-input"
                        type="text"
                        value={newStaff.username}
                        onChange={(e) => setNewStaff({ ...newStaff, username: e.target.value })}
                        placeholder="username"
                        required
                      />
                    </div>

                    <div className="eds-form-group">
                      <label className="eds-form-label">Password *</label>
                      <div style={{ position: 'relative' }}>
                        <input
                          className="eds-form-input"
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
                            color: 'var(--eds-color-text-muted)'
                          }}
                        >
                          {showStaffPassword ? 'Hide' : 'Show'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="eds-modal-footer">
                <button
                  type="button"
                  className="eds-button eds-button-secondary"
                  onClick={() => setShowCreateStaffModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="eds-button eds-button-primary">
                  Register Staff
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </EnterpriseLayout>
  );
};

export default HospitalAdminDashboard;
