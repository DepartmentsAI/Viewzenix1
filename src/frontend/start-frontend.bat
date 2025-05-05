@echo off
echo Starting Viewzenix1 Frontend Application...
echo Current directory: %~dp0

cd /d %~dp0

rem Check if Node.js is installed
node -v >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    exit /b 1
)

echo Node.js is installed.

rem Check if node_modules exists
if not exist "node_modules\" (
    echo Installing dependencies...
    call npm install
    if %ERRORLEVEL% neq 0 (
        echo Error installing dependencies. Please check npm error messages.
        exit /b %ERRORLEVEL%
    )
)

rem Check for .env file and create if needed
if not exist ".env" (
    echo Creating default .env file...
    echo REACT_APP_API_URL=http://localhost:5000/api/v1> .env
    echo PORT=3000>> .env
    echo BROWSER=none>> .env
)

rem Check if port 3000 is in use (simplified check for Windows)
netstat -ano | findstr :3000 >nul
if %ERRORLEVEL% equ 0 (
    echo Warning: Port 3000 is already in use!
    echo You may need to terminate existing React processes or use a different port.
    echo To use a different port, update the PORT value in your .env file.
)

echo Starting frontend development server...
call npm start

rem If npm start fails, provide troubleshooting info
if %ERRORLEVEL% neq 0 (
    echo Failed to start the frontend application.
    echo Troubleshooting steps:
    echo 1. Make sure all required packages are installed: npm install
    echo 2. Check for errors in .env file
    echo 3. Try clearing the npm cache: npm cache clean --force
    echo 4. If all else fails, delete node_modules and try again: rmdir /s /q node_modules ^&^& npm install
) 