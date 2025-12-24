/**
 * Patient Dashboard
 * Personal health dashboard for patients to view their scan history and reports
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import LoadingSpinner from './LoadingSpinner';
import LogoutButton from './LogoutButton';
import './PatientDashboard.css';

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

const PatientDashboard = () => {
  const { user } = useAuth();
  
  // Create axios-like instance using fetch
  const axiosInstance = {
    get: async (url, config = {}) => {
      const token = localStorage.getItem('token');
      const fetchUrl = url.startsWith('http') ? url : `http://localhost:8001/api${url}`;
      const response = await fetch(fetchUrl, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          ...config.headers
        },
        ...(config.responseType && { responseType: config.responseType })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      // Handle blob response for file downloads
      if (config.responseType === 'blob') {
        return { data: await response.blob() };
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
    fetchProfile(); // ✅ ADDED: Fetch full profile including email/phone
  }, []);

  const fetchDashboardData = async () => {
    try {
      // ✅ FIXED: Use correct endpoint /patient-portal/dashboard
      const response = await axiosInstance.get('/patient-portal/dashboard');
      console.log('✅ Dashboard data received:', response.data);
      setDashboardData(response.data);
      setLoading(false);
    } catch (error) {
      console.error('❌ Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  const fetchScans = async () => {
    try {
      // ✅ FIXED: Use correct endpoint /patient-portal/scans
      const response = await axiosInstance.get('/patient-portal/scans');
      console.log('✅ Patient scans received:', response.data);
      setScans(response.data);
    } catch (error) {
      console.error('❌ Error fetching scans:', error);
    }
  };

  const fetchProfile = async () => {
    try {
      // ✅ NEW: Fetch full patient profile with email, phone, etc.
      const response = await axiosInstance.get('/patient-portal/profile');
      console.log('✅ Patient profile received:', response.data);
      setFullPatientProfile(response.data);
      // Populate profile form data
      setProfileData({
        email: response.data.email || '',
        phone: response.data.phone || '',
        address: response.data.address || '',
        emergency_contact_name: response.data.emergency_contact_name || '',
        emergency_contact_phone: response.data.emergency_contact_phone || '',
      });
    } catch (error) {
      console.error('❌ Error fetching profile:', error);
    }
  };

  const handleDownloadReport = async (scanId, scanNumber) => {
    setDownloadingReport(scanId);
    try {
      // ✅ FIXED: Use correct endpoint /patient-portal/scans/{scanId}/download-report
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
      console.error('❌ Error downloading report:', error);
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
      // ✅ FIXED: Use correct endpoint /patient-portal/profile
      await axiosInstance.put('/patient-portal/profile', profileData);
      setShowProfileModal(false);
      alert('Profile updated successfully!');
      fetchDashboardData();
      fetchProfile(); // ✅ ADDED: Refresh profile data after update
    } catch (error) {
      console.error('❌ Error updating profile:', error);
      alert('Failed to update profile. Please try again.');
    }
  };

  const getRiskBadgeColor = (riskLevel) => {
    if (!riskLevel) return colors.textMuted;
    const level = riskLevel.toLowerCase();
    if (level.includes('very high') || level.includes('high')) return colors.error;
    if (level.includes('moderate')) return colors.warning;
    return colors.success;
  };

  const getPredictionBadgeColor = (prediction) => {
    if (!prediction) return colors.textMuted;
    const pred = prediction.toLowerCase();
    if (pred.includes('malignant')) return colors.error;
    return colors.success;
  };

  if (loading) {
    return <LoadingSpinner message="Loading your dashboard..." />;
  }

  return (
    <div className="patient-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div>
          <h1>👤 Welcome, {dashboardData?.patient_name || user?.full_name}</h1>
          <p>MRN: <strong>{dashboardData?.mrn}</strong> | Age: <strong>{dashboardData?.age}</strong> | Gender: <strong>{dashboardData?.gender}</strong></p>
        </div>
        <div className="header-actions">
          <button className="btn-profile" onClick={() => setShowProfileModal(true)}>
            ⚙️ Edit Profile
          </button>
          <LogoutButton variant="sidebar" />
        </div>
      </div>

      {/* Statistics Cards */}
      {dashboardData && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon" style={{ background: colors.primary }}>
              🔬
            </div>
            <div className="stat-content">
              <h3>{dashboardData.total_scans || 0}</h3>
              <p>Total Scans</p>
              <span className="stat-detail">All time</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: colors.secondary }}>
              📊
            </div>
            <div className="stat-content">
              <h3>{dashboardData.scans_this_year || 0}</h3>
              <p>Scans This Year</p>
              <span className="stat-detail">{new Date().getFullYear()}</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: colors.success }}>
              ✓
            </div>
            <div className="stat-content">
              <h3>{dashboardData.benign_results || 0}</h3>
              <p>Benign Results</p>
              <span className="stat-detail">Healthy tissue</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: colors.info }}>
              📅
            </div>
            <div className="stat-content">
              <h3>{dashboardData.last_scan_date ? new Date(dashboardData.last_scan_date).toLocaleDateString() : 'N/A'}</h3>
              <p>Last Scan</p>
              <span className="stat-detail">Most recent</span>
            </div>
          </div>
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
            className={`tab ${activeTab === 'scans' ? 'active' : ''}`}
            onClick={() => setActiveTab('scans')}
          >
            🔬 My Scans ({scans.length})
          </button>
          <button
            className={`tab ${activeTab === 'scanDetails' ? 'active' : ''}`}
            onClick={() => setActiveTab('scanDetails')}
            disabled={!selectedScan}
          >
            📄 Scan Details
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            <div className="section">
              <h2>Health Summary</h2>
              <div className="health-summary">
                <div className="summary-card">
                  <h4>📊 Risk Assessment</h4>
                  <p>
                    Based on your scan history, {dashboardData?.malignant_results > 0 
                      ? 'some scans show areas that require follow-up with your doctor.' 
                      : 'no high-risk indicators have been detected. Continue regular screenings.'}
                  </p>
                  {dashboardData?.malignant_results > 0 && (
                    <div className="alert-box warning">
                      <strong>⚠️ Action Required:</strong> {dashboardData.malignant_results} scan(s) require medical consultation.
                    </div>
                  )}
                </div>

                <div className="summary-card">
                  <h4>📅 Screening Schedule</h4>
                  <p>
                    {dashboardData?.next_screening_due 
                      ? `Your next screening is due on ${new Date(dashboardData.next_screening_due).toLocaleDateString()}.`
                      : 'Please consult with your doctor for screening schedule recommendations.'}
                  </p>
                  <ul className="recommendations">
                    <li>Monthly self-breast examinations</li>
                    <li>Annual clinical breast examination</li>
                    <li>Regular mammogram screening (age-dependent)</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="section">
              <h2>Recent Scans</h2>
              {scans.length === 0 ? (
                <div className="empty-state">
                  <p>No scans found. Your scan history will appear here once you have your first screening.</p>
                </div>
              ) : (
                <div className="scans-list">
                  {scans.slice(0, 5).map((scan) => (
                    <div key={scan.id} className="scan-card-mini" onClick={() => handleViewScanDetails(scan)}>
                      <div className="scan-info">
                        <span className="scan-number">{scan.scan_number}</span>
                        <span className="scan-date">
                          {new Date(scan.scan_date).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="scan-result">
                        {scan.prediction && (
                          <span
                            className="prediction-badge"
                            style={{
                              background: `${getPredictionBadgeColor(scan.prediction)}20`,
                              color: getPredictionBadgeColor(scan.prediction),
                            }}
                          >
                            {scan.prediction}
                          </span>
                        )}
                        <span
                          className="risk-badge"
                          style={{
                            background: `${getRiskBadgeColor(scan.risk_level)}20`,
                            color: getRiskBadgeColor(scan.risk_level),
                          }}
                        >
                          {scan.risk_level || 'N/A'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="section">
              <h2>Contact Information</h2>
              <div className="contact-grid">
                <div className="contact-item">
                  <strong>📧 Email:</strong>
                  <span>{dashboardData?.email || 'Not provided'}</span>
                </div>
                <div className="contact-item">
                  <strong>📞 Phone:</strong>
                  <span>{dashboardData?.phone || 'Not provided'}</span>
                </div>
                <div className="contact-item">
                  <strong>🏥 Hospital:</strong>
                  <span>{dashboardData?.hospital_name || 'N/A'}</span>
                </div>
                <div className="contact-item">
                  <strong>🚨 Emergency Contact:</strong>
                  <span>
                    {dashboardData?.emergency_contact_name 
                      ? `${dashboardData.emergency_contact_name} - ${dashboardData.emergency_contact_phone}`
                      : 'Not provided'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'scans' && (
          <div className="scans-tab">
            <div className="scans-table-container">
              {scans.length === 0 ? (
                <div className="empty-state">
                  <p>No scan history available.</p>
                </div>
              ) : (
                <table className="scans-table">
                  <thead>
                    <tr>
                      <th>Scan #</th>
                      <th>Date</th>
                      <th>Prediction</th>
                      <th>Risk Level</th>
                      <th>Confidence</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scans.map((scan) => (
                      <tr key={scan.id}>
                        <td>
                          <span className="scan-number-badge">{scan.scan_number}</span>
                        </td>
                        <td>{new Date(scan.scan_date).toLocaleDateString()}</td>
                        <td>
                          <span
                            className="prediction-badge"
                            style={{
                              background: `${getPredictionBadgeColor(scan.prediction)}20`,
                              color: getPredictionBadgeColor(scan.prediction),
                            }}
                          >
                            {scan.prediction || 'Pending'}
                          </span>
                        </td>
                        <td>
                          <span
                            className="risk-badge"
                            style={{
                              background: `${getRiskBadgeColor(scan.risk_level)}20`,
                              color: getRiskBadgeColor(scan.risk_level),
                            }}
                          >
                            {scan.risk_level || 'N/A'}
                          </span>
                        </td>
                        <td>{scan.confidence ? `${(scan.confidence * 100).toFixed(1)}%` : 'N/A'}</td>
                        <td>
                          <span className={`status-badge ${scan.status}`}>
                            {scan.status}
                          </span>
                        </td>
                        <td>
                          <div className="action-buttons">
                            <button
                              className="btn-view"
                              onClick={() => handleViewScanDetails(scan)}
                            >
                              View
                            </button>
                            <button
                              className="btn-download"
                              onClick={() => handleDownloadReport(scan.id, scan.scan_number)}
                              disabled={downloadingReport === scan.id}
                            >
                              {downloadingReport === scan.id ? 'Downloading...' : '📥 Report'}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {activeTab === 'scanDetails' && selectedScan && (
          <div className="scan-details-tab">
            <button className="btn-back" onClick={() => setActiveTab('scans')}>
              ← Back to Scans
            </button>
            
            <div className="scan-details-header">
              <h2>Scan Details: {selectedScan.scan_number}</h2>
              <span className="scan-date">
                {new Date(selectedScan.scan_date).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </span>
            </div>

            <div className="scan-details-grid">
              <div className="detail-card">
                <h4>🔬 Analysis Results</h4>
                <div className="detail-row">
                  <span>Prediction:</span>
                  <strong
                    style={{ color: getPredictionBadgeColor(selectedScan.prediction) }}
                  >
                    {selectedScan.prediction || 'Pending'}
                  </strong>
                </div>
                <div className="detail-row">
                  <span>Risk Level:</span>
                  <strong style={{ color: getRiskBadgeColor(selectedScan.risk_level) }}>
                    {selectedScan.risk_level || 'N/A'}
                  </strong>
                </div>
                <div className="detail-row">
                  <span>Confidence:</span>
                  <strong>
                    {selectedScan.confidence
                      ? `${(selectedScan.confidence * 100).toFixed(2)}%`
                      : 'N/A'}
                  </strong>
                </div>
              </div>

              <div className="detail-card">
                <h4>📊 Probabilities</h4>
                <div className="detail-row">
                  <span>Malignant:</span>
                  <strong style={{ color: colors.error }}>
                    {selectedScan.malignant_probability
                      ? `${selectedScan.malignant_probability.toFixed(2)}%`
                      : 'N/A'}
                  </strong>
                </div>
                <div className="detail-row">
                  <span>Benign:</span>
                  <strong style={{ color: colors.success }}>
                    {selectedScan.benign_probability
                      ? `${selectedScan.benign_probability.toFixed(2)}%`
                      : 'N/A'}
                  </strong>
                </div>
              </div>

              <div className="detail-card">
                <h4>👨‍⚕️ Medical Information</h4>
                <div className="detail-row">
                  <span>Reviewed By:</span>
                  <strong>{selectedScan.doctor_name || 'Pending Review'}</strong>
                </div>
                <div className="detail-row">
                  <span>Status:</span>
                  <span className={`status-badge ${selectedScan.status}`}>
                    {selectedScan.status}
                  </span>
                </div>
              </div>
            </div>

            {selectedScan.doctor_notes && (
              <div className="doctor-notes">
                <h4>📝 Doctor's Notes</h4>
                <div className="notes-content">
                  {selectedScan.doctor_notes}
                </div>
              </div>
            )}

            {selectedScan.findings && (
              <div className="findings">
                <h4>🔍 AI Findings</h4>
                <div className="findings-content">
                  {selectedScan.findings}
                </div>
              </div>
            )}

            <div className="scan-actions">
              <button
                className="btn-download-full"
                onClick={() => handleDownloadReport(selectedScan.id, selectedScan.scan_number)}
                disabled={downloadingReport === selectedScan.id}
              >
                {downloadingReport === selectedScan.id ? 'Downloading...' : '📥 Download Full Report'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Profile Edit Modal */}
      {showProfileModal && (
        <div className="modal-overlay" onClick={() => setShowProfileModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Edit Profile</h2>
              <button className="close-button" onClick={() => setShowProfileModal(false)}>
                ×
              </button>
            </div>
            <form onSubmit={handleUpdateProfile} className="profile-form">
              <div className="form-group">
                <label>Email Address</label>
                <input
                  type="email"
                  value={profileData.email || fullPatientProfile?.email || 'Not provided'}
                  readOnly
                  style={{ background: '#f5f5f5', cursor: 'not-allowed' }}
                  title="Email cannot be changed through this form"
                />
                <small style={{ color: '#666' }}>Email cannot be changed</small>
              </div>

              <div className="form-group">
                <label>Phone Number</label>
                <input
                  type="tel"
                  value={profileData.phone}
                  onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                  placeholder="+91-xxx-xxx-xxxx"
                />
              </div>

              <div className="form-group">
                <label>Address</label>
                <textarea
                  value={profileData.address}
                  onChange={(e) => setProfileData({ ...profileData, address: e.target.value })}
                  placeholder="Your address"
                  rows="3"
                />
              </div>

              <div className="form-section-header">Emergency Contact</div>

              <div className="form-group">
                <label>Contact Name</label>
                <input
                  type="text"
                  value={profileData.emergency_contact_name}
                  onChange={(e) =>
                    setProfileData({ ...profileData, emergency_contact_name: e.target.value })
                  }
                  placeholder="Full name"
                />
              </div>

              <div className="form-group">
                <label>Contact Phone</label>
                <input
                  type="tel"
                  value={profileData.emergency_contact_phone}
                  onChange={(e) =>
                    setProfileData({ ...profileData, emergency_contact_phone: e.target.value })
                  }
                  placeholder="+91-xxx-xxx-xxxx"
                />
              </div>

              <div className="form-actions">
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => setShowProfileModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-submit">
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PatientDashboard;

