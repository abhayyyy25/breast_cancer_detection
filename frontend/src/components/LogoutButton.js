/**
 * Reusable Logout Button Component
 * Handles logout and navigation for all user roles
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './LogoutButton.css';

const LogoutButton = ({ className = '', variant = 'default' }) => {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = async () => {
    try {
      // Clear all localStorage items
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('role');
      
      // Call logout from context (if available)
      if (logout) {
        await logout();
      }
      
      // Redirect to login
      navigate('/login', { replace: true });
    } catch (error) {
      console.error('Logout error:', error);
      // Force redirect even if there's an error
      navigate('/login', { replace: true });
    }
  };

  return (
    <button 
      className={`logout-button logout-button-${variant} ${className}`}
      onClick={handleLogout}
      title="Logout"
    >
      <span className="logout-icon">🚪</span>
      <span className="logout-text">Logout</span>
    </button>
  );
};

export default LogoutButton;

