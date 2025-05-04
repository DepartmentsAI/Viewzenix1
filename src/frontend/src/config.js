/**
 * Frontend Application Configuration
 * 
 * This file centralizes application configuration settings
 * like API URLs, environment-specific feature flags, and
 * other configuration values.
 */

// API Configuration
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api/v1';

// Feature Flags
const ENABLE_MOCK_DATA = process.env.REACT_APP_ENABLE_MOCK_DATA === 'true';

// Configuration Object
const config = {
  // API Settings
  api: {
    baseUrl: API_URL,
    timeout: 10000, // 10 seconds
    retryAttempts: 3
  },
  
  // Feature Flags
  features: {
    useMockData: ENABLE_MOCK_DATA,
    enableAnalytics: process.env.NODE_ENV === 'production',
  },
  
  // Environment Information
  environment: {
    isDevelopment: process.env.NODE_ENV === 'development',
    isProduction: process.env.NODE_ENV === 'production',
    isTest: process.env.NODE_ENV === 'test',
  }
};

export default config; 