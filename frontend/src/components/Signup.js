import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Auth.css';

function Signup() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const { signup } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!name || !email || !password || !confirmPassword) {
      setError('Please fill in all fields');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters with uppercase, lowercase, and digit');
      return;
    }

    const result = await signup(name, email, password);
    if (result.success) {
      setError('Account creation requires admin approval. Please contact your system administrator.');
    } else {
      setError(result.error || 'Signup failed. Only administrators can create new user accounts. Please login with existing credentials or contact your administrator.');
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

      <div className="auth-card">
        <div className="auth-header">
          <h1>Create Account</h1>
          <p>Sign up to start using Breast Cancer Detection</p>
          <div style={{background: '#fff3cd', padding: '12px', borderRadius: '8px', marginTop: '16px', border: '1px solid #ffc107'}}>
            <p style={{margin: 0, fontSize: '14px', color: '#856404'}}>
              ⚠️ <strong>Note:</strong> This is an enterprise hospital system. New accounts require administrator approval. 
              If you already have credentials, please <Link to="/login" style={{color: '#0056b3', fontWeight: 'bold'}}>login here</Link>.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label htmlFor="name">Full Name</label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your full name"
              autoComplete="name"
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              autoComplete="new-password"
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm your password"
              autoComplete="new-password"
            />
          </div>

          <button type="submit" className="auth-button">
            Sign Up
          </button>

          <div className="auth-footer">
            <p>
              Already have an account?{' '}
              <Link to="/login" className="auth-link">
                Login
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}

export default Signup;

