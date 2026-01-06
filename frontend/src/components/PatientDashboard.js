/**
 * Patient Dashboard
 * Personal health dashboard for patients to view their scan history and reports
 * Refactored with Enterprise Design System (Softer, patient-friendly variant)
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import EnterpriseLayout from './common/EnterpriseLayout';
import EnterpriseTable from './common/EnterpriseTable';
import EnterpriseMetricTile from './common/EnterpriseMetricTile';
import LoadingSpinner from './LoadingSpinner';
import '../styles/enterpriseDesignSystem.css';
import './PatientDashboard.css';

// API Base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const PatientDashboard = () => {
  const { user } = useAuth();

  // Create axios-like instance using fetch
  const axiosInstance = {
    get: async (url, config = {}) => {
      const token = localStorage.getItem('token');
      const fetchUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
      const response = await fetch(fetchUrl, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          ...config.headers
        },
        ...(config.responseType && { responseType: config.responseType })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      if (config.responseType === 'blob') {
        return { data: await response.blob() };
      }
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
    }
  };

  const [dashboardData, setDashboardData] = useState(null);
  const [scans, setScans] = useState([]);
  const [selectedScan, setSelectedScan] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [downloadingReport, setDownloadingReport] = useState(null);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [profileData, setProfileData] = useState({
    email: '',
    phone: '',
    address: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
  });
  const [fullPatientProfile, setFullPatientProfile] = useState(null);

  useEffect(() => {
    fetchDashboardData();
    fetchScans();
    fetchProfile();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axiosInstance.get('/patient-portal/dashboard');
      setDashboardData(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  const fetchScans = async () => {
    try {
      const response = await axiosInstance.get('/patient-portal/scans');
      setScans(response.data);
    } catch (error) {
      console.error('Error fetching scans:', error);
    }
  };

  const fetchProfile = async () => {
    try {
      const response = await axiosInstance.get('/patient-portal/profile');
      setFullPatientProfile(response.data);
      setProfileData({
        email: response.data.email || '',
        phone: response.data.phone || '',
        address: response.data.address || '',
        emergency_contact_name: response.data.emergency_contact_name || '',
        emergency_contact_phone: response.data.emergency_contact_phone || '',
      });
    } catch (error) {
      console.error('Error fetching profile:', error);
    }
  };

  const handleDownloadReport = async (scanId, scanNumber) => {
    setDownloadingReport(scanId);
    try {
      const response = await axiosInstance.get(`/patient-portal/scans/${scanId}/download-report`, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `breast_cancer_report_${scanNumber}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading report:', error);
      alert('Failed to download report. Please try again.');
    } finally {
      setDownloadingReport(null);
    }
  };

  const handleViewScanDetails = (scan) => {
    setSelectedScan(scan);
    setActiveTab('scanDetails');
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    try {
      await axiosInstance.put('/patient-portal/profile', profileData);
      setShowProfileModal(false);
      alert('Profile updated successfully');
      fetchDashboardData();
      fetchProfile();
    } catch (error) {
      console.error('Error updating profile:', error);
      alert('Failed to update profile. Please try again.');
    }
  };

  const getPredictionColor = (prediction) => {
    if (!prediction) return 'neutral';
    return prediction.toLowerCase().includes('malignant') ? 'error' : 'success';
  };

  const getRiskColor = (riskLevel) => {
    if (!riskLevel) return 'neutral';
    const level = riskLevel.toLowerCase();
    if (level.includes('very high') || level.includes('high')) return 'error';
    if (level.includes('moderate')) return 'warning';
    return 'success';
  };

  const navigationItems = [
    { id: 'overview', label: 'Overview', icon: '■', active: activeTab === 'overview', onClick: () => setActiveTab('overview') },
    { id: 'scans', label: 'My Scans', icon: '⬒', active: activeTab === 'scans', onClick: () => setActiveTab('scans'), badge: scans.length },
  ];

  if (selectedScan) {
    navigationItems.push({
      id: 'scanDetails',
      label: 'Scan Details',
      icon: '▦',
      active: activeTab === 'scanDetails',
      onClick: () => setActiveTab('scanDetails')
    });
  }

  const scanColumns = [
    {
      header: 'Scan Number',
      accessor: 'scan_number',
      width: '160px',
      render: (row) => <span className="eds-text-mono" style={{ fontWeight: 600 }}>{row.scan_number}</span>,
    },
    {
      header: 'Date',
      accessor: 'scan_date',
      width: '140px',
      render: (row) => <span className="eds-text-small">{new Date(row.scan_date).toLocaleDateString()}</span>,
    },
    {
      header: 'Result',
      accessor: 'prediction',
      width: '140px',
      render: (row) => row.prediction ? (
        <span className={`eds-badge eds-badge-${getPredictionColor(row.prediction)}`}>
          {row.prediction}
        </span>
      ) : <span className="eds-text-muted">Pending</span>,
    },
    {
      header: 'Risk Level',
      accessor: 'risk_level',
      width: '140px',
      render: (row) => row.risk_level ? (
        <span className={`eds-badge eds-badge-${getRiskColor(row.risk_level)}`}>
          {row.risk_level}
        </span>
      ) : <span className="eds-text-muted">N/A</span>,
    },
    {
      header: 'Confidence',
      accessor: 'confidence',
      width: '120px',
      render: (row) => row.confidence ? (
        <span className="eds-text-mono">{(row.confidence * 100).toFixed(1)}%</span>
      ) : <span className="eds-text-muted">N/A</span>,
    },
    {
      header: 'Status',
      accessor: 'status',
      width: '120px',
      render: (row) => <span className="eds-badge eds-badge-neutral">{row.status}</span>,
    },
    {
      header: 'Actions',
      accessor: 'id',
      width: '180px',
      render: (row) => (
        <div style={{ display: 'flex', gap: 'var(--eds-space-2)' }}>
          <button
            className="eds-button eds-button-sm eds-button-secondary"
            onClick={(e) => {
              e.stopPropagation();
              handleViewScanDetails(row);
            }}
          >
            View
          </button>
          <button
            className="eds-button eds-button-sm eds-button-primary"
            onClick={(e) => {
              e.stopPropagation();
              handleDownloadReport(row.id, row.scan_number);
            }}
            disabled={downloadingReport === row.id}
          >
            {downloadingReport === row.id ? 'Loading...' : 'Report'}
          </button>
        </div>
      ),
    },
  ];

  if (loading) {
    return <LoadingSpinner message="Loading your dashboard..." />;
  }

  return (
    <EnterpriseLayout
      user={user}
      pageTitle={`Welcome, ${dashboardData?.patient_name || user?.full_name || 'Patient'}`}
      navigationItems={navigationItems}
    >
      {activeTab === 'overview' && (
        <div>
          {/* Patient Info Header */}
          <div className="eds-card" style={{ marginBottom: 'var(--eds-space-8)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
              <div>
                <div className="eds-text-small" style={{ marginBottom: 'var(--eds-space-2)' }}>Patient Information</div>
                <div style={{ display: 'flex', gap: 'var(--eds-space-6)', flexWrap: 'wrap' }}>
                  <div>
                    <span className="eds-text-small" style={{ color: 'var(--eds-color-text-muted)' }}>MRN: </span>
                    <span className="eds-text-mono">{dashboardData?.mrn}</span>
                  </div>
                  <div>
                    <span className="eds-text-small" style={{ color: 'var(--eds-color-text-muted)' }}>Age: </span>
                    <span>{dashboardData?.age}</span>
                  </div>
                  <div>
                    <span className="eds-text-small" style={{ color: 'var(--eds-color-text-muted)' }}>Gender: </span>
                    <span>{dashboardData?.gender}</span>
                  </div>
                </div>
              </div>
              <button
                className="eds-button eds-button-secondary"
                onClick={() => setShowProfileModal(true)}
              >
                Edit Profile
              </button>
            </div>
          </div>

          {/* Metrics */}
          {dashboardData && (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: 'var(--eds-space-4)',
              marginBottom: 'var(--eds-space-8)'
            }}>
              <EnterpriseMetricTile
                label="Total Scans"
                value={dashboardData.total_scans || 0}
                subtitle="All time"
              />
              <EnterpriseMetricTile
                label="Scans This Year"
                value={dashboardData.scans_this_year || 0}
                subtitle={new Date().getFullYear().toString()}
              />
              <EnterpriseMetricTile
                label="Healthy Results"
                value={dashboardData.benign_results || 0}
                subtitle="Benign findings"
              />
              <EnterpriseMetricTile
                label="Last Scan"
                value={dashboardData.last_scan_date ? new Date(dashboardData.last_scan_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : 'N/A'}
                subtitle="Most recent"
              />
            </div>
          )}

          {/* Health Summary */}
          <div className="eds-card" style={{ marginBottom: 'var(--eds-space-6)' }}>
            <h3 className="eds-card-title">Health Summary</h3>
            <div style={{ marginTop: 'var(--eds-space-4)' }}>
              <p className="eds-text-body">
                {dashboardData?.malignant_results > 0
                  ? 'Some scans show areas that require follow-up with your doctor. Please consult with your healthcare provider for next steps.'
                  : 'Based on your scan history, no high-risk indicators have been detected. Continue regular screenings as recommended by your doctor.'}
              </p>
              {dashboardData?.malignant_results > 0 && (
                <div style={{
                  marginTop: 'var(--eds-space-4)',
                  padding: 'var(--eds-space-4)',
                  background: 'var(--eds-color-warning-bg)',
                  border: '1px solid var(--eds-color-warning-border)',
                  borderRadius: 'var(--eds-radius-md)'
                }}>
                  <strong>Action Required:</strong> {dashboardData.malignant_results} scan(s) require medical consultation.
                </div>
              )}
            </div>
          </div>

          {/* Recent Scans */}
          <div className="eds-card" style={{ marginBottom: 'var(--eds-space-6)' }}>
            <h3 className="eds-card-title">Recent Scans</h3>
            <div style={{ marginTop: 'var(--eds-space-4)' }}>
              {scans.length === 0 ? (
                <p className="eds-text-body" style={{ color: 'var(--eds-color-text-muted)', textAlign: 'center', padding: 'var(--eds-space-8)' }}>
                  No scans found. Your scan history will appear here once you have your first screening.
                </p>
              ) : (
                <EnterpriseTable
                  columns={scanColumns.slice(0, -1).concat([{
                    header: '',
                    accessor: 'id',
                    width: '100px',
                    render: (row) => (
                      <button
                        className="eds-button eds-button-sm eds-button-secondary"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewScanDetails(row);
                        }}
                      >
                        View
                      </button>
                    ),
                  }])}
                  data={scans.slice(0, 5)}
                  emptyMessage="No scans available"
                />
              )}
            </div>
          </div>

          {/* Contact Information */}
          <div className="eds-card">
            <h3 className="eds-card-title">Contact Information</h3>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: 'var(--eds-space-4)',
              marginTop: 'var(--eds-space-4)'
            }}>
              <div>
                <div className="eds-text-small" style={{ marginBottom: 'var(--eds-space-1)' }}>Email</div>
                <div className="eds-text-body">{dashboardData?.email || 'Not provided'}</div>
              </div>
              <div>
                <div className="eds-text-small" style={{ marginBottom: 'var(--eds-space-1)' }}>Phone</div>
                <div className="eds-text-body">{dashboardData?.phone || 'Not provided'}</div>
              </div>
              <div>
                <div className="eds-text-small" style={{ marginBottom: 'var(--eds-space-1)' }}>Hospital</div>
                <div className="eds-text-body">{dashboardData?.hospital_name || 'N/A'}</div>
              </div>
              <div>
                <div className="eds-text-small" style={{ marginBottom: 'var(--eds-space-1)' }}>Emergency Contact</div>
                <div className="eds-text-body">
                  {dashboardData?.emergency_contact_name
                    ? `${dashboardData.emergency_contact_name} - ${dashboardData.emergency_contact_phone}`
                    : 'Not provided'}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'scans' && (
        <div className="eds-card">
          <h3 className="eds-card-title">All Scans</h3>
          <div style={{ marginTop: 'var(--eds-space-4)' }}>
            <EnterpriseTable
              columns={scanColumns}
              data={scans}
              emptyMessage="No scan history available"
            />
          </div>
        </div>
      )}

      {activeTab === 'scanDetails' && selectedScan && (
        <div>
          <button
            className="eds-button eds-button-secondary"
            onClick={() => setActiveTab('scans')}
            style={{ marginBottom: 'var(--eds-space-6)' }}
          >
            ← Back to Scans
          </button>

          <div className="eds-card" style={{ marginBottom: 'var(--eds-space-6)' }}>
            <h2 className="eds-heading-3">Scan Details: {selectedScan.scan_number}</h2>
            <div className="eds-text-small" style={{ marginTop: 'var(--eds-space-2)' }}>
              {new Date(selectedScan.scan_date).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </div>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: 'var(--eds-space-6)',
            marginBottom: 'var(--eds-space-6)'
          }}>
            <div className="eds-card">
              <h4 className="eds-card-title">Analysis Results</h4>
              <div style={{ marginTop: 'var(--eds-space-4)' }}>
                <div style={{ marginBottom: 'var(--eds-space-3)' }}>
                  <span className="eds-text-small">Prediction:</span>
                  <div style={{ marginTop: 'var(--eds-space-1)' }}>
                    <span className={`eds-badge eds-badge-${getPredictionColor(selectedScan.prediction)}`}>
                      {selectedScan.prediction || 'Pending'}
                    </span>
                  </div>
                </div>
                <div style={{ marginBottom: 'var(--eds-space-3)' }}>
                  <span className="eds-text-small">Risk Level:</span>
                  <div style={{ marginTop: 'var(--eds-space-1)' }}>
                    <span className={`eds-badge eds-badge-${getRiskColor(selectedScan.risk_level)}`}>
                      {selectedScan.risk_level || 'N/A'}
                    </span>
                  </div>
                </div>
                <div>
                  <span className="eds-text-small">Confidence:</span>
                  <div style={{ marginTop: 'var(--eds-space-1)', fontSize: 'var(--eds-font-size-lg)', fontWeight: 600 }}>
                    {selectedScan.confidence ? `${(selectedScan.confidence * 100).toFixed(2)}%` : 'N/A'}
                  </div>
                </div>
              </div>
            </div>

            <div className="eds-card">
              <h4 className="eds-card-title">Medical Information</h4>
              <div style={{ marginTop: 'var(--eds-space-4)' }}>
                <div style={{ marginBottom: 'var(--eds-space-3)' }}>
                  <span className="eds-text-small">Reviewed By:</span>
                  <div style={{ marginTop: 'var(--eds-space-1)' }}>
                    {selectedScan.doctor_name || 'Pending Review'}
                  </div>
                </div>
                <div>
                  <span className="eds-text-small">Status:</span>
                  <div style={{ marginTop: 'var(--eds-space-1)' }}>
                    <span className="eds-badge eds-badge-neutral">{selectedScan.status}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {selectedScan.doctor_notes && (
            <div className="eds-card" style={{ marginBottom: 'var(--eds-space-6)' }}>
              <h4 className="eds-card-title">Doctor's Notes</h4>
              <div className="eds-text-body" style={{ marginTop: 'var(--eds-space-4)' }}>
                {selectedScan.doctor_notes}
              </div>
            </div>
          )}

          {selectedScan.findings && (
            <div className="eds-card" style={{ marginBottom: 'var(--eds-space-6)' }}>
              <h4 className="eds-card-title">AI Findings</h4>
              <div className="eds-text-body" style={{ marginTop: 'var(--eds-space-4)' }}>
                {selectedScan.findings}
              </div>
            </div>
          )}

          <button
            className="eds-button eds-button-primary"
            onClick={() => handleDownloadReport(selectedScan.id, selectedScan.scan_number)}
            disabled={downloadingReport === selectedScan.id}
          >
            {downloadingReport === selectedScan.id ? 'Downloading...' : 'Download Full Report'}
          </button>
        </div>
      )}

      {/* Profile Edit Modal */}
      {showProfileModal && (
        <div className="eds-modal-overlay" onClick={() => setShowProfileModal(false)}>
          <div className="eds-modal" onClick={(e) => e.stopPropagation()}>
            <div className="eds-modal-header">
              <h2 className="eds-modal-title">Edit Profile</h2>
              <button className="eds-modal-close" onClick={() => setShowProfileModal(false)}>
                ×
              </button>
            </div>
            <form onSubmit={handleUpdateProfile}>
              <div className="eds-modal-body">
                <div className="eds-form-group">
                  <label className="eds-form-label">Email Address</label>
                  <input
                    className="eds-form-input"
                    type="email"
                    value={profileData.email || fullPatientProfile?.email || 'Not provided'}
                    readOnly
                    style={{ background: 'var(--eds-color-surface-raised)', cursor: 'not-allowed' }}
                  />
                  <span className="eds-form-hint">Email cannot be changed</span>
                </div>

                <div className="eds-form-group">
                  <label className="eds-form-label">Phone Number</label>
                  <input
                    className="eds-form-input"
                    type="tel"
                    value={profileData.phone}
                    onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                    placeholder="+1-xxx-xxx-xxxx"
                  />
                </div>

                <div className="eds-form-group">
                  <label className="eds-form-label">Address</label>
                  <textarea
                    className="eds-form-textarea"
                    value={profileData.address}
                    onChange={(e) => setProfileData({ ...profileData, address: e.target.value })}
                    placeholder="Your address"
                    rows="3"
                  />
                </div>

                <div style={{
                  borderTop: '1px solid var(--eds-color-border)',
                  marginTop: 'var(--eds-space-6)',
                  paddingTop: 'var(--eds-space-6)'
                }}>
                  <h4 style={{ fontSize: 'var(--eds-font-size-md)', fontWeight: 600, marginBottom: 'var(--eds-space-4)' }}>
                    Emergency Contact
                  </h4>

                  <div className="eds-form-group">
                    <label className="eds-form-label">Contact Name</label>
                    <input
                      className="eds-form-input"
                      type="text"
                      value={profileData.emergency_contact_name}
                      onChange={(e) => setProfileData({ ...profileData, emergency_contact_name: e.target.value })}
                      placeholder="Full name"
                    />
                  </div>

                  <div className="eds-form-group">
                    <label className="eds-form-label">Contact Phone</label>
                    <input
                      className="eds-form-input"
                      type="tel"
                      value={profileData.emergency_contact_phone}
                      onChange={(e) => setProfileData({ ...profileData, emergency_contact_phone: e.target.value })}
                      placeholder="+1-xxx-xxx-xxxx"
                    />
                  </div>
                </div>
              </div>

              <div className="eds-modal-footer">
                <button
                  type="button"
                  className="eds-button eds-button-secondary"
                  onClick={() => setShowProfileModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="eds-button eds-button-primary">
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </EnterpriseLayout>
  );
};

export default PatientDashboard;
