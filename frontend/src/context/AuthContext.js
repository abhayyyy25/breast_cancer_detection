import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';

const AuthContext = createContext(null);

// API Base URL - Backend is on port 8001 with /api prefix
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001/api';
console.log('🌐 API_BASE_URL configured as:', API_BASE_URL);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Logout function (defined early so it can be used in verifyToken)
  const logout = useCallback(async () => {
    try {
      console.log('🚪 Logging out...');
      // Clear local state first
      setUser(null);
      setToken(null);
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      console.log('✅ Logged out successfully');
    } catch (error) {
      console.error('Logout error:', error);
    }
  }, []);

  const verifyToken = useCallback(async (authToken) => {
    try {
      console.log('🔐 Verifying token...');
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      if (!response.ok) {
        console.log('❌ Token invalid, logging out...');
        // Token is invalid, clear storage
        await logout();
        return false;
      }
      
      console.log('✅ Token valid');
      return true;
    } catch (error) {
      console.error('❌ Token verification failed:', error);
      await logout();
      return false;
    }
  }, [logout]);

  useEffect(() => {
    // Check if user is logged in (from localStorage)
    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    
    if (storedToken && storedUser) {
      console.log('🔍 Found stored token, verifying...');
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
      
      // Verify token is still valid
      verifyToken(storedToken).finally(() => {
        setLoading(false);
      });
    } else {
      console.log('❌ No stored credentials found');
      setLoading(false);
    }
  }, [verifyToken]);

  const login = async (username, password) => {
    try {
      console.log('🔐 Attempting login to:', `${API_BASE_URL}/auth/login`);
      console.log('👤 Username:', username);
      
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      console.log('📡 Response status:', response.status);
      
      if (!response.ok) {
        const data = await response.json();
        console.log('❌ Error response:', data);
        return { 
          success: false, 
          error: data.detail || 'Invalid username or password. Please try again.' 
        };
      }

      const data = await response.json();
      console.log('📦 Response data:', data);

      // Store token and user data
      const accessToken = data.access_token;
      const userData = data.user;

      // 🔍 DEBUG: Log the exact role value from backend
      console.log('✅ Login successful!');
      console.log('👤 User role (exact):', userData?.role);
      console.log('👤 User role (type):', typeof userData?.role);
      console.log('👤 Full user object:', JSON.stringify(userData, null, 2));

      setToken(accessToken);
      setUser(userData);
      
      localStorage.setItem('token', accessToken);
      localStorage.setItem('user', JSON.stringify(userData));

      return { success: true, user: userData };
    } catch (error) {
      console.error('❌ Login error:', error);
      console.error('Error details:', error.message);
      return { 
        success: false, 
        error: 'Network error. Please check your connection and try again.' 
      };
    }
  };

  const signup = async (name, email, password) => {
    // Note: In production, signup should only be available to admins
    // This is kept for backward compatibility, but should be called via admin panel
    try {
      const response = await fetch(`${API_BASE_URL}/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` // Requires admin token
        },
        body: JSON.stringify({ 
        email,
          password,
          full_name: name,
          role: 'doctor'
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        return { 
          success: false, 
          error: data.detail || 'Signup failed. Please try again.' 
        };
      }

      return { success: true };
    } catch (error) {
      console.error('Signup error:', error);
      return { 
        success: false, 
        error: 'Network error. Please check your connection and try again.' 
      };
    }
  };


  const getAuthHeader = () => {
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  };

  const value = {
    user,
    token,
    login,
    signup,
    logout,
    loading,
    getAuthHeader,
    API_BASE_URL
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

