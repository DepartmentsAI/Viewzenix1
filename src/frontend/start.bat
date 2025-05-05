@echo off
REM Batch script to start the Viewzenix1 frontend application on Windows

echo ====== Viewzenix1 Frontend Startup (Windows) ======

REM Check if .env file exists
if exist .env (
    echo [√] .env file found
) else (
    echo [!] No .env file found, using default settings
)

REM Check for Node.js installation
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [X] Node.js not found. Please install Node.js 14 or newer
    exit /b 1
)

REM Display Node.js version
for /f "tokens=*" %%i in ('node -v') do set NODE_VERSION=%%i
echo [√] Node.js detected: %NODE_VERSION%

REM Check for npm
where npm >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [X] npm not found. Please install npm
    exit /b 1
)

REM Display npm version
for /f "tokens=*" %%i in ('npm -v') do set NPM_VERSION=%%i
echo [√] npm detected: %NPM_VERSION%

REM Check for port 3000 usage (simplified version)
netstat -ano | findstr :3000 >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [!] Port 3000 is already in use. You may encounter issues starting the application.
    echo     Consider adjusting the PORT in .env file or closing the application using that port.
)

REM Check for dependencies
echo Checking dependencies...
if not exist node_modules (
    echo Installing dependencies (this may take a few minutes)...
    call npm install
    if %ERRORLEVEL% neq 0 (
        echo [X] Failed to install dependencies
        exit /b 1
    )
    echo [√] Dependencies installed successfully
) else (
    echo [√] Dependencies already installed
)

REM Start the application
echo Starting Viewzenix1 Frontend...
call npm start

REM Script end
echo Frontend server has stopped. 