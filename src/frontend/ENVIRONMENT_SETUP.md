# Viewzenix1 Frontend Environment Setup

This document provides instructions for setting up and troubleshooting the Viewzenix1 frontend environment across different platforms.

## Prerequisites

- Node.js 14.x or higher
- npm 6.x or higher
- Git

## Quick Start

We provide platform-specific startup scripts to make it easy to get started:

- **Windows (PowerShell)**: `./start.ps1`
- **Windows (Command Prompt)**: `start.bat`
- **macOS/Linux**: `./start.sh`

These scripts will automatically:
1. Check your environment for required dependencies
2. Install Node.js modules if needed
3. Start the development server

## Manual Setup

If you prefer a manual setup, follow these steps:

1. Navigate to the frontend directory:
   ```bash
   cd /path/to/Viewzenix1/src/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file with the following content:
   ```
   REACT_APP_API_URL=http://localhost:5000/api
   PORT=3000
   HOST=0.0.0.0
   REACT_APP_ENABLE_MOCK_API=false
   ```

4. Start the development server:
   ```bash
   npm start
   ```

## Using Docker

The frontend can also be run using Docker:

### Development Mode

```bash
docker-compose up frontend-dev
```

This will start the frontend with hot reloading enabled.

### Production Mode

```bash
docker-compose up frontend
```

This will build and serve the optimized production build.

## Environment Configuration

### Environment Variables

The frontend application uses the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `REACT_APP_API_URL` | `http://localhost:5000/api` | Base URL for API requests |
| `PORT` | `3000` | Port to run the development server on |
| `HOST` | `0.0.0.0` | Host to bind the development server to |
| `REACT_APP_ENABLE_MOCK_API` | `false` | Whether to use mock API responses |
| `NODE_ENV` | `development` | Environment mode: `development`, `test`, or `production` |

### Configuration File

The application uses a centralized configuration system in `config.js`. This file loads environment variables and provides defaults for all configuration settings.

## Troubleshooting

### Health Check

We provide a health check utility to diagnose common issues:

```bash
node health-check.js
```

This will check:
- Node.js and npm versions
- Required dependencies
- Port availability
- Environment configuration
- Backend API connectivity
- Browser compatibility

### Common Issues

#### Port 3000 Already in Use

If port 3000 is already in use, you can:
1. Close the application using that port
2. Specify a different port in the `.env` file
3. Run with a different port:
   ```bash
   PORT=3001 npm start
   ```

#### Cannot Connect to Backend API

If you see errors connecting to the backend API:
1. Ensure the backend server is running
2. Check the `REACT_APP_API_URL` environment variable
3. Verify network connectivity between frontend and backend

#### Environment Setup on Windows

If you encounter issues with CRLF line endings on Windows:
1. Configure Git to use LF line endings:
   ```bash
   git config --global core.autocrlf false
   ```
2. Ensure `.env` file uses LF line endings

#### Node Module Issues

If you encounter issues with node modules:
1. Delete the `node_modules` directory
2. Delete `package-lock.json`
3. Run `npm install` to reinstall dependencies

## Browser Compatibility

The application is tested and supported on:
- Chrome 60+
- Firefox 60+
- Safari 12+
- Edge 79+

For older browsers, a compatibility warning will be displayed.

## Additional Resources

- React Documentation: https://reactjs.org/docs/getting-started.html
- Material UI Documentation: https://mui.com/material-ui/getting-started/
- Frontend Architecture: See `/workspace/Viewzenix1/docs/architecture/frontend.md` 