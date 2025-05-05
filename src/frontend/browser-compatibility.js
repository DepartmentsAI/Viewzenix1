/**
 * Browser Compatibility Check
 * 
 * This script runs in the browser to verify compatibility with the Viewzenix1 application.
 * It checks for required features and warns users about any missing functionality.
 * 
 * Usage: Include this script before the main application script in index.html
 */

(function() {
  // Enable strict mode for better error detection
  'use strict';

  // Create a container for compatibility messages
  const createMessageContainer = () => {
    const container = document.createElement('div');
    container.id = 'compatibility-warning';
    container.style.position = 'fixed';
    container.style.top = '0';
    container.style.left = '0';
    container.style.width = '100%';
    container.style.backgroundColor = '#fff3cd';
    container.style.color = '#856404';
    container.style.padding = '10px';
    container.style.boxSizing = 'border-box';
    container.style.zIndex = '9999';
    container.style.fontFamily = 'Arial, sans-serif';
    container.style.fontSize = '14px';
    container.style.textAlign = 'center';
    container.style.borderBottom = '1px solid #ffeeba';
    return container;
  };

  // Show a warning message to the user
  const showWarning = (message) => {
    // Only add warning if the DOM is ready
    const displayWarning = () => {
      // Create container if it doesn't exist
      let container = document.getElementById('compatibility-warning');
      if (!container) {
        container = createMessageContainer();
        document.body.prepend(container);
      }
      
      // Add the message
      const messageElement = document.createElement('p');
      messageElement.style.margin = '4px 0';
      messageElement.innerHTML = message;
      container.appendChild(messageElement);
    };

    // Check if DOM is already loaded
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', displayWarning);
    } else {
      displayWarning();
    }
  };

  // Feature detection dictionary
  const requiredFeatures = {
    'ES6 Support': () => {
      try {
        // Test arrow functions
        eval('() => {}');
        // Test template literals
        eval('`test`');
        // Test const/let
        eval('const x = 1; let y = 2;');
        // Test spread operator
        eval('[...Array(3)]');
        // Test async/await
        eval('async function test() { await Promise.resolve(); }');
        return true;
      } catch (e) {
        return false;
      }
    },
    'Fetch API': () => typeof fetch === 'function',
    'Promise': () => typeof Promise === 'function',
    'localStorage': () => {
      try {
        localStorage.setItem('test', 'test');
        localStorage.removeItem('test');
        return true;
      } catch (e) {
        return false;
      }
    },
    'JSON Parsing': () => typeof JSON !== 'undefined' && typeof JSON.parse === 'function',
    'Flexbox Support': () => {
      const div = document.createElement('div');
      return (
        'flexBasis' in div.style ||
        'webkitFlexBasis' in div.style ||
        'msFlexBasis' in div.style
      );
    }
  };

  // Check recommended browser versions
  const recommendedBrowsers = {
    'Chrome': 88,
    'Firefox': 85,
    'Safari': 14,
    'Edge': 88,
    'Opera': 74
  };

  // Detect current browser and version
  const detectBrowser = () => {
    const ua = navigator.userAgent;
    let browser = 'Unknown';
    let version = 'Unknown';

    // Chrome
    if (/Chrome/.test(ua) && !/Chromium|Edge|OPR|Opera/.test(ua)) {
      browser = 'Chrome';
      version = parseFloat(ua.match(/Chrome\/(\d+\.\d+)/)[1]);
    }
    // Firefox
    else if (/Firefox/.test(ua)) {
      browser = 'Firefox';
      version = parseFloat(ua.match(/Firefox\/(\d+\.\d+)/)[1]);
    }
    // Safari (excluding Chrome)
    else if (/Safari/.test(ua) && !/Chrome/.test(ua)) {
      browser = 'Safari';
      version = parseFloat(ua.match(/Version\/(\d+\.\d+)/)[1]);
    }
    // Edge (Chromium-based)
    else if (/Edg/.test(ua)) {
      browser = 'Edge';
      version = parseFloat(ua.match(/Edg\/(\d+\.\d+)/)[1]);
    }
    // Opera
    else if (/OPR|Opera/.test(ua)) {
      browser = 'Opera';
      version = parseFloat((ua.match(/OPR\/(\d+\.\d+)/) || ua.match(/Opera\/(\d+\.\d+)/))[1]);
    }
    
    return { browser, version };
  };

  // Run compatibility checks
  const runCompatibilityChecks = () => {
    // Check browser version
    const { browser, version } = detectBrowser();
    const recommendedVersion = recommendedBrowsers[browser];
    
    if (recommendedVersion && version < recommendedVersion) {
      showWarning(
        `<strong>Browser Upgrade Recommended:</strong> You're using ${browser} ${version}. ` +
        `For the best experience, we recommend ${browser} ${recommendedVersion} or higher. ` +
        `<a href="https://browsehappy.com/" target="_blank" rel="noopener">Upgrade your browser</a>`
      );
    }
    
    // Check required features
    for (const [feature, testFn] of Object.entries(requiredFeatures)) {
      if (!testFn()) {
        showWarning(
          `<strong>Browser Compatibility Issue:</strong> Your browser doesn't support ${feature}, ` +
          `which is required for this application. Some features may not work correctly. ` +
          `Please update to a modern browser.`
        );
      }
    }
  };

  // Run checks
  runCompatibilityChecks();
})(); 