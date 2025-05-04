/**
 * Custom start script for frontend application
 * This script ensures the application starts on the correct port (3000)
 */

const { spawn } = require('child_process');
const path = require('path');

// Set environment variables
process.env.PORT = process.env.PORT || 3000;
process.env.HOST = process.env.HOST || '0.0.0.0';
process.env.REACT_APP_API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api/v1';

console.log('Starting frontend application...');
console.log(`Port: ${process.env.PORT}`);
console.log(`Host: ${process.env.HOST}`);
console.log(`API URL: ${process.env.REACT_APP_API_URL}`);

// Use cross-platform compatible path for react-scripts
const reactScriptsPath = path.join('node_modules', '.bin', process.platform === 'win32' ? 'react-scripts.cmd' : 'react-scripts');

// Start the react application
const reactProcess = spawn(reactScriptsPath, ['start'], {
  env: { ...process.env },
  stdio: 'inherit'
});

// Handle process events
reactProcess.on('error', (err) => {
  console.error('Failed to start React application:', err);
  process.exit(1);
});

reactProcess.on('close', (code) => {
  console.log(`React application process exited with code ${code}`);
  process.exit(code);
}); 