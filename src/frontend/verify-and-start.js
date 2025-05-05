#!/usr/bin/env node
/**
 * Viewzenix1 Frontend Verification and Auto-Start Utility
 * 
 * This tool checks for common issues with frontend environment setup,
 * attempts to automatically correct them, and starts the application.
 */

const fs = require('fs');
const http = require('http');
const path = require('path');
const { exec, execSync, spawn } = require('child_process');
const os = require('os');
const net = require('net');

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
console.log(`${colors.bright}====== Viewzenix1 Frontend Verification and Auto-Start ======${colors.reset}`);
console.log(`Running on: ${os.type()} ${os.release()} (${os.platform()}, ${os.arch()})\n`);

// Track issues to provide summary at the end
const issues = [];
const warnings = [];
const passes = [];
const fixes = [];

// Check if Node.js is installed and version is compatible
function checkNodeVersion() {
  return new Promise((resolve) => {
    const nodeVersion = process.version;
    console.log(`${colors.cyan}Checking Node.js version...${colors.reset}`);
    console.log(`${colors.green}✓ Node.js detected: ${nodeVersion}${colors.reset}`);
    
    // Parse version (e.g., "v14.17.0" -> 14)
    const majorVersion = parseInt(nodeVersion.substring(1).split('.')[0]);
    
    if (majorVersion < 14) {
      issues.push(`Node.js version is ${nodeVersion}, but >= 14.x is recommended`);
      console.log(`${colors.red}✗ Node.js version ${nodeVersion} is below recommended (>= 14.x)${colors.reset}`);
      console.log(`  Please update Node.js to version 14 or higher`);
    } else {
      passes.push(`Node.js version is compatible: ${nodeVersion}`);
    }
    
    resolve();
  });
}

// Check if package.json exists and is valid
function checkPackageJson() {
  return new Promise((resolve) => {
    console.log(`${colors.cyan}Checking package.json...${colors.reset}`);
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
    console.log(`${colors.cyan}Checking node_modules...${colors.reset}`);
    const nodeModulesPath = path.join(process.cwd(), 'node_modules');
    
    if (!fs.existsSync(nodeModulesPath)) {
      issues.push("node_modules directory not found - will run 'npm install'");
      console.log(`${colors.red}✗ node_modules directory not found${colors.reset}`);
      console.log(`${colors.yellow}⚠ Attempting to fix: Running 'npm install'...${colors.reset}`);
      
      try {
        console.log(`Installing dependencies...`);
        execSync('npm install', { stdio: 'inherit' });
        fixes.push("Installed dependencies with 'npm install'");
        console.log(`${colors.green}✓ Dependencies installed successfully${colors.reset}`);
      } catch (error) {
        issues.push(`Failed to install dependencies: ${error.message}`);
        console.log(`${colors.red}✗ Failed to install dependencies: ${error.message}${colors.reset}`);
      }
      
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
      console.log(`${colors.yellow}⚠ Attempting to fix: Running 'npm install'...${colors.reset}`);
      
      try {
        console.log(`Installing dependencies...`);
        execSync('npm install', { stdio: 'inherit' });
        fixes.push("Reinstalled dependencies to fix missing packages");
        console.log(`${colors.green}✓ Dependencies reinstalled successfully${colors.reset}`);
      } catch (error) {
        issues.push(`Failed to reinstall dependencies: ${error.message}`);
        console.log(`${colors.red}✗ Failed to reinstall dependencies: ${error.message}${colors.reset}`);
      }
    } else {
      passes.push("All critical packages installed in node_modules");
    }
    
    resolve();
  });
}

