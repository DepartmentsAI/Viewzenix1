/**
 * Cross-platform frontend startup script
 * 
 * This script detects the operating system and starts the frontend development server
 * with the appropriate configuration for Windows, macOS, or Linux.
 */

const { spawn, exec } = require('child_process');
const os = require('os');
const fs = require('fs');
const path = require('path');

// Configuration
const DEFAULT_PORT = 3000;
const DEFAULT_HOST = 'localhost';
const ENV_FILE = '.env';
const ENV_EXAMPLE_FILE = '.env.example';

// Detect platform
const platform = os.platform();
console.log(`Detected platform: ${platform}`);

// Helper function to check if a port is in use
function checkPort(port) {
  return new Promise((resolve) => {
    const netCommand = platform === 'win32' 
      ? `netstat -ano | findstr :${port}`
      : `lsof -i:${port}`;
    
    exec(netCommand, (error, stdout) => {
      if (error || !stdout.trim()) {
        // Port is available
        resolve(false);
      } else {
        // Port is in use
        resolve(true);
      }
    });
  });
}

// Helper function to create .env file if it doesn't exist
function ensureEnvFile() {
  const envPath = path.join(__dirname, ENV_FILE);
  const envExamplePath = path.join(__dirname, ENV_EXAMPLE_FILE);
  
  if (!fs.existsSync(envPath)) {
    console.log(`${ENV_FILE} not found, checking for ${ENV_EXAMPLE_FILE}...`);
    
    if (fs.existsSync(envExamplePath)) {
      // Copy example file to .env
      fs.copyFileSync(envExamplePath, envPath);
      console.log(`Created ${ENV_FILE} from ${ENV_EXAMPLE_FILE}`);
    } else {
      // Create basic .env file
      const defaultEnv = `REACT_APP_API_URL=http://${DEFAULT_HOST}:5000/api/v1\nPORT=${DEFAULT_PORT}\nBROWSER=none\n`;
      fs.writeFileSync(envPath, defaultEnv);
      console.log(`Created default ${ENV_FILE} file`);
    }
  } else {
    console.log(`${ENV_FILE} file exists`);
  }
}

// Helper function to check for and handle node_modules
async function checkNodeModules() {
  const nodeModulesPath = path.join(__dirname, 'node_modules');
  
  if (!fs.existsSync(nodeModulesPath) || !fs.readdirSync(nodeModulesPath).length) {
    console.log('node_modules missing or empty, installing dependencies...');
    
    return new Promise((resolve, reject) => {
      const npmCommand = platform === 'win32' ? 'npm.cmd' : 'npm';
      const install = spawn(npmCommand, ['install'], { cwd: __dirname, stdio: 'inherit' });
      
      install.on('close', (code) => {
        if (code === 0) {
          console.log('Dependencies installed successfully');
          resolve();
        } else {
          console.error(`npm install failed with code ${code}`);
          reject(new Error(`npm install failed with code ${code}`));
        }
      });
    });
  }
  
  console.log('node_modules exists, continuing...');
}

// Main function to start the development server
async function startDevServer() {
  try {
    // Ensure environment configuration
    ensureEnvFile();
    
    // Check node_modules
    await checkNodeModules();
    
    // Check if default port is available
    const portInUse = await checkPort(DEFAULT_PORT);
    
    if (portInUse) {
      console.warn(`Warning: Port ${DEFAULT_PORT} is already in use!`);
      console.warn('You may need to terminate existing React processes or use a different port.');
      console.warn('To use a different port, update the PORT value in your .env file.');
    }
    
    console.log('Starting development server...');
    
    // Run npm start
    const npmCommand = platform === 'win32' ? 'npm.cmd' : 'npm';
    const startProcess = spawn(npmCommand, ['start'], { cwd: __dirname, stdio: 'inherit' });
    
    startProcess.on('close', (code) => {
      if (code !== 0) {
        console.error(`Development server exited with code ${code}`);
        process.exit(code);
      }
    });
    
    console.log(`Frontend application should be available at: http://${DEFAULT_HOST}:${DEFAULT_PORT}`);
    
  } catch (error) {
    console.error('Failed to start development server:', error);
    process.exit(1);
  }
}

// Run the startup process
startDevServer(); 