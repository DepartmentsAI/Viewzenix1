/**
 * Notification Service
 * 
 * Centralized service for managing application notifications and error handling.
 * Provides methods to display success, error, warning and info notifications
 * with consistent styling and behavior.
 */

// Types of notifications
export const NOTIFICATION_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info'
};

// Default options
const DEFAULT_OPTIONS = {
  autoClose: true,
  duration: 5000, // 5 seconds
  position: 'top-right'
};

// Store for active notifications
let notifications = [];
let listeners = [];
let lastId = 0;

/**
 * Create a new notification
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, error, warning, info)
 * @param {Object} options - Additional options
 * @returns {Object} The created notification object
 */
const createNotification = (message, type = NOTIFICATION_TYPES.INFO, options = {}) => {
  const id = ++lastId;
  const timestamp = new Date();
  
  const notification = {
    id,
    message,
    type,
    timestamp,
    ...DEFAULT_OPTIONS,
    ...options
  };
  
  notifications.push(notification);
  notifyListeners();
  
  // Auto-close after duration if enabled
  if (notification.autoClose) {
    setTimeout(() => {
      removeNotification(id);
    }, notification.duration);
  }
  
  return notification;
};

/**
 * Remove a notification by ID
 * @param {number} id - Notification ID
 */
const removeNotification = (id) => {
  notifications = notifications.filter(notification => notification.id !== id);
  notifyListeners();
};

/**
 * Clear all notifications
 */
const clearAllNotifications = () => {
  notifications = [];
  notifyListeners();
};

/**
 * Subscribe to notification changes
 * @param {Function} listener - Function to call when notifications change
 * @returns {Function} Unsubscribe function
 */
const subscribe = (listener) => {
  listeners.push(listener);
  
  // Immediately notify new listener of current state
  listener([...notifications]);
  
  // Return unsubscribe function
  return () => {
    listeners = listeners.filter(l => l !== listener);
  };
};

/**
 * Notify all listeners of notification changes
 */
const notifyListeners = () => {
  listeners.forEach(listener => listener([...notifications]));
};

/**
 * Show a success notification
 * @param {string} message - Success message
 * @param {Object} options - Additional options
 * @returns {Object} Created notification
 */
const success = (message, options = {}) => {
  return createNotification(message, NOTIFICATION_TYPES.SUCCESS, options);
};

/**
 * Show an error notification
 * @param {string} message - Error message
 * @param {Object|Error} options - Additional options or Error object
 * @returns {Object} Created notification
 */
const error = (message, options = {}) => {
  // If options is an Error object, extract message and use as details
  if (options instanceof Error) {
    options = { details: options.message };
    // If no message provided, use error message
    if (!message) {
      message = options.details;
    }
  }
  
  return createNotification(message, NOTIFICATION_TYPES.ERROR, options);
};

/**
 * Show a warning notification
 * @param {string} message - Warning message
 * @param {Object} options - Additional options
 * @returns {Object} Created notification
 */
const warning = (message, options = {}) => {
  return createNotification(message, NOTIFICATION_TYPES.WARNING, options);
};

/**
 * Show an info notification
 * @param {string} message - Info message
 * @param {Object} options - Additional options
 * @returns {Object} Created notification
 */
const info = (message, options = {}) => {
  return createNotification(message, NOTIFICATION_TYPES.INFO, options);
};

/**
 * Handle API errors from standardized API service error format
 * @param {Object} apiError - Error from API service
 * @param {string} fallbackMessage - Default message if error doesn't provide one
 * @returns {Object} Created notification
 */
const handleApiError = (apiError, fallbackMessage = 'An unexpected error occurred') => {
  const message = apiError.message || fallbackMessage;
  const options = {
    autoClose: false,
    details: apiError.data?.details || apiError.statusText,
    statusCode: apiError.status
  };
  
  return error(message, options);
};

export default {
  success,
  error,
  warning,
  info,
  handleApiError,
  removeNotification,
  clearAllNotifications,
  subscribe,
  getNotifications: () => [...notifications]
}; 