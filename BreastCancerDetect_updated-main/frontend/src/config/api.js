/**
 * Centralized API Configuration
 * Single source of truth for API base URL across the application
 */

export const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

/**
 * Get authorization header with token
 * @returns {Object} Authorization header object
 */
export const getAuthHeader = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

/**
 * Default fetch options with auth
 */
export const getDefaultFetchOptions = () => ({
  headers: {
    'Content-Type': 'application/json',
    ...getAuthHeader(),
  },
});

export default { API_BASE_URL, getAuthHeader, getDefaultFetchOptions };

