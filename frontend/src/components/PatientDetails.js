/**
 * Patient Details Page
 * Shows complete patient information, medical history, and scans
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import LoadingSpinner from './LoadingSpinner';
import './PatientDetails.css';

// API Base URL - uses environment variable for production, falls back to localhost for development
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001/api';

const PatientDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [patient, setPatient] = useState(null);
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('profile');

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
    }
  };

  useEffect(() => {
    fetchPatientDetails();
    fetchPatientScans();
  }, [id]);

  const fetchPatientDetails = async () => {
    try {
      const response = await axiosInstance.get(`/hospital-admin/patients/${id}`);
      setPatient(response.data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching patient details:', err);
      setError('Failed to load patient details');
      setLoading(false);
    }
  };

  const fetchPatientScans = async () => {
    try {
      const response = await axiosInstance.get(`/medical-staff/patients/${id}/history`);
      setScans(response.data);
    } catch (err) {
      console.error('Error fetching patient scans:', err);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading patient details..." />;
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>❌ {error}</h2>
        <button onClick={() => navigate(-1)}>← Go Back</button>
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="error-container">
        <h2>❌ Patient not found</h2>
        <button onClick={() => navigate(-1)}>← Go Back</button>
      </div>
    );
  }

  return (
    <div className="patient-details-container">
      {/* Header */}
      <div className="details-header">
        <button className="btn-back" onClick={() => navigate(-1)}>
          ← Back to Dashboard
        </button>
        <h1>Patient Details</h1>
      </div>

      {/* Patient Info Card */}
      <div className="patient-info-card">
        <div className="patient-avatar-large">
          {patient.full_name.charAt(0)}
        </div>
        <div className="patient-header-info">
          <h2>{patient.full_name}</h2>
          <p className="patient-mrn">MRN: {patient.mrn}</p>
          <div className="patient-quick-info">
            <span>📧 {patient.email}</span>
            <span>📞 {patient.phone}</span>
            <span>🎂 {new Date(patient.date_of_birth).toLocaleDateString()}</span>
            <span>👤 {patient.gender}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="details-tabs">
        <button
          className={activeTab === 'profile' ? 'active' : ''}
          onClick={() => setActiveTab('profile')}
        >
          Profile
        </button>
        <button
          className={activeTab === 'scans' ? 'active' : ''}
          onClick={() => setActiveTab('scans')}
        >
          Scans ({scans.length})
        </button>
        <button
          className={activeTab === 'medical' ? 'active' : ''}
          onClick={() => setActiveTab('medical')}
        >
          Medical History
        </button>
      </div>

      {/* Tab Content */}
      <div className="details-content">
        {activeTab === 'profile' && (
          <div className="profile-section">
            <div className="info-grid">
              <div className="info-item">
                <label>Full Name:</label>
                <span>{patient.full_name}</span>
              </div>
              <div className="info-item">
                <label>MRN:</label>
                <span>{patient.mrn}</span>
              </div>
              <div className="info-item">
                <label>Email:</label>
                <span>{patient.email}</span>
              </div>
              <div className="info-item">
                <label>Phone:</label>
                <span>{patient.phone}</span>
              </div>
              <div className="info-item">
                <label>Date of Birth:</label>
                <span>{new Date(patient.date_of_birth).toLocaleDateString()}</span>
              </div>
              <div className="info-item">
                <label>Gender:</label>
                <span>{patient.gender}</span>
              </div>
              <div className="info-item">
                <label>Blood Group:</label>
                <span>{patient.blood_group || 'Not specified'}</span>
              </div>
              <div className="info-item">
                <label>Address:</label>
                <span>{patient.address || 'Not provided'}</span>
              </div>
              <div className="info-item">
                <label>City:</label>
                <span>{patient.city || 'Not provided'}</span>
              </div>
              <div className="info-item">
                <label>State:</label>
                <span>{patient.state || 'Not provided'}</span>
              </div>
              <div className="info-item">
                <label>Emergency Contact:</label>
                <span>{patient.emergency_contact_name || 'Not provided'}</span>
              </div>
              <div className="info-item">
                <label>Emergency Phone:</label>
                <span>{patient.emergency_contact_phone || 'Not provided'}</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'scans' && (
          <div className="scans-section">
            {scans.length === 0 ? (
              <div className="empty-state">
                <p>No scans found for this patient.</p>
              </div>
            ) : (
              <div className="scans-table">
                <table>
                  <thead>
                    <tr>
                      <th>Scan ID</th>
                      <th>Date</th>
                      <th>Prediction</th>
                      <th>Risk Level</th>
                      <th>Confidence</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scans.map((scan) => (
                      <tr key={scan.id}>
                        <td>{scan.scan_number}</td>
                        <td>{new Date(scan.scan_date).toLocaleDateString()}</td>
                        <td>
                          <span className={`badge ${scan.prediction === 'malignant' ? 'danger' : 'success'}`}>
                            {scan.prediction}
                          </span>
                        </td>
                        <td>{scan.risk_assessment || 'N/A'}</td>
                        <td>{scan.confidence_score ? `${(scan.confidence_score * 100).toFixed(1)}%` : 'N/A'}</td>
                        <td>
                          <span className={`badge ${scan.status}`}>{scan.status}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {activeTab === 'medical' && (
          <div className="medical-section">
            <div className="medical-history">
              <h3>Medical History</h3>
              {patient.medical_history_json && Object.keys(patient.medical_history_json).length > 0 ? (
                <pre>{JSON.stringify(patient.medical_history_json, null, 2)}</pre>
              ) : (
                <p>No medical history recorded.</p>
              )}
            </div>

            <div className="family-history">
              <h3>Family History</h3>
              {patient.family_history_json && Object.keys(patient.family_history_json).length > 0 ? (
                <pre>{JSON.stringify(patient.family_history_json, null, 2)}</pre>
              ) : (
                <p>No family history recorded.</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PatientDetails;

