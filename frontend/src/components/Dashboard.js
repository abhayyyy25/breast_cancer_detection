import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import Screening from './Screening';
import PatientHistory from './PatientHistory';
import PatientRegistration from './PatientRegistration';
import Overview from './Overview';
import './Dashboard.css';

/**
 * Main Dashboard Component
 * 
 * Hospital System hub with navigation:
 * - Overview: System statistics
 * - Register Patient: DOCTORS ONLY - Register new patients
 * - Screening: Patient selection and image analysis
 * - History: View patient scan history
 */
function Dashboard() {
  const { user, logout } = useAuth();
  const [activeView, setActiveView] = useState('overview');
  const [selectedPatient, setSelectedPatient] = useState(null);

  const handleViewHistory = (patient) => {
    setSelectedPatient(patient);
    setActiveView('history');
  };

  const handleBackFromHistory = () => {
    setSelectedPatient(null);
    setActiveView('screening');
  };

  const handlePatientRegistered = (newPatient) => {
    // Optionally navigate to screening after registration
    console.log('Patient registered:', newPatient);
    // You can add a success notification here
  };

  const renderView = () => {
    switch (activeView) {
      case 'overview':
        return <Overview onNavigate={setActiveView} />;
      case 'register':
        // Only doctors can register patients
        if (user?.role === 'doctor') {
          return (
            <PatientRegistration 
              onBack={() => setActiveView('overview')}
              onPatientRegistered={handlePatientRegistered}
            />
          );
        } else {
          return (
            <div style={{ padding: '40px', textAlign: 'center' }}>
              <h2 style={{ color: '#DC2626' }}>Access Denied</h2>
              <p>Only Doctors can register patients.</p>
              <button 
                onClick={() => setActiveView('overview')}
                style={{
                  padding: '10px 20px',
                  background: '#9C2B6D',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  marginTop: '20px'
                }}
              >
                Back to Overview
              </button>
            </div>
          );
        }
      case 'screening':
        return <Screening onViewHistory={handleViewHistory} />;
      case 'history':
        return <PatientHistory patient={selectedPatient} onBack={handleBackFromHistory} />;
      default:
        return <Screening />;
    }
  };

  return (
    <div className="dashboard-container">
      <aside className="dashboard-sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <span className="logo-icon">🏥</span>
            <span className="logo-text">Breast Cancer<br />Detection System</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <button
            className={`nav-item ${activeView === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveView('overview')}
          >
            <span className="nav-icon">📊</span>
            <span className="nav-text">Overview</span>
          </button>

          {/* DOCTORS ONLY: Register Patient */}
          {user?.role === 'doctor' && (
            <button
              className={`nav-item ${activeView === 'register' ? 'active' : ''}`}
              onClick={() => setActiveView('register')}
            >
              <span className="nav-icon">👤</span>
              <span className="nav-text">Register Patient</span>
            </button>
          )}

          <button
            className={`nav-item ${activeView === 'screening' ? 'active' : ''}`}
            onClick={() => setActiveView('screening')}
          >
            <span className="nav-icon">🔬</span>
            <span className="nav-text">Screening</span>
          </button>

          <button
            className={`nav-item ${activeView === 'history' ? 'active' : ''}`}
            onClick={() => setActiveView('history')}
          >
            <span className="nav-icon">📋</span>
            <span className="nav-text">Patient History</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">
              {user?.full_name ? user.full_name[0] : user?.email[0]}
            </div>
            <div className="user-details">
              <div className="user-name">{user?.full_name || user?.email}</div>
              <div className="user-role">{user?.role || 'Doctor'}</div>
            </div>
          </div>
          <button className="btn-logout" onClick={logout}>
            🚪 Logout
          </button>
        </div>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-header">
          <div className="header-content">
            <h1>Welcome, Dr. {user?.full_name?.split(' ')[0] || user?.email?.split('@')[0]}</h1>
            <p className="header-subtitle">Hospital-Grade AI-Assisted Breast Cancer Detection</p>
          </div>
          <div className="header-badge">
            <span className="badge-icon">⚕️</span>
            <span className="badge-text">{user?.license_number || 'Licensed Physician'}</span>
          </div>
        </header>

        <div className="dashboard-content">
          {renderView()}
        </div>

        <footer className="dashboard-footer">
          <p>
            ⚠️ <strong>Medical Disclaimer:</strong> This AI system is for assistive purposes only.
            All diagnoses must be confirmed by licensed medical professionals through standard clinical protocols.
          </p>
          <p className="footer-meta">
            Version 2.0.0 | Enterprise Hospital System | HIPAA Compliant
          </p>
        </footer>
      </main>
    </div>
  );
}

export default Dashboard;

