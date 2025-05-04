#!/bin/bash
# Environment Verification Script
# Runs the environment verification and generates a report

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RESULTS_DIR="$SCRIPT_DIR/results"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
RESULTS_FILE="$RESULTS_DIR/environment_verification_$TIMESTAMP.log"

# Make sure results directory exists
mkdir -p "$RESULTS_DIR"

echo "Starting environment verification at $(date)"
echo "Results will be saved to $RESULTS_FILE"

# Run the verification script with verbose output
python "$SCRIPT_DIR/environment_verification.py" --verbose | tee "$RESULTS_FILE"

# Check the exit code
if [ ${PIPESTATUS[0]} -eq 0 ]; then
  echo -e "\033[92mEnvironment verification PASSED! Ready for testing.\033[0m"
  echo "Environment verification PASSED. Ready for testing." >> "$RESULTS_FILE"
  
  # Create a status file to indicate passage
  echo "PASSED" > "$RESULTS_DIR/environment_status.txt"
  exit 0
else
  echo -e "\033[91mEnvironment verification FAILED. See log for details.\033[0m"
  echo "Environment verification FAILED. See above for details." >> "$RESULTS_FILE"
  
  # Create a status file to indicate failure
  echo "FAILED" > "$RESULTS_DIR/environment_status.txt"
  exit 1
fi 