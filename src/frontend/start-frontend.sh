#!/bin/bash
# Shell script to start the frontend application
# Usage: ./start-frontend.sh

# Change to the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting Viewzenix1 Frontend Application..."
echo "Current directory: $SCRIPT_DIR"

# Check if node is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed or not in PATH" >&2
    echo "Please install Node.js from https://nodejs.org/" >&2
    exit 1
fi

NODE_VERSION=$(node -v)
echo "Node.js version: $NODE_VERSION"

# Check if node_modules exists
if [ ! -d "node_modules" ] || [ -z "$(ls -A node_modules)" ]; then
    echo "Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "Error installing dependencies. Please check npm error messages." >&2
        exit 1
    fi
fi

# Check for .env file and create if needed
if [ ! -f ".env" ]; then
    echo "Creating default .env file..."
    cat > .env << EOF
REACT_APP_API_URL=http://localhost:5000/api/v1
PORT=3000
BROWSER=none
EOF
fi

# Check if port 3000 is in use
if command -v lsof &> /dev/null; then
    PORT_IN_USE=$(lsof -i:3000 -t)
    if [ -n "$PORT_IN_USE" ]; then
        echo "Warning: Port 3000 is already in use!" >&2
        echo "You may need to terminate existing React processes or use a different port." >&2
        echo "To use a different port, update the PORT value in your .env file." >&2
    fi
else
    echo "Note: 'lsof' command not found, skipping port check."
fi

# Start the React application
echo "Starting frontend development server..."
npm start

# If npm start fails, provide troubleshooting info
if [ $? -ne 0 ]; then
    echo "Failed to start the frontend application." >&2
    echo "Troubleshooting steps:" >&2
    echo "1. Make sure all required packages are installed: npm install" >&2
    echo "2. Check for errors in .env file" >&2
    echo "3. Try clearing the npm cache: npm cache clean --force" >&2
    echo "4. If all else fails, delete node_modules and try again: rm -rf node_modules && npm install" >&2
    exit 1
fi 