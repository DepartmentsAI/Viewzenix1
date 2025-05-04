import axios from 'axios';

/**
 * Centralized API Service for frontend
 * 
 * This service provides a consistent way to interact with backend APIs,
 * with built-in support for:
 * - Configuration with environment variables
 * - Retry mechanism for failed requests
 * - Timeout handling
 * - Error standardization
 * - Request/response interceptors
 */

// Default configuration
const DEFAULT_CONFIG = {
  baseURL: process.env.REACT_APP_API_URL || '/api/v1',
  timeout: 10000,
  retries: 3,
  retryDelay: 1000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
};

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: DEFAULT_CONFIG.baseURL,
  timeout: DEFAULT_CONFIG.timeout,
  headers: DEFAULT_CONFIG.headers
});

// Request interceptor
apiClient.interceptors.request.use(
  config => {
    // You can add authentication tokens here if needed
    // const token = getToken();
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    
    // Add retry configuration to the request
    config.metadata = { 
      ...config.metadata,
      startTime: new Date().getTime(),
      retryCount: 0,
      maxRetries: config.maxRetries || DEFAULT_CONFIG.retries
    };
    
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  response => {
    return response;
  },
  async error => {
    const { config } = error;
    
    // If there's no config, we can't retry
    if (!config || !config.metadata) {
      return Promise.reject(error);
    }
    
    // Increment the retry count
    config.metadata.retryCount = (config.metadata.retryCount || 0) + 1;
    
    // Check if we've reached max retries
    if (config.metadata.retryCount > config.metadata.maxRetries) {
      return Promise.reject(error);
    }
    
    // Only retry on network errors or 5xx responses
    const shouldRetry = !error.response || 
      (error.response.status >= 500 && error.response.status < 600);
    
    if (!shouldRetry) {
      return Promise.reject(error);
    }
    
    // Calculate retry delay with exponential backoff
    const delay = config.metadata.retryDelay || 
      DEFAULT_CONFIG.retryDelay * Math.pow(2, config.metadata.retryCount - 1);
    
    // Wait for the delay
    await new Promise(resolve => setTimeout(resolve, delay));
    
    // Retry the request
    return apiClient(config);
  }
);

/**
 * Standardizes error objects from API responses
 * @param {Object} error - The axios error object
 * @returns {Object} Standardized error object
 */
const standardizeError = (error) => {
  if (error.response) {
    // The server responded with a status code outside of 2xx range
    return {
      status: error.response.status,
      statusText: error.response.statusText,
      data: error.response.data,
      message: error.response.data?.message || error.message,
      isServerError: error.response.status >= 500
    };
  } else if (error.request) {
    // The request was made but no response was received
    return {
      status: 0,
      statusText: 'No Response',
      data: null,
      message: 'The server did not respond to your request.',
      isNetworkError: true
    };
  } else {
    // Something else happened while setting up the request
    return {
      status: 0,
      statusText: 'Request Failed',
      data: null,
      message: error.message,
      isConfigError: true
    };
  }
};

/**
 * Generic GET request
 * @param {string} url - The endpoint URL
 * @param {Object} params - URL parameters
 * @param {Object} config - Additional axios config
 * @returns {Promise} Promise with the response data
 */
const get = async (url, params = {}, config = {}) => {
  try {
    const response = await apiClient.get(url, { ...config, params });
    return response.data;
  } catch (error) {
    throw standardizeError(error);
  }
};

/**
 * Generic POST request
 * @param {string} url - The endpoint URL
 * @param {Object} data - The data to send
 * @param {Object} config - Additional axios config
 * @returns {Promise} Promise with the response data
 */
const post = async (url, data = {}, config = {}) => {
  try {
    const response = await apiClient.post(url, data, config);
    return response.data;
  } catch (error) {
    throw standardizeError(error);
  }
};

/**
 * Generic PUT request
 * @param {string} url - The endpoint URL
 * @param {Object} data - The data to send
 * @param {Object} config - Additional axios config
 * @returns {Promise} Promise with the response data
 */
const put = async (url, data = {}, config = {}) => {
  try {
    const response = await apiClient.put(url, data, config);
    return response.data;
  } catch (error) {
    throw standardizeError(error);
  }
};

/**
 * Generic DELETE request
 * @param {string} url - The endpoint URL
 * @param {Object} config - Additional axios config
 * @returns {Promise} Promise with the response data
 */
const del = async (url, config = {}) => {
  try {
    const response = await apiClient.delete(url, config);
    return response.data;
  } catch (error) {
    throw standardizeError(error);
  }
};

/**
 * Get the current API configuration
 * @returns {Object} Current API configuration
 */
const getConfig = () => {
  return {
    baseURL: apiClient.defaults.baseURL,
    timeout: apiClient.defaults.timeout,
    headers: apiClient.defaults.headers,
    retries: DEFAULT_CONFIG.retries,
    retryDelay: DEFAULT_CONFIG.retryDelay
  };
};

/**
 * Set new configuration for the API client
 * @param {Object} config - New configuration
 */
const setConfig = (config = {}) => {
  if (config.baseURL) {
    apiClient.defaults.baseURL = config.baseURL;
  }
  
  if (config.timeout) {
    apiClient.defaults.timeout = config.timeout;
  }
  
  if (config.headers) {
    apiClient.defaults.headers = {
      ...apiClient.defaults.headers,
      ...config.headers
    };
  }
  
  // Update default config as well
  Object.assign(DEFAULT_CONFIG, config);
};

// Export API methods
export default {
  get,
  post,
  put,
  delete: del,
  client: apiClient,
  getConfig,
  setConfig,
  standardizeError
}; 