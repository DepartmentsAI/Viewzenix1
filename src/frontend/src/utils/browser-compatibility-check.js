/**
 * Browser Compatibility Check Utility for React
 * 
 * This module exports functions to check browser compatibility
 * in a React application.
 */

// Define minimum browser versions
const MIN_BROWSER_VERSIONS = {
  chrome: 80,
  firefox: 74,
  safari: 13,
  edge: 80, // Chromium-based Edge
  opera: 67,
  samsung: 11.1,
  ie: false // IE is not supported
};

// Expose to window for use in the component
if (typeof window !== 'undefined') {
  window.MIN_BROWSER_VERSIONS = MIN_BROWSER_VERSIONS;
}

/**
 * Parse browser and version from user agent
 * @param {string} userAgent - The browser's user agent string
 * @returns {Object} Browser info object with name and version
 */
export function parseUserAgent(userAgent = '') {
  if (typeof userAgent !== 'string') {
    userAgent = typeof navigator !== 'undefined' ? navigator.userAgent : '';
  }
  
  const ua = userAgent.toLowerCase();
  let browser = {
    name: 'unknown',
    version: 0
  };

  // Chrome
  let match = ua.match(/(chrome|chromium)\/(\d+)/);
  if (match) {
    browser.name = 'chrome';
    browser.version = parseInt(match[2], 10);
    
    // Edge (Chromium-based) needs to be checked after Chrome
    if (ua.indexOf('edg') > -1) {
      match = ua.match(/edg\/(\d+)/);
      if (match) {
        browser.name = 'edge';
        browser.version = parseInt(match[1], 10);
      }
    }
    
    // Opera (Chromium-based) needs to be checked after Chrome
    if (ua.indexOf('opr') > -1) {
      match = ua.match(/opr\/(\d+)/);
      if (match) {
        browser.name = 'opera';
        browser.version = parseInt(match[1], 10);
      }
    }
    
    // Samsung Internet (Chromium-based)
    if (ua.indexOf('samsungbrowser') > -1) {
      match = ua.match(/samsungbrowser\/(\d+\.\d+)/);
      if (match) {
        browser.name = 'samsung';
        browser.version = parseFloat(match[1]);
      }
    }
  }
  
  // Firefox
  else if ((match = ua.match(/firefox\/(\d+)/))) {
    browser.name = 'firefox';
    browser.version = parseInt(match[1], 10);
  }
  
  // Safari
  else if (ua.indexOf('safari') > -1 && ua.indexOf('chrome') === -1) {
    match = ua.match(/version\/(\d+)/);
    if (match) {
      browser.name = 'safari';
      browser.version = parseInt(match[1], 10);
    }
  }
  
  // Internet Explorer
  else if ((match = ua.match(/msie\s(\d+)|trident\/.*rv:(\d+)/))) {
    browser.name = 'ie';
    browser.version = parseInt(match[1] || match[2], 10);
  }

  return browser;
}

/**
 * Checks if the current browser version is supported
 * @param {Object} browser - Browser object from parseUserAgent
 * @returns {Object} Result with supported status
 */
export function checkBrowserVersion(browser = null) {
  if (!browser) {
    browser = parseUserAgent();
  }
  
  const minVersion = MIN_BROWSER_VERSIONS[browser.name];
  const isSupported = 
    // If minVersion is false, the browser is not supported at all
    minVersion !== false && 
    // If minVersion is a number, check browser version
    typeof minVersion === 'number' && browser.version >= minVersion;
  
  return {
    browser,
    supported: isSupported,
    minVersion
  };
}

/**
 * Checks for required browser features
 * @returns {Object} Result with missing features
 */
export function checkFeatures() {
  const requiredFeatures = [
    { name: 'ES6 Promise', test: () => typeof Promise !== 'undefined' },
    { name: 'Fetch API', test: () => typeof fetch !== 'undefined' },
    { name: 'localStorage', test: () => {
      try {
        return typeof localStorage !== 'undefined';
      } catch (e) {
        return false;
      }
    }},
    { name: 'sessionStorage', test: () => {
      try {
        return typeof sessionStorage !== 'undefined';
      } catch (e) {
        return false;
      }
    }},
    { name: 'CSS Grid', test: () => {
      if (typeof document === 'undefined') return true; // SSR check
      const div = document.createElement('div');
      return typeof div.style.grid !== 'undefined';
    }},
    { name: 'Flexbox', test: () => {
      if (typeof document === 'undefined') return true; // SSR check
      const div = document.createElement('div');
      return typeof div.style.flexDirection !== 'undefined';
    }}
  ];
  
  const missingFeatures = [];
  
  for (const feature of requiredFeatures) {
    if (!feature.test()) {
      missingFeatures.push(feature.name);
    }
  }
  
  return {
    missingFeatures,
    supported: missingFeatures.length === 0
  };
}

/**
 * Checks for private browsing mode
 * @returns {Object} Result with private mode status
 */
export async function checkPrivateMode() {
  // Modern method to detect private browsing
  try {
    // Try to use localStorage as a test
    if (typeof localStorage === 'undefined') {
      return { enabled: true };
    }
    
    // In Safari private mode, localStorage is available but throws when written to
    localStorage.setItem('__test', '1');
    localStorage.removeItem('__test');
    
    // In some browsers, indexed DB is not available in private mode
    if (typeof indexedDB === 'undefined') {
      return { enabled: true };
    }
    
    return { enabled: false };
  } catch (e) {
    // If we get an error trying to access localStorage, we're likely in private mode
    return { enabled: true };
  }
}

/**
 * Tests local storage availability
 * @returns {Object} Result with storage support status
 */
export function checkStorage() {
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('__test', '1');
      localStorage.removeItem('__test');
      return { supported: true };
    }
    return { supported: false };
  } catch (e) {
    return { supported: false };
  }
}

/**
 * Comprehensive browser compatibility check
 * @returns {Promise<Object>} Full compatibility results
 */
export async function checkCompatibility() {
  const browserVersion = checkBrowserVersion();
  const features = checkFeatures();
  const storage = checkStorage();
  const privateMode = await checkPrivateMode();
  
  const fullCompatibility = 
    browserVersion.supported && 
    features.supported && 
    storage.supported;
  
  return {
    browserVersion,
    features,
    storage,
    privateMode,
    fullCompatibility,
    timestamp: new Date().toISOString()
  };
}

/**
 * Initialize the compatibility checker in the app
 * @param {Object} options - Configuration options
 * @returns {Promise<Object>} Compatibility results
 */
export async function initCompatibilityCheck(options = {}) {
  const {
    showWarning = true,
    blockIncompatible = false,
    onCheck = null
  } = options;
  
  const results = await checkCompatibility();
  
  if (onCheck && typeof onCheck === 'function') {
    onCheck(results);
  }
  
  if (!results.fullCompatibility) {
    if (blockIncompatible) {
      // Redirect to incompatible browser page
      if (typeof window !== 'undefined') {
        window.location.href = '/incompatible-browser.html';
      }
    } else if (showWarning) {
      // Show warning is handled by the React component
    }
  }
  
  return results;
}

export default {
  checkCompatibility,
  parseUserAgent,
  checkBrowserVersion,
  checkFeatures,
  checkStorage,
  checkPrivateMode,
  initCompatibilityCheck,
  MIN_BROWSER_VERSIONS
}; 