# Frontend Environment Setup Guide

This guide covers setting up the Viewzenix1 frontend development environment, troubleshooting common issues, and explains the available configuration options.

## Quick Start

### Windows

1. Navigate to the frontend directory:
   ```
   cd Viewzenix1/src/frontend
   ```

2. Run the startup script:
   ```
   .\start-frontend.ps1
   ```
   
   If you prefer CMD or don't have PowerShell, use:
   ```
   start-frontend.bat
   ```

### macOS/Linux

1. Navigate to the frontend directory:
   ```
   cd Viewzenix1/src/frontend
   ```

2. Make the startup script executable (first time only):
   ```
   chmod +x start-frontend.sh
   ```

3. Run the startup script:
   ```
   ./start-frontend.sh
   ```

## Manual Setup

If you prefer manual setup or the startup scripts aren't working:

1. Navigate to the frontend directory:
   ```
   cd Viewzenix1/src/frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Create a `.env` file with:
   ```
   REACT_APP_API_URL=http://localhost:5000/api/v1
   PORT=3000
   BROWSER=none
   ```

4. Start the development server:
   ```
   npm start
   ```

## Environment Configuration

### Environment Variables

The application uses the following environment variables which can be set in a `.env` file:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `REACT_APP_API_URL` | Base URL for API requests | `http://localhost:5000/api/v1` |
| `PORT` | Port for development server | `3000` |
| `BROWSER` | Whether to open browser when starting | `none` |
| `REACT_APP_API_TIMEOUT` | API request timeout (ms) | `5000` |
| `REACT_APP_API_WITH_CREDENTIALS` | Include credentials in API requests | `false` |
| `REACT_APP_API_MAX_RETRIES` | Max retries for failed requests | `3` |
| `REACT_APP_API_RETRY_DELAY` | Initial retry delay (ms) | `1000` |
| `REACT_APP_API_RETRY_FACTOR` | Exponential backoff factor | `2` |
| `REACT_APP_THEME` | UI theme | `light` |
| `REACT_APP_DISABLE_ANIMATIONS` | Disable UI animations | `false` |
| `REACT_APP_NOTIFICATION_POSITION` | Toast notification position | `top-right` |
| `REACT_APP_NOTIFICATION_DURATION` | Toast notification duration (ms) | `5000` |
| `REACT_APP_NOTIFICATION_MAX_COUNT` | Max visible notifications | `5` |
| `REACT_APP_DEFAULT_PAGE_SIZE` | Default pagination size | `10` |
| `REACT_APP_ENABLE_RISK_MANAGEMENT` | Enable risk management features | `true` |
| `REACT_APP_ENABLE_PAPER_TRADING` | Enable paper trading features | `false` |
| `REACT_APP_ENABLE_NOTIFICATIONS` | Enable notification system | `true` |
| `REACT_APP_ENABLE_DARK_MODE` | Enable dark mode | `false` |
| `REACT_APP_ENABLE_BETA_FEATURES` | Enable beta features | `false` |

### Configuration File

The application uses a centralized configuration system in `src/config.js`, which reads these environment variables and provides sensible defaults.

## Docker Support

The frontend includes Docker support for containerized development and deployment.

### Building the Docker Image

```
cd Viewzenix1/src/frontend
docker build -t viewzenix-frontend .
```

### Running with Docker Compose

```
cd Viewzenix1/src/frontend
docker-compose up
```

## Troubleshooting

### Common Issues

1. **"Port 3000 is already in use"**
   - Find and terminate the process using port 3000:
     - Windows: `netstat -ano | findstr :3000` then `taskkill /PID <PID> /F`
     - macOS/Linux: `lsof -i:3000` then `kill -9 <PID>`
   - Or change the port in `.env`: `PORT=3001`

2. **"Module not found" errors**
   - Delete the `node_modules` folder and reinstall:
     ```
     rm -rf node_modules
     npm install
     ```

3. **API Connection Issues**
   - Verify the backend is running
   - Check that `REACT_APP_API_URL` is correct in `.env`
   - Run `node healthcheck.js` to diagnose

4. **Blank Screen / React Not Loading**
   - Check browser console for errors
   - Verify that the React app is building correctly
   - Try clearing browser cache

5. **Changes Not Reflecting**
   - Some changes require a restart of the development server
   - Try stopping and restarting with the startup script

### Running Health Checks

The application includes a health check utility to diagnose common issues:

```
cd Viewzenix1/src/frontend
node healthcheck.js
```

This will check:
- Dependencies are installed
- Build configuration is valid
- Development port is available
- API is accessible

## Browser Support

The application officially supports:
- Chrome 88+
- Firefox 85+
- Safari 14+
- Edge 88+
- Opera 74+

A browser compatibility check runs automatically when the application loads, warning users about potential issues. 