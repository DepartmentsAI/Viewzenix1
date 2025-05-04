import axios from 'axios';
import config from '../src/config';

/**
 * Risk Management API Service
 * 
 * Provides methods for interacting with the Risk Management API endpoints
 */

const API_BASE_URL = config.api.baseUrl;

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
 * Fetch current risk metrics
 * @returns {Promise<Object>} Current risk metrics
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
 * Fetch orders with their risk parameters
 * @param {Object} filters - Optional filters (symbol, status, etc.)
 * @returns {Promise<Array>} Orders with risk parameters
 */
export const fetchOrdersWithRiskParams = async (filters = {}) => {
  try {
    const queryParams = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) queryParams.append(key, value);
    });
    
    const response = await axios.get(`${API_BASE_URL}/risk/orders?${queryParams}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching orders with risk parameters:', error);
    throw error;
  }
};

/**
 * Update risk parameters for a specific order
 * @param {string} orderId - The order ID
 * @param {Object} riskParams - Risk parameters to update (slPrice, tpPrice, etc.)
 * @returns {Promise<Object>} The updated order
 */
export const updateOrderRiskParams = async (orderId, riskParams) => {
  try {
    const response = await axios.put(`${API_BASE_URL}/risk/orders/${orderId}`, riskParams);
    return response.data;
  } catch (error) {
    console.error('Error updating order risk parameters:', error);
    throw error;
  }
};

/**
 * Get risk level information based on a risk percentage
 * @param {number} riskPercentage - Risk percentage (0-100)
 * @returns {Object} Risk level info with level name and color
 */
export const getRiskLevelInfo = (riskPercentage) => {
  if (riskPercentage <= 30) {
    return { level: 'Low', color: 'success' };
  } else if (riskPercentage <= 60) {
    return { level: 'Moderate', color: 'warning' };
  } else if (riskPercentage <= 80) {
    return { level: 'High', color: 'error' };
  } else {
    return { level: 'Critical', color: 'error' };
  }
};

/**
 * Execute emergency stop (close all positions)
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