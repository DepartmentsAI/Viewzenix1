/**
 * Risk Management Service
 * 
 * This service handles risk management API interactions for the trading platform,
 * including risk profiles, settings, and calculations.
 */

import apiService from './apiService';

// API endpoint base paths
const ENDPOINTS = {
  RISK_PROFILES: '/risk-profiles',
  RISK_SETTINGS: '/risk-settings',
  RISK_CALCULATIONS: '/risk-calculations',
  POSITION_SIZE: '/position-size',
  RISK_REWARD: '/risk-reward'
};

/**
 * Get all risk profiles for the current user
 * @returns {Promise<Array>} Promise resolving to array of risk profiles
 */
const getRiskProfiles = async () => {
  return apiService.get(ENDPOINTS.RISK_PROFILES);
};

/**
 * Get a specific risk profile by ID
 * @param {string} profileId - Risk profile ID
 * @returns {Promise<Object>} Promise resolving to risk profile object
 */
const getRiskProfileById = async (profileId) => {
  return apiService.get(`${ENDPOINTS.RISK_PROFILES}/${profileId}`);
};

/**
 * Create a new risk profile
 * @param {Object} profileData - Risk profile data
 * @returns {Promise<Object>} Promise resolving to created risk profile
 */
const createRiskProfile = async (profileData) => {
  return apiService.post(ENDPOINTS.RISK_PROFILES, profileData);
};

/**
 * Update an existing risk profile
 * @param {string} profileId - Risk profile ID
 * @param {Object} profileData - Updated risk profile data
 * @returns {Promise<Object>} Promise resolving to updated risk profile
 */
const updateRiskProfile = async (profileId, profileData) => {
  return apiService.put(`${ENDPOINTS.RISK_PROFILES}/${profileId}`, profileData);
};

/**
 * Delete a risk profile
 * @param {string} profileId - Risk profile ID to delete
 * @returns {Promise<void>} Promise resolving when profile is deleted
 */
const deleteRiskProfile = async (profileId) => {
  return apiService.delete(`${ENDPOINTS.RISK_PROFILES}/${profileId}`);
};

/**
 * Get user's risk settings
 * @returns {Promise<Object>} Promise resolving to risk settings
 */
const getRiskSettings = async () => {
  return apiService.get(ENDPOINTS.RISK_SETTINGS);
};

/**
 * Update user's risk settings
 * @param {Object} settingsData - Updated risk settings
 * @returns {Promise<Object>} Promise resolving to updated risk settings
 */
const updateRiskSettings = async (settingsData) => {
  return apiService.put(ENDPOINTS.RISK_SETTINGS, settingsData);
};

/**
 * Calculate position size based on risk parameters
 * @param {Object} params - Position sizing parameters
 * @param {number} params.accountSize - Total account size in currency
 * @param {number} params.riskPercentage - Risk percentage (0-100)
 * @param {number} params.entryPrice - Entry price
 * @param {number} params.stopLoss - Stop loss price
 * @param {string} params.symbol - Trading symbol
 * @returns {Promise<Object>} Promise resolving to position size calculation
 */
const calculatePositionSize = async (params) => {
  return apiService.post(`${ENDPOINTS.POSITION_SIZE}`, params);
};

/**
 * Calculate risk/reward ratio
 * @param {Object} params - Risk/reward parameters
 * @param {number} params.entryPrice - Entry price
 * @param {number} params.stopLoss - Stop loss price
 * @param {number} params.takeProfit - Take profit price
 * @returns {Promise<Object>} Promise resolving to risk/reward calculation
 */
const calculateRiskReward = async (params) => {
  return apiService.post(`${ENDPOINTS.RISK_REWARD}`, params);
};

/**
 * Get risk assessment for a given trading setup
 * @param {Object} tradingSetup - Trading setup parameters
 * @returns {Promise<Object>} Promise resolving to risk assessment
 */
const assessTradeRisk = async (tradingSetup) => {
  return apiService.post(`${ENDPOINTS.RISK_CALCULATIONS}/assessment`, tradingSetup);
};

/**
 * Check if trade meets user's risk criteria
 * @param {Object} tradeParams - Trade parameters
 * @returns {Promise<Object>} Promise with validation result
 */
const validateTrade = async (tradeParams) => {
  return apiService.post(`${ENDPOINTS.RISK_CALCULATIONS}/validate`, tradeParams);
};

export default {
  getRiskProfiles,
  getRiskProfileById,
  createRiskProfile,
  updateRiskProfile,
  deleteRiskProfile,
  getRiskSettings,
  updateRiskSettings,
  calculatePositionSize,
  calculateRiskReward,
  assessTradeRisk,
  validateTrade
}; 