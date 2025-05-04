# Viewzenix1 Frontend Environment Guide

This guide provides detailed instructions for setting up, configuring, and running the Viewzenix1 Trading Platform frontend application across different environments.

## Table of Contents

- [Getting Started](#getting-started)
- [Environment Configuration](#environment-configuration)
- [Running the Application](#running-the-application)
- [Cross-Platform Support](#cross-platform-support)
- [Docker Support](#docker-support)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Node.js (v14.x or higher)
- npm (v6.x or higher)
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/DepartmentsAI/Viewzenix1.git
   cd Viewzenix1/src/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## Environment Configuration

The frontend application uses a centralized configuration system located in `src/config.js`. This file reads environment variables and provides default values where needed.

### Configuration Files

- `.env`: Default environment variables (committed to repository)
- `.env.local`: Local overrides (not committed to repository)
- `.env.development`: Development-specific variables
- `.env.production`: Production-specific variables

You can create these files manually or use the provided scripts which will create/update the `.env.local` file:

```bash
# Windows Command Prompt
node start.js

# PowerShell
./start-frontend.ps1

# Linux/macOS
node start.js
```

## Running the Application

### Universal Script (Recommended)

The frontend includes a cross-platform start script that detects your operating system and runs the appropriate commands:

```bash
node start.js
```

### Platform-Specific Commands

#### Windows

```bash
# Command Prompt
start-frontend.bat

# PowerShell
./start-frontend.ps1

# Or directly through npm
npm run start:windows
```

#### macOS/Linux

```bash
npm run start:unix
```

### Manual Configuration

If you prefer to set environment variables manually:

```bash
# Windows (Command Prompt)
set PORT=3000
set HOST=0.0.0.0
set REACT_APP_API_URL=http://localhost:5000/api/v1
npm start

# Windows (PowerShell)
$env:PORT=3000
$env:HOST=0.0.0.0
$env:REACT_APP_API_URL=http://localhost:5000/api/v1
npm start

# macOS/Linux
PORT=3000 HOST=0.0.0.0 REACT_APP_API_URL=http://localhost:5000/api/v1 npm start
```

## Cross-Platform Support

The frontend is designed to run consistently across different operating systems. Platform-specific configurations are handled automatically by the start scripts.

### Windows-Specific Notes

- Windows environments require setting environment variables differently from Unix-based systems
- The `start-frontend.bat` script handles this automatically
- For PowerShell users, use `start-frontend.ps1` which provides enhanced error reporting

### macOS/Linux-Specific Notes

- Unix-based environments use the `PORT=3000 npm start` format for environment variables
- The start scripts ensure proper variable setting

## Docker Support

The frontend includes Docker support for containerized development and deployment.

### Running with Docker

1. Build the Docker image:
   ```bash
   npm run docker:build
   # or
   docker build -t viewzenix-frontend .
   ```

2. Run the container:
   ```bash
   npm run docker:start
   # or
   docker run -p 3000:3000 viewzenix-frontend
   ```

### Using Docker Compose

For a more complete setup with customizable environment variables:

```bash
npm run docker:compose
# or
docker-compose up
```

To rebuild the image when making changes:

```bash
npm run docker:compose:build
# or
docker-compose up --build
```

## Environment Variables

Here are the key environment variables used by the frontend:

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | The port on which the frontend server runs | `3000` |
| `HOST` | The host address to bind to | `0.0.0.0` (all interfaces) |
| `REACT_APP_API_URL` | URL for the backend API | `http://localhost:5000/api/v1` |
| `NODE_ENV` | Environment mode (development/production) | `development` |
| `REACT_APP_NAME` | Application name | `Viewzenix Trading Platform` |
| `REACT_APP_ENABLE_RISK_MANAGEMENT` | Enable risk management features | `true` |
| `REACT_APP_ENABLE_DARK_MODE` | Enable dark mode support | `true` |

See `src/config.js` for a complete list of supported environment variables and their default values.

## Troubleshooting

### Common Issues

#### "Cannot access the application on localhost:3000"

- Ensure the application is running (check terminal output)
- Verify no other application is using port 3000
- Try accessing via IP address (e.g., http://127.0.0.1:3000)
- Check your firewall settings

#### "API requests are failing"

- Verify the backend API is running
- Check the `REACT_APP_API_URL` environment variable
- Look for CORS issues in the browser console
- Ensure network connectivity between frontend and backend

#### "Application won't start on Windows"

- Try running with the batch file: `start-frontend.bat`
- Ensure environment variables are set correctly
- Check for permissions issues

### Health Check

The application includes a health check script to verify it's running correctly:

```bash
npm run healthcheck
# or
node healthcheck.js
```

## Additional Resources

- [React.js Documentation](https://reactjs.org/docs/getting-started.html)
- [Create React App Documentation](https://create-react-app.dev/docs/getting-started)
- [Environment Variables in Create React App](https://create-react-app.dev/docs/adding-custom-environment-variables) 