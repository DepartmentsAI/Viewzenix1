/**
 * Browser Compatibility Checker
 * 
 * This module provides functionality to check if the current browser
 * is compatible with the application's requirements.
 */

/**
 * Minimum browser versions required
 */
const MIN_BROWSER_VERSIONS = {
  chrome: 80,
  firefox: 74,
  safari: 13,
  edge: 80, // Chromium-based Edge
  opera: 67,
  samsung: 11.1,
  ie: false // IE is not supported
};

/**
 * Required browser features
 */
const REQUIRED_FEATURES = [
  { name: 'Promise', test: () => typeof Promise !== 'undefined' },
  { name: 'Fetch API', test: () => typeof fetch !== 'undefined' },
  { name: 'async/await', test: () => {
    try {
      eval('(async function() {})()');
      return true;
    } catch (e) {
      return false;
    }
  }},
  { name: 'Array.prototype.includes', test: () => Array.prototype.includes !== undefined },
  { name: 'Object.entries', test: () => Object.entries !== undefined },
  { name: 'localStorage', test: () => {
    try {
      return localStorage !== undefined;
    } catch (e) {
      return false;
    }
  }},
  { name: 'sessionStorage', test: () => {
    try {
      return sessionStorage !== undefined;
    } catch (e) {
      return false;
    }
  }},
  { name: 'CSS Grid', test: () => {
    return window.CSS && CSS.supports && CSS.supports('display', 'grid');
  }},
  { name: 'CSS Flexbox', test: () => {
    return window.CSS && CSS.supports && CSS.supports('display', 'flex');
  }},
  { name: 'WebSockets', test: () => {
    return typeof WebSocket !== 'undefined';
  }},
  { name: 'Intersection Observer', test: () => {
    return typeof IntersectionObserver !== 'undefined';
  }}
];

/**
 * Detect browser name and version
 * @returns {Object} Browser information including name and version
 */
function detectBrowser() {
  const userAgent = navigator.userAgent;
  let browser = {
    name: 'unknown',
    version: 0,
    userAgent
  };

  // Chrome
  let match = userAgent.match(/(chrome|chromium)\/(\d+)/i);
  if (match && !userAgent.match(/edg/i)) {
    browser.name = 'chrome';
    browser.version = parseInt(match[2], 10);
    return browser;
  }

  // Edge (Chromium)
  match = userAgent.match(/edg\/(\d+)/i);
  if (match) {
    browser.name = 'edge';
    browser.version = parseInt(match[1], 10);
    return browser;
  }

  // Firefox
  match = userAgent.match(/firefox\/(\d+)/i);
  if (match) {
    browser.name = 'firefox';
    browser.version = parseInt(match[1], 10);
    return browser;
  }

  // Safari
  match = userAgent.match(/version\/(\d+).*safari/i);
  if (match && !userAgent.match(/chrome/i)) {
    browser.name = 'safari';
    browser.version = parseInt(match[1], 10);
    return browser;
  }

  // Opera
  match = userAgent.match(/opr\/(\d+)/i);
  if (match) {
    browser.name = 'opera';
    browser.version = parseInt(match[1], 10);
    return browser;
  }

  // Samsung Internet
  match = userAgent.match(/samsungbrowser\/(\d+\.\d+)/i);
  if (match) {
    browser.name = 'samsung';
    browser.version = parseFloat(match[1]);
    return browser;
  }

  // Internet Explorer
  match = userAgent.match(/msie|trident.*rv[ :](\d+)/i);
  if (match) {
    browser.name = 'ie';
    browser.version = parseInt(match[1], 10);
    return browser;
  }

  return browser;
}

/**
 * Check if the current browser meets version requirements
 * @returns {Object} Result of the browser version check
 */
function checkBrowserVersion() {
  const browser = detectBrowser();
  const minVersion = MIN_BROWSER_VERSIONS[browser.name];

  // If browser not in our list or explicitly set to false (not supported)
  if (minVersion === undefined || minVersion === false) {
    return {
      supported: false,
      reason: `Browser ${browser.name} is not officially supported`,
      browser
    };
  }

  const isSupported = browser.version >= minVersion;
  return {
    supported: isSupported,
    reason: isSupported ? 
      `Browser ${browser.name} version ${browser.version} is supported` : 
      `Browser ${browser.name} version ${browser.version} is below minimum required version ${minVersion}`,
    browser
  };
}

