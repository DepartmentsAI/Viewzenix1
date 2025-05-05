# PowerShell script to start the Viewzenix1 frontend application
# This script is designed for Windows environments

# Display header
Write-Host "====== Viewzenix1 Frontend Startup (Windows) ======" -ForegroundColor Green

# Check if .env file exists
if (Test-Path -Path ".env") {
    Write-Host "✓ .env file found" -ForegroundColor Green
} else {
    Write-Host "⚠ No .env file found, using default settings" -ForegroundColor Yellow
}

# Check for Node.js installation
try {
    $nodeVersion = node -v
    Write-Host "✓ Node.js detected: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Please install Node.js 14 or newer" -ForegroundColor Red
    exit 1
}

# Check for npm
try {
    $npmVersion = npm -v
    Write-Host "✓ npm detected: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ npm not found. Please install npm" -ForegroundColor Red
    exit 1
}

# Check if port 3000 is already in use
$portCheck = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($portCheck) {
    Write-Host "⚠ Port 3000 is already in use. You may encounter issues starting the application." -ForegroundColor Yellow
    Write-Host "  Consider adjusting the PORT in .env file or closing the application using that port." -ForegroundColor Yellow
}

# Check for dependencies
Write-Host "Checking dependencies..." -ForegroundColor Yellow
$nodeModulesExists = Test-Path -Path "node_modules"
if (-not $nodeModulesExists) {
    Write-Host "Installing dependencies (this may take a few minutes)..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "✓ Dependencies already installed" -ForegroundColor Green
}

# Start the application
Write-Host "Starting Viewzenix1 Frontend..." -ForegroundColor Green
npm start

# Script end
Write-Host "Frontend server has stopped." -ForegroundColor Yellow 