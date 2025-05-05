# Viewzenix1 Frontend Verification and Auto-Start

This document provides instructions for using the frontend application verification and auto-start tools to ensure proper environment setup and application startup.

## Overview

The verification tools are designed to:

1. Check for common environment issues
2. Automatically fix identified problems
3. Start the frontend application with the correct configuration

These tools are especially helpful for:
- QA testing environments
- New developer onboarding
- Diagnosing startup issues
- Ensuring consistent configuration across environments

## Available Scripts

Choose the appropriate script for your operating system:

### Windows:

- **Command Prompt**: `verify-and-start.bat`
- **PowerShell**: `verify-and-start.ps1`

### macOS/Linux:

- **Bash/Shell**: `./verify-and-start.sh` (may need to run `chmod +x verify-and-start.sh` first)

### Cross-Platform:

- **Node.js**: `node verify-and-start.js`

## What These Tools Check

The verification tools check:

1. **Node.js**: Ensures correct version is installed
2. **Package.json**: Verifies the file exists and has required dependencies
3. **Node_modules**: Confirms dependencies are installed, installs them if missing
4. **Environment Variables**: Creates or updates .env file with required variables
5. **Port Availability**: Checks if the configured port is available, finds an alternative if needed
6. **Backend API**: Tests connectivity to the backend API or enables mock API if unavailable

## Automatic Fixes

The tools will automatically attempt to fix issues including:

- Installing missing dependencies
- Creating .env file with appropriate defaults
- Finding available ports if the configured port is in use
- Enabling mock API mode if the backend is unreachable

## Troubleshooting

If you encounter issues:

1. **Missing Dependencies**: Make sure Node.js is installed (version 14+)
2. **Permission Issues**: On Unix systems, ensure the script has execute permissions (`chmod +x verify-and-start.sh`)
3. **Port Conflicts**: If all ports are in use, manually stop processes using port 3000 (or other specified port)
4. **Backend Connectivity**: If backend issues persist, check if the backend server is running and network configuration is correct

## For QA Testing

QA testers should:

1. Navigate to the frontend directory: `cd /workspace/Viewzenix1/src/frontend`
2. Run the appropriate verification script for your OS
3. The script will check, configure, and start the application automatically
4. If successful, the frontend will be available at `http://localhost:3000` (or another port if 3000 is in use)
5. Any issues or applied fixes will be displayed in the console output

## Additional Resources

For more information, see:
- Basic environment setup: `ENVIRONMENT_SETUP.md`
- More detailed health checks: `health-check.js`
- Browser compatibility checks: `browser-compatibility-check.js` 