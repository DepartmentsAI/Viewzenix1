#!/bin/bash
# Environment verification script for Viewzenix1
# May 10, 2025 - Part of contingency test plan

# Set working directory to script location
cd "$(dirname "$0")"

echo "=================================="
echo "Viewzenix1 Environment Verification"
echo "=================================="
echo "Date: $(date)"
echo "Environment: ${ENV:-development}"
echo "=================================="

# Check if python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if broker config exists or create a default one
if [ ! -f "./broker_config.json" ]; then
    echo "⚠️ WARNING: broker_config.json not found, creating a default one..."
    cat > "./broker_config.json" << EOL
{
    "api_key": "PK_YOUR_API_KEY",
    "api_secret": "YOUR_API_SECRET",
    "paper_trading": true,
    "base_url": "https://paper-api.alpaca.markets"
}
EOL
    echo "✅ Created default broker_config.json (update with real credentials)"
fi

# Check if requests library is installed, install if missing
python3 -c "import requests" 2>/dev/null || {
    echo "⚠️ WARNING: Python 'requests' package not found, installing..."
    pip install requests
    if [ $? -ne 0 ]; then
        echo "❌ ERROR: Failed to install required dependencies"
        exit 1
    fi
}

# Create fixtures directory if it doesn't exist
if [ ! -d "./fixtures" ]; then
    echo "⚠️ WARNING: fixtures directory not found, creating..."
    mkdir -p ./fixtures
fi

# Run the verification script
echo "Starting environment verification..."
python3 environment_verification.py "$@"

# Check the exit code
if [ $? -eq 0 ]; then
    echo "✅ Environment verification PASSED!"
    exit 0
else
    echo "❌ Environment verification FAILED! Check the logs for details."
    exit 1
fi 