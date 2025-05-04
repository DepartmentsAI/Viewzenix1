#!/bin/bash
# Viewzenix1 Backend Startup Script for Linux/macOS
# This script starts the Viewzenix1 backend API service

echo "Starting Viewzenix1 Backend API..."

# Set environment variables if .env file doesn't exist
if [ ! -f "$(dirname "$0")/../.env" ]; then
    echo "No .env file found, using default environment variables"
    export FLASK_APP=src.backend.app
    export FLASK_ENV=development
    export DEBUG=True
    export PORT=5000
else
    echo "Loading environment variables from .env file"
    # Load variables from .env file
    set -a
    source "$(dirname "$0")/../.env"
    set +a
fi

# Create logs directory if it doesn't exist
if [ ! -d "$(dirname "$0")/../logs" ]; then
    echo "Creating logs directory..."
    mkdir -p "$(dirname "$0")/../logs"
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

# Move to project root
cd "$(dirname "$0")/.." || exit

# Check if PostgreSQL is running (if using local PostgreSQL)
if [[ "$DATABASE_URL" == *"localhost"* ]] || [[ "$DATABASE_URL" == *"127.0.0.1"* ]]; then
    echo "Checking if PostgreSQL is running..."
    if command -v pg_isready &> /dev/null; then
        if ! pg_isready -h localhost -q; then
            echo "WARNING: PostgreSQL does not appear to be running. The application may fail to start."
        else
            echo "PostgreSQL is running."
        fi
    fi
fi

# Install required packages if not already installed
echo "Checking required packages..."
python3 -m pip install -r requirements.txt

echo "Starting Backend API server on port $PORT..."
echo "Access the health check endpoint at: http://localhost:$PORT/api/health"

# Check if port is already in use
if command -v lsof &> /dev/null; then
    if lsof -i:$PORT -t &> /dev/null; then
        echo "WARNING: Port $PORT is already in use. The application may fail to start."
        echo "Use 'lsof -i:$PORT' to identify the process and 'kill <PID>' to terminate it."
    fi
fi

# Start the Flask application
python3 -m src.backend.run

echo "If the server failed to start, check the logs directory for error information." 