/**
 * Check for required browser features
 * @returns {Object} Results of feature checks
 */
function checkFeatures() {
  const results = {
    supported: true,
    features: [],
    missingFeatures: []
  };

  REQUIRED_FEATURES.forEach(feature => {
    const isSupported = feature.test();
    results.features.push({
      name: feature.name,
      supported: isSupported
    });

    if (!isSupported) {
      results.supported = false;
      results.missingFeatures.push(feature.name);
    }
  });

  return results;
}

/**
 * Check if browser allows cookies
 * @returns {boolean} Whether cookies are enabled
 */
function checkCookiesEnabled() {
  let cookiesEnabled = navigator.cookieEnabled;
  
  if (!cookiesEnabled) {
    // Try to create a test cookie
    document.cookie = "testcookie=1";
    cookiesEnabled = document.cookie.indexOf("testcookie=") !== -1;
    
    // Clean up test cookie
    if (cookiesEnabled) {
      document.cookie = "testcookie=1; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    }
  }
  
  return cookiesEnabled;
}

/**
 * Check if localStorage and sessionStorage are available and working
 * @returns {Object} Results of the storage check
 */
function checkStorage() {
  const result = {
    localStorage: false,
    sessionStorage: false,
    supported: false
  };
  
  try {
    localStorage.setItem('test', 'test');
    localStorage.removeItem('test');
    result.localStorage = true;
  } catch (e) {
    result.localStorage = false;
  }
  
  try {
    sessionStorage.setItem('test', 'test');
    sessionStorage.removeItem('test');
    result.sessionStorage = true;
  } catch (e) {
    result.sessionStorage = false;
  }
  
  result.supported = result.localStorage && result.sessionStorage;
  return result;
}

/**
 * Check if the browser is in private/incognito mode
 * @returns {Promise<boolean>} Whether the browser is in private mode
 */
function checkPrivateMode() {
  return new Promise(resolve => {
    const isPrivate = () => {
      try {
        // Try to use localStorage
        localStorage.setItem('test', 'test');
        localStorage.removeItem('test');
        
        // Firefox private browsing has reduced storage quota
        const db = indexedDB.open('test');
        db.onerror = () => resolve(true);
        db.onsuccess = () => resolve(false);
      } catch (e) {
        // localStorage failed, likely private mode
        resolve(true);
      }
    };
    
    isPrivate();
    
    // Safeguard: resolve after 1 second if no resolution yet
    setTimeout(() => resolve(false), 1000);
  });
}

/**
 * Perform a comprehensive compatibility check
 * @returns {Promise<Object>} Comprehensive compatibility results
 */
async function checkCompatibility() {
  const versionCheck = checkBrowserVersion();
  const featureCheck = checkFeatures();
  const cookiesEnabled = checkCookiesEnabled();
  const storageCheck = checkStorage();
  const isPrivateMode = await checkPrivateMode();
  
  const isFullySupported = 
    versionCheck.supported && 
    featureCheck.supported && 
    cookiesEnabled && 
    storageCheck.supported;
  
  return {
    fullCompatibility: isFullySupported,
    browserVersion: versionCheck,
    features: featureCheck,
    cookies: {
      enabled: cookiesEnabled
    },
    storage: storageCheck,
    privateMode: {
      enabled: isPrivateMode,
      supported: true // We support private browsing
    },
    summary: isFullySupported ? 
      'Your browser is fully compatible' : 
      'Your browser has compatibility issues'
  };
}

/**
 * Format compatibility results into HTML
 * @param {Object} results Compatibility check results
 * @returns {string} HTML representation of results
 */
function formatResultsAsHTML(results) {
  const statusIcon = (status) => status ? '✅' : '❌';
  
  return `
    <div class="compatibility-report">
      <h2>Browser Compatibility Report</h2>
      <div class="summary ${results.fullCompatibility ? 'success' : 'error'}">
        ${results.summary}
      </div>
      
      <div class="section">
        <h3>Browser Information</h3>
        <p>
          ${statusIcon(results.browserVersion.supported)} 
          ${results.browserVersion.browser.name} ${results.browserVersion.browser.version}
          ${results.browserVersion.supported ? '' : ` (Required: ${MIN_BROWSER_VERSIONS[results.browserVersion.browser.name]}+)`}
        </p>
      </div>
      
      <div class="section">
        <h3>Required Features</h3>
        <ul>
          ${results.features.features.map(feature => 
            `<li>${statusIcon(feature.supported)} ${feature.name}</li>`
          ).join('')}
        </ul>
      </div>
      
      <div class="section">
        <h3>Browser Settings</h3>
        <ul>
          <li>${statusIcon(results.cookies.enabled)} Cookies Enabled</li>
          <li>${statusIcon(results.storage.localStorage)} LocalStorage Available</li>
          <li>${statusIcon(results.storage.sessionStorage)} SessionStorage Available</li>
          <li>${statusIcon(true)} Private Browsing: ${results.privateMode.enabled ? 'Enabled' : 'Disabled'}</li>
        </ul>
      </div>
      
      ${!results.fullCompatibility ? `
      <div class="section recommendations">
        <h3>Recommendations</h3>
        <ul>
          ${!results.browserVersion.supported ? 
            `<li>Upgrade to a newer version of ${results.browserVersion.browser.name} or try a different browser</li>` : ''}
          ${results.features.missingFeatures.length > 0 ? 
            `<li>Your browser is missing required features: ${results.features.missingFeatures.join(', ')}</li>` : ''}
          ${!results.cookies.enabled ? 
            `<li>Enable cookies in your browser settings</li>` : ''}
          ${!results.storage.supported ? 
            `<li>Enable local storage in your browser settings or try a different browser</li>` : ''}
        </ul>
      </div>
      ` : ''}
    </div>
  `;
}

/**
 * Inject compatibility check results into the DOM
 * @param {string} selector CSS selector for the target element
 * @param {Object} results Compatibility check results
 */
function displayResults(selector, results) {
  const targetElement = document.querySelector(selector);
  if (!targetElement) {
    console.error(`Element not found: ${selector}`);
    return;
  }
  
  targetElement.innerHTML = formatResultsAsHTML(results);
  
  // Add some basic styling
  const style = document.createElement('style');
  style.textContent = `
    .compatibility-report {
      font-family: Arial, sans-serif;
      margin: 20px 0;
      padding: 15px;
      border-radius: 5px;
      border: 1px solid #ddd;
      max-width: 600px;
    }
    .summary {
      padding: 10px;
      border-radius: 4px;
      margin-bottom: 15px;
      font-weight: bold;
    }
    .success {
      background-color: #dff0d8;
      color: #3c763d;
    }
    .error {
      background-color: #f2dede;
      color: #a94442;
    }
    .section {
      margin-bottom: 15px;
    }
    .section h3 {
      margin-top: 0;
      border-bottom: 1px solid #eee;
      padding-bottom: 5px;
    }
    .recommendations {
      background-color: #fcf8e3;
      padding: 10px;
      border-radius: 4px;
    }
  `;
  document.head.appendChild(style);
}

/**
 * Run compatibility check and display results
 * @param {string} selector CSS selector for the target element
 * @returns {Promise<Object>} Compatibility check results
 */
async function runCompatibilityCheck(selector = '#compatibility-results') {
  const results = await checkCompatibility();
  
  if (typeof document !== 'undefined') {
    displayResults(selector, results);
  }
  
  return results;
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    detectBrowser,
    checkBrowserVersion,
    checkFeatures,
    checkCookiesEnabled,
    checkStorage,
    checkPrivateMode,
    checkCompatibility,
    runCompatibilityCheck,
    MIN_BROWSER_VERSIONS,
    REQUIRED_FEATURES
  };
} 