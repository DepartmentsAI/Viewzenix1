#!/usr/bin/env node
/**
 * Viewzenix1 Frontend Health Check Utility
 * 
 * This tool checks for common issues with frontend environment setup
 * and provides recommendations to fix problems.
 */

const fs = require('fs');
const http = require('http');
const path = require('path');
const { exec } = require('child_process');
const os = require('os');

// Define colors for console output
const colors = {
  reset: "\x1b[0m",
  bright: "\x1b[1m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  magenta: "\x1b[35m",
  cyan: "\x1b[36m"
};

// Print header
console.log(`${colors.bright}====== Viewzenix1 Frontend Health Check ======${colors.reset}`);
console.log(`Running on: ${os.type()} ${os.release()} (${os.platform()}, ${os.arch()})\n`);

// Track issues to provide summary at the end
const issues = [];
const warnings = [];
const passes = [];

// Check if running as admin/root (Windows: Administrators, macOS/Linux: root)
function checkAdminRights() {
  return new Promise((resolve) => {
    if (os.platform() === 'win32') {
      exec('net session', (error) => {
        if (error) {
          warnings.push("Not running with Administrator privileges");
          console.log(`${colors.yellow}⚠ Not running as Administrator${colors.reset}`);
          console.log(`  Some checks might be limited without admin rights`);
        } else {
          console.log(`${colors.green}✓ Running as Administrator${colors.reset}`);
        }
        resolve();
      });
    } else {
      exec('id -u', (error, stdout) => {
        if (error || parseInt(stdout.trim()) !== 0) {
          warnings.push("Not running with root privileges");
          console.log(`${colors.yellow}⚠ Not running as root${colors.reset}`);
          console.log(`  Some checks might be limited without root rights`);
        } else {
          console.log(`${colors.green}✓ Running as root${colors.reset}`);
        }
        resolve();
      });
    }
  });
}

// Check if Node.js is installed and version is compatible
function checkNodeVersion() {
  return new Promise((resolve) => {
    const nodeVersion = process.version;
    console.log(`${colors.green}✓ Node.js detected: ${nodeVersion}${colors.reset}`);
    
    // Parse version (e.g., "v14.17.0" -> 14)
    const majorVersion = parseInt(nodeVersion.substring(1).split('.')[0]);
    
    if (majorVersion < 14) {
      issues.push(`Node.js version is ${nodeVersion}, but >= 14.x is recommended`);
      console.log(`${colors.red}✗ Node.js version ${nodeVersion} is below recommended (>= 14.x)${colors.reset}`);
    } else {
      passes.push(`Node.js version is compatible: ${nodeVersion}`);
    }
    
    resolve();
  });
}

// Check if package.json exists and is valid
function checkPackageJson() {
  return new Promise((resolve) => {
    const packageJsonPath = path.join(process.cwd(), 'package.json');
    
    if (!fs.existsSync(packageJsonPath)) {
      issues.push("package.json not found - are you in the correct directory?");
      console.log(`${colors.red}✗ package.json not found${colors.reset}`);
      console.log(`  Make sure you're running this script from the frontend directory`);
      return resolve();
    }
    
    try {
      const packageJson = require(packageJsonPath);
      console.log(`${colors.green}✓ package.json found: ${packageJson.name} v${packageJson.version}${colors.reset}`);
      
      // Check for critical dependencies
      const criticalDeps = ['react', 'react-dom', 'react-scripts'];
      const missingDeps = criticalDeps.filter(dep => !packageJson.dependencies || !packageJson.dependencies[dep]);
      
      if (missingDeps.length > 0) {
        issues.push(`Missing critical dependencies: ${missingDeps.join(', ')}`);
        console.log(`${colors.red}✗ Missing critical dependencies: ${missingDeps.join(', ')}${colors.reset}`);
      } else {
        passes.push("All critical dependencies present in package.json");
      }
      
      // Check for start script
      if (!packageJson.scripts || !packageJson.scripts.start) {
        issues.push("No 'start' script found in package.json");
        console.log(`${colors.red}✗ No 'start' script found in package.json${colors.reset}`);
      } else {
        passes.push("Start script found in package.json");
      }
    } catch (error) {
      issues.push("Invalid package.json: " + error.message);
      console.log(`${colors.red}✗ Invalid package.json: ${error.message}${colors.reset}`);
    }
    
    resolve();
  });
}

// Check if node_modules exists and has core dependencies installed
function checkNodeModules() {
  return new Promise((resolve) => {
    const nodeModulesPath = path.join(process.cwd(), 'node_modules');
    
    if (!fs.existsSync(nodeModulesPath)) {
      issues.push("node_modules directory not found - run 'npm install'");
      console.log(`${colors.red}✗ node_modules directory not found${colors.reset}`);
      console.log(`  Run 'npm install' to install dependencies`);
      return resolve();
    }
    
    console.log(`${colors.green}✓ node_modules directory found${colors.reset}`);
    
    // Check for critical packages
    const criticalPackages = ['react', 'react-dom', 'react-scripts'];
    const missingPackages = [];
    
    for (const pkg of criticalPackages) {
      const pkgPath = path.join(nodeModulesPath, pkg);
      if (!fs.existsSync(pkgPath)) {
        missingPackages.push(pkg);
      }
    }
    
    if (missingPackages.length > 0) {
      issues.push(`Critical packages missing from node_modules: ${missingPackages.join(', ')}`);
      console.log(`${colors.red}✗ Critical packages missing: ${missingPackages.join(', ')}${colors.reset}`);
      console.log(`  Run 'npm install' to fix this issue`);
    } else {
      passes.push("All critical packages installed in node_modules");
    }
    
    resolve();
  });
}

// Check if .env file exists
function checkEnvFile() {
  return new Promise((resolve) => {
    const envPath = path.join(process.cwd(), '.env');
    
    if (!fs.existsSync(envPath)) {
      warnings.push("No .env file found - will use default settings");
      console.log(`${colors.yellow}⚠ No .env file found${colors.reset}`);
      console.log(`  Default settings will be used, or create a .env file with custom settings`);
      return resolve();
    }
    
    console.log(`${colors.green}✓ .env file found${colors.reset}`);
    
    // Read .env file and check required variables
    const envContent = fs.readFileSync(envPath, 'utf8');
    const envLines = envContent.split('\n');
    const envVars = {};
    
    envLines.forEach(line => {
      const match = line.match(/^\s*([\w.-]+)\s*=\s*(.*)?\s*$/);
      if (match) {
        envVars[match[1]] = match[2] || '';
      }
    });
    
    // Check for specific environment variables
    const requiredVars = ['PORT', 'HOST', 'REACT_APP_API_URL'];
    const missingVars = requiredVars.filter(v => !envVars[v]);
    
    if (missingVars.length > 0) {
      warnings.push(`Missing recommended environment variables: ${missingVars.join(', ')}`);
      console.log(`${colors.yellow}⚠ Missing recommended environment variables: ${missingVars.join(', ')}${colors.reset}`);
    } else {
      passes.push("All recommended environment variables found in .env");
    }
    
    resolve();
  });
}

// Check if port 3000 (or the port specified in .env) is already in use
function checkPortAvailability() {
  return new Promise((resolve) => {
    let port = 3000;
    
    // Check if port is specified in .env
    try {
      const envPath = path.join(process.cwd(), '.env');
      if (fs.existsSync(envPath)) {
        const envContent = fs.readFileSync(envPath, 'utf8');
        const portMatch = envContent.match(/^\s*PORT\s*=\s*(\d+)/m);
        if (portMatch) {
          port = parseInt(portMatch[1], 10);
        }
      }
    } catch (error) {
      // Ignore error, use default port 3000
    }
    
    const server = http.createServer();
    
    server.once('error', (err) => {
      if (err.code === 'EADDRINUSE') {
        issues.push(`Port ${port} is already in use`);
        console.log(`${colors.red}✗ Port ${port} is already in use${colors.reset}`);
        console.log(`  Change the PORT in .env or stop the process using port ${port}`);
      } else {
        issues.push(`Port check error: ${err.message}`);
        console.log(`${colors.red}✗ Error checking port ${port}: ${err.message}${colors.reset}`);
      }
      resolve();
    });
    
    server.once('listening', () => {
      server.close();
      passes.push(`Port ${port} is available`);
      console.log(`${colors.green}✓ Port ${port} is available${colors.reset}`);
      resolve();
    });
    
    server.listen(port);
  });
}

// Check if webpack config has been ejected or modified
function checkWebpackConfig() {
  return new Promise((resolve) => {
    const ejectedConfigPath = path.join(process.cwd(), 'config', 'webpack.config.js');
    
    if (fs.existsSync(ejectedConfigPath)) {
      warnings.push("Ejected React configuration detected");
      console.log(`${colors.yellow}⚠ Ejected React configuration detected${colors.reset}`);
      console.log(`  Custom webpack configuration might affect application startup`);
    } else {
      passes.push("Using standard React Scripts configuration");
    }
    
    resolve();
  });
}

// Check if the backend API is reachable
function checkBackendApiReachability() {
  return new Promise((resolve) => {
    let apiUrl = 'http://localhost:5000/api';
    
    // Check if API URL is specified in .env
    try {
      const envPath = path.join(process.cwd(), '.env');
      if (fs.existsSync(envPath)) {
        const envContent = fs.readFileSync(envPath, 'utf8');
        const apiMatch = envContent.match(/^\s*REACT_APP_API_URL\s*=\s*(.+)/m);
        if (apiMatch) {
          apiUrl = apiMatch[1].trim();
        }
      }
    } catch (error) {
      // Ignore error, use default API URL
    }
    
    // Try to extract just the base URL
    let apiBaseUrl;
    try {
      const url = new URL(apiUrl);
      apiBaseUrl = `${url.protocol}//${url.host}`;
    } catch (error) {
      apiBaseUrl = apiUrl;
    }
    
    console.log(`Checking API reachability: ${apiBaseUrl}`);
    
    // Sending a simple request to check if the server is running
    const request = http.get(apiBaseUrl, (response) => {
      if (response.statusCode >= 200 && response.statusCode < 500) {
        passes.push(`Backend API is reachable: ${apiBaseUrl}`);
        console.log(`${colors.green}✓ Backend API is reachable: ${apiBaseUrl}${colors.reset}`);
      } else {
        warnings.push(`Backend API returned status code ${response.statusCode}`);
        console.log(`${colors.yellow}⚠ Backend API returned status code ${response.statusCode}${colors.reset}`);
      }
      resolve();
    });
    
    request.on('error', (err) => {
      issues.push(`Cannot reach backend API: ${err.message}`);
      console.log(`${colors.red}✗ Cannot reach backend API: ${err.message}${colors.reset}`);
      console.log(`  Make sure the backend server is running and accessible at ${apiBaseUrl}`);
      resolve();
    });
    
    request.setTimeout(5000, () => {
      request.destroy();
      issues.push(`Backend API connection timed out`);
      console.log(`${colors.red}✗ Backend API connection timed out${colors.reset}`);
      console.log(`  Make sure the backend server is running and accessible at ${apiBaseUrl}`);
      resolve();
    });
  });
}

// Check disk space
function checkDiskSpace() {
  return new Promise((resolve) => {
    const platform = os.platform();
    let command;
    
    if (platform === 'win32') {
      command = 'wmic logicaldisk get freespace,size,caption';
    } else if (platform === 'darwin' || platform === 'linux') {
      command = 'df -h .';
    } else {
      warnings.push(`Cannot check disk space on ${platform}`);
      console.log(`${colors.yellow}⚠ Cannot check disk space on ${platform}${colors.reset}`);
      return resolve();
    }
    
    exec(command, (error, stdout) => {
      if (error) {
        warnings.push("Could not check disk space");
        console.log(`${colors.yellow}⚠ Could not check disk space: ${error.message}${colors.reset}`);
      } else {
        console.log(`${colors.green}✓ Disk space check${colors.reset}`);
        console.log(`  ${stdout.trim().split('\n')[0]}`);
        console.log(`  ${stdout.trim().split('\n')[1]}`);
      }
      resolve();
    });
  });
}

// Check for browser compatibility issues
function checkBrowserCompatibility() {
  return new Promise((resolve) => {
    const packageJsonPath = path.join(process.cwd(), 'package.json');
    
    if (!fs.existsSync(packageJsonPath)) {
      return resolve();
    }
    
    try {
      const packageJson = require(packageJsonPath);
      if (packageJson.browserslist) {
        console.log(`${colors.green}✓ Browserslist configuration found${colors.reset}`);
        console.log(`  Production: ${packageJson.browserslist.production ? packageJson.browserslist.production.join(', ') : 'Default'}`);
        console.log(`  Development: ${packageJson.browserslist.development ? packageJson.browserslist.development.join(', ') : 'Default'}`);
      } else {
        warnings.push("No browserslist configuration found");
        console.log(`${colors.yellow}⚠ No browserslist configuration found${colors.reset}`);
        console.log(`  Default browser compatibility settings will be used`);
      }
    } catch (error) {
      // Ignore error, we already checked package.json earlier
    }
    
    resolve();
  });
}

// Print summary
function printSummary() {
  console.log(`\n${colors.bright}====== Health Check Summary ======${colors.reset}`);
  
  if (issues.length > 0) {
    console.log(`\n${colors.red}${issues.length} issues found:${colors.reset}`);
    issues.forEach((issue, index) => {
      console.log(`${colors.red}${index + 1}. ${issue}${colors.reset}`);
    });
  }
  
  if (warnings.length > 0) {
    console.log(`\n${colors.yellow}${warnings.length} warnings found:${colors.reset}`);
    warnings.forEach((warning, index) => {
      console.log(`${colors.yellow}${index + 1}. ${warning}${colors.reset}`);
    });
  }
  
  if (passes.length > 0) {
    console.log(`\n${colors.green}${passes.length} checks passed${colors.reset}`);
  }
  
  // Overall assessment
  console.log(`\n${colors.bright}Overall Assessment:${colors.reset}`);
  if (issues.length === 0 && warnings.length === 0) {
    console.log(`${colors.green}✓ Your frontend environment looks healthy!${colors.reset}`);
    console.log(`  Run one of the start scripts to launch the application:`);
    console.log(`  • Windows PowerShell: ./start.ps1`);
    console.log(`  • Windows Command Prompt: start.bat`);
    console.log(`  • macOS/Linux: ./start.sh`);
  } else if (issues.length === 0) {
    console.log(`${colors.yellow}⚠ Your frontend environment has some warnings but should work${colors.reset}`);
    console.log(`  You can try to run the application using one of the start scripts`);
  } else {
    console.log(`${colors.red}✗ Your frontend environment has issues that need to be resolved${colors.reset}`);
    console.log(`  Fix the issues above before trying to run the application`);
  }
}

// Run all checks in sequence
async function runAllChecks() {
  try {
    await checkAdminRights();
    await checkNodeVersion();
    await checkPackageJson();
    await checkNodeModules();
    await checkEnvFile();
    await checkPortAvailability();
    await checkWebpackConfig();
    await checkBackendApiReachability();
    await checkDiskSpace();
    await checkBrowserCompatibility();
    
    printSummary();
  } catch (error) {
    console.error(`${colors.red}An unexpected error occurred during health check:${colors.reset}`, error);
  }
}

// Start the checks
runAllChecks(); 