import notificationService, { NOTIFICATION_TYPES } from '../../../../src/frontend/services/notificationService';

// Mock setTimeout and clearTimeout
jest.useFakeTimers();

describe('Notification Service', () => {
  // Reset the notification service before each test
  beforeEach(() => {
    // Clear all notifications
    notificationService.clearAllNotifications();
    
    // Reset mocks
    jest.clearAllMocks();
    jest.clearAllTimers();
  });

  describe('Basic Functionality', () => {
    test('should create a notification with default options', () => {
      // Create a notification
      const notification = notificationService.info('Test notification');
      
      // Get all notifications
      const notifications = notificationService.getNotifications();
      
      // Verify notification was created
      expect(notifications).toHaveLength(1);
      expect(notifications[0]).toBe(notification);
      expect(notification.message).toBe('Test notification');
      expect(notification.type).toBe(NOTIFICATION_TYPES.INFO);
      expect(notification.autoClose).toBe(true);
      expect(notification.duration).toBe(5000);
    });

    test('should create notifications of different types', () => {
      // Create notifications of each type
      const infoNotification = notificationService.info('Info message');
      const successNotification = notificationService.success('Success message');
      const warningNotification = notificationService.warning('Warning message');
      const errorNotification = notificationService.error('Error message');
      
      // Get all notifications
      const notifications = notificationService.getNotifications();
      
      // Verify notifications were created with correct types
      expect(notifications).toHaveLength(4);
      expect(infoNotification.type).toBe(NOTIFICATION_TYPES.INFO);
      expect(successNotification.type).toBe(NOTIFICATION_TYPES.SUCCESS);
      expect(warningNotification.type).toBe(NOTIFICATION_TYPES.WARNING);
      expect(errorNotification.type).toBe(NOTIFICATION_TYPES.ERROR);
    });

    test('should allow customizing notification options', () => {
      // Create a notification with custom options
      const customOptions = {
        autoClose: false,
        duration: 10000,
        position: 'bottom-center',
        customField: 'custom value'
      };
      
      const notification = notificationService.info('Custom notification', customOptions);
      
      // Verify custom options were applied
      expect(notification.autoClose).toBe(false);
      expect(notification.duration).toBe(10000);
      expect(notification.position).toBe('bottom-center');
      expect(notification.customField).toBe('custom value');
    });
  });

  describe('Notification Management', () => {
    test('should remove a notification by ID', () => {
      // Create notifications
      const notification1 = notificationService.info('Notification 1');
      const notification2 = notificationService.info('Notification 2');
      
      // Verify both notifications exist
      expect(notificationService.getNotifications()).toHaveLength(2);
      
      // Remove the first notification
      notificationService.removeNotification(notification1.id);
      
      // Verify only the second notification remains
      const remaining = notificationService.getNotifications();
      expect(remaining).toHaveLength(1);
      expect(remaining[0].id).toBe(notification2.id);
    });

    test('should clear all notifications', () => {
      // Create multiple notifications
      notificationService.info('Notification 1');
      notificationService.success('Notification 2');
      notificationService.warning('Notification 3');
      
      // Verify notifications were created
      expect(notificationService.getNotifications()).toHaveLength(3);
      
      // Clear all notifications
      notificationService.clearAllNotifications();
      
      // Verify all notifications were cleared
      expect(notificationService.getNotifications()).toHaveLength(0);
    });

    test('should auto-close notifications after duration', () => {
      // Create a notification with auto-close
      const notification = notificationService.info('Auto-close test', { duration: 3000 });
      
      // Verify notification was created
      expect(notificationService.getNotifications()).toHaveLength(1);
      
      // Advance timers to just before expiration
      jest.advanceTimersByTime(2999);
      expect(notificationService.getNotifications()).toHaveLength(1);
      
      // Advance timers to after expiration
      jest.advanceTimersByTime(1);
      expect(notificationService.getNotifications()).toHaveLength(0);
    });

    test('should not auto-close notifications when autoClose is false', () => {
      // Create a notification with auto-close disabled
      notificationService.info('No auto-close test', { autoClose: false });
      
      // Verify notification was created
      expect(notificationService.getNotifications()).toHaveLength(1);
      
      // Advance timers far beyond the default duration
      jest.advanceTimersByTime(60000);
      
      // Verify notification still exists
      expect(notificationService.getNotifications()).toHaveLength(1);
    });
  });

  describe('Subscription', () => {
    test('should notify subscribers when notifications change', () => {
      // Create a mock subscriber
      const mockSubscriber = jest.fn();
      
      // Subscribe to notifications
      const unsubscribe = notificationService.subscribe(mockSubscriber);
      
      // Verify subscriber was called immediately with empty notifications
      expect(mockSubscriber).toHaveBeenCalledTimes(1);
      expect(mockSubscriber).toHaveBeenCalledWith([]);
      
      // Create a notification
      const notification = notificationService.info('Test notification');
      
      // Verify subscriber was called with the new notification
      expect(mockSubscriber).toHaveBeenCalledTimes(2);
      expect(mockSubscriber).toHaveBeenCalledWith([notification]);
      
      // Remove the notification
      notificationService.removeNotification(notification.id);
      
      // Verify subscriber was called with empty notifications
      expect(mockSubscriber).toHaveBeenCalledTimes(3);
      expect(mockSubscriber).toHaveBeenCalledWith([]);
      
      // Unsubscribe
      unsubscribe();
      
      // Create another notification
      notificationService.success('After unsubscribe');
      
      // Verify subscriber was not called again
      expect(mockSubscriber).toHaveBeenCalledTimes(3);
    });
  });

  describe('API Error Handling', () => {
    test('should handle API errors correctly', () => {
      // Create a mock API error
      const apiError = {
        status: 404,
        statusText: 'Not Found',
        message: 'Resource not found',
        data: {
          details: 'The requested resource does not exist'
        }
      };
      
      // Handle the API error
      const notification = notificationService.handleApiError(apiError);
      
      // Verify notification was created with correct properties
      expect(notification.type).toBe(NOTIFICATION_TYPES.ERROR);
      expect(notification.message).toBe('Resource not found');
      expect(notification.autoClose).toBe(false);
      expect(notification.details).toBe('The requested resource does not exist');
      expect(notification.statusCode).toBe(404);
    });

    test('should use fallback message when API error has no message', () => {
      // Create a mock API error without a message
      const apiError = {
        status: 500,
        statusText: 'Internal Server Error'
      };
      
      // Handle the API error with a fallback message
      const notification = notificationService.handleApiError(apiError, 'Something went wrong');
      
      // Verify notification uses the fallback message
      expect(notification.message).toBe('Something went wrong');
      expect(notification.details).toBe('Internal Server Error');
    });
  });

  describe('Error Object Handling', () => {
    test('should handle Error objects correctly', () => {
      // Create an Error object
      const error = new Error('This is a JavaScript error');
      
      // Create an error notification with the Error object
      const notification = notificationService.error('Custom message', error);
      
      // Verify notification was created with correct properties
      expect(notification.message).toBe('Custom message');
      expect(notification.details).toBe('This is a JavaScript error');
    });

    test('should use Error message as notification message if no message provided', () => {
      // Create an Error object
      const error = new Error('This is a JavaScript error');
      
      // Create an error notification with only the Error object
      const notification = notificationService.error(null, error);
      
      // Verify notification uses Error message
      expect(notification.message).toBe('This is a JavaScript error');
    });
  });
}); 