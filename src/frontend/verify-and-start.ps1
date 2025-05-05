# Viewzenix1 Frontend Verification and Auto-Start
Write-Host "Viewzenix1 Frontend Verification and Auto-Start" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check if Node.js is installed
try {
    $nodeVersion = node -v
    Write-Host "Node.js detected: $nodeVersion" -ForegroundColor Green
}
catch {
    Write-Host "Error: Node.js is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# Make script executable on Unix systems if copied there
if ((Get-Content verify-and-start.js -Raw) -match "`r`n") {
    Write-Host "Converting CRLF to LF for compatibility..." -ForegroundColor Yellow
    $content = Get-Content verify-and-start.js -Raw
    $content = $content -replace "`r`n", "`n"
    Set-Content -Path verify-and-start.js -Value $content -NoNewline
}

# Run the verification and auto-start script
Write-Host "Running verification and auto-start script..." -ForegroundColor Cyan
node verify-and-start.js

# Check if the script failed
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Error: Frontend verification failed with error code $LASTEXITCODE" -ForegroundColor Red
    Write-Host "Please check the log output above for details." -ForegroundColor Yellow
    exit $LASTEXITCODE
}

exit 0 