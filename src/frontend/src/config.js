/**
 * Frontend Configuration
 * 
 * This file centralizes all configuration settings for the frontend application.
 * It handles environment-specific settings and provides defaults where needed.
 */

// Environment detection
const isProduction = process.env.NODE_ENV === 'production';
const isDevelopment = process.env.NODE_ENV === 'development' || !process.env.NODE_ENV;
const isTest = process.env.NODE_ENV === 'test';

// API configuration
const API_CONFIG = {
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000/api/v1',
  timeout: parseInt(process.env.REACT_APP_API_TIMEOUT || '10000', 10),
  retries: parseInt(process.env.REACT_APP_API_RETRIES || '3', 10),
};

// Authentication configuration
const AUTH_CONFIG = {
  tokenKey: 'auth_token',
  refreshTokenKey: 'refresh_token',
  expireKey: 'token_expire',
  tokenLifespan: parseInt(process.env.REACT_APP_TOKEN_LIFESPAN || '86400', 10), // 24 hours in seconds
};

// Feature flags
const FEATURES = {
  enableRiskManagement: process.env.REACT_APP_ENABLE_RISK_MANAGEMENT !== 'false',
  enableBacktesting: process.env.REACT_APP_ENABLE_BACKTESTING === 'true',
  enableNotifications: process.env.REACT_APP_ENABLE_NOTIFICATIONS !== 'false',
  enableDarkMode: process.env.REACT_APP_ENABLE_DARK_MODE !== 'false',
  enableExperimentalFeatures: process.env.REACT_APP_ENABLE_EXPERIMENTAL === 'true'
};

// Platform settings
const PLATFORM = {
  appName: process.env.REACT_APP_NAME || 'Viewzenix Trading Platform',
  defaultTheme: process.env.REACT_APP_DEFAULT_THEME || 'light',
  defaultLanguage: process.env.REACT_APP_DEFAULT_LANGUAGE || 'en',
  sentryDSN: process.env.REACT_APP_SENTRY_DSN || '',
  buildVersion: process.env.REACT_APP_VERSION || '0.1.0',
  buildTime: process.env.REACT_APP_BUILD_TIME || new Date().toISOString(),
  supportEmail: process.env.REACT_APP_SUPPORT_EMAIL || 'support@viewzenix.com',
  maxUploadSize: parseInt(process.env.REACT_APP_MAX_UPLOAD_SIZE || '5242880', 10), // 5MB
};

// Local storage keys
const STORAGE_KEYS = {
  theme: 'viewzenix_theme',
  language: 'viewzenix_language',
  lastLogin: 'viewzenix_last_login',
  userPreferences: 'viewzenix_user_prefs',
  recentSymbols: 'viewzenix_recent_symbols',
};

// Default pagination settings
const PAGINATION = {
  defaultPageSize: parseInt(process.env.REACT_APP_DEFAULT_PAGE_SIZE || '20', 10),
  pageSizeOptions: [10, 20, 50, 100],
};

// Timeouts and intervals
const TIMEOUTS = {
  sessionTimeout: parseInt(process.env.REACT_APP_SESSION_TIMEOUT || '1800000', 10), // 30 minutes
  dataRefreshInterval: parseInt(process.env.REACT_APP_DATA_REFRESH || '60000', 10), // 1 minute
  notificationDuration: parseInt(process.env.REACT_APP_NOTIFICATION_DURATION || '5000', 10), // 5 seconds
};

// External services URLs
const EXTERNAL_SERVICES = {
  documentationUrl: process.env.REACT_APP_DOCS_URL || 'https://docs.viewzenix.com',
  termsUrl: process.env.REACT_APP_TERMS_URL || 'https://viewzenix.com/terms',
  privacyUrl: process.env.REACT_APP_PRIVACY_URL || 'https://viewzenix.com/privacy',
};

// Export the configuration
export default {
  isProduction,
  isDevelopment,
  isTest,
  api: API_CONFIG,
  auth: AUTH_CONFIG,
  features: FEATURES,
  platform: PLATFORM,
  storage: STORAGE_KEYS,
  pagination: PAGINATION,
  timeouts: TIMEOUTS,
  externalServices: EXTERNAL_SERVICES,
};

// Helper function to get a feature flag value
export const isFeatureEnabled = (featureName) => {
  return FEATURES[featureName] === true;
}; 