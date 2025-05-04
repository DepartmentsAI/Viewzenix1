import axios from 'axios';

const API_BASE_URL = '/api/v1';

/**
 * Fetch risk management settings
 * @returns {Promise<Object>} The risk management settings
 */
export const fetchRiskSettings = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/risk/settings`);
    return response.data;
  } catch (error) {
    console.error('Error fetching risk settings:', error);
    throw error;
  }
};

/**
 * Update risk management settings
 * @param {Object} settings - The risk settings to update
 * @returns {Promise<Object>} The updated risk settings
 */
export const updateRiskSettings = async (settings) => {
  try {
    const response = await axios.put(`${API_BASE_URL}/risk/settings`, settings);
    return response.data;
  } catch (error) {
    console.error('Error updating risk settings:', error);
    throw error;
  }
};

/**
 * Fetch current portfolio risk metrics
 * @returns {Promise<Object>} The portfolio risk metrics
 */
export const fetchRiskMetrics = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/risk/metrics`);
    return response.data;
  } catch (error) {
    console.error('Error fetching risk metrics:', error);
    throw error;
  }
};

/**
 * Fetch orders with their associated risk parameters
 * @param {Object} filters - Optional filters
 * @returns {Promise<Array>} List of orders with risk parameters
 */
export const fetchOrdersWithRiskParams = async (filters = {}) => {
  try {
    const queryParams = new URLSearchParams();
    
    // Add filters to query params if they exist
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value);
      }
    });
    
    const response = await axios.get(`${API_BASE_URL}/risk/orders?${queryParams.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching orders with risk parameters:', error);
    throw error;
  }
};

/**
 * Update risk parameters for specific order
 * @param {string} orderId - The ID of the order
 * @param {Object} riskParams - Risk parameters to update (stop loss, take profit)
 * @returns {Promise<Object>} The updated order with risk parameters
 */
export const updateOrderRiskParams = async (orderId, riskParams) => {
  try {
    const response = await axios.put(`${API_BASE_URL}/risk/orders/${orderId}`, riskParams);
    return response.data;
  } catch (error) {
    console.error(`Error updating risk parameters for order ${orderId}:`, error);
    throw error;
  }
};

/**
 * Get risk level information based on exposure percentage
 * @param {number} exposurePercent - Risk exposure percentage
 * @returns {Object} Risk level info with label and color
 */
export const getRiskLevelInfo = (exposurePercent) => {
  if (exposurePercent <= 30) {
    return { level: 'Low', color: 'success' };
  } else if (exposurePercent <= 60) {
    return { level: 'Moderate', color: 'warning' };
  } else if (exposurePercent <= 80) {
    return { level: 'High', color: 'error' };
  } else {
    return { level: 'Critical', color: 'error' };
  }
};

/**
 * Emergency stop - close all positions
 * @returns {Promise<Object>} Result of the emergency stop operation
 */
export const executeEmergencyStop = async () => {
  try {
    const response = await axios.post(`${API_BASE_URL}/risk/emergency-stop`);
    return response.data;
  } catch (error) {
    console.error('Error executing emergency stop:', error);
    throw error;
  }
}; 