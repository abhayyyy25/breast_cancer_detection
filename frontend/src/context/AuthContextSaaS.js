/**
 * Authentication Context - Multi-Tenant SaaS
 * Handles authentication for all user roles with tenant isolation
 */

import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Configure axios defaults
  const axiosInstance = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Add token to requests
  axiosInstance.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Handle 401 errors
  axiosInstance.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        logout();
      }
      return Promise.reject(error);
    }
  );

  // Check if user is logged in on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const response = await axiosInstance.get('/auth/me');
          setUser(response.data);
        } catch (error) {
          console.error('Auth check failed:', error);
          localStorage.removeItem('token');
          setUser(null);
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (username, password) => {
    try {
      setError(null);
      setLoading(true);

      const response = await axiosInstance.post('/auth/login', {
        username,
        password,
      });

      const { access_token, user: userData } = response.data;

      localStorage.setItem('token', access_token);
      setUser(userData);

      return { success: true, user: userData };
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail || 'Login failed. Please try again.';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await axiosInstance.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('token');
      setUser(null);
    }
  };

  const changePassword = async (oldPassword, newPassword) => {
    try {
      setError(null);
      await axiosInstance.post('/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword,
      });
      return { success: true };
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail || 'Password change failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  const updateProfile = async (profileData) => {
    try {
      setError(null);
      const response = await axiosInstance.put('/auth/profile', profileData);
      setUser(response.data);
      return { success: true, user: response.data };
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail || 'Profile update failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  // Role checking utilities
  const isSuperAdmin = () => user?.role === 'super_admin';
  const isOrgAdmin = () => user?.role === 'organization_admin';
  const isDoctor = () => user?.role === 'doctor';
  const isLabTech = () => user?.role === 'lab_tech';
  const isPatient = () => user?.role === 'patient';
  const isMedicalStaff = () => isDoctor() || isLabTech();
  const isAdmin = () => isSuperAdmin() || isOrgAdmin();

  const hasRole = (roles) => {
    if (!user) return false;
    return Array.isArray(roles) ? roles.includes(user.role) : user.role === roles;
  };

  const value = {
    user,
    loading,
    error,
    login,
    logout,
    changePassword,
    updateProfile,
    axiosInstance,
    isAuthenticated: !!user,
    isSuperAdmin,
    isOrgAdmin,
    isDoctor,
    isLabTech,
    isPatient,
    isMedicalStaff,
    isAdmin,
    hasRole,
    tenantId: user?.tenant_id,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;

