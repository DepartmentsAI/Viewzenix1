/**
 * Frontend Configuration
 * 
 * This file centralizes all configuration settings for the frontend application.
 * It reads from environment variables when available, falling back to defaults.
 */

// API Configuration
const API_CONFIG = {
  // Base URL for API requests, e.g., http://localhost:5000/api/v1
  baseUrl: process.env.REACT_APP_API_URL || 'http://localhost:5000/api/v1',
  
  // Request timeout in milliseconds (5 seconds default)
  timeout: parseInt(process.env.REACT_APP_API_TIMEOUT || '5000', 10),
  
  // Whether to include credentials in cross-origin requests
  withCredentials: process.env.REACT_APP_API_WITH_CREDENTIALS === 'true',
  
  // Default headers to include with all requests
  defaultHeaders: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  
  // Retry configuration for failed requests
  retry: {
    maxRetries: parseInt(process.env.REACT_APP_API_MAX_RETRIES || '3', 10),
    initialDelay: parseInt(process.env.REACT_APP_API_RETRY_DELAY || '1000', 10),
    factor: parseFloat(process.env.REACT_APP_API_RETRY_FACTOR || '2'),
  }
};

// Auth Configuration
const AUTH_CONFIG = {
  // JWT token storage key
  tokenKey: 'auth_token',
  
  // Token refresh settings
  refreshBeforeExpiry: parseInt(process.env.REACT_APP_REFRESH_BEFORE_EXPIRY || '300000', 10), // 5 minutes
  
  // Auth endpoints
  endpoints: {
    login: '/auth/login',
    register: '/auth/register',
    refreshToken: '/auth/refresh',
    forgotPassword: '/auth/forgot-password',
    resetPassword: '/auth/reset-password',
    logout: '/auth/logout',
  }
};

// UI Configuration
const UI_CONFIG = {
  // Theme settings
  theme: process.env.REACT_APP_THEME || 'light',
  
  // Animation settings
  animations: process.env.REACT_APP_DISABLE_ANIMATIONS !== 'true',
  
  // Notification defaults
  notifications: {
    position: process.env.REACT_APP_NOTIFICATION_POSITION || 'top-right', // top-right, top-left, bottom-right, bottom-left, top-center, bottom-center
    duration: parseInt(process.env.REACT_APP_NOTIFICATION_DURATION || '5000', 10), // 5 seconds
    maxCount: parseInt(process.env.REACT_APP_NOTIFICATION_MAX_COUNT || '5', 10)
  },
  
  // Default pagination settings
  pagination: {
    defaultPageSize: parseInt(process.env.REACT_APP_DEFAULT_PAGE_SIZE || '10', 10),
    pageSizeOptions: [5, 10, 20, 50, 100],
  }
};

// Feature flags (for enabling/disabling features)
const FEATURE_FLAGS = {
  enableRiskManagement: process.env.REACT_APP_ENABLE_RISK_MANAGEMENT !== 'false', // Enabled by default
  enablePaperTrading: process.env.REACT_APP_ENABLE_PAPER_TRADING === 'true',
  enableNotifications: process.env.REACT_APP_ENABLE_NOTIFICATIONS !== 'false', // Enabled by default
  enableDarkMode: process.env.REACT_APP_ENABLE_DARK_MODE === 'true',
  betaFeatures: process.env.REACT_APP_ENABLE_BETA_FEATURES === 'true',
};

// Exported configuration with namespaces
const config = {
  api: API_CONFIG,
  auth: AUTH_CONFIG,
  ui: UI_CONFIG,
  features: FEATURE_FLAGS,
  
  // Environment information
  env: {
    isProduction: process.env.NODE_ENV === 'production',
    isDevelopment: process.env.NODE_ENV === 'development',
    isTest: process.env.NODE_ENV === 'test',
    buildVersion: process.env.REACT_APP_VERSION || 'development',
    buildDate: process.env.REACT_APP_BUILD_DATE || new Date().toISOString(),
  }
};

export default config; 