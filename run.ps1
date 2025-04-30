# PowerShell script to start the Flask application

# Set environment variables from .env file if it exists
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^#=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

# Set default values if not provided in environment
if (-not $env:FLASK_APP) {
    $env:FLASK_APP = "src.backend.app:create_app"
}
if (-not $env:FLASK_ENV) {
    $env:FLASK_ENV = "development"
}
if (-not $env:PORT) {
    $env:PORT = 5000
}

# Create log directory if it doesn't exist
if (-not (Test-Path "logs")) {
    New-Item -Path "logs" -ItemType Directory
}

# Run the application
python -m src.backend.run 