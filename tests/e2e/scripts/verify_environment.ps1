# Environment Verification Script for Windows
# Runs the environment verification and reports the results

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ResultsDir = Join-Path -Path $ScriptDir -ChildPath "..\..\e2e\results"
$Timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$ResultsFile = Join-Path -Path $ResultsDir -ChildPath "environment_verification_$Timestamp.log"

# Create results directory if it doesn't exist
if (-not (Test-Path -Path $ResultsDir)) {
    New-Item -ItemType Directory -Path $ResultsDir | Out-Null
}

Write-Host "Starting environment verification at $(Get-Date)"
Write-Host "Results will be saved to $ResultsFile"

# Run the verification script with verbose output
$VerificationScript = Join-Path -Path $ScriptDir -ChildPath "environment_verification.py"
$Output = & python $VerificationScript --verbose
$ExitCode = $LASTEXITCODE

# Save output to file
$Output | Out-File -FilePath $ResultsFile

# Display output
$Output | ForEach-Object { Write-Host $_ }

# Check the exit code
if ($ExitCode -eq 0) {
    Write-Host "Environment verification PASSED! Ready for testing." -ForegroundColor Green
    Add-Content -Path $ResultsFile -Value "Environment verification PASSED at $(Get-Date)"
    exit 0
} else {
    Write-Host "Environment verification FAILED! See details above." -ForegroundColor Red
    Add-Content -Path $ResultsFile -Value "Environment verification FAILED at $(Get-Date)"
    exit 1
} 