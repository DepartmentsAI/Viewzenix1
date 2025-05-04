import { useCallback } from 'react';
import notificationService from '../../services/notificationService';

/**
 * React hook for using notification service in functional components
 * 
 * @returns {Object} Notification methods
 */
const useNotification = () => {
  /**
   * Show a success notification
   * @param {string} message - Success message
   * @param {Object} options - Additional options
   */
  const success = useCallback((message, options = {}) => {
    return notificationService.success(message, options);
  }, []);

  /**
   * Show an error notification
   * @param {string} message - Error message
   * @param {Object|Error} options - Additional options or Error object
   */
  const error = useCallback((message, options = {}) => {
    return notificationService.error(message, options);
  }, []);

  /**
   * Show a warning notification
   * @param {string} message - Warning message
   * @param {Object} options - Additional options
   */
  const warning = useCallback((message, options = {}) => {
    return notificationService.warning(message, options);
  }, []);

  /**
   * Show an info notification
   * @param {string} message - Info message
   * @param {Object} options - Additional options
   */
  const info = useCallback((message, options = {}) => {
    return notificationService.info(message, options);
  }, []);

  /**
   * Handle API errors from standardized API service
   * @param {Object} apiError - Error from API service
   * @param {string} fallbackMessage - Default message if error doesn't provide one
   */
  const handleApiError = useCallback((apiError, fallbackMessage = 'An unexpected error occurred') => {
    return notificationService.handleApiError(apiError, fallbackMessage);
  }, []);

  /**
   * Remove a notification by ID
   * @param {number} id - Notification ID
   */
  const removeNotification = useCallback((id) => {
    notificationService.removeNotification(id);
  }, []);

  /**
   * Clear all notifications
   */
  const clearAll = useCallback(() => {
    notificationService.clearAllNotifications();
  }, []);

  return {
    success,
    error,
    warning,
    info,
    handleApiError,
    removeNotification,
    clearAll
  };
};

export default useNotification; 