/**
 * Frontend Configuration Template
 * 
 * Copy this file to config.js and modify the values according to your environment.
 * 
 * Usage:
 *   cp config.template.js config.js
 */

const config = {
  /**
   * API configuration
   */
  api: {
    // Base URL for API requests
    baseUrl: process.env.REACT_APP_API_URL || 'http://localhost:5000/api',
    
    // Timeout for API requests in milliseconds
    timeout: 10000,
    
    // Retry configuration
    retry: {
      // Maximum number of retries
      maxRetries: 3,
      // Delay between retries in milliseconds
      delay: 1000,
      // Whether to use exponential backoff
      useExponentialBackoff: true
    }
  },

  /**
   * Frontend server configuration
   */
  frontend: {
    // Port to run the frontend on
    port: process.env.PORT || 3000,
    
    // Host to bind to
    host: process.env.HOST || '0.0.0.0',
    
    // Environment type (development, testing, production)
    environment: process.env.NODE_ENV || 'development'
  },

  /**
   * Feature flags
   */
  features: {
    // Enable/disable features
    enableNotifications: true,
    enableRiskManagement: true,
    enableOrderTracking: true,
    enableDebugMode: process.env.NODE_ENV === 'development'
  },

  /**
   * Logging configuration
   */
  logging: {
    // Log level (debug, info, warn, error)
    level: process.env.NODE_ENV === 'production' ? 'error' : 'debug',
    
    // Whether to log to console
    console: true,
    
    // Whether to log to file
    file: false,
    
    // File path for logs
    filePath: './logs/frontend.log'
  }
};

module.exports = config; 