/**
 * Viewzenix1 Browser Compatibility Check
 * 
 * This file contains code to check if the user's browser is compatible
 * with the application's requirements. Include this in your index.html
 * before loading React to prevent compatibility issues.
 */

(function() {
  // Minimum required browser versions
  const MIN_BROWSER_VERSIONS = {
    chrome: 60,
    firefox: 60,
    safari: 12,
    edge: 79,
    opera: 47,
    ie: Infinity // Not supported
  };

  // Feature detection checks
  const REQUIRED_FEATURES = [
    { name: 'ES6 Support', test: () => typeof Symbol !== 'undefined' && typeof Promise !== 'undefined' },
    { name: 'Arrow Functions', test: () => { try { eval('() => {}'); return true; } catch (e) { return false; } } },
    { name: 'Fetch API', test: () => typeof fetch !== 'undefined' },
    { name: 'LocalStorage', test: () => { try { return 'localStorage' in window; } catch (e) { return false; } } },
    { name: 'CSS Grid', test: () => { try { return 'grid-template-columns' in document.createElement('div').style; } catch (e) { return false; } } },
    { name: 'Flexbox', test: () => { try { return 'flex' in document.createElement('div').style; } catch (e) { return false; } } }
  ];

  // Get browser info
  function getBrowserInfo() {
    const ua = navigator.userAgent;
    let browserName = 'unknown';
    let fullVersion = '0';
    let majorVersion = 0;
    let nameOffset, verOffset, ix;

    // In Opera
    if ((verOffset = ua.indexOf('Opera')) !== -1) {
      browserName = 'opera';
      fullVersion = ua.substring(verOffset + 6);
      if ((verOffset = ua.indexOf('Version')) !== -1) {
        fullVersion = ua.substring(verOffset + 8);
      }
    }
    // In Opera Next/Edge (Chromium based Edge)
    else if ((verOffset = ua.indexOf('Edg')) !== -1) {
      browserName = 'edge';
      fullVersion = ua.substring(verOffset + 4);
    }
    // In MS old Edge
    else if ((verOffset = ua.indexOf('Edge')) !== -1) {
      browserName = 'edge';
      fullVersion = ua.substring(verOffset + 5);
    }
    // In MSIE
    else if ((verOffset = ua.indexOf('MSIE')) !== -1) {
      browserName = 'ie';
      fullVersion = ua.substring(verOffset + 5);
    }
    // In Chrome
    else if ((verOffset = ua.indexOf('Chrome')) !== -1) {
      browserName = 'chrome';
      fullVersion = ua.substring(verOffset + 7);
    }
    // In Safari
    else if ((verOffset = ua.indexOf('Safari')) !== -1) {
      browserName = 'safari';
      fullVersion = ua.substring(verOffset + 7);
      if ((verOffset = ua.indexOf('Version')) !== -1)
        fullVersion = ua.substring(verOffset + 8);
    }
    // In Firefox
    else if ((verOffset = ua.indexOf('Firefox')) !== -1) {
      browserName = 'firefox';
      fullVersion = ua.substring(verOffset + 8);
    }
    // In most other browsers, 'name/version' is at the end of userAgent
    else if ((nameOffset = ua.lastIndexOf(' ') + 1) < (verOffset = ua.lastIndexOf('/'))) {
      browserName = ua.substring(nameOffset, verOffset);
      fullVersion = ua.substring(verOffset + 1);
      if (browserName.toLowerCase() === browserName.toUpperCase()) {
        browserName = navigator.appName;
      }
    }

    // Trim whitespace and get version number
    fullVersion = fullVersion.trim();
    if ((ix = fullVersion.indexOf(';')) !== -1) {
      fullVersion = fullVersion.substring(0, ix);
    }
    if ((ix = fullVersion.indexOf(' ')) !== -1) {
      fullVersion = fullVersion.substring(0, ix);
    }
    if ((ix = fullVersion.indexOf(')')) !== -1) {
      fullVersion = fullVersion.substring(0, ix);
    }

    // Convert version to integer
    majorVersion = parseInt(fullVersion, 10) || 0;

    return {
      name: browserName,
      version: majorVersion,
      fullVersion: fullVersion,
      userAgent: ua
    };
  }

  // Check browser compatibility
  function checkBrowserCompatibility() {
    const browser = getBrowserInfo();
    const minVersion = MIN_BROWSER_VERSIONS[browser.name.toLowerCase()] || Infinity;
    
    if (browser.version < minVersion) {
      return {
        compatible: false,
        reason: `Your browser (${browser.name} ${browser.fullVersion}) is not supported. Please upgrade to a newer version or try a different browser.`,
        browser: browser
      };
    }
    
    // Check required features
    const missingFeatures = REQUIRED_FEATURES
      .filter(feature => !feature.test())
      .map(feature => feature.name);
    
    if (missingFeatures.length > 0) {
      return {
        compatible: false,
        reason: `Your browser is missing required features: ${missingFeatures.join(', ')}`,
        browser: browser,
        missingFeatures: missingFeatures
      };
    }
    
    return {
      compatible: true,
      browser: browser
    };
  }

  // Display compatibility warning
  function showCompatibilityWarning(result) {
    if (!result.compatible && typeof document !== 'undefined') {
      const warningDiv = document.createElement('div');
      warningDiv.style.position = 'fixed';
      warningDiv.style.top = '0';
      warningDiv.style.left = '0';
      warningDiv.style.right = '0';
      warningDiv.style.backgroundColor = '#f44336';
      warningDiv.style.color = 'white';
      warningDiv.style.padding = '15px';
      warningDiv.style.textAlign = 'center';
      warningDiv.style.zIndex = '9999';
      warningDiv.style.fontFamily = 'Arial, sans-serif';
      
      warningDiv.innerHTML = `
        <p><strong>Browser Compatibility Issue</strong></p>
        <p>${result.reason}</p>
        <p>For the best experience, please use the latest version of Chrome, Firefox, Safari, or Edge.</p>
        <p><button id="browser-check-dismiss" style="background-color: white; color: #f44336; border: none; padding: 5px 10px; cursor: pointer;">Dismiss</button></p>
      `;
      
      document.body.appendChild(warningDiv);
      
      // Add event listener to dismiss button
      document.getElementById('browser-check-dismiss').addEventListener('click', function() {
        warningDiv.style.display = 'none';
        localStorage.setItem('browser-warning-dismissed', 'true');
      });
      
      return warningDiv;
    }
    return null;
  }

  // Check if this is running in a browser environment
  if (typeof window !== 'undefined') {
    window.viewzenixBrowserCheck = {
      check: checkBrowserCompatibility,
      showWarning: showCompatibilityWarning
    };
    
    // Automatically run check if the script is not imported as a module
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function() {
        const dismissed = localStorage.getItem('browser-warning-dismissed') === 'true';
        if (!dismissed) {
          const result = checkBrowserCompatibility();
          showCompatibilityWarning(result);
        }
      });
    } else {
      const dismissed = localStorage.getItem('browser-warning-dismissed') === 'true';
      if (!dismissed) {
        const result = checkBrowserCompatibility();
        showCompatibilityWarning(result);
      }
    }
  }
})(); 