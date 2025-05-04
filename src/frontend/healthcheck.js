/**
 * Frontend Health Check
 * 
 * This script performs a health check on the frontend application and its dependencies.
 * It verifies that the application can start, connect to APIs, and function properly.
 * 
 * Usage: node healthcheck.js
 */

const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration
const DEFAULT_PORT = process.env.PORT || 3000;
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api/v1';
const HEALTH_CHECK_TIMEOUT = 5000; // 5 seconds

// Status codes
const STATUS = {
  SUCCESS: 'SUCCESS',
  WARNING: 'WARNING',
  ERROR: 'ERROR'
};

// ANSI color codes for terminal output
const COLORS = {
  RESET: '\x1b[0m',
  GREEN: '\x1b[32m',
  YELLOW: '\x1b[33m',
  RED: '\x1b[31m',
  BLUE: '\x1b[34m',
  GRAY: '\x1b[90m'
};

// Format console output with colors
const log = {
  info: (message) => console.log(`${COLORS.BLUE}[INFO]${COLORS.RESET} ${message}`),
  success: (message) => console.log(`${COLORS.GREEN}[SUCCESS]${COLORS.RESET} ${message}`),
  warning: (message) => console.log(`${COLORS.YELLOW}[WARNING]${COLORS.RESET} ${message}`),
  error: (message) => console.log(`${COLORS.RED}[ERROR]${COLORS.RESET} ${message}`),
  step: (message) => console.log(`${COLORS.GRAY}[STEP]${COLORS.RESET} ${message}`)
};

// Check if a specific port is in use
async function isPortInUse(port) {
  return new Promise((resolve) => {
    const server = http.createServer();
    
    server.once('error', (err) => {
      if (err.code === 'EADDRINUSE') {
        resolve(true);
      } else {
        resolve(false);
      }
    });
    
    server.once('listening', () => {
      server.close();
      resolve(false);
    });
    
    server.listen(port);
  });
}

// Make an HTTP request to check endpoint availability
function checkEndpoint(url) {
  return new Promise((resolve) => {
    const protocol = url.startsWith('https') ? https : http;
    
    const req = protocol.get(url, { timeout: HEALTH_CHECK_TIMEOUT }, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        resolve({
          status: res.statusCode < 400 ? STATUS.SUCCESS : STATUS.ERROR,
          statusCode: res.statusCode,
          data: data
        });
      });
    });
    
    req.on('error', (error) => {
      resolve({
        status: STATUS.ERROR,
        error: error.message
      });
    });
    
    req.on('timeout', () => {
      req.abort();
      resolve({
        status: STATUS.ERROR,
        error: 'Request timed out'
      });
    });
  });
}

// Check if required dependencies are installed
function checkDependencies() {
  log.step('Checking Node.js dependencies...');
  
  try {
    const packageJson = JSON.parse(fs.readFileSync(path.join(__dirname, 'package.json'), 'utf8'));
    const dependencies = { ...packageJson.dependencies, ...packageJson.devDependencies };
    
    const missingDeps = [];
    
    for (const [dep, version] of Object.entries(dependencies)) {
      try {
        const depPath = path.join(__dirname, 'node_modules', dep);
        if (!fs.existsSync(depPath)) {
          missingDeps.push(dep);
        }
      } catch (err) {
        missingDeps.push(dep);
      }
    }
    
    if (missingDeps.length > 0) {
      log.warning(`Missing dependencies: ${missingDeps.join(', ')}`);
      log.info('Run "npm install" to install missing dependencies');
      return { status: STATUS.WARNING, missingDeps };
    }
    
    log.success('All dependencies are installed');
    return { status: STATUS.SUCCESS };
  } catch (error) {
    log.error(`Failed to check dependencies: ${error.message}`);
    return { status: STATUS.ERROR, error: error.message };
  }
}

