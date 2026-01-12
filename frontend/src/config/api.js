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

// ============================================================================
// SUPER ADMIN API FUNCTIONS
// ============================================================================

/**
 * Get platform-wide statistics for analytics dashboard
 * @returns {Promise<Object>} Stats including tenant counts, scan data, charts
 */
export const getAdminStats = async () => {
  const response = await fetch(`${API_BASE_URL}/super-admin/stats`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch stats: ${response.status}`);
  }
  
  return await response.json();
};

/**
 * Get all tenants/organizations
 * @returns {Promise<Array>} List of all tenants
 */
export const getAllTenants = async () => {
  const response = await fetch(`${API_BASE_URL}/super-admin/tenants`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch tenants: ${response.status}`);
  }
  
  return await response.json();
};

/**
 * Create a new tenant/organization (Quick Onboard)
 * @param {Object} data - Organization data { name, email, password, location, plan_type }
 * @returns {Promise<Object>} Created tenant details
 */
export const createTenant = async (data) => {
  const response = await fetch(`${API_BASE_URL}/super-admin/tenants/onboard?name=${encodeURIComponent(data.name)}&email=${encodeURIComponent(data.email)}&password=${encodeURIComponent(data.password)}&location=${encodeURIComponent(data.location)}&plan_type=${encodeURIComponent(data.plan_type || 'trial')}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to create tenant: ${response.status}`);
  }
  
  return await response.json();
};

/**
 * Update tenant status (activate or suspend)
 * @param {number} id - Tenant ID
 * @param {string} status - 'active' or 'suspended'
 * @returns {Promise<Object>} Updated tenant info
 */
export const updateTenantStatus = async (id, status) => {
  const response = await fetch(`${API_BASE_URL}/super-admin/tenants/${id}/status?status=${status}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to update status: ${response.status}`);
  }
  
  return await response.json();
};

export default { 
  API_BASE_URL, 
  getAuthHeader, 
  getDefaultFetchOptions,
  // Super Admin functions
  getAdminStats,
  getAllTenants,
  createTenant,
  updateTenantStatus
};

