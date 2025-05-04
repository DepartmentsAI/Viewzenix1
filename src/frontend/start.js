/**
 * Cross-platform Frontend Start Script
 * 
 * This script detects the operating system and executes the appropriate
 * start command to ensure the frontend application runs correctly on any platform.
 */

const { execSync } = require('child_process');
const os = require('os');
const fs = require('fs');
const path = require('path');

// Detect operating system
const platform = os.platform();
console.log(`Detected platform: ${platform}`);

// Configuration
const PORT = process.env.PORT || 3000;
const HOST = process.env.HOST || '0.0.0.0';
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api/v1';

console.log(`Using configuration:
- PORT: ${PORT}
- HOST: ${HOST}
- API_URL: ${API_URL}
`);

// Ensure .env file exists with required variables
function createEnvFileIfNeeded() {
  const envPath = path.join(__dirname, '.env.local');
  let envContent = '';
  
  if (fs.existsSync(envPath)) {
    envContent = fs.readFileSync(envPath, 'utf8');
  }
  
  // Check if variables need to be updated/added
  const envVars = {
    PORT: PORT,
    HOST: HOST,
    REACT_APP_API_URL: API_URL
  };
  
  let updatedContent = envContent;
  
  // Update each variable in the .env file
  Object.entries(envVars).forEach(([key, value]) => {
    const regex = new RegExp(`^${key}=.*$`, 'm');
    if (regex.test(updatedContent)) {
      // Update existing variable
      updatedContent = updatedContent.replace(regex, `${key}=${value}`);
    } else {
      // Add new variable
      updatedContent += `\n${key}=${value}`;
    }
  });
  
  // Write the updated content if changed
  if (updatedContent !== envContent) {
    fs.writeFileSync(envPath, updatedContent.trim() + '\n');
    console.log('.env.local file updated with current configuration.');
  }
}

// Start the application using the appropriate platform-specific method
function startApplication() {
  try {
    // Create or update .env file
    createEnvFileIfNeeded();
    
    if (platform === 'win32') {
      // Windows
      console.log('Starting frontend application for Windows...');
      execSync('start-frontend.bat', { stdio: 'inherit' });
    } else if (platform === 'darwin' || platform === 'linux') {
      // macOS or Linux
      console.log('Starting frontend application for macOS/Linux...');
      
      // Set environment variables
      process.env.PORT = PORT;
      process.env.HOST = HOST;
      process.env.REACT_APP_API_URL = API_URL;
      
      // Execute start command
      execSync('npm run start:unix', { stdio: 'inherit' });
    } else {
      // Other platforms
      console.warn(`WARNING: Unrecognized platform: ${platform}`);
      console.log('Attempting to start with generic command...');
      
      // Set environment variables
      process.env.PORT = PORT;
      process.env.HOST = HOST;
      process.env.REACT_APP_API_URL = API_URL;
      
      // Try generic start
      execSync('npm start', { stdio: 'inherit' });
    }
  } catch (error) {
    console.error('Error starting frontend application:');
    console.error(error.message || error);
    process.exit(1);
  }
}

// Run the application
startApplication(); 