import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Auth.css';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (!username || !password) {
      setError('Please fill in all fields');
      setLoading(false);
      return;
    }

    try {
      const result = await login(username, password);
      
      // 🔍 DEBUG: Log the entire response
      console.log('Login Response:', result);
      console.log('Success:', result.success);
      console.log('User Object:', result.user);
      console.log('Role (raw):', result.user?.role);
      
      if (result.success) {
        // Redirect based on user role
        const role = result.user?.role;
        
        // ✅ Normalize role to lowercase to prevent case-sensitivity issues
        const normalizedRole = role?.toLowerCase().trim();
        
        console.log('Role (normalized):', normalizedRole);
        
        // Switch statement for better readability
        switch (normalizedRole) {
          case 'super_admin':
          case 'superadmin':
            console.log('🚀 Redirecting to /superadmin');
            navigate('/superadmin');
            break;
          case 'organization_admin':
          case 'admin':
          case 'hospital_admin':
            console.log('🚀 Redirecting to /admin');
            navigate('/admin');
            break;
          case 'doctor':
          case 'lab_tech':
          case 'medical_staff':
            console.log('🚀 Redirecting to /doctor');
            navigate('/doctor');
            break;
          case 'patient':
            console.log('🚀 Redirecting to /patient');
            navigate('/patient');
            break;
          default:
            console.warn('⚠️ Unknown role:', normalizedRole, '- Redirecting to /');
            navigate('/');
        }
      } else {
        console.error('❌ Login failed:', result.error);
        setError(result.error || 'Invalid username or password');
      }
    } catch (err) {
      console.error('❌ Login exception:', err);
      setError('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <video 
        autoPlay 
        muted 
        loop 
        playsInline
        id="bg-video"
      >
        <source src="/backgroundpink.mp4" type="video/mp4" />
        Your browser does not support the video tag.
      </video>
      <div className="bg-overlay" />

      <div className="auth-card professional">
        <div className="auth-logo">
          <div className="logo-circle">
            <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
              <path d="M30 5C16.2 5 5 16.2 5 30s11.2 25 25 25 25-11.2 25-25S43.8 5 30 5zm0 45c-11 0-20-9-20-20s9-20 20-20 20 9 20 20-9 20-20 20z" fill="#9C2B6D"/>
              <path d="M30 15c-8.3 0-15 6.7-15 15s6.7 15 15 15 15-6.7 15-15-6.7-15-15-15zm0 25c-5.5 0-10-4.5-10-10s4.5-10 10-10 10 4.5 10 10-4.5 10-10 10z" fill="#D946A6"/>
            </svg>
          </div>
        </div>

        <div className="auth-header">
          <h1>Welcome Back</h1>
          <p>Sign in to access your Breast Cancer Detection dashboard</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && (
            <div className="error-message">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="username">Username or Email</label>
            <div className="input-with-icon">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" />
              </svg>
              <input
                type="text"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username or email"
                autoComplete="username"
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="input-with-icon">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
              </svg>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                autoComplete="current-password"
                disabled={loading}
              />
            </div>
          </div>

          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? (
              <>
                <span className="spinner"></span>
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </button>

          <div className="auth-divider">
            <span>Quick Access</span>
          </div>

          <div className="demo-credentials">
            <div className="demo-section">
              <strong>Demo Accounts:</strong>
              <div className="demo-list">
                <div className="demo-item" onClick={() => { setUsername('superadmin'); setPassword('SuperAdmin@123'); }}>
                  <span className="demo-role">Super Admin</span>
                  <span className="demo-username">superadmin</span>
                </div>
                <div className="demo-item" onClick={() => { setUsername('admin.apollo'); setPassword('Apollo@123'); }}>
                  <span className="demo-role">Hospital Admin</span>
                  <span className="demo-username">admin.apollo</span>
                </div>
                <div className="demo-item" onClick={() => { setUsername('dr.rajesh.sharma'); setPassword('Doctor@123'); }}>
                  <span className="demo-role">Doctor</span>
                  <span className="demo-username">dr.rajesh.sharma</span>
                </div>
                <div className="demo-item" onClick={() => { setUsername('priya.patel'); setPassword('Patient@123'); }}>
                  <span className="demo-role">Patient</span>
                  <span className="demo-username">priya.patel</span>
                </div>
              </div>
            </div>
          </div>

          <div className="auth-footer">
            <p>
              Need access?{' '}
              <Link to="/signup" className="auth-link">
                Contact Administrator
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}

export default Login;

