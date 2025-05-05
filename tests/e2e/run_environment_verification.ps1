# Environment verification script for Viewzenix1 (PowerShell)
# May 10, 2025 - Part of contingency test plan

# Set working directory to script location
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path $scriptPath

Write-Host "=================================="
Write-Host "Viewzenix1 Environment Verification"
Write-Host "=================================="
Write-Host "Date: $(Get-Date)"
Write-Host "Environment: $($env:ENV ? $env:ENV : 'development')"
Write-Host "=================================="

# Check if python is installed
try {
    $pythonVersion = python --version
    Write-Host "✅ Found Python: $pythonVersion"
}
catch {
    Write-Host "❌ ERROR: Python is not installed or not in PATH"
    exit 1
}

# Check if broker config exists or create a default one
if (-not (Test-Path -Path ".\broker_config.json")) {
    Write-Host "⚠️ WARNING: broker_config.json not found, creating a default one..."
    $brokerConfig = @{
        api_key = "PK_YOUR_API_KEY"
        api_secret = "YOUR_API_SECRET"
        paper_trading = $true
        base_url = "https://paper-api.alpaca.markets"
    } | ConvertTo-Json

    $brokerConfig | Out-File -FilePath ".\broker_config.json"
    Write-Host "✅ Created default broker_config.json (update with real credentials)"
}

# Check if requests library is installed, install if missing
try {
    python -c "import requests" 2>$null
    Write-Host "✅ Python 'requests' package is installed"
}
catch {
    Write-Host "⚠️ WARNING: Python 'requests' package not found, installing..."
    pip install requests
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ ERROR: Failed to install required dependencies"
        exit 1
    }
}

# Create fixtures directory if it doesn't exist
if (-not (Test-Path -Path ".\fixtures")) {
    Write-Host "⚠️ WARNING: fixtures directory not found, creating..."
    New-Item -Path ".\fixtures" -ItemType Directory | Out-Null
}

# Run the verification script
Write-Host "Starting environment verification..."
python environment_verification.py $args

# Check the exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Environment verification PASSED!"
    exit 0
}
else {
    Write-Host "❌ Environment verification FAILED! Check the logs for details."
    exit 1
} 