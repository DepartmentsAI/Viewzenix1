#!/bin/bash
echo "================================================"
echo "Starting Viewzenix1 Backend API Server"
echo "================================================"

# Set the current directory to the repo root
cd "$(dirname "$0")/.."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found in PATH"
    echo "Please install Python3 and ensure it's added to your PATH"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found in $(pwd)"
    echo "Creating a default .env file with required settings..."
    
    cat > .env << EOL
# Flask Application Settings
FLASK_APP=src/backend/app.py
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000
# Alpaca API Credentials
APCA_API_KEY_ID=PKG1F8EEMI2HWAFFWSD7
APCA_API_SECRET_KEY=PKG1F8EEMI2HWAFFWSD7
APCA_API_BASE_URL=https://paper-api.alpaca.markets/v2
EOL
    
    echo "Created .env file with default settings"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

echo "Validating environment setup..."
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'Environment loaded: FLASK_APP={os.environ.get(\"FLASK_APP\", \"Not set\")}'); print(f'Alpaca API Key: {os.environ.get(\"APCA_API_KEY_ID\", \"Not set\")[:5]}...')"

echo "Validating Alpaca API credentials..."
python3 src/backend/utils/alpaca_validator.py

echo "Starting backend API server..."
echo "Server output will be logged to logs/backend.log"
echo "Press Ctrl+C to stop the server"
python3 src/backend/run.py 2>&1 | tee logs/backend.log 