// Check if .env file exists and create if missing
function checkEnvFile() {
  return new Promise((resolve) => {
    console.log(`${colors.cyan}Checking .env file...${colors.reset}`);
    const envPath = path.join(process.cwd(), '.env');
    const envTemplatePath = path.join(process.cwd(), '.env.template');
    
    if (!fs.existsSync(envPath)) {
      warnings.push("No .env file found - will create one with default settings");
      console.log(`${colors.yellow}⚠ No .env file found${colors.reset}`);
      
      // Create .env file with default settings
      try {
        let envContent;
        
        if (fs.existsSync(envTemplatePath)) {
          console.log(`Using .env.template as a starting point...`);
          envContent = fs.readFileSync(envTemplatePath, 'utf8');
        } else {
          console.log(`Creating default .env file...`);
          envContent = 
`REACT_APP_API_URL=http://localhost:5000/api
PORT=3000
HOST=0.0.0.0
REACT_APP_ENABLE_MOCK_API=false
`;
        }
        
        fs.writeFileSync(envPath, envContent);
        fixes.push("Created .env file with default settings");
        console.log(`${colors.green}✓ Created .env file with default settings${colors.reset}`);
      } catch (error) {
        issues.push(`Failed to create .env file: ${error.message}`);
        console.log(`${colors.red}✗ Failed to create .env file: ${error.message}${colors.reset}`);
      }
      
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
    const requiredVars = [
      { key: 'PORT', defaultValue: '3000' },
      { key: 'HOST', defaultValue: '0.0.0.0' },
      { key: 'REACT_APP_API_URL', defaultValue: 'http://localhost:5000/api' }
    ];
    
    const missingVars = requiredVars.filter(v => !envVars[v.key]);
    
    if (missingVars.length > 0) {
      warnings.push(`Missing recommended environment variables: ${missingVars.map(v => v.key).join(', ')}`);
      console.log(`${colors.yellow}⚠ Missing recommended environment variables: ${missingVars.map(v => v.key).join(', ')}${colors.reset}`);
      console.log(`${colors.yellow}⚠ Attempting to fix: Updating .env file...${colors.reset}`);
      
      let updatedEnvContent = envContent;
      missingVars.forEach(v => {
        updatedEnvContent += `\n${v.key}=${v.defaultValue}`;
      });
      
      try {
        fs.writeFileSync(envPath, updatedEnvContent);
        fixes.push(`Added missing environment variables: ${missingVars.map(v => v.key).join(', ')}`);
        console.log(`${colors.green}✓ Updated .env file with missing variables${colors.reset}`);
      } catch (error) {
        issues.push(`Failed to update .env file: ${error.message}`);
        console.log(`${colors.red}✗ Failed to update .env file: ${error.message}${colors.reset}`);
      }
    } else {
      passes.push("All recommended environment variables found in .env");
    }
    
    resolve();
  });
}

// Check if port is available
function checkPortAvailability() {
  return new Promise((resolve) => {
    console.log(`${colors.cyan}Checking port availability...${colors.reset}`);
    
    // Skip port check if running in CI environment
    if (process.env.CI === 'true' || process.env.CI === true) {
      console.log(`${colors.yellow}⚠ Skipping port availability check in CI environment${colors.reset}`);
      warnings.push('Port availability check skipped in CI environment');
      return resolve();
    }
    
    // Get PORT from .env or use default 3000
    let port = 3000;
    try {
      const envPath = path.join(process.cwd(), '.env');
      if (fs.existsSync(envPath)) {
        const envContent = fs.readFileSync(envPath, 'utf8');
        const portMatch = envContent.match(/PORT\s*=\s*(\d+)/);
        if (portMatch && portMatch[1]) {
          port = parseInt(portMatch[1]);
        }
      }
    } catch (error) {
      console.log(`${colors.yellow}⚠ Error reading PORT from .env: ${error.message}${colors.reset}`);
    }
    
    console.log(`Checking if port ${port} is available...`);
    
    const server = net.createServer();
    server.once('error', (err) => {
      if (err.code === 'EADDRINUSE') {
        issues.push(`Port ${port} is already in use`);
        console.log(`${colors.red}✗ Port ${port} is already in use${colors.reset}`);
        console.log(`${colors.yellow}⚠ Attempting to fix: Finding available port...${colors.reset}`);
        
        // Try to find an available port between 3001 and 3010
        let portFound = false;
        for (let testPort = 3001; testPort <= 3010; testPort++) {
          try {
            const testServer = net.createServer();
            testServer.listen(testPort);
            testServer.once('listening', () => {
              testServer.close();
              
              // Update .env with the new port
              try {
                const envPath = path.join(process.cwd(), '.env');
                let envContent = '';
                if (fs.existsSync(envPath)) {
                  envContent = fs.readFileSync(envPath, 'utf8');
                  
                  // Replace existing PORT if found
                  if (envContent.match(/PORT\s*=\s*\d+/)) {
                    envContent = envContent.replace(/PORT\s*=\s*\d+/, `PORT=${testPort}`);
                  } else {
                    // Add PORT if not found
                    envContent += `\nPORT=${testPort}`;
                  }
                } else {
                  envContent = `PORT=${testPort}\n`;
                }
                
                fs.writeFileSync(envPath, envContent);
                port = testPort;
                fixes.push(`Updated PORT to ${testPort} in .env file`);
                console.log(`${colors.green}✓ Found available port ${testPort} and updated .env${colors.reset}`);
                portFound = true;
              } catch (error) {
                issues.push(`Failed to update PORT in .env: ${error.message}`);
                console.log(`${colors.red}✗ Failed to update PORT in .env: ${error.message}${colors.reset}`);
              }
            });
            
            testServer.once('error', () => {
              // Port is in use, try the next one
            });
            
            break;
          } catch (error) {
            // Try the next port
          }
        }
        
        if (!portFound) {
          issues.push("Could not find an available port between 3001 and 3010");
          console.log(`${colors.red}✗ Could not find an available port between 3001 and 3010${colors.reset}`);
          console.log(`  Please manually stop the process using port ${port} or specify a different port`);
        }
      } else {
        issues.push(`Error checking port availability: ${err.message}`);
        console.log(`${colors.red}✗ Error checking port availability: ${err.message}${colors.reset}`);
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

// Check backend API reachability
function checkBackendApiReachability() {
  return new Promise((resolve) => {
    console.log(`${colors.cyan}Checking backend API reachability...${colors.reset}`);
    
    // Skip backend check if running in CI environment
    if (process.env.CI === 'true' || process.env.CI === true) {
      console.log(`${colors.yellow}⚠ Skipping backend API check in CI environment${colors.reset}`);
      warnings.push('Backend API check skipped in CI environment');
      return resolve();
    }
    
    // Get API URL from .env or use default
    let apiUrl = 'http://localhost:5000/api';
    try {
      const envPath = path.join(process.cwd(), '.env');
      if (fs.existsSync(envPath)) {
        const envContent = fs.readFileSync(envPath, 'utf8');
        const apiMatch = envContent.match(/REACT_APP_API_URL\s*=\s*([^\s]+)/);
        if (apiMatch && apiMatch[1]) {
          apiUrl = apiMatch[1];
        }
      }
    } catch (error) {
      console.log(`${colors.yellow}⚠ Error reading REACT_APP_API_URL from .env: ${error.message}${colors.reset}`);
    }
    
    console.log(`Checking API endpoint: ${apiUrl}/health...`);
    
    // Use HTTP client to check API reachability
    const request = http.get(`${apiUrl}/health`, (res) => {
      if (res.statusCode >= 200 && res.statusCode < 300) {
        passes.push(`Backend API is reachable: ${apiUrl}`);
        console.log(`${colors.green}✓ Backend API is reachable: ${apiUrl}${colors.reset}`);
      } else {
        warnings.push(`Backend API returned status code ${res.statusCode}: ${apiUrl}`);
        console.log(`${colors.yellow}⚠ Backend API returned status code ${res.statusCode}: ${apiUrl}${colors.reset}`);
        console.log(`  API may be functioning but health endpoint is not implemented`);
      }
      
      resolve();
    });
    
    request.on('error', (err) => {
      warnings.push(`Cannot connect to backend API at ${apiUrl}: ${err.message}`);
      console.log(`${colors.yellow}⚠ Cannot connect to backend API at ${apiUrl}: ${err.message}${colors.reset}`);
      console.log(`${colors.yellow}⚠ Frontend will still start, but API functionality will not work${colors.reset}`);
      console.log(`  You might want to enable mock API if available by setting REACT_APP_ENABLE_MOCK_API=true in .env`);
      
      try {
        const envPath = path.join(process.cwd(), '.env');
        let envContent = '';
        if (fs.existsSync(envPath)) {
          envContent = fs.readFileSync(envPath, 'utf8');
          
          // Check if mock API setting exists
          if (envContent.match(/REACT_APP_ENABLE_MOCK_API\s*=\s*(true|false)/)) {
            // Update to true if false
            if (envContent.match(/REACT_APP_ENABLE_MOCK_API\s*=\s*false/)) {
              envContent = envContent.replace(/REACT_APP_ENABLE_MOCK_API\s*=\s*false/, 'REACT_APP_ENABLE_MOCK_API=true');
              fixes.push("Enabled mock API by setting REACT_APP_ENABLE_MOCK_API=true");
              console.log(`${colors.green}✓ Updated .env to enable mock API${colors.reset}`);
            }
          } else {
            // Add mock API setting
            envContent += '\nREACT_APP_ENABLE_MOCK_API=true';
            fixes.push("Added and enabled mock API setting");
            console.log(`${colors.green}✓ Added mock API setting to .env${colors.reset}`);
          }
          
          fs.writeFileSync(envPath, envContent);
        }
      } catch (error) {
        console.log(`${colors.red}✗ Failed to update mock API setting: ${error.message}${colors.reset}`);
      }
      
      resolve();
    });
    
    request.setTimeout(5000, () => {
      request.abort();
      warnings.push(`Backend API request timed out: ${apiUrl}`);
      console.log(`${colors.yellow}⚠ Backend API request timed out: ${apiUrl}${colors.reset}`);
      console.log(`${colors.yellow}⚠ Frontend will still start, but API functionality may not work${colors.reset}`);
      resolve();
    });
  });
}

// Print summary of issues, warnings, and passes
function printSummary() {
  console.log('\n' + '-'.repeat(70));
  console.log(`${colors.bright}Summary:${colors.reset}`);
  
  if (issues.length === 0 && warnings.length === 0) {
    console.log(`${colors.green}All checks passed! The frontend should start without issues.${colors.reset}`);
  } else {
    if (issues.length > 0) {
      console.log(`\n${colors.red}Issues (${issues.length}):${colors.reset}`);
      issues.forEach((issue, i) => {
        console.log(`${colors.red}${i+1}.${colors.reset} ${issue}`);
      });
    }
    
    if (warnings.length > 0) {
      console.log(`\n${colors.yellow}Warnings (${warnings.length}):${colors.reset}`);
      warnings.forEach((warning, i) => {
        console.log(`${colors.yellow}${i+1}.${colors.reset} ${warning}`);
      });
    }
  }
  
  if (fixes.length > 0) {
    console.log(`\n${colors.green}Applied Fixes (${fixes.length}):${colors.reset}`);
    fixes.forEach((fix, i) => {
      console.log(`${colors.green}${i+1}.${colors.reset} ${fix}`);
    });
  }
  
  if (passes.length > 0) {
    console.log(`\n${colors.green}Passed Checks (${passes.length}):${colors.reset}`);
    passes.forEach((pass, i) => {
      console.log(`${colors.green}${i+1}.${colors.reset} ${pass}`);
    });
  }
  
  console.log('-'.repeat(70));
}

// Start the frontend application
function startFrontendApp() {
  return new Promise((resolve) => {
    console.log(`\n${colors.bright}Starting Frontend Application...${colors.reset}`);
    
    let startCommand;
    let args = [];
    
    if (os.platform() === 'win32') {
      // Windows
      if (fs.existsSync(path.join(process.cwd(), 'start.bat'))) {
        startCommand = process.cwd() + '\\start.bat';
      } else {
        startCommand = 'npm';
        args = ['start'];
      }
    } else {
      // macOS/Linux
      if (fs.existsSync(path.join(process.cwd(), 'start.sh'))) {
        startCommand = './start.sh';
      } else {
        startCommand = 'npm';
        args = ['start'];
      }
    }
    
    console.log(`Executing: ${startCommand} ${args.join(' ')}`);
    
    const startProcess = spawn(startCommand, args, {
      stdio: 'inherit',
      shell: true
    });
    
    startProcess.on('error', (error) => {
      console.log(`${colors.red}✗ Failed to start frontend application: ${error.message}${colors.reset}`);
      resolve();
    });
    
    startProcess.on('close', (code) => {
      if (code !== 0) {
        console.log(`${colors.red}✗ Frontend application process exited with code ${code}${colors.reset}`);
      }
      resolve();
    });
    
    console.log(`${colors.green}Frontend application starting...${colors.reset}`);
    console.log(`${colors.cyan}Press Ctrl+C to stop the application${colors.reset}`);
    
    // We don't resolve this promise until the process exits
  });
}

// Main function to run all checks and start the app
async function runVerificationAndStart() {
  try {
    console.log(`${colors.cyan}Running verification checks...${colors.reset}\n`);
    
    // Check if running in CI environment
    if (process.env.CI === 'true' || process.env.CI === true) {
      console.log(`${colors.yellow}⚠ Running in CI environment - some checks may be skipped${colors.reset}`);
    }
    
    await checkNodeVersion();
    await checkPackageJson();
    await checkNodeModules();
    await checkEnvFile();
    await checkPortAvailability();
    await checkBackendApiReachability();
    
    printSummary();
    
    // Decide whether to start based on issues
    if (issues.length > 0) {
      console.log(`\n${colors.yellow}⚠ There are unresolved issues that might prevent the application from starting properly.${colors.reset}`);
      console.log(`${colors.yellow}⚠ Please fix these issues and try again.${colors.reset}`);
    } else {
      console.log(`\n${colors.green}✓ All critical checks passed or were automatically fixed.${colors.reset}`);
      console.log(`${colors.green}✓ Starting frontend application...${colors.reset}\n`);
      
      await startFrontendApp();
    }
  } catch (error) {
    console.log(`${colors.red}An unexpected error occurred: ${error.message}${colors.reset}`);
  }
}

// Run the main function
runVerificationAndStart(); 