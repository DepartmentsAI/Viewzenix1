# Viewzenix Frontend PowerShell Startup Script

Write-Host "Starting Viewzenix Frontend Application with PowerShell..." -ForegroundColor Green

# Set environment variables if not already set
if (-not $env:PORT) { $env:PORT = "3000" }
if (-not $env:HOST) { $env:HOST = "0.0.0.0" }
if (-not $env:REACT_APP_API_URL) { $env:REACT_APP_API_URL = "http://localhost:5000/api/v1" }

# Display configuration
Write-Host "Using configuration:" -ForegroundColor Cyan
Write-Host "- PORT: $env:PORT" -ForegroundColor White
Write-Host "- HOST: $env:HOST" -ForegroundColor White
Write-Host "- API_URL: $env:REACT_APP_API_URL" -ForegroundColor White
Write-Host ""

# Check if npm is installed
try {
    $npmVersion = npm --version
    Write-Host "Detected npm version: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: npm is not installed or not in the PATH." -ForegroundColor Red
    Write-Host "Please install Node.js and npm from https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# Check if we're in the right directory (should have package.json)
if (-not (Test-Path "package.json")) {
    Write-Host "WARNING: package.json not found in current directory." -ForegroundColor Yellow
    Write-Host "Make sure you're running this script from the frontend directory." -ForegroundColor Yellow
    
    # Try to find package.json in parent or child directories
    $packageJsonPaths = Get-ChildItem -Path ".." -Filter "package.json" -Recurse -Depth 2 -ErrorAction SilentlyContinue
    
    if ($packageJsonPaths.Count -gt 0) {
        Write-Host "Found package.json files in other directories:" -ForegroundColor Cyan
        foreach ($path in $packageJsonPaths) {
            Write-Host "  - $($path.Directory.FullName)" -ForegroundColor White
        }
        Write-Host "Please change to one of these directories and try again." -ForegroundColor Yellow
        exit 1
    }
}

# Create or update .env.local file
function Update-EnvFile {
    $envPath = ".env.local"
    $envContent = ""
    
    if (Test-Path $envPath) {
        $envContent = Get-Content $envPath -Raw
    }
    
    $envVars = @{
        "PORT" = $env:PORT
        "HOST" = $env:HOST
        "REACT_APP_API_URL" = $env:REACT_APP_API_URL
    }
    
    $updatedContent = $envContent
    
    foreach ($key in $envVars.Keys) {
        $value = $envVars[$key]
        $pattern = "^$key=.*$"
        
        if ($updatedContent -match $pattern) {
            # Update existing variable
            $updatedContent = $updatedContent -replace $pattern, "$key=$value"
        } else {
            # Add new variable
            $updatedContent += "`n$key=$value"
        }
    }
    
    # Write the updated content if changed
    if ($updatedContent -ne $envContent) {
        $updatedContent = $updatedContent.Trim() + "`n"
        Set-Content -Path $envPath -Value $updatedContent
        Write-Host ".env.local file updated with current configuration." -ForegroundColor Green
    }
}

# Update the .env file
Update-EnvFile

# Check if the Windows-specific script exists in package.json
$packageJson = Get-Content "package.json" -Raw | ConvertFrom-Json
$hasWindowsScript = $packageJson.scripts.PSObject.Properties.Name -contains "start:windows"

# Start the application
Write-Host "Starting React application..." -ForegroundColor Green

# Set environment variables for React
$env:PORT = $env:PORT
$env:HOST = $env:HOST
$env:REACT_APP_API_URL = $env:REACT_APP_API_URL

# Run the application with the appropriate script
if ($hasWindowsScript) {
    npm run start:windows
} else {
    # Fallback to regular start script
    npm start
}

# Check if application started successfully
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nERROR: Failed to start the frontend application." -ForegroundColor Red
    Write-Host "Please check the error messages above for more information." -ForegroundColor Yellow
    exit 1
}

exit 0 