/**
 * Role-Based Dashboard Router
 * Redirects users to their appropriate dashboard based on role
 */

import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import LoadingSpinner from './LoadingSpinner';
import SuperAdminDashboard from './SuperAdminDashboard';
import HospitalAdminDashboard from './HospitalAdminDashboard';
import PatientDashboard from './PatientDashboard';
import Dashboard from './Dashboard'; // For doctors and lab techs

function RoleBasedDashboard() {
  const { user, loading } = useAuth();

  // Show loading state while checking authentication
  if (loading) {
    return <LoadingSpinner message="Loading your dashboard..." />;
  }

  // If no user, redirect to login
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Route based on user role
  switch (user.role) {
    case 'super_admin':
      return <SuperAdminDashboard />;
    
    case 'organization_admin':
      return <HospitalAdminDashboard />;
    
    case 'doctor':
    case 'lab_tech':
      return <Dashboard />; // Medical staff dashboard
    
    case 'patient':
      return <PatientDashboard />;
    
    default:
      console.error('Unknown user role:', user.role);
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          gap: '20px'
        }}>
          <h2 style={{ color: '#DC2626' }}>Access Denied</h2>
          <p>Your role ({user.role}) is not recognized.</p>
          <button
            onClick={() => window.location.href = '/login'}
            style={{
              padding: '12px 24px',
              background: '#9C2B6D',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer'
            }}
          >
            Back to Login
          </button>
        </div>
      );
  }
}

export default RoleBasedDashboard;

