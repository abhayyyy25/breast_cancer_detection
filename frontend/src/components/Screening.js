import React, { useState } from "react";
import { useAuth } from '../context/AuthContext';
import PatientManagement from './PatientManagement';
import DisclaimerModal from './DisclaimerModal';
import './Screening.css';

/**
 * Enhanced Screening Component
 * 
 * Hospital System workflow:
 * 1. Select patient
 * 2. Accept disclaimer
 * 3. Upload scan
 * 4. View AI analysis results
 */
function Screening({ onViewHistory }) {
  const { API_BASE_URL, getAuthHeader } = useAuth();

  const [selectedPatient, setSelectedPatient] = useState(null);
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [disclaimerAccepted, setDisclaimerAccepted] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [doctorNotes, setDoctorNotes] = useState('');

  const handlePatientSelect = (patient) => {
    setSelectedPatient(patient);
    setResults(null); // Clear previous results
    setError(null);
    setSelectedFile(null);
    setPreviewUrl(null);
    setDisclaimerAccepted(false);
    setShowDisclaimer(false);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        setError('Please select an image file');
        return;
      }

      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setError(null);
      // Don't show disclaimer here - wait for user to click "Start Analysis"
    }
  };

  const handleDisclaimerAccept = async () => {
    setShowDisclaimer(false);
    setDisclaimerAccepted(true);
    await performAnalysis();
  };

  const handleDisclaimerDecline = () => {
    setShowDisclaimer(false);
    setSelectedFile(null);
    setPreviewUrl(null);
    setDisclaimerAccepted(false);
  };

  const performAnalysis = async () => {
    if (!selectedFile || !selectedPatient) {
      return;
    }

    setAnalyzing(true);
    setError(null);

    try {
      // Create FormData
      const formData = new FormData();
      formData.append('image', selectedFile); // CORRECT: Backend expects 'image'

      // Add doctor notes if provided
      if (doctorNotes.trim()) {
        formData.append('doctor_notes', doctorNotes);
      }

      // CRITICAL FIX: Send boolean as Form field value
      // FastAPI will parse form field values, so we send the string 'true'
      // But we need to ensure patient_id is an integer in the URL
      formData.append('disclaimer_accepted', 'true');

      // Call SaaS analysis endpoint
      // IMPORTANT: Ensure patient_id is sent as integer (not string)
      const response = await fetch(
        `${API_BASE_URL}/medical-staff/scans/analyze?patient_id=${parseInt(selectedPatient.id)}`,
        {
          method: 'POST',
          headers: {
            ...getAuthHeader()
            // CORRECT: Do NOT set Content-Type for FormData
            // Browser will automatically set it with the correct boundary
          },
          body: formData
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('❌ Analysis failed:', errorData);
        throw new Error(errorData.detail || `Analysis failed with status ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ Analysis successful:', data);
      setResults(data);
    } catch (err) {
      console.error('❌ Error during analysis:', err);
      setError(err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const resetAnalysis = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResults(null);
    setError(null);
    setDoctorNotes('');
    setDisclaimerAccepted(false);
  };

  const getRiskColor = (riskLevel) => {
    if (riskLevel.includes('Very High') || riskLevel.includes('High')) {
      return '#dc2626';
    } else if (riskLevel.includes('Moderate')) {
      return '#f59e0b';
    } else {
      return '#10b981';
    }
  };

  // If no patient selected, show patient management
  if (!selectedPatient) {
    return (
      <div className="screening-container">
        <PatientManagement
          onPatientSelect={handlePatientSelect}
          onViewHistory={onViewHistory}
        />
      </div>
    );
  }

  return (
    <div className="screening-container">
      <DisclaimerModal
        isOpen={showDisclaimer}
        onAccept={handleDisclaimerAccept}
        onDecline={handleDisclaimerDecline}
        patientName={selectedPatient.full_name}
      />

      <div className="screening-header">
        <div>
          <h2>Breast Cancer Screening</h2>
          <p className="selected-patient-info">
            Patient: <strong>{selectedPatient.full_name}</strong>
            (MRN: {selectedPatient.mrn})
          </p>
        </div>
        <button
          className="btn-change-patient"
          onClick={() => setSelectedPatient(null)}
        >
          Change Patient
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          ⚠️ {error}
        </div>
      )}

      {!results ? (
        <div className="upload-section">
          <div className="upload-card">
            <h3>Upload Medical Image</h3>

            {!previewUrl ? (
              <div className="file-upload-area">
                <input
                  type="file"
                  id="file-input"
                  accept="image/*"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                />
                <label htmlFor="file-input" className="upload-label">
                  <div className="upload-icon">📤</div>
                  <p>Click to select image or drag and drop</p>
                  <small>Supports: JPG, PNG, DICOM, etc.</small>
                </label>
              </div>
            ) : (
              <div className="preview-section">
                <img src={previewUrl} alt="Preview" className="image-preview" />

                <div className="notes-section">
                  <label htmlFor="doctor-notes">Doctor's Notes (Optional)</label>
                  <textarea
                    id="doctor-notes"
                    value={doctorNotes}
                    onChange={(e) => setDoctorNotes(e.target.value)}
                    placeholder="Enter clinical observations, patient history, or other relevant notes..."
                    rows="4"
                  />
                </div>

                <div className="upload-actions">
                  <button
                    className="btn-secondary"
                    onClick={resetAnalysis}
                    disabled={analyzing}
                  >
                    Cancel
                  </button>
                  <button
                    className="btn-primary"
                    onClick={() => {
                      if (!disclaimerAccepted) {
                        setShowDisclaimer(true);
                      } else {
                        performAnalysis();
                      }
                    }}
                    disabled={analyzing}
                  >
                    {analyzing ? 'Analyzing...' : 'Start Analysis'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="results-section">
          <div className="results-header">
            <h3>✅ Analysis Complete</h3>
            <button className="btn-new-scan" onClick={resetAnalysis}>
              New Scan
            </button>
          </div>

          {/* FIXED: Added optional chaining and null checks */}
          {results?.analysis?.mode && results.analysis.mode.includes('DEMO') && (
            <div className="demo-mode-banner">
              <div className="demo-icon">⚠️</div>
              <div className="demo-content">
                <strong>DEMO MODE ACTIVE:</strong> Using simulated AI predictions for demonstration purposes.
                {results?.analysis?.demo_warning && (
                  <span className="demo-details"> {results.analysis.demo_warning}</span>
                )}
              </div>
            </div>
          )}

          <div className="results-grid">
            <div className="result-card primary">
              <h4>Prediction Result</h4>
              <div className="result-value" style={{
                color: results?.analysis?.result?.includes('Malignant') ? '#dc2626' : '#10b981'
              }}>
                {results?.analysis?.result || 'N/A'}
              </div>
              <div className="confidence-score">
                Confidence: {(results?.analysis?.probability || 0).toFixed(1)}%
              </div>
            </div>

            <div className="result-card">
              <h4>Risk Assessment</h4>
              <div className="risk-level" style={{ color: getRiskColor(results?.analysis?.risk_level || 'Unknown') }}>
                {results?.analysis?.risk_icon || '⚠️'} {results?.analysis?.risk_level || 'Unknown'}
              </div>
            </div>

            <div className="result-card">
              <h4>Probabilities</h4>
              <div className="probability-bars">
                <div className="prob-item">
                  <span>Malignant:</span>
                  <div className="prob-bar">
                    <div
                      className="prob-fill malignant"
                      style={{ width: `${results?.analysis?.malignant_prob || 0}%` }}
                    />
                  </div>
                  <span>{(results?.analysis?.malignant_prob || 0).toFixed(1)}%</span>
                </div>
                <div className="prob-item">
                  <span>Benign:</span>
                  <div className="prob-bar">
                    <div
                      className="prob-fill benign"
                      style={{ width: `${results?.analysis?.benign_prob || 0}%` }}
                    />
                  </div>
                  <span>{(results?.analysis?.benign_prob || 0).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          </div>

          <div className="scan-info-banner">
            <strong>Scan ID:</strong> {results?.scan_id || 'N/A'} |
            <strong> Saved for:</strong> {results?.patient_name || 'Unknown'}
          </div>
        </div>
      )}
    </div>
  );
}

export default Screening;