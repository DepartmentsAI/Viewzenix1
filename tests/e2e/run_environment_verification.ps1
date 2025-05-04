# Environment Verification Script for Windows
# Runs the environment verification and generates a report

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ResultsDir = Join-Path -Path $ScriptDir -ChildPath "results"
$Timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$ResultsFile = Join-Path -Path $ResultsDir -ChildPath "environment_verification_$Timestamp.log"

# Make sure results directory exists
if (-not (Test-Path -Path $ResultsDir)) {
    New-Item -ItemType Directory -Path $ResultsDir | Out-Null
}

Write-Host "Starting environment verification at $(Get-Date)"
Write-Host "Results will be saved to $ResultsFile"

# Run the verification script with verbose output
$VerificationScript = Join-Path -Path $ScriptDir -ChildPath "environment_verification.py"
$Output = python $VerificationScript --verbose
$ExitCode = $LASTEXITCODE

# Save output to file
$Output | Out-File -FilePath $ResultsFile -Encoding utf8

# Display output 
$Output

# Check the exit code
if ($ExitCode -eq 0) {
    Write-Host "Environment verification PASSED! Ready for testing." -ForegroundColor Green
    Add-Content -Path $ResultsFile -Value "Environment verification PASSED. Ready for testing."
    
    # Create a status file to indicate passage
    "PASSED" | Out-File -FilePath (Join-Path -Path $ResultsDir -ChildPath "environment_status.txt") -Encoding utf8
    exit 0
} else {
    Write-Host "Environment verification FAILED. See log for details." -ForegroundColor Red
    Add-Content -Path $ResultsFile -Value "Environment verification FAILED. See above for details."
    
    # Create a status file to indicate failure
    "FAILED" | Out-File -FilePath (Join-Path -Path $ResultsDir -ChildPath "environment_status.txt") -Encoding utf8
    exit 1
} 