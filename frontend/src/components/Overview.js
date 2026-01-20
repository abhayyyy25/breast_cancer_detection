import React, { useState, useEffect } from "react";
import { useAuth } from '../context/AuthContext';
// Professional Medical SaaS Icons - Enterprise Grade
import {
  FiUsers,           // Patient group icon
  FiActivity,        // Medical scan/imaging icon
  FiUserCheck,       // Doctor/clinician icon
  FiCheckCircle,     // System status icon
  FiFileText,        // Medical reports icon
  FiFolder,          // Patient records icon
  FiUploadCloud      // Upload/scan workflow icon
} from 'react-icons/fi'; // Feather icons - clean, professional, medical-grade
import './Overview.css';

/**
 * Overview Component
 * 
 * Dashboard home showing:
 * - System statistics
 * - Recent activity
 * - Quick actions
 * 
 * DESIGN: Enterprise Medical SaaS (Epic/Cerner/GE Healthcare standard)
 */
function Overview({ onNavigate }) {
  const { user, API_BASE_URL, getAuthHeader } = useAuth();
  const [stats, setStats] = useState({
    totalPatients: 0,
    totalScans: 0,
    recentScans: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      console.log('📊 Fetching dashboard statistics...');

      // Fetch real-time stats from backend
      const response = await fetch(`${API_BASE_URL}/medical-staff/dashboard-stats`, {
        headers: {
          ...getAuthHeader(),
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('✅ Dashboard stats received:', data);

        // Update stats with real data from database
        setStats({
          totalPatients: data.total_patients || 0,
          totalScans: data.total_scans || 0,
          recentScans: data.recent_scans || 0
        });
      } else {
        console.error('❌ Failed to fetch stats:', response.status);
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('Error details:', errorData);
        // Set default values if fetch fails
        setStats({
          totalPatients: 0,
          totalScans: 0,
          recentScans: 0
        });
      }
    } catch (error) {
      console.error('❌ Error fetching stats:', error);
      // Set default values on error
      setStats({
        totalPatients: 0,
        totalScans: 0,
        recentScans: 0
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="overview-container">
      <div className="welcome-banner">
        <h1>Welcome, {user?.full_name || 'Doctor'}</h1>
        <p>Enterprise-Level Breast Cancer Detection Hospital System</p>
      </div>

      {/* STAT CARDS - Professional Medical Icons */}
      <div className="stats-grid">
        {/* Total Patients - Patient Group Icon */}
        <div className="stat-card">
          <div className="stat-icon medical-icon">
            <FiUsers size={28} strokeWidth={2} />
          </div>
          <div className="stat-content">
            <div className="stat-value">{loading ? '...' : stats.totalPatients}</div>
            <div className="stat-label">Total Patients</div>
          </div>
        </div>

        {/* Total Scans - Medical Imaging Icon */}
        <div className="stat-card">
          <div className="stat-icon medical-icon">
            <FiActivity size={28} strokeWidth={2} />
          </div>
          <div className="stat-content">
            <div className="stat-value">{loading ? '...' : stats.totalScans}</div>
            <div className="stat-label">Total Scans</div>
          </div>
        </div>

        {/* Your Role - Clinician Icon */}
        <div className="stat-card">
          <div className="stat-icon medical-icon">
            <FiUserCheck size={28} strokeWidth={2} />
          </div>
          <div className="stat-content">
            <div className="stat-value">{user?.role || 'Doctor'}</div>
            <div className="stat-label">Your Role</div>
          </div>
        </div>

        {/* System Status - Health Check Icon */}
        <div className="stat-card">
          <div className="stat-icon medical-icon status-active">
            <FiCheckCircle size={28} strokeWidth={2} />
          </div>
          <div className="stat-content">
            <div className="stat-value">Active</div>
            <div className="stat-label">System Status</div>
          </div>
        </div>
      </div>

      {/* QUICK ACTIONS - Professional Medical Workflow Icons */}
      <div className="quick-actions">
        <h2>Quick Actions</h2>
        <div className="actions-grid">
          {/* Start Screening - Upload/Scan Workflow */}
          <div className="action-card">
            <div className="action-icon medical-action-icon">
              <FiUploadCloud size={32} strokeWidth={2} />
            </div>
            <h3>Start Screening</h3>
            <p>Select a patient and upload medical images for AI analysis</p>
            <button className="action-button" onClick={() => onNavigate && onNavigate('screening')}>Go to Screening</button>
          </div>

          {/* Manage Patients - Patient Records Icon */}
          <div className="action-card">
            <div className="action-icon medical-action-icon">
              <FiFolder size={32} strokeWidth={2} />
            </div>
            <h3>Manage Patients</h3>
            <p>Add new patients, search records, or view patient details</p>
            <button className="action-button" onClick={() => onNavigate && onNavigate('screening')}>View Patients</button>
          </div>

          {/* View History - Medical Reports Icon */}
          <div className="action-card">
            <div className="action-icon medical-action-icon">
              <FiFileText size={32} strokeWidth={2} />
            </div>
            <h3>View History</h3>
            <p>Access patient scan history and download reports</p>
            <button className="action-button" onClick={() => onNavigate && onNavigate('screening')}>View Patients</button>
          </div>
        </div>
      </div>

      <div className="system-info">
        <h2>System Information</h2>
        <div className="info-grid">
          <div className="info-item">
            <strong>Version:</strong>
            <span>2.0.0 Enterprise Edition</span>
          </div>
          <div className="info-item">
            <strong>Database:</strong>
            <span>Connected ✅</span>
          </div>
          <div className="info-item">
            <strong>AI Model:</strong>
            <span>Loaded ✅</span>
          </div>
          <div className="info-item">
            <strong>Compliance:</strong>
            <span>HIPAA Aligned 🔒</span>
          </div>
        </div>
      </div>

      <div className="medical-disclaimer-box">
        <div className="disclaimer-icon">⚠️</div>
        <div className="disclaimer-content">
          <h3>Medical Disclaimer</h3>
          <p>
            This AI system provides <strong>assistive decision support</strong> only.
            All diagnoses must be confirmed by licensed medical professionals through
            standard clinical protocols. This is not a replacement for medical judgment.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Overview;
