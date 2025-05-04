/**
 * Frontend Health Check Script
 * 
 * This script can be used to verify that the frontend application is running correctly.
 * It checks if the server is accessible at the defined port and that the React app 
 * has been properly loaded.
 */

const http = require('http');
const https = require('https');

// Configuration
const config = {
  protocol: process.env.PROTOCOL || 'http',
  host: process.env.HOST || 'localhost',
  port: process.env.PORT || 3000,
  path: process.env.HEALTH_CHECK_PATH || '/',
  timeout: parseInt(process.env.HEALTH_CHECK_TIMEOUT) || 5000,
  expectedStatus: parseInt(process.env.EXPECTED_STATUS) || 200,
  verbose: process.env.VERBOSE === 'true'
};

// Log function that respects verbose setting
function log(message) {
  if (config.verbose) {
    console.log(`[Health Check] ${message}`);
  }
}

log('Starting health check...');
log(`Checking ${config.protocol}://${config.host}:${config.port}${config.path}`);

// Choose the appropriate protocol module
const client = config.protocol === 'https' ? https : http;

// Define request options
const options = {
  host: config.host,
  port: config.port,
  path: config.path,
  timeout: config.timeout,
  method: 'GET',
  headers: {
    'User-Agent': 'Frontend-Health-Check/1.0'
  }
};

// Perform the request
const req = client.request(options, (res) => {
  log(`Status: ${res.statusCode}`);
  
  // Check if status code is the expected one
  if (res.statusCode === config.expectedStatus) {
    let data = '';
    
    res.on('data', (chunk) => {
      data += chunk;
    });
    
    res.on('end', () => {
      // Basic check to verify it's the React app by looking for root div or react signature
      if (data.includes('<div id="root">') || data.includes('react')) {
        log('Health check passed: React app verified');
        process.exit(0);
      } else {
        log('Health check failed: Received response but React app signature not found');
        process.exit(1);
      }
    });
  } else {
    log(`Health check failed: Unexpected status code ${res.statusCode}`);
    process.exit(1);
  }
});

req.on('error', (error) => {
  log(`Health check failed: ${error.message}`);
  process.exit(1);
});

req.on('timeout', () => {
  log(`Health check failed: Request timed out after ${config.timeout}ms`);
  req.destroy();
  process.exit(1);
});

req.end(); 