@echo off
echo Starting Viewzenix Frontend Application on Windows...

:: Set environment variables if not already set
if "%PORT%"=="" set PORT=3000
if "%HOST%"=="" set HOST=0.0.0.0
if "%REACT_APP_API_URL%"=="" set REACT_APP_API_URL=http://localhost:5000/api/v1

:: Display configuration
echo Using configuration:
echo - PORT: %PORT%
echo - HOST: %HOST%
echo - API_URL: %REACT_APP_API_URL%
echo.

:: Check if npm is installed
where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
  echo ERROR: npm is not installed or not in the PATH.
  echo Please install Node.js and npm from https://nodejs.org/
  exit /b 1
)

:: Start the application
echo Starting React application...
set PORT=%PORT%
set HOST=%HOST%
set REACT_APP_API_URL=%REACT_APP_API_URL%

:: Run the application
npm run start:windows

:: Check if application started successfully
if %ERRORLEVEL% NEQ 0 (
  echo.
  echo ERROR: Failed to start the frontend application.
  echo Please check the error messages above for more information.
  exit /b 1
)

exit /b 0 