/**
 * Centralized API Configuration
 * Single source of truth for API base URL across the application
 */

// Determine API base URL based on environment
export const API_BASE_URL =
  process.env.NODE_ENV === 'production'
    ? process.env.REACT_APP_API_BASE_URL || 'https://breast-cancer-detection-ra6i.onrender.com/api'
    : (process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api');

// Log the configured URL for debugging (helps identify env var issues)
console.log('🌐 API_BASE_URL =', API_BASE_URL);
console.log('📦 NODE_ENV =', process.env.NODE_ENV);
console.log('🔧 REACT_APP_API_BASE_URL =', process.env.REACT_APP_API_BASE_URL);

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

