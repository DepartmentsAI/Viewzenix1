#!/bin/bash
# Shell script to start the Viewzenix1 frontend application on macOS and Linux

# Set text formatting
BOLD="\033[1m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
RESET="\033[0m"

# Display header
echo -e "${BOLD}====== Viewzenix1 Frontend Startup (macOS/Linux) ======${RESET}"

# Check if .env file exists
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env file found${RESET}"
else
    echo -e "${YELLOW}⚠ No .env file found, using default settings${RESET}"
fi

# Check for Node.js installation
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js not found. Please install Node.js 14 or newer${RESET}"
    exit 1
fi

# Display Node.js version
NODE_VERSION=$(node -v)
echo -e "${GREEN}✓ Node.js detected: $NODE_VERSION${RESET}"

# Check for npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm not found. Please install npm${RESET}"
    exit 1
fi

# Display npm version
NPM_VERSION=$(npm -v)
echo -e "${GREEN}✓ npm detected: $NPM_VERSION${RESET}"

# Check if port 3000 is already in use
if command -v lsof &> /dev/null; then
    PORT_CHECK=$(lsof -i:3000 -t)
    if [ ! -z "$PORT_CHECK" ]; then
        echo -e "${YELLOW}⚠ Port 3000 is already in use. You may encounter issues starting the application.${RESET}"
        echo -e "${YELLOW}  Consider adjusting the PORT in .env file or closing the application using that port.${RESET}"
    fi
elif command -v netstat &> /dev/null; then
    PORT_CHECK=$(netstat -tuln | grep ":3000")
    if [ ! -z "$PORT_CHECK" ]; then
        echo -e "${YELLOW}⚠ Port 3000 is already in use. You may encounter issues starting the application.${RESET}"
        echo -e "${YELLOW}  Consider adjusting the PORT in .env file or closing the application using that port.${RESET}"
    fi
fi

# Check for dependencies
echo -e "Checking dependencies..."
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies (this may take a few minutes)...${RESET}"
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to install dependencies${RESET}"
        exit 1
    fi
    echo -e "${GREEN}✓ Dependencies installed successfully${RESET}"
else
    echo -e "${GREEN}✓ Dependencies already installed${RESET}"
fi

# Make script executable
chmod +x "$0"

# Start the application
echo -e "${GREEN}Starting Viewzenix1 Frontend...${RESET}"
npm start

# Script end
echo -e "${YELLOW}Frontend server has stopped.${RESET}" 