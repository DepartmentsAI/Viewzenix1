#!/usr/bin/env node
/**
 * Frontend Environment Verification Script
 * 
 * This script runs environment verification tests to ensure
 * the frontend environment is properly configured before starting.
 * 
 * Usage:
 *   node verify-environment.js [--silent] [--ci]
 * 
 * Options:
 *   --silent  Only output errors, not diagnostic information
 *   --ci      Exit with non-zero code on failure (for CI/CD pipelines)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// CLI arguments
const args = process.argv.slice(2);
const SILENT_MODE = args.includes('--silent');
const CI_MODE = args.includes('--ci');

// Colors for output
const colors = {
  reset: "\x1b[0m",
  bright: "\x1b[1m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m"
};

// Format output
function log(message, type = 'info') {
  if (SILENT_MODE && type === 'info') return;
  
  switch (type) {
    case 'error':
      console.error(`${colors.red}✘ Error: ${message}${colors.reset}`);
      break;
    case 'warning':
      console.warn(`${colors.yellow}⚠ Warning: ${message}${colors.reset}`);
      break;
    case 'success':
      console.log(`${colors.green}✓ ${message}${colors.reset}`);
      break;
    case 'header':
      console.log(`\n${colors.bright}${message}${colors.reset}`);
      break;
    default:
      console.log(`  ${message}`);
  }
}

// Track verification status
const verificationResults = {
  passed: [],
  failed: [],
  warnings: []
};

// Run verification checks
async function runVerification() {
  try {
    log('FRONTEND ENVIRONMENT VERIFICATION', 'header');
    log(`Running on ${process.platform} (${process.arch})`);
    
    // Check 1: Node.js version
    await verifyNodeVersion();
    
    // Check 2: Essential files exist
    await verifyEssentialFiles();
    
    // Check 3: Configuration
    await verifyConfiguration();
    
    // Check 4: Environment variables
    await verifyEnvironmentVariables();
    
    // Check 5: Package dependencies
    await verifyDependencies();
    
    // Check 6: Run actual tests if available
    await runEnvironmentTests();
    
    // Print summary
    printSummary();
    
    // Exit with appropriate code for CI environments
    if (CI_MODE && verificationResults.failed.length > 0) {
      process.exit(1);
    }
  } catch (error) {
    log(`Unexpected error during verification: ${error.message}`, 'error');
    if (CI_MODE) {
      process.exit(1);
    }
  }
}

// Check 1: Verify Node.js version
async function verifyNodeVersion() {
  log('Checking Node.js version', 'header');
  
  const nodeVersion = process.version;
  log(`Detected Node.js ${nodeVersion}`);
  
  // Parse version (e.g., "v14.17.0" -> 14)
  const majorVersion = parseInt(nodeVersion.substring(1).split('.')[0]);
  
  if (majorVersion < 14) {
    verificationResults.failed.push(`Node.js version ${nodeVersion} is below recommended (>= 14.x)`);
    log(`Node.js version ${nodeVersion} is below recommended (>= 14.x)`, 'error');
  } else {
    verificationResults.passed.push(`Node.js version ${nodeVersion} is compatible`);
    log(`Node.js version is compatible`, 'success');
  }
}

// Check 2: Verify essential files exist
async function verifyEssentialFiles() {
  log('Checking essential files', 'header');
  
  const essentialFiles = [
    { name: 'package.json', path: path.resolve(__dirname, 'package.json') },
    { name: 'PowerShell script', path: path.resolve(__dirname, 'start.ps1') },
    { name: 'Batch script', path: path.resolve(__dirname, 'start.bat') },
    { name: 'Shell script', path: path.resolve(__dirname, 'start.sh') },
    { name: 'Config', path: path.resolve(__dirname, 'config.js') },
    { name: 'Health check', path: path.resolve(__dirname, 'health-check.js') }
  ];
  
  const essentialDirs = [
    { name: 'src', path: path.resolve(__dirname, 'src') },
    { name: 'public', path: path.resolve(__dirname, 'public') }
  ];
  
  // Check files
  for (const file of essentialFiles) {
    if (fs.existsSync(file.path)) {
      verificationResults.passed.push(`${file.name} exists`);
      log(`${file.name} exists`, 'success');
    } else {
      verificationResults.failed.push(`Missing ${file.name}`);
      log(`Missing ${file.name}`, 'error');
    }
  }
  
  // Check directories
  for (const dir of essentialDirs) {
    if (fs.existsSync(dir.path) && fs.statSync(dir.path).isDirectory()) {
      verificationResults.passed.push(`${dir.name} directory exists`);
      log(`${dir.name} directory exists`, 'success');
    } else {
      verificationResults.failed.push(`Missing ${dir.name} directory`);
      log(`Missing ${dir.name} directory`, 'error');
    }
  }
}

// Check 3: Verify configuration
async function verifyConfiguration() {
  log('Checking configuration', 'header');
  
  try {
    // Import config
    const configPath = path.resolve(__dirname, 'config.js');
    if (!fs.existsSync(configPath)) {
      verificationResults.failed.push('config.js not found');
      log('config.js not found', 'error');
      return;
    }
    
    const config = require(configPath);
    
    // Check required properties
    const requiredProps = ['api', 'frontend'];
    const missingProps = [];
    
    for (const prop of requiredProps) {
      if (!config[prop]) {
        missingProps.push(prop);
      }
    }
    
    if (missingProps.length > 0) {
      verificationResults.failed.push(`Configuration missing required properties: ${missingProps.join(', ')}`);
      log(`Configuration missing required properties: ${missingProps.join(', ')}`, 'error');
    } else {
      verificationResults.passed.push('Configuration has required properties');
      log('Configuration has required properties', 'success');
    }
    
    // Check API URL format
    if (config.api && config.api.baseUrl) {
      try {
        new URL(config.api.baseUrl);
        verificationResults.passed.push('API URL is properly formatted');
        log('API URL is properly formatted', 'success');
      } catch (e) {
        verificationResults.warnings.push(`API URL format may be invalid: ${config.api.baseUrl}`);
        log(`API URL format may be invalid: ${config.api.baseUrl}`, 'warning');
      }
    }
    
    // Check port is valid
    if (config.frontend && config.frontend.port) {
      const port = parseInt(config.frontend.port);
      if (isNaN(port) || port <= 0 || port >= 65536) {
        verificationResults.warnings.push(`Frontend port may be invalid: ${config.frontend.port}`);
        log(`Frontend port may be invalid: ${config.frontend.port}`, 'warning');
      } else {
        verificationResults.passed.push('Frontend port is valid');
        log('Frontend port is valid', 'success');
      }
    }
  } catch (error) {
    verificationResults.failed.push(`Error loading configuration: ${error.message}`);
    log(`Error loading configuration: ${error.message}`, 'error');
  }
}

// Check 4: Verify environment variables
async function verifyEnvironmentVariables() {
  log('Checking environment variables', 'header');
  
  // Check if .env file exists
  const envPath = path.resolve(__dirname, '.env');
  if (fs.existsSync(envPath)) {
    verificationResults.passed.push('.env file exists');
    log('.env file exists', 'success');
    
    // Read .env file and check required variables
    const envContent = fs.readFileSync(envPath, 'utf8');
    const requiredVars = ['REACT_APP_API_URL', 'PORT', 'HOST'];
    const foundVars = [];
    
    // Simple parsing - note: this is not a full-featured .env parser
    const envLines = envContent.split('\n');
    envLines.forEach(line => {
      const match = line.match(/^\s*([\w.-]+)\s*=\s*(.*)?\s*$/);
      if (match && requiredVars.includes(match[1])) {
        foundVars.push(match[1]);
      }
    });
    
    const missingVars = requiredVars.filter(v => !foundVars.includes(v));
    if (missingVars.length > 0) {
      verificationResults.warnings.push(`Missing recommended environment variables: ${missingVars.join(', ')}`);
      log(`Missing recommended environment variables: ${missingVars.join(', ')}`, 'warning');
    } else {
      verificationResults.passed.push('All recommended environment variables found in .env');
      log('All recommended environment variables found in .env', 'success');
    }
  } else {
    verificationResults.warnings.push('No .env file found - will use default settings');
    log('No .env file found - will use default settings', 'warning');
  }
}

// Check 5: Verify dependencies
async function verifyDependencies() {
  log('Checking package dependencies', 'header');
  
  const packageJsonPath = path.resolve(__dirname, 'package.json');
  if (!fs.existsSync(packageJsonPath)) {
    return; // Already reported in file check
  }
  
  try {
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    
    // Check for essential dependencies
    const essentialDeps = ['react', 'react-dom', 'react-scripts'];
    const missingDeps = [];
    
    essentialDeps.forEach(dep => {
      if (!packageJson.dependencies || !packageJson.dependencies[dep]) {
        missingDeps.push(dep);
      }
    });
    
    if (missingDeps.length > 0) {
      verificationResults.failed.push(`Missing critical dependencies: ${missingDeps.join(', ')}`);
      log(`Missing critical dependencies: ${missingDeps.join(', ')}`, 'error');
    } else {
      verificationResults.passed.push('All critical dependencies present in package.json');
      log('All critical dependencies present', 'success');
    }
    
    // Check for required scripts
    const requiredScripts = ['start', 'build', 'test'];
    const missingScripts = [];
    
    requiredScripts.forEach(script => {
      if (!packageJson.scripts || !packageJson.scripts[script]) {
        missingScripts.push(script);
      }
    });
    
    if (missingScripts.length > 0) {
      verificationResults.failed.push(`Missing required npm scripts: ${missingScripts.join(', ')}`);
      log(`Missing required npm scripts: ${missingScripts.join(', ')}`, 'error');
    } else {
      verificationResults.passed.push('All required npm scripts present');
      log('All required npm scripts present', 'success');
    }
    
    // Check for environment helper scripts
    const helperScripts = ['health-check', 'start:win', 'start:unix'];
    const missingHelperScripts = [];
    
    helperScripts.forEach(script => {
      if (!packageJson.scripts || !packageJson.scripts[script]) {
        missingHelperScripts.push(script);
      }
    });
    
    if (missingHelperScripts.length > 0) {
      verificationResults.warnings.push(`Missing helper npm scripts: ${missingHelperScripts.join(', ')}`);
      log(`Missing helper npm scripts: ${missingHelperScripts.join(', ')}`, 'warning');
    } else {
      verificationResults.passed.push('All helper npm scripts present');
      log('All helper npm scripts present', 'success');
    }
    
    // Check if node_modules exists
    const nodeModulesPath = path.resolve(__dirname, 'node_modules');
    if (!fs.existsSync(nodeModulesPath)) {
      verificationResults.warnings.push('node_modules directory not found - consider running npm install');
      log('node_modules directory not found - consider running npm install', 'warning');
    } else {
      verificationResults.passed.push('node_modules directory exists');
      log('node_modules directory exists', 'success');
    }
  } catch (error) {
    verificationResults.failed.push(`Error parsing package.json: ${error.message}`);
    log(`Error parsing package.json: ${error.message}`, 'error');
  }
}

// Check 6: Run actual environment tests if available
async function runEnvironmentTests() {
  log('Running environment tests', 'header');
  
  const testFilePath = path.resolve(__dirname, 'tests/environment.test.js');
  
  if (!fs.existsSync(testFilePath)) {
    verificationResults.warnings.push('Environment test file not found - skipping test run');
    log('Environment test file not found - skipping test run', 'warning');
    return;
  }
  
  try {
    // Since we need to run the jest tests, we'll use execSync for simplicity
    // In a real production implementation, this could be improved to use the jest API
    log('Executing environment tests...');
    
    // Set environment variable to skip API tests in CI mode
    const env = {
      ...process.env,
      SKIP_API_TESTS: CI_MODE ? 'true' : 'false'
    };
    
    // Run jest with the environment test file
    // Note: This assumes jest is installed and configured in the project
    const result = execSync(
      `npx jest ${testFilePath} --silent --forceExit`,
      { env, encoding: 'utf8' }
    );
    
    verificationResults.passed.push('Environment tests passed');
    log('Environment tests passed', 'success');
    
    if (!SILENT_MODE) {
      log(result);
    }
  } catch (error) {
    verificationResults.failed.push('Environment tests failed');
    log('Environment tests failed', 'error');
    
    if (!SILENT_MODE && error.stdout) {
      log(error.stdout);
    }
  }
}

// Print summary at the end
function printSummary() {
  log('ENVIRONMENT VERIFICATION SUMMARY', 'header');
  
  log(`Tests passed: ${verificationResults.passed.length}`);
  log(`Tests failed: ${verificationResults.failed.length}`);
  log(`Warnings: ${verificationResults.warnings.length}`);
  
  if (verificationResults.failed.length > 0) {
    log('\nFailed tests:', 'header');
    verificationResults.failed.forEach((failure, index) => {
      log(`${index + 1}. ${failure}`, 'error');
    });
  }
  
  if (verificationResults.warnings.length > 0) {
    log('\nWarnings:', 'header');
    verificationResults.warnings.forEach((warning, index) => {
      log(`${index + 1}. ${warning}`, 'warning');
    });
  }
  
  log('\nOverall status:', 'header');
  if (verificationResults.failed.length === 0) {
    if (verificationResults.warnings.length === 0) {
      log('Environment is fully ready for frontend development!', 'success');
    } else {
      log('Environment is ready, but has some warnings that should be addressed', 'warning');
    }
  } else {
    log('Environment has issues that need to be resolved before running the application', 'error');
  }
}

// Run verification
runVerification(); 