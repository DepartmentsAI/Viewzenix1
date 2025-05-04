Write-Host "Starting Frontend Application on port 3000..." -ForegroundColor Green

# Change to the script's directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Set environment variables
$env:PORT = 3000
$env:HOST = "0.0.0.0"
$env:REACT_APP_API_URL = "http://localhost:5000/api/v1"

Write-Host "Environment variables set:" -ForegroundColor Cyan
Write-Host "Port: $env:PORT"
Write-Host "Host: $env:HOST"
Write-Host "API URL: $env:REACT_APP_API_URL"

# Start the application
npm start 