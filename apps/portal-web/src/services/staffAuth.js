// src/services/staffAuth.js
import apiClient from './apiClient';

const API_BASE = '/users';

/**
 * Staff-specific login function
 * Uses the separate staff login endpoint that enforces staff-only access
 */
export const staffLogin = async (credentials) => {
  try {
    const response = await apiClient.post(`${API_BASE}/staff-login/`, credentials);
    
    // With HTTP-only cookies, tokens are automatically set by the server
    return { 
      success: true, 
      user: response.data.user,
      message: response.data.message || "Staff login successful"
    };
  } catch (error) {
    return {
      success: false,
      message: error.response?.data?.error || 
               error.response?.data?.message || 
               error.response?.data?.detail || 
               "Staff login failed",
      data: error.response?.data,
      status: error.response?.status
    };
  }
};

// Removed staffLogin - staff login handled via Keycloak SSO

/**
 * Check if current user has staff permissions
 */
export const checkStaffPermissions = (user) => {
  return user && user.is_staff === true;
};

/**
 * Check if current user has admin permissions
 */
export const checkAdminPermissions = (user) => {
  return user && (user.is_superuser === true || user.groups?.includes('Admin'));
};

/**
 * Get staff-specific profile information
 * This uses the same profile endpoint but validates staff status
 */
export const getStaffProfile = async () => {
  try {
    const response = await apiClient.get(`${API_BASE}/profile/`);
    const user = response.data;
    
    // Validate that the user is actually staff
    if (!checkStaffPermissions(user)) {
      return {
        success: false,
        message: "User does not have staff permissions",
        status: 403
      };
    }
    
    return { 
      success: true, 
      user: user,
      permissions: {
        isStaff: checkStaffPermissions(user),
        isAdmin: checkAdminPermissions(user),
        canAccessTenants: checkAdminPermissions(user),
        canAccessUsers: checkStaffPermissions(user)
      }
    };
  } catch (error) {
    if (error.response?.status === 401) {
      return {
        success: false,
        message: "Staff authentication required",
        status: 401
      };
    }
    
    return {
      success: false,
      message: error.response?.data?.message || "Failed to fetch staff profile",
      data: error.response?.data,
      status: error.response?.status
    };
  }
};

export default {
  staffLogin,
  checkStaffPermissions,
  checkAdminPermissions,
  getStaffProfile
}; 