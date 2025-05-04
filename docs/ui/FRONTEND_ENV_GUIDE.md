# Frontend Environment Setup and Troubleshooting Guide

## Overview

This document provides instructions for setting up and troubleshooting the Viewzenix1 frontend environment. The frontend application is built with React and runs on port 3000 by default.

## Environment Configuration

The frontend application can be configured using several methods:

### 1. Environment Variables

The following environment variables are supported:

- `PORT`: The port on which the application will run (default: 3000)
- `HOST`: The host address to bind to (default: 0.0.0.0)
- `REACT_APP_API_URL`: The backend API URL (default: http://localhost:5000/api/v1)
- `REACT_APP_ENABLE_MOCK_DATA`: Whether to use mock data instead of real API calls (default: false)

### 2. Configuration File

The application uses a centralized configuration file at `src/frontend/src/config.js` which provides:

- API URL management
- Feature flag settings
- Environment detection
- Default fallback values

## Starting the Frontend Application

### Standard Method

```bash
# Navigate to the frontend directory
cd Viewzenix1/src/frontend

# Install dependencies
npm install

# Start the application
npm start
```

### Windows-Specific Method

```bash
# Navigate to the frontend directory
cd Viewzenix1/src/frontend

# Run the Windows batch file
start-frontend.bat
```

### PowerShell Method

```powershell
# Navigate to the frontend directory
cd Viewzenix1/src/frontend

# Run the PowerShell script
.\start-frontend.ps1
```

## Verifying the Application

After starting the application, verify it's running correctly:

1. Open a browser and navigate to `http://localhost:3000`
2. Check the console output for any errors
3. Verify API connectivity by checking network requests

## Troubleshooting Common Issues

### Port Already in Use

**Symptom**: Error message indicating port 3000 is already in use.

**Solution**:
1. Find the process using port 3000:
   ```bash
   # Windows
   netstat -ano | findstr :3000
   
   # Linux/Mac
   lsof -i :3000
   ```
2. Terminate the process or use a different port:
   ```bash
   # Set a different port
   SET PORT=3001 && npm start
   ```

### API Connection Issues

**Symptom**: Application loads but data doesn't appear or errors in console about API requests.

**Solution**:
1. Verify the backend is running on the expected port (default: 5000)
2. Check if the `REACT_APP_API_URL` environment variable is set correctly
3. Verify network connectivity between frontend and backend
4. Check for CORS issues in the browser console

### Node Module Issues

**Symptom**: Errors about missing modules or dependency conflicts.

**Solution**:
1. Delete the `node_modules` directory
2. Delete `package-lock.json`
3. Run `npm install` to reinstall dependencies

## Environment Validation Checklist

- [ ] Node.js and npm are installed with compatible versions
- [ ] All dependencies are installed (`npm install` completed successfully)
- [ ] Frontend application starts without errors
- [ ] Application is accessible at http://localhost:3000
- [ ] API connections are working (check network tab in browser devtools)
- [ ] Console is free of critical errors

## Contact

For additional help with frontend environment issues, contact the Frontend Agent (FE) via the communication inbox. 