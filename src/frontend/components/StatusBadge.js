import React from 'react';
import { Chip, useTheme } from '@mui/material';
import {
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Pending as PendingIcon,
  Cancel as CancelledIcon,
  HourglassEmpty as ProcessingIcon
} from '@mui/icons-material';

/**
 * Status badge component for displaying status indicators with consistent styling
 * 
 * @param {string} status - The status value to display (success, error, warning, pending, cancelled, processing)
 * @param {string} label - Optional custom label (defaults to capitalized status)
 * @param {boolean} outlined - Whether to use outlined variant (default: false)
 * @param {object} sx - Additional styles
 */
const StatusBadge = ({ 
  status, 
  label, 
  outlined = false, 
  sx = {} 
}) => {
  const theme = useTheme();
  
  // Define color and icon mapping based on status
  const statusConfig = {
    success: {
      color: 'success',
      icon: <SuccessIcon style={{ fontSize: '1rem' }} />,
      defaultLabel: 'Success',
    },
    error: {
      color: 'error',
      icon: <ErrorIcon style={{ fontSize: '1rem' }} />,
      defaultLabel: 'Error',
    },
    warning: {
      color: 'warning',
      icon: <WarningIcon style={{ fontSize: '1rem' }} />,
      defaultLabel: 'Warning',
    },
    pending: {
      color: 'info',
      icon: <PendingIcon style={{ fontSize: '1rem' }} />,
      defaultLabel: 'Pending',
    },
    cancelled: {
      color: 'default',
      icon: <CancelledIcon style={{ fontSize: '1rem' }} />,
      defaultLabel: 'Cancelled',
    },
    processing: {
      color: 'primary',
      icon: <ProcessingIcon style={{ fontSize: '1rem' }} />,
      defaultLabel: 'Processing',
    },
    // Map order statuses to visual states
    open: {
      color: 'info',
      icon: <PendingIcon style={{ fontSize: '1rem' }} />,
      defaultLabel: 'Open',
    },
    filled: {
      color: 'success',
      icon: <SuccessIcon style={{ fontSize: '1rem' }} />,
      defaultLabel: 'Filled',
    },
    rejected: {
      color: 'error',
      icon: <ErrorIcon style={{ fontSize: '1rem' }} />,
      defaultLabel: 'Rejected',
    },
    canceled: {
      color: 'default',
      icon: <CancelledIcon style={{ fontSize: '1rem' }} />,
      defaultLabel: 'Canceled',
    },
    partial: {
      color: 'warning',
      icon: <WarningIcon style={{ fontSize: '1rem' }} />,
      defaultLabel: 'Partial Fill',
    },
  };

  // Default to 'pending' if status not found
  const config = statusConfig[status?.toLowerCase()] || statusConfig.pending;
  const displayLabel = label || config.defaultLabel;
  
  return (
    <Chip 
      icon={config.icon}
      label={displayLabel}
      color={config.color}
      variant={outlined ? 'outlined' : 'filled'}
      size="small"
      sx={{ 
        fontWeight: 500,
        fontSize: '0.75rem',
        ...sx 
      }}
    />
  );
};

export default StatusBadge; 