// Check if the application can build successfully
function checkBuild() {
  log.step('Checking build configuration...');
  
  try {
    // Just validate the build script without actually building
    execSync('npm run build --dry-run', { stdio: 'pipe' });
    log.success('Build configuration is valid');
    return { status: STATUS.SUCCESS };
  } catch (error) {
    log.error(`Build configuration is invalid: ${error.message}`);
    return { status: STATUS.ERROR, error: error.message };
  }
}

// Check if the backend API is accessible
async function checkApi() {
  log.step(`Checking API connectivity to ${API_URL}...`);
  
  try {
    // Try to reach the health endpoint first, fall back to root if not available
    const healthEndpoint = `${API_URL}/health`;
    const result = await checkEndpoint(healthEndpoint);
    
    if (result.status === STATUS.SUCCESS) {
      log.success(`API is accessible (${result.statusCode})`);
      return { status: STATUS.SUCCESS };
    } else {
      // Try the root API endpoint
      const rootResult = await checkEndpoint(API_URL);
      
      if (rootResult.status === STATUS.SUCCESS) {
        log.success(`API is accessible (${rootResult.statusCode})`);
        return { status: STATUS.SUCCESS };
      } else {
        log.error(`API is not accessible: ${result.error || rootResult.error || 'Unknown error'}`);
        return { status: STATUS.ERROR, error: result.error || rootResult.error || 'Unknown error' };
      }
    }
  } catch (error) {
    log.error(`Failed to check API: ${error.message}`);
    return { status: STATUS.ERROR, error: error.message };
  }
}

// Main health check function
async function runHealthCheck() {
  log.info('Starting frontend health check...');
  
  const results = {
    dependencies: checkDependencies(),
    build: checkBuild(),
    port: null,
    api: null,
    overall: STATUS.SUCCESS
  };
  
  // Check if development port is available
  log.step(`Checking if port ${DEFAULT_PORT} is available...`);
  const portInUse = await isPortInUse(DEFAULT_PORT);
  
  if (portInUse) {
    log.warning(`Port ${DEFAULT_PORT} is already in use`);
    results.port = { status: STATUS.WARNING, message: `Port ${DEFAULT_PORT} is already in use` };
  } else {
    log.success(`Port ${DEFAULT_PORT} is available`);
    results.port = { status: STATUS.SUCCESS };
  }
  
  // Check API connectivity
  results.api = await checkApi();
  
  // Determine overall status
  if (results.dependencies.status === STATUS.ERROR || 
      results.build.status === STATUS.ERROR || 
      results.api.status === STATUS.ERROR) {
    results.overall = STATUS.ERROR;
  } else if (results.dependencies.status === STATUS.WARNING || 
             results.port.status === STATUS.WARNING) {
    results.overall = STATUS.WARNING;
  }
  
  // Output summary
  console.log('\n--- Health Check Summary ---');
  console.log(`Dependencies: ${colorizeStatus(results.dependencies.status)}`);
  console.log(`Build Config: ${colorizeStatus(results.build.status)}`);
  console.log(`Port Status: ${colorizeStatus(results.port.status)}`);
  console.log(`API Access: ${colorizeStatus(results.api.status)}`);
  console.log(`---------------------------`);
  console.log(`Overall Status: ${colorizeStatus(results.overall)}`);
  
  if (results.overall === STATUS.SUCCESS) {
    log.success('Frontend application is healthy and ready to run');
    process.exit(0);
  } else if (results.overall === STATUS.WARNING) {
    log.warning('Frontend application has warnings but should run with limitations');
    process.exit(0);
  } else {
    log.error('Frontend application has critical issues and may not run correctly');
    process.exit(1);
  }
}

// Helper to colorize status text
function colorizeStatus(status) {
  switch (status) {
    case STATUS.SUCCESS:
      return `${COLORS.GREEN}${status}${COLORS.RESET}`;
    case STATUS.WARNING:
      return `${COLORS.YELLOW}${status}${COLORS.RESET}`;
    case STATUS.ERROR:
      return `${COLORS.RED}${status}${COLORS.RESET}`;
    default:
      return status;
  }
}

// Run the health check
runHealthCheck(); 