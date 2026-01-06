/**
 * Main Dashboard Component (Doctor / Lab Tech)
 * Hospital System hub with navigation
 * Refactored with Enterprise Design System
 */

import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import EnterpriseLayout from './common/EnterpriseLayout';
import Screening from './Screening';
import PatientHistory from './PatientHistory';
import PatientRegistration from './PatientRegistration';
import Overview from './Overview';
import ReportSettings from './ReportSettings';
import '../styles/enterpriseDesignSystem.css';
import './Dashboard.css';

function Dashboard() {
  const { user } = useAuth();
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
    console.log('Patient registered:', newPatient);
  };

  // Navigation items based on role
  const navigationItems = [
    {
      id: 'overview',
      label: 'Overview',
      icon: '■',
      active: activeView === 'overview',
      onClick: () => setActiveView('overview')
    },
  ];

  // Only doctors can register patients
  if (user?.role === 'doctor') {
    navigationItems.push({
      id: 'register',
      label: 'Register Patient',
      icon: '⬒',
      active: activeView === 'register',
      onClick: () => setActiveView('register')
    });
  }

  navigationItems.push(
    {
      id: 'screening',
      label: 'Screening',
      icon: '▦',
      active: activeView === 'screening',
      onClick: () => setActiveView('screening')
    },
    {
      id: 'history',
      label: 'Patient History',
      icon: '▭',
      active: activeView === 'history',
      onClick: () => setActiveView('history')
    },
    {
      id: 'settings',
      label: 'Report Settings',
      icon: '⚙',
      active: activeView === 'settings',
      onClick: () => setActiveView('settings')
    }
  );

  const getPageTitle = () => {
    switch (activeView) {
      case 'overview':
        return 'Clinical Overview';
      case 'register':
        return 'Register Patient';
      case 'screening':
        return 'Screening Analysis';
      case 'history':
        return 'Patient History';
      case 'settings':
        return 'Report Settings';
      default:
        return 'Dashboard';
    }
  };

  const renderView = () => {
    switch (activeView) {
      case 'overview':
        return <Overview onNavigate={setActiveView} />;
      case 'register':
        if (user?.role === 'doctor') {
          return (
            <PatientRegistration
              onBack={() => setActiveView('overview')}
              onPatientRegistered={handlePatientRegistered}
            />
          );
        } else {
          return (
            <div className="eds-card" style={{ padding: 'var(--eds-space-8)', textAlign: 'center' }}>
              <h2 className="eds-heading-3" style={{ color: 'var(--eds-color-error)', marginBottom: 'var(--eds-space-4)' }}>
                Access Denied
              </h2>
              <p className="eds-text-body" style={{ marginBottom: 'var(--eds-space-6)' }}>
                Only Doctors can register patients.
              </p>
              <button
                className="eds-button eds-button-secondary"
                onClick={() => setActiveView('overview')}
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
      case 'settings':
        return <ReportSettings onBack={() => setActiveView('overview')} />;
      default:
        return <Screening />;
    }
  };

  return (
    <EnterpriseLayout
      user={user}
      pageTitle={getPageTitle()}
      navigationItems={navigationItems}
    >
      {renderView()}

      {/* Medical Disclaimer Footer */}
      <div style={{
        marginTop: 'var(--eds-space-12)',
        padding: 'var(--eds-space-4)',
        background: 'var(--eds-color-surface-raised)',
        border: '1px solid var(--eds-color-border)',
        borderRadius: 'var(--eds-radius-md)'
      }}>
        <p className="eds-text-small" style={{ marginBottom: 'var(--eds-space-2)' }}>
          <strong>Medical Disclaimer:</strong> This AI system is for assistive purposes only.
          All diagnoses must be confirmed by licensed medical professionals through standard clinical protocols.
        </p>
        <p className="eds-text-small" style={{ color: 'var(--eds-color-text-muted)' }}>
          Version 2.0.0 | Enterprise Hospital System | HIPAA Compliant
        </p>
      </div>
    </EnterpriseLayout>
  );
}

export default Dashboard;
