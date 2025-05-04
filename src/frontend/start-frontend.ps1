# PowerShell script to start the frontend application
# Usage: .\start-frontend.ps1

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "Starting Viewzenix1 Frontend Application..."
Write-Host "Current directory: $scriptPath"

# Check if node is installed
try {
    $nodeVersion = node -v
    Write-Host "Node.js version: $nodeVersion"
} catch {
    Write-Host "Error: Node.js is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Check if node_modules exists
if (-not (Test-Path -Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error installing dependencies. Please check npm error messages." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

# Check for .env file and create if needed
if (-not (Test-Path -Path ".env")) {
    Write-Host "Creating default .env file..." -ForegroundColor Yellow
    "REACT_APP_API_URL=http://localhost:5000/api/v1`nPORT=3000`nBROWSER=none" | Out-File -FilePath ".env" -Encoding utf8
}

# Check if port 3000 is in use
$portInUse = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "Warning: Port 3000 is already in use!" -ForegroundColor Yellow
    Write-Host "You may need to terminate existing React processes or use a different port." -ForegroundColor Yellow
    Write-Host "To use a different port, update the PORT value in your .env file." -ForegroundColor Yellow
}

# Start the React application
Write-Host "Starting frontend development server..." -ForegroundColor Green
npm start

# If npm start fails, provide troubleshooting info
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to start the frontend application." -ForegroundColor Red
    Write-Host "Troubleshooting steps:" -ForegroundColor Yellow
    Write-Host "1. Make sure all required packages are installed: npm install" -ForegroundColor Yellow
    Write-Host "2. Check for errors in .env file" -ForegroundColor Yellow
    Write-Host "3. Try clearing the npm cache: npm cache clean --force" -ForegroundColor Yellow
    Write-Host "4. If all else fails, delete node_modules and try again: rm -r node_modules && npm install" -ForegroundColor Yellow
} 