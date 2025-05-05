/**
 * Centralized configuration for Viewzenix1 frontend application
 * This file provides a single source of truth for all environment configuration
 */

// Default configuration values - used if no environment variables are set
const defaultConfig = {
  // API configuration
  api: {
    baseUrl: 'http://localhost:5000/api',
    timeout: 30000, // 30 seconds
    retryAttempts: 3,
  },
  
  // Frontend configuration
  frontend: {
    port: 3000,
    host: '0.0.0.0', // Use 0.0.0.0 to bind to all interfaces for cross-device testing
    devMode: true,
  },
  
  // Feature flags
  features: {
    enableMockApi: false,
    enableDetailedLogs: true,
    experimentalFeatures: false,
  },
  
  // Theme configuration
  theme: {
    defaultDarkMode: true,
    animationSpeed: 'normal', // 'fast', 'normal', 'slow', 'none'
  }
};

// Environment-specific overrides based on NODE_ENV
const environmentOverrides = {
  development: {
    features: {
      enableMockApi: true,
      enableDetailedLogs: true,
    },
  },
  test: {
    api: {
      baseUrl: 'http://localhost:5000/api',
    },
    features: {
      enableMockApi: true,
      enableDetailedLogs: false,
    },
  },
  production: {
    frontend: {
      devMode: false,
    },
    features: {
      enableMockApi: false,
      enableDetailedLogs: false,
    },
  },
};

// Load environment-specific configuration
const currentEnv = process.env.NODE_ENV || 'development';
const envConfig = environmentOverrides[currentEnv] || {};

// Override with specific environment variables if present
const apiBaseUrl = process.env.REACT_APP_API_URL;
const frontendPort = process.env.PORT;
const frontendHost = process.env.HOST;
const mockApiEnabled = process.env.REACT_APP_ENABLE_MOCK_API;

// Merge configurations with environment variables taking precedence
const config = {
  ...defaultConfig,
  ...envConfig,
  api: {
    ...defaultConfig.api,
    ...(envConfig.api || {}),
    ...(apiBaseUrl ? { baseUrl: apiBaseUrl } : {}),
  },
  frontend: {
    ...defaultConfig.frontend,
    ...(envConfig.frontend || {}),
    ...(frontendPort ? { port: parseInt(frontendPort, 10) } : {}),
    ...(frontendHost ? { host: frontendHost } : {}),
  },
  features: {
    ...defaultConfig.features,
    ...(envConfig.features || {}),
    ...(mockApiEnabled !== undefined ? { enableMockApi: mockApiEnabled === 'true' } : {}),
  },
};

// Helper diagnostic function that can be called to verify configuration is loaded correctly
export const logConfig = () => {
  console.log('====== Viewzenix1 Configuration ======');
  console.log(`Environment: ${currentEnv}`);
  console.log(`API URL: ${config.api.baseUrl}`);
  console.log(`Frontend: ${config.frontend.host}:${config.frontend.port}`);
  console.log(`Dev Mode: ${config.frontend.devMode}`);
  console.log(`Mock API: ${config.features.enableMockApi}`);
  console.log('======================================');
};

export default config; 