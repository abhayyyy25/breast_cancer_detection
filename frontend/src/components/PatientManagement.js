import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import './PatientManagement.css';

/**
 * Patient Management Component
 * 
 * Allows doctors to:
 * - Search for existing patients
 * - View patient details
 * - Add new patients
 * - Select patient for scanning
 * - View patient history
 */
const PatientManagement = ({ onPatientSelect, onViewHistory }) => {
  const { API_BASE_URL, getAuthHeader } = useAuth();

  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/medical-staff/patients?limit=100`, {
        headers: {
          ...getAuthHeader()
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch patients');
      }

      const data = await response.json();
      setPatients(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();

    if (!searchQuery.trim()) {
      fetchPatients();
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/medical-staff/patients?search=${encodeURIComponent(searchQuery)}`,
        {
          headers: {
            ...getAuthHeader()
          }
        }
      );

      if (!response.ok) {
        throw new Error('Search failed');
      }

      const data = await response.json();
      setPatients(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Registration form removed - use Register Patient section from main dashboard

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const calculateAge = (dateString) => {
    const birthDate = new Date(dateString);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();

    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }

    return age;
  };

  const getPatientInitials = (patient) => {
    if (!patient.full_name) return 'PA';

    const nameParts = patient.full_name.trim().split(/\s+/);
    if (nameParts.length === 0) return 'PA';

    const first = nameParts[0]?.[0] ?? '';
    const last = nameParts.length > 1 ? nameParts[nameParts.length - 1]?.[0] ?? '' : '';
    const initials = `${first}${last}`.trim();

    return (initials || 'PA').toUpperCase();
  };

  return (
    <div className="patient-management">
      <div className="patient-management-header">
        <h2>👥 Select Patient for Screening</h2>
      </div>

      {error && (
        <div className="alert alert-error">
          ⚠️ {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          ✅ {success}
        </div>
      )}


      <div className="patient-search">
        <form onSubmit={handleSearch}>
          <input
            type="text"
            placeholder="🔍 Search by MRN or Name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          <button type="submit" className="btn-search">
            Search
          </button>
          {searchQuery && (
            <button
              type="button"
              className="btn-clear"
              onClick={() => {
                setSearchQuery('');
                fetchPatients();
              }}
            >
              Clear
            </button>
          )}
        </form>
      </div>

      {loading && <div className="loading">Loading patients...</div>}

      <div className="patients-grid">
        {patients.length === 0 && !loading ? (
          <div className="no-patients">
            <p>No patients found.</p>
            <p className="workflow-guidance">Register patients using "Register Patient" from the main dashboard before screening.</p>
          </div>
        ) : (
          patients.map(patient => (
            <div key={patient.id} className="patient-card">
              <div className="patient-card-grid">
                <div className="patient-avatar-pill">
                  {getPatientInitials(patient)}
                </div>
                <div className="patient-card-header">
                  <h3>{patient.full_name}</h3>
                  <span className="patient-mrn">MRN: {patient.mrn}</span>
                </div>
              </div>

              <div className="patient-card-body">
                <div className="patient-info">
                  <span className="info-label">Age:</span>
                  <span>{calculateAge(patient.date_of_birth)} years</span>
                </div>
                <div className="patient-info">
                  <span className="info-label">DOB:</span>
                  <span>{formatDate(patient.date_of_birth)}</span>
                </div>
                <div className="patient-info">
                  <span className="info-label">Gender:</span>
                  <span>{patient.gender}</span>
                </div>
                {patient.contact_phone && (
                  <div className="patient-info">
                    <span className="info-label">Phone:</span>
                    <span>{patient.contact_phone}</span>
                  </div>
                )}
              </div>

              <div className="patient-card-actions">
                <button
                  className="btn-select-patient"
                  onClick={() => onPatientSelect(patient)}
                >
                  Select for Scan
                </button>
                {onViewHistory && (
                  <button
                    className="btn-view-history"
                    onClick={() => onViewHistory(patient)}
                  >
                    📋 View History
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default PatientManagement;

