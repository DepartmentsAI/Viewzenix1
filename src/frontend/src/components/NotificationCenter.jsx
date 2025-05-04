import React, { useState, useEffect } from 'react';
import notificationService, { NOTIFICATION_TYPES } from '../../services/notificationService';

// Styles for the notification container
const containerStyles = {
  position: 'fixed',
  zIndex: 1000,
  display: 'flex',
  flexDirection: 'column',
  gap: '10px',
  maxWidth: '400px',
  width: '100%'
};

// Position styles
const positions = {
  'top-right': { top: '20px', right: '20px' },
  'top-left': { top: '20px', left: '20px' },
  'bottom-right': { bottom: '20px', right: '20px' },
  'bottom-left': { bottom: '20px', left: '20px' },
  'top-center': { top: '20px', left: '50%', transform: 'translateX(-50%)' },
  'bottom-center': { bottom: '20px', left: '50%', transform: 'translateX(-50%)' }
};

// Notification type styles
const typeStyles = {
  [NOTIFICATION_TYPES.SUCCESS]: {
    backgroundColor: '#4caf50',
    color: 'white',
    borderLeft: '5px solid #388e3c'
  },
  [NOTIFICATION_TYPES.ERROR]: {
    backgroundColor: '#f44336',
    color: 'white',
    borderLeft: '5px solid #d32f2f'
  },
  [NOTIFICATION_TYPES.WARNING]: {
    backgroundColor: '#ff9800',
    color: 'white',
    borderLeft: '5px solid #f57c00'
  },
  [NOTIFICATION_TYPES.INFO]: {
    backgroundColor: '#2196f3',
    color: 'white',
    borderLeft: '5px solid #1976d2'
  }
};

/**
 * Individual notification item component
 */
const Notification = ({ notification, onClose }) => {
  const { id, type, message, details, statusCode } = notification;
  
  const notificationStyles = {
    padding: '15px 20px',
    borderRadius: '4px',
    boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
    position: 'relative',
    ...typeStyles[type]
  };
  
  const closeButtonStyles = {
    position: 'absolute',
    top: '10px',
    right: '10px',
    background: 'transparent',
    border: 'none',
    color: 'inherit',
    fontSize: '16px',
    cursor: 'pointer'
  };
  
  const detailsStyles = {
    fontSize: '0.85em',
    marginTop: '8px',
    opacity: 0.9
  };
  
  const statusStyles = {
    fontSize: '0.85em',
    marginTop: '8px',
    fontWeight: 'bold'
  };
  
  return (
    <div role="alert" style={notificationStyles}>
      <button 
        onClick={() => onClose(id)} 
        style={closeButtonStyles}
        aria-label="Close notification"
      >
        ✖
      </button>
      
      <div>{message}</div>
      
      {statusCode && (
        <div style={statusStyles}>Status: {statusCode}</div>
      )}
      
      {details && (
        <div style={detailsStyles}>{details}</div>
      )}
    </div>
  );
};

/**
 * NotificationCenter component
 * Displays notifications from the notification service
 * 
 * @param {Object} props - Component props
 * @param {string} props.position - Position of notifications (default: 'top-right')
 * @param {number} props.maxNotifications - Maximum number of notifications to show (default: 5)
 */
const NotificationCenter = ({ 
  position = 'top-right',
  maxNotifications = 5
}) => {
  const [notifications, setNotifications] = useState([]);
  
  useEffect(() => {
    // Subscribe to notification service
    const unsubscribe = notificationService.subscribe(notifications => {
      // Limit the number of visible notifications
      setNotifications(
        notifications.slice(0, maxNotifications)
      );
    });
    
    // Cleanup subscription on unmount
    return () => unsubscribe();
  }, [maxNotifications]);
  
  const handleClose = (id) => {
    notificationService.removeNotification(id);
  };
  
  const positionStyle = positions[position] || positions['top-right'];
  
  if (notifications.length === 0) return null;
  
  return (
    <div style={{ ...containerStyles, ...positionStyle }}>
      {notifications.map(notification => (
        <Notification
          key={notification.id}
          notification={notification}
          onClose={handleClose}
        />
      ))}
    </div>
  );
};

export default NotificationCenter; 