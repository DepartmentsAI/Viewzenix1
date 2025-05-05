import React, { useEffect, useState } from 'react';
import { Alert, AlertTitle, Box, Button, Collapse, Typography, List, ListItem, ListItemIcon, ListItemText } from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import CloseIcon from '@mui/icons-material/Close';

/**
 * Component that checks browser compatibility and displays warnings if needed
 * 
 * @param {Object} props Component props
 * @param {Function} props.onCompatibilityChecked Callback function when check completes
 * @param {boolean} props.showOnlyWhenIncompatible Only show when browser is incompatible
 * @param {boolean} props.allowDismiss Allow user to dismiss the warning
 * @param {string} props.severity Alert severity (error, warning, info)
 */
function BrowserCompatibilityChecker({
  onCompatibilityChecked,
  showOnlyWhenIncompatible = true,
  allowDismiss = true,
  severity = 'warning'
}) {
  const [compatibility, setCompatibility] = useState(null);
  const [checking, setChecking] = useState(true);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    // Check if warning was previously dismissed
    const wasWarningDismissed = localStorage.getItem('browser-warning-dismissed');
    if (wasWarningDismissed === 'true') {
      setDismissed(true);
    }

    // Import module dynamically to avoid errors in SSR environment
    import('../utils/browser-compatibility-check').then(module => {
      const { checkCompatibility } = module;
      
      checkCompatibility().then(results => {
        setCompatibility(results);
        
        if (onCompatibilityChecked) {
          onCompatibilityChecked(results);
        }
        
        setChecking(false);
      }).catch(err => {
        console.error('Error checking browser compatibility:', err);
        setChecking(false);
      });
    }).catch(err => {
      console.error('Error loading browser compatibility module:', err);
      setChecking(false);
    });
  }, [onCompatibilityChecked]);

  const handleDismiss = () => {
    setDismissed(true);
    localStorage.setItem('browser-warning-dismissed', 'true');
  };

  // Don't render anything while checking
  if (checking) {
    return null;
  }

  // Don't render if compatibility check failed
  if (!compatibility) {
    return null;
  }

  // Don't show if browser is compatible and we're configured to only show incompatibility
  if (compatibility.fullCompatibility && showOnlyWhenIncompatible) {
    return null;
  }

  // Don't show if dismissed and dismissal is allowed
  if (dismissed && allowDismiss) {
    return null;
  }

  return (
    <Collapse in={!dismissed}>
      <Alert 
        severity={compatibility.fullCompatibility ? 'success' : severity}
        action={
          allowDismiss ? (
            <Button 
              color="inherit" 
              size="small" 
              onClick={handleDismiss}
              startIcon={<CloseIcon />}
            >
              Dismiss
            </Button>
          ) : null
        }
        sx={{ mb: 2 }}
      >
        <AlertTitle>
          {compatibility.fullCompatibility 
            ? 'Browser Compatibility: Compatible' 
            : 'Browser Compatibility Warning'}
        </AlertTitle>
        
        <Box sx={{ mt: 1 }}>
          {/* Browser Information */}
          <Typography variant="body2" component="div" gutterBottom>
            You're using <strong>{compatibility.browserVersion.browser.name} {compatibility.browserVersion.browser.version}</strong>
            {!compatibility.browserVersion.supported && compatibility.browserVersion.browser.name !== 'unknown' && (
              <>
                {' '}(minimum version required: <strong>{window.MIN_BROWSER_VERSIONS?.[compatibility.browserVersion.browser.name]}</strong>)
              </>
            )}
          </Typography>
          
          {/* Features Check */}
          {compatibility.features && compatibility.features.missingFeatures && compatibility.features.missingFeatures.length > 0 && (
            <>
              <Typography variant="body2" component="div" gutterBottom>
                Missing features:
              </Typography>
              <List dense disablePadding sx={{ ml: 2 }}>
                {compatibility.features.missingFeatures.map((feature, index) => (
                  <ListItem key={index} disableGutters disablePadding>
                    <ListItemIcon sx={{ minWidth: 24 }}>
                      <ErrorOutlineIcon color="error" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={feature} />
                  </ListItem>
                ))}
              </List>
            </>
          )}
          
          {/* Storage Information */}
          {!compatibility.storage?.supported && (
            <Typography variant="body2" color="error" gutterBottom>
              Local storage is not available. Some features may not work correctly.
            </Typography>
          )}
          
          {/* Private Mode Information */}
          {compatibility.privateMode?.enabled && (
            <Typography variant="body2" color="info" sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
              <InfoOutlinedIcon fontSize="small" sx={{ mr: 0.5 }} />
              Private browsing mode detected. Data may not persist between sessions.
            </Typography>
          )}
          
          {/* Recommendation for incompatible browsers */}
          {!compatibility.fullCompatibility && (
            <Typography variant="body2" sx={{ mt: 1 }}>
              For the best experience, please use the latest version of Chrome, Firefox, Edge, or Safari.
            </Typography>
          )}
        </Box>
      </Alert>
    </Collapse>
  );
}

export default BrowserCompatibilityChecker; 