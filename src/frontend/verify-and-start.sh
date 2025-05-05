#!/bin/bash
# Viewzenix1 Frontend Verification and Auto-Start

# ANSI color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}Viewzenix1 Frontend Verification and Auto-Start${NC}"
echo -e "${CYAN}==============================================${NC}"
echo ""

# Check if Node.js is installed
if ! command -v node &>/dev/null; then
  echo -e "${RED}Error: Node.js is not installed or not in PATH.${NC}"
  echo -e "${YELLOW}Please install Node.js from https://nodejs.org/${NC}"
  exit 1
fi

NODE_VERSION=$(node -v)
echo -e "${GREEN}Node.js detected: $NODE_VERSION${NC}"

# Make script executable
chmod +x verify-and-start.js 2>/dev/null || true

# Ensure LF line endings on Unix
if [[ "$(uname)" != "MINGW"* ]] && [[ "$(uname)" != "MSYS"* ]] && [[ "$(uname)" != "CYGWIN"* ]]; then
  if grep -q $'\r' verify-and-start.js; then
    echo -e "${YELLOW}Converting CRLF to LF for compatibility...${NC}"
    sed -i 's/\r$//' verify-and-start.js
  fi
fi

# Run the verification and auto-start script
echo -e "${CYAN}Running verification and auto-start script...${NC}"
node verify-and-start.js

# Check if the script failed
if [ $? -ne 0 ]; then
  echo ""
  echo -e "${RED}Error: Frontend verification failed.${NC}"
  echo -e "${YELLOW}Please check the log output above for details.${NC}"
  exit 1
fi

exit 0 