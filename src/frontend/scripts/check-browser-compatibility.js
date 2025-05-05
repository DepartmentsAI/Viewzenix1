#!/usr/bin/env node
/**
 * Browser Compatibility Checker - CLI Tool
 * 
 * This CLI tool allows checking browser compatibility based on a user agent string.
 * Useful for CI/CD environments and server-side validation.
 * 
 * Usage:
 *   node check-browser-compatibility.js [--user-agent "USER_AGENT_STRING"]
 *   node check-browser-compatibility.js --list-supported
 *   node check-browser-compatibility.js --check-common
 */

// Setup mock browser environment for non-browser testing
global.navigator = { userAgent: '' };
global.window = {};
global.document = {
  cookie: '',
  createElement: () => ({ textContent: '' }),
  head: { appendChild: () => {} },
  querySelector: () => null
};

// Import compatibility checker
const path = require('path');
const fs = require('fs');

// Parse command line arguments
const args = process.argv.slice(2);
const options = {
  userAgent: null,
  listSupported: false,
  checkCommon: false,
  json: false,
  verbose: false
};

// Parse arguments
for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  
  if (arg === '--user-agent' && i + 1 < args.length) {
    options.userAgent = args[++i];
  } else if (arg === '--list-supported') {
    options.listSupported = true;
  } else if (arg === '--check-common') {
    options.checkCommon = true;
  } else if (arg === '--json') {
    options.json = true;
  } else if (arg === '--verbose') {
    options.verbose = true;
  } else if (arg === '--help') {
    showHelp();
    process.exit(0);
  }
}

// Try to load the compatibility checker
let compatibilityChecker;
try {
  // Try to require directly
  compatibilityChecker = require('../browser-compatibility-check');
} catch (e) {
  try {
    // Try to find it in the parent directory
    const checkerPath = path.resolve(__dirname, '../browser-compatibility-check.js');
    
    // If file exists, load it
    if (fs.existsSync(checkerPath)) {
      compatibilityChecker = require(checkerPath);
    } else {
      console.error('Error: Could not find browser-compatibility-check.js');
      console.error('Please run this script from the frontend directory or its scripts subdirectory.');
      process.exit(1);
    }
  } catch (e) {
    console.error('Error loading browser-compatibility-check.js:', e.message);
    process.exit(1);
  }
}

// Destructure the compatibility checker functions and constants
const {
  MIN_BROWSER_VERSIONS,
  REQUIRED_FEATURES,
  detectBrowser,
  checkBrowserVersion
} = compatibilityChecker;

/**
 * Display help information
 */
function showHelp() {
  console.log(`
Browser Compatibility Checker - CLI Tool

Usage:
  node check-browser-compatibility.js [OPTIONS]

Options:
  --user-agent "STRING"  Check compatibility for specific user agent
  --list-supported       List all supported browsers and versions
  --check-common         Check compatibility for common browsers
  --json                 Output results in JSON format
  --verbose              Show detailed information
  --help                 Show this help message

Examples:
  node check-browser-compatibility.js --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
  node check-browser-compatibility.js --list-supported
  node check-browser-compatibility.js --check-common --json
  `);
}

/**
 * Check compatibility for a specific user agent
 */
function checkUserAgentCompatibility(userAgent) {
  // Override navigator.userAgent
  navigator.userAgent = userAgent;
  
  // Check browser version
  const versionCheck = checkBrowserVersion();
  
  // Print results
  if (options.json) {
    console.log(JSON.stringify(versionCheck, null, 2));
  } else {
    console.log(`User Agent: ${userAgent}`);
    console.log(`Browser: ${versionCheck.browser.name} ${versionCheck.browser.version}`);
    console.log(`Supported: ${versionCheck.supported ? 'Yes ✅' : 'No ❌'}`);
    
    if (!versionCheck.supported) {
      console.log(`Reason: ${versionCheck.reason}`);
      
      // If it's a known browser that's just too old, show the minimum version
      if (MIN_BROWSER_VERSIONS[versionCheck.browser.name]) {
        console.log(`Minimum required version: ${MIN_BROWSER_VERSIONS[versionCheck.browser.name]}`);
      }
    }
    
    if (options.verbose) {
      console.log('\nBrowser Details:');
      console.log(JSON.stringify(versionCheck.browser, null, 2));
    }
  }
  
  // Return true if supported, false otherwise
  return versionCheck.supported;
}

/**
 * List all supported browsers and versions
 */
function listSupportedBrowsers() {
  console.log('Supported Browsers and Minimum Versions:');
  console.log('======================================');
  
  for (const [browser, version] of Object.entries(MIN_BROWSER_VERSIONS)) {
    if (version === false) {
      console.log(`${browser}: Not supported`);
    } else {
      console.log(`${browser}: ${version}+`);
    }
  }
  
  console.log('\nRequired Features:');
  console.log('=================');
  REQUIRED_FEATURES.forEach(feature => {
    console.log(`- ${feature.name}`);
  });
}

/**
 * Check compatibility for common browsers
 */
function checkCommonBrowsers() {
  const commonBrowsers = [
    {
      name: 'Chrome (Latest)',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    },
    {
      name: 'Firefox (Latest)',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    },
    {
      name: 'Safari (Latest)',
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
    },
    {
      name: 'Edge (Latest)',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
    },
    {
      name: 'Chrome (Old)',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36'
    },
    {
      name: 'Internet Explorer 11',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'
    },
    {
      name: 'Safari (Old)',
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2 Safari/605.1.15'
    }
  ];
  
  const results = [];
  
  // Print header
  if (!options.json) {
    console.log('Compatibility Check for Common Browsers:');
    console.log('=======================================');
  }
  
  // Check each browser
  commonBrowsers.forEach(browser => {
    // Override navigator.userAgent
    navigator.userAgent = browser.userAgent;
    
    // Check browser version
    const versionCheck = checkBrowserVersion();
    
    // Add to results
    results.push({
      name: browser.name,
      detected: `${versionCheck.browser.name} ${versionCheck.browser.version}`,
      supported: versionCheck.supported,
      reason: versionCheck.reason
    });
    
    // Print result if not in JSON mode
    if (!options.json) {
      console.log(`\n${browser.name}:`);
      console.log(`  Detected as: ${versionCheck.browser.name} ${versionCheck.browser.version}`);
      console.log(`  Supported: ${versionCheck.supported ? 'Yes ✅' : 'No ❌'}`);
      
      if (!versionCheck.supported) {
        console.log(`  Reason: ${versionCheck.reason}`);
      }
    }
  });
  
  // Print JSON results if requested
  if (options.json) {
    console.log(JSON.stringify(results, null, 2));
  }
  
  // Return true if all supported, false otherwise
  return results.every(r => r.supported);
}

// Main execution
if (options.listSupported) {
  listSupportedBrowsers();
} else if (options.checkCommon) {
  const allSupported = checkCommonBrowsers();
  
  // Exit with appropriate code
  process.exit(allSupported ? 0 : 1);
} else if (options.userAgent) {
  const isSupported = checkUserAgentCompatibility(options.userAgent);
  
  // Exit with appropriate code
  process.exit(isSupported ? 0 : 1);
} else {
  console.error('Error: No option specified.');
  console.error('Use --help to see available options.');
  process.exit(1);
} 