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
  const [showAddForm, setShowAddForm] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // New patient form state
  const [newPatient, setNewPatient] = useState({
    medical_record_number: '',
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: 'Female',
    contact_phone: '',
    contact_email: '',
    address: '',
    emergency_contact_name: '',
    emergency_contact_phone: ''
  });

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

  const handleAddPatient = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Convert to SaaS API format
      const patientData = {
        full_name: `${newPatient.first_name} ${newPatient.last_name}`,
        date_of_birth: newPatient.date_of_birth,
        gender: newPatient.gender.toLowerCase(),
        email: newPatient.contact_email,
        phone: newPatient.contact_phone,
        address: newPatient.address,
        city: '',
        state: '',
        postal_code: '',
        emergency_contact_name: newPatient.emergency_contact_name,
        emergency_contact_phone: newPatient.emergency_contact_phone,
        emergency_contact_relation: '',
        blood_group: '',
        medical_history_json: {},
        family_history_json: {},
        risk_factors_json: {}
      };

      const response = await fetch(`${API_BASE_URL}/medical-staff/patients`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify(patientData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to add patient');
      }

      const addedPatient = await response.json();
      
      setSuccess(`Patient ${addedPatient.full_name} added successfully! MRN: ${addedPatient.mrn}`);
      setShowAddForm(false);
      
      // Reset form
      setNewPatient({
        medical_record_number: '',
        first_name: '',
        last_name: '',
        date_of_birth: '',
        gender: 'Female',
        contact_phone: '',
        contact_email: '',
        address: '',
        emergency_contact_name: '',
        emergency_contact_phone: ''
      });

      // Refresh patient list
      fetchPatients();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewPatient(prev => ({
      ...prev,
      [name]: value
    }));
  };

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
    const first = patient.first_name?.trim()?.[0] ?? '';
    const last = patient.last_name?.trim()?.[0] ?? '';
    const initials = `${first}${last}`.trim();
    return (initials || 'PA').toUpperCase();
  };

  return (
    <div className="patient-management">
      <div className="patient-management-header">
        <h2>Patient Management</h2>
        <button 
          className="btn-add-patient"
          onClick={() => setShowAddForm(!showAddForm)}
        >
          {showAddForm ? 'Cancel' : 'Add New Patient'}
        </button>
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

      {showAddForm && (
        <div className="add-patient-form">
          <h3>Add New Patient</h3>
          <form onSubmit={handleAddPatient}>
            <div className="form-grid">
              <div className="form-group">
                <label>Medical Record Number *</label>
                <input
                  type="text"
                  name="medical_record_number"
                  value={newPatient.medical_record_number}
                  onChange={handleInputChange}
                  required
                  placeholder="MRN-001"
                />
              </div>

              <div className="form-group">
                <label>First Name *</label>
                <input
                  type="text"
                  name="first_name"
                  value={newPatient.first_name}
                  onChange={handleInputChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Last Name *</label>
                <input
                  type="text"
                  name="last_name"
                  value={newPatient.last_name}
                  onChange={handleInputChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Date of Birth *</label>
                <input
                  type="date"
                  name="date_of_birth"
                  value={newPatient.date_of_birth}
                  onChange={handleInputChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Gender *</label>
                <select
                  name="gender"
                  value={newPatient.gender}
                  onChange={handleInputChange}
                  required
                >
                  <option value="Female">Female</option>
                  <option value="Male">Male</option>
                  <option value="Other">Other</option>
                  <option value="Prefer not to say">Prefer not to say</option>
                </select>
              </div>

              <div className="form-group">
                <label>Contact Phone</label>
                <input
                  type="tel"
                  name="contact_phone"
                  value={newPatient.contact_phone}
                  onChange={handleInputChange}
                  placeholder="+1-555-0100"
                />
              </div>

              <div className="form-group">
                <label>Contact Email</label>
                <input
                  type="email"
                  name="contact_email"
                  value={newPatient.contact_email}
                  onChange={handleInputChange}
                  placeholder="patient@email.com"
                />
              </div>

              <div className="form-group full-width">
                <label>Address</label>
                <textarea
                  name="address"
                  value={newPatient.address}
                  onChange={handleInputChange}
                  rows="2"
                  placeholder="123 Main St, City, State ZIP"
                />
              </div>

              <div className="form-group">
                <label>Emergency Contact Name</label>
                <input
                  type="text"
                  name="emergency_contact_name"
                  value={newPatient.emergency_contact_name}
                  onChange={handleInputChange}
                />
              </div>

              <div className="form-group">
                <label>Emergency Contact Phone</label>
                <input
                  type="tel"
                  name="emergency_contact_phone"
                  value={newPatient.emergency_contact_phone}
                  onChange={handleInputChange}
                  placeholder="+1-555-0200"
                />
              </div>
            </div>

            <div className="form-actions">
              <button 
                type="button" 
                className="btn-secondary"
                onClick={() => setShowAddForm(false)}
              >
                Cancel
              </button>
              <button 
                type="submit" 
                className="btn-primary"
                disabled={loading}
              >
                {loading ? 'Adding...' : 'Add Patient'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="patient-search">
        <form onSubmit={handleSearch}>
          <input
            type="text"
            placeholder="Search by MRN or Name..."
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
            <p>No patients found. Add a new patient to get started.</p>
          </div>
        ) : (
          patients.map(patient => (
          <div key={patient.id} className="patient-card">
            <div className="patient-card-grid">
              <div className="patient-avatar-pill">
                {getPatientInitials(patient)}
              </div>
              <div className="patient-card-header">
                <h3>{patient.first_name} {patient.last_name}</h3>
                <span className="patient-mrn">MRN: {patient.medical_record_number}</span>
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
                    View History
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

