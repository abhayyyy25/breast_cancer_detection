/**
 * Reusable Loading Spinner Component
 * Full-screen centered spinner with modern animation
 */

import React from 'react';
import './LoadingSpinner.css';

const LoadingSpinner = ({ message = 'Loading...' }) => {
  return (
    <div className="loading-spinner-overlay">
      <div className="loading-spinner-container">
        <div className="spinner">
          <div className="spinner-ring"></div>
          <div className="spinner-ring"></div>
          <div className="spinner-ring"></div>
          <div className="spinner-ring"></div>
        </div>
        <p className="loading-text">{message}</p>
      </div>
    </div>
  );
};

export default LoadingSpinner;

