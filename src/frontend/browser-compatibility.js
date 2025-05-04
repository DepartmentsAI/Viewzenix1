/**
 * Browser Compatibility Check
 * 
 * This script checks if the current browser environment has the required features
 * to run the Viewzenix1 trading platform properly.
 */

// Main compatibility check function to be called on application startup
function checkBrowserCompatibility() {
  const results = {};
  let allPassed = true;
  
  // Check for essential browser features
  results.localStorage = checkLocalStorage();
  results.sessionStorage = checkSessionStorage();
  results.fetch = checkFetchAPI();
  results.promises = checkPromises();
  results.async = checkAsyncAwait();
  results.cors = checkCORS();
  results.flexbox = checkFlexbox();
  results.grid = checkGrid();
  
  // Check if any tests failed
  for (const test in results) {
    if (!results[test].supported) {
      allPassed = false;
      break;
    }
  }
  
  // Return overall results
  return {
    compatible: allPassed,
    details: results,
    browserInfo: getBrowserInfo()
  };
}

// Helper function to get browser information
function getBrowserInfo() {
  const ua = navigator.userAgent;
  let browserName = "Unknown";
  let browserVersion = "Unknown";
  
  // Detect browser name and version
  if (ua.indexOf("Firefox") > -1) {
    browserName = "Firefox";
    browserVersion = ua.match(/Firefox\/([\d.]+)/)[1];
  } else if (ua.indexOf("SamsungBrowser") > -1) {
    browserName = "Samsung Browser";
    browserVersion = ua.match(/SamsungBrowser\/([\d.]+)/)[1];
  } else if (ua.indexOf("Opera") > -1 || ua.indexOf("OPR") > -1) {
    browserName = "Opera";
    browserVersion = ua.indexOf("Opera") > -1 ? 
      ua.match(/Opera\/([\d.]+)/) ? ua.match(/Opera\/([\d.]+)/)[1] : ua.match(/Opera ([\d.]+)/)[1] :
      ua.match(/OPR\/([\d.]+)/)[1];
  } else if (ua.indexOf("Edge") > -1) {
    browserName = "Edge";
    browserVersion = ua.match(/Edge\/([\d.]+)/)[1];
  } else if (ua.indexOf("Edg") > -1) {
    browserName = "Edge Chromium";
    browserVersion = ua.match(/Edg\/([\d.]+)/)[1];
  } else if (ua.indexOf("Chrome") > -1) {
    browserName = "Chrome";
    browserVersion = ua.match(/Chrome\/([\d.]+)/)[1];
  } else if (ua.indexOf("Safari") > -1) {
    browserName = "Safari";
    browserVersion = ua.match(/Version\/([\d.]+)/)[1];
  } else if (ua.indexOf("MSIE") > -1 || ua.indexOf("Trident") > -1) {
    browserName = "Internet Explorer";
    browserVersion = ua.indexOf("MSIE") > -1 ? 
      ua.match(/MSIE ([\d.]+)/)[1] : 
      ua.match(/rv:([\d.]+)/)[1];
  }
  
  return {
    name: browserName,
    version: browserVersion,
    userAgent: ua,
    platform: navigator.platform,
    language: navigator.language
  };
}

// Individual feature checks
function checkLocalStorage() {
  try {
    const test = 'test';
    localStorage.setItem(test, test);
    localStorage.removeItem(test);
    return { supported: true };
  } catch (e) {
    return { 
      supported: false, 
      reason: 'Local Storage is not available. This may be due to private browsing mode or browser settings.'
    };
  }
}

function checkSessionStorage() {
  try {
    const test = 'test';
    sessionStorage.setItem(test, test);
    sessionStorage.removeItem(test);
    return { supported: true };
  } catch (e) {
    return { 
      supported: false, 
      reason: 'Session Storage is not available. This may be due to private browsing mode or browser settings.'
    };
  }
}

function checkFetchAPI() {
  if (window.fetch) {
    return { supported: true };
  }
  return { 
    supported: false, 
    reason: 'Fetch API is not supported in this browser. Please use a modern browser.'
  };
}

function checkPromises() {
  if (window.Promise) {
    return { supported: true };
  }
  return { 
    supported: false, 
    reason: 'Promises are not supported in this browser. Please use a modern browser.'
  };
}

function checkAsyncAwait() {
  try {
    eval("async function test() {}");
    return { supported: true };
  } catch (e) {
    return { 
      supported: false, 
      reason: 'Async/Await is not supported in this browser. Please use a modern browser.'
    };
  }
}

function checkCORS() {
  return { 
    supported: 'XMLHttpRequest' in window && 'withCredentials' in new XMLHttpRequest() 
  };
}

function checkFlexbox() {
  const div = document.createElement('div');
  div.style.display = 'flex';
  return { 
    supported: div.style.display === 'flex' 
  };
}

function checkGrid() {
  const div = document.createElement('div');
  div.style.display = 'grid';
  return { 
    supported: div.style.display === 'grid' 
  };
}

// Function to display compatibility warnings to the user
function showCompatibilityWarnings(results) {
  if (!results.compatible) {
    // Create warning container
    const warningContainer = document.createElement('div');
    warningContainer.style.position = 'fixed';
    warningContainer.style.top = '0';
    warningContainer.style.left = '0';
    warningContainer.style.right = '0';
    warningContainer.style.backgroundColor = '#ff9800';
    warningContainer.style.color = 'black';
    warningContainer.style.padding = '10px';
    warningContainer.style.zIndex = '9999';
    warningContainer.style.textAlign = 'center';
    
    // Add warning text
    const warningText = document.createElement('p');
    warningText.textContent = 'Your browser may not fully support this application. For the best experience, please use a modern browser like Chrome, Firefox, Safari, or Edge.';
    warningContainer.appendChild(warningText);
    
    // Add details of what's not supported
    const detailsList = document.createElement('ul');
    detailsList.style.textAlign = 'left';
    detailsList.style.display = 'inline-block';
    detailsList.style.margin = '10px auto';
    
    for (const test in results.details) {
      if (!results.details[test].supported) {
        const detail = document.createElement('li');
        detail.textContent = results.details[test].reason || `${test} is not supported`;
        detailsList.appendChild(detail);
      }
    }
    
    // Only add the list if there are issues to report
    if (detailsList.children.length > 0) {
      warningContainer.appendChild(detailsList);
    }
    
    // Add close button
    const closeButton = document.createElement('button');
    closeButton.textContent = 'Dismiss';
    closeButton.style.margin = '10px';
    closeButton.style.padding = '5px 10px';
    closeButton.style.cursor = 'pointer';
    closeButton.onclick = function() {
      document.body.removeChild(warningContainer);
    };
    warningContainer.appendChild(closeButton);
    
    // Add to body when DOM is ready
    if (document.body) {
      document.body.appendChild(warningContainer);
    } else {
      window.addEventListener('DOMContentLoaded', function() {
        document.body.appendChild(warningContainer);
      });
    }
  }
}

// Export for usage in application
export { checkBrowserCompatibility, showCompatibilityWarnings }; 