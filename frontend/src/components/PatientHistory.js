import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import './PatientHistory.css';

/**
 * All Patients History Component
 * 
 * Displays complete scan history for ALL patients:
 * - List of all patients with their scans
 * - Prediction results and risk levels
 * - Doctor notes
 * - Ability to view/download reports
 * - Search and filter capabilities
 */
const PatientHistory = ({ patient, onBack }) => {
  const { API_BASE_URL, getAuthHeader } = useAuth();

  const [allPatientsHistory, setAllPatientsHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [downloadingReport, setDownloadingReport] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedPatient, setExpandedPatient] = useState(null);

  useEffect(() => {
    fetchAllPatientsHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchAllPatientsHistory = async () => {
    setLoading(true);
    setError(null);

    try {
      console.log('📥 Fetching patients...');
      const response = await fetch(
        `${API_BASE_URL}/medical-staff/patients?limit=100`,
        {
          headers: {
            ...getAuthHeader()
          }
        }
      );

      console.log('📡 Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Error response:', errorText);
        throw new Error('Failed to fetch patients');
      }

      const patients = await response.json();
      console.log('✅ Received patients:', patients);
      
      // Ensure patients is an array
      const patientsArray = Array.isArray(patients) ? patients : [];
      
      // Fetch scans for each patient
      console.log('📥 Fetching scans for', patientsArray.length, 'patients...');
      const patientsWithHistory = await Promise.all(
        patientsArray.map(async (patient) => {
          try {
            // Fetch scans for this patient
            const scansResponse = await fetch(
              `${API_BASE_URL}/medical-staff/patients/${patient.id}/history`,
              {
                headers: {
                  ...getAuthHeader()
                }
              }
            );

            let scans = [];
            if (scansResponse.ok) {
              scans = await scansResponse.json();
              console.log(`✅ Fetched ${scans.length} scans for patient ${patient.full_name}`);
            } else {
              console.warn(`⚠️ Failed to fetch scans for patient ${patient.full_name}`);
            }

            // Sort scans by date (most recent first)
            scans.sort((a, b) => new Date(b.scan_date) - new Date(a.scan_date));

            return {
              patient: {
                id: patient?.id || null,
                mrn: patient?.mrn || 'N/A',
                full_name: patient?.full_name || 'Unknown',
                date_of_birth: patient?.date_of_birth || null,
                gender: patient?.gender || 'Unknown',
                phone: patient?.phone || null,
                email: patient?.email || null
              },
              scans: scans.map(scan => ({
                id: scan.id,
                scan_date: scan.scan_date,
                prediction_result: scan.prediction,
                risk_level: scan.risk_assessment,
                confidence_score: scan.confidence_score,
                doctor_name: scan.performed_by_name || 'Unknown',
                doctor_notes: scan.doctor_notes,
                report_generated: scan.status === 'completed'
              })),
              total_scans: scans.length,
              latest_scan: scans.length > 0 ? scans[0].scan_date : null
            };
          } catch (err) {
            console.error(`❌ Error fetching scans for patient ${patient.full_name}:`, err);
            return {
              patient: {
                id: patient?.id || null,
                mrn: patient?.mrn || 'N/A',
                full_name: patient?.full_name || 'Unknown',
                date_of_birth: patient?.date_of_birth || null,
                gender: patient?.gender || 'Unknown',
                phone: patient?.phone || null,
                email: patient?.email || null
              },
              scans: [],
              total_scans: 0,
              latest_scan: null
            };
          }
        })
      );
      
      console.log('✅ All patient histories loaded:', patientsWithHistory);
      setAllPatientsHistory(patientsWithHistory);
    } catch (err) {
      console.error('❌ Fetch error:', err);
      setError(err.message);
      setAllPatientsHistory([]); // Ensure it's always an array
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReport = async (scanId) => {
    setDownloadingReport(scanId);

    try {
      console.log('📥 Attempting to download report for scan:', scanId);
      console.log('🌐 API URL:', `${API_BASE_URL}/scans/${scanId}/download-report`);
      console.log('🔑 Auth headers:', getAuthHeader());

      const response = await fetch(
        `${API_BASE_URL}/medical-staff/scans/${scanId}/download-report`,
        {
          headers: {
            ...getAuthHeader()
          }
        }
      );

      console.log('📡 Response status:', response.status);
      console.log('📡 Response ok:', response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Error response:', errorText);
        throw new Error(`Failed to download report: ${response.status} ${response.statusText}`);
      }

      // Create blob and download
      const blob = await response.blob();
      console.log('📦 Blob size:', blob.size, 'bytes');

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `scan_${scanId}_report.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      console.log('✅ Report downloaded successfully!');
    } catch (err) {
      console.error('❌ Download error:', err);
      alert(`Error downloading report: ${err.message}`);
    } finally {
      setDownloadingReport(null);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return 'Invalid Date';
      
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      console.error('Error formatting date:', error);
      return 'N/A';
    }
  };

  const calculateAge = (dateString) => {
    if (!dateString) return 'N/A';
    
    try {
      const birthDate = new Date(dateString);
      if (isNaN(birthDate.getTime())) return 'N/A';
      
      const today = new Date();
      let age = today.getFullYear() - birthDate.getFullYear();
      const monthDiff = today.getMonth() - birthDate.getMonth();

      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
      }

      return age;
    } catch (error) {
      console.error('Error calculating age:', error);
      return 'N/A';
    }
  };

  const getRiskLevelClass = (riskLevel) => {
    if (!riskLevel) return 'risk-low';
    const level = String(riskLevel).toLowerCase();
    if (level.includes('very high') || level.includes('high')) {
      return 'risk-high';
    } else if (level.includes('moderate')) {
      return 'risk-moderate';
    } else {
      return 'risk-low';
    }
  };

  const getResultClass = (result) => {
    if (!result) return 'result-benign';
    return String(result).toLowerCase().includes('malignant') ? 'result-malignant' : 'result-benign';
  };

  const togglePatientExpansion = (patientId) => {
    setExpandedPatient(expandedPatient === patientId ? null : patientId);
  };

  // Filter patients based on search query
  const filteredPatients = Array.isArray(allPatientsHistory) 
    ? allPatientsHistory.filter((patientData) => {
        const patient = patientData?.patient;
        if (!patient) return false;
        
        const searchLower = searchQuery.toLowerCase();
        return (
          patient.full_name?.toLowerCase().includes(searchLower) ||
          patient.mrn?.toLowerCase().includes(searchLower) ||
          (patient.phone && patient.phone.includes(searchQuery))
        );
      })
    : [];

  if (loading) {
    return (
      <div className="patient-history-loading">
        <div className="loading-spinner"></div>
        <p>Loading all patients history...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="patient-history-error">
        <div className="error-icon">⚠️</div>
        <h3>Error Loading History</h3>
        <p>{error}</p>
        <button onClick={fetchAllPatientsHistory} className="btn-back">
          🔄 Retry
        </button>
      </div>
    );
  }

  return (
    <div className="patient-history all-patients-view">
      <div className="history-header">
        <div className="header-title">
          <h1>📋 All Patients History</h1>
          <p className="subtitle">Complete scan history and medical records for all patients</p>
        </div>
        <div className="header-stats">
          <div className="stat-badge">
            <span className="stat-number">{Array.isArray(allPatientsHistory) ? allPatientsHistory.length : 0}</span>
            <span className="stat-label">Total Patients</span>
          </div>
          <div className="stat-badge">
            <span className="stat-number">
              {Array.isArray(allPatientsHistory) 
                ? allPatientsHistory.reduce((sum, p) => sum + (p?.total_scans || 0), 0)
                : 0}
            </span>
            <span className="stat-label">Total Scans</span>
          </div>
        </div>
      </div>

      <div className="search-filter-bar">
        <div className="search-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Search by patient name, MRN, or phone..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>
        <button onClick={fetchAllPatientsHistory} className="btn-refresh">
          🔄 Refresh
        </button>
      </div>

      {!Array.isArray(filteredPatients) || filteredPatients.length === 0 ? (
        <div className="no-results">
          <div className="no-results-icon">🔍</div>
          <h3>{searchQuery ? 'No Patients Found' : 'No Patients Yet'}</h3>
          <p>
            {searchQuery
              ? 'Try adjusting your search criteria'
              : 'No patient records available in the system'}
          </p>
        </div>
      ) : (
        <div className="patients-history-list">
          {filteredPatients.map((patientData) => (
            <div key={patientData?.patient?.id || Math.random()} className="patient-history-card">
              <div
                className="patient-card-header"
                onClick={() => togglePatientExpansion(patientData.patient.id)}
              >
                <div className="patient-info-section">
                  <div className="patient-avatar-large">
                    {(() => {
                      const fullName = patientData?.patient?.full_name || 'Unknown';
                      const nameParts = fullName.split(' ');
                      const firstInitial = nameParts[0]?.[0] || 'U';
                      const lastInitial = nameParts[nameParts.length - 1]?.[0] || 'N';
                      return `${firstInitial}${lastInitial}`;
                    })()}
                  </div>
                  <div className="patient-basic-info">
                    <h2 className="patient-name">{patientData?.patient?.full_name || 'Unknown Patient'}</h2>
                    <div className="patient-meta-row">
                      <span className="meta-badge">
                        <strong>MRN:</strong> {patientData?.patient?.mrn || 'N/A'}
                      </span>
                      {patientData?.patient?.date_of_birth && (
                        <span className="meta-badge">
                          <strong>Age:</strong> {calculateAge(patientData.patient.date_of_birth)} years
                        </span>
                      )}
                      {patientData?.patient?.gender && (
                        <span className="meta-badge">
                          <strong>Gender:</strong> {patientData.patient.gender}
                        </span>
                      )}
                      {patientData?.patient?.phone && (
                        <span className="meta-badge">
                          <strong>📞</strong> {patientData.patient.phone}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="patient-stats-section">
                  <div className="stat-item">
                    <span className="stat-value">{patientData?.total_scans || 0}</span>
                    <span className="stat-label">Scans</span>
                  </div>
                  {patientData?.latest_scan && (
                    <div className="stat-item">
                      <span className="stat-value">
                        {new Date(patientData.latest_scan).toLocaleDateString()}
                      </span>
                      <span className="stat-label">Latest Scan</span>
                    </div>
                  )}
                  <div className="expand-icon">
                    {expandedPatient === patientData?.patient?.id ? '▼' : '▶'}
                  </div>
                </div>
              </div>

              {expandedPatient === patientData?.patient?.id && (
                <div className="patient-scans-section">
                  {(!patientData?.scans || patientData.scans.length === 0) ? (
                    <div className="no-scans-message">
                      <span className="no-scans-icon">📋</span>
                      <p>No scans recorded for this patient</p>
                    </div>
                  ) : (
                    <div className="scans-table-container">
                      <table className="scans-table">
                        <thead>
                          <tr>
                            <th>Scan ID</th>
                            <th>Date & Time</th>
                            <th>Prediction Result</th>
                            <th>Risk Level</th>
                            <th>Confidence</th>
                            <th>Doctor</th>
                            <th>Report</th>
                            <th>Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(patientData?.scans || []).map((scan) => (
                            <tr key={scan?.id || Math.random()}>
                              <td className="scan-id">#{scan?.id || 'N/A'}</td>
                              <td className="scan-date">
                                {scan?.scan_date ? formatDate(scan.scan_date) : 'N/A'}
                              </td>
                              <td>
                                <span className={`result-badge ${getResultClass(scan?.prediction_result || '')}`}>
                                  {scan?.prediction_result || 'Unknown'}
                                </span>
                              </td>
                              <td>
                                <span className={`risk-badge ${getRiskLevelClass(scan?.risk_level || 'Unknown')}`}>
                                  {scan?.risk_level || 'Unknown'}
                                </span>
                              </td>
                              <td className="confidence-cell">
                                {scan?.confidence_score 
                                  ? `${(scan.confidence_score * 100).toFixed(1)}%` 
                                  : 'N/A'}
                              </td>
                              <td className="doctor-cell">{scan?.doctor_name || 'N/A'}</td>
                              <td className="report-cell">
                                {scan?.report_generated ? (
                                  <span className="report-status generated">✓ Generated</span>
                                ) : (
                                  <span className="report-status pending">⏳ Pending</span>
                                )}
                              </td>
                              <td className="actions-cell">
                                <button
                                  className="btn-download-mini"
                                  onClick={() => handleDownloadReport(scan?.id)}
                                  disabled={downloadingReport === scan?.id || !scan?.id}
                                  title="Download Report"
                                >
                                  {downloadingReport === scan?.id ? '⏳' : '📥'}
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>

                      {patientData?.scans?.[0]?.doctor_notes && (
                        <div className="doctor-notes-section">
                          <h4>📝 Latest Doctor's Notes:</h4>
                          <p>{patientData.scans[0].doctor_notes}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PatientHistory;

