#!/bin/bash
# Environment Verification Script
# Runs the environment verification and reports the results

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RESULTS_DIR="$SCRIPT_DIR/../../e2e/results"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
RESULTS_FILE="$RESULTS_DIR/environment_verification_$TIMESTAMP.log"

# Create results directory if it doesn't exist
mkdir -p "$RESULTS_DIR"

echo "Starting environment verification at $(date)"
echo "Results will be saved to $RESULTS_FILE"

# Run the verification script with verbose output
python "$SCRIPT_DIR/environment_verification.py" --verbose | tee "$RESULTS_FILE"

# Check the exit code
if [ ${PIPESTATUS[0]} -eq 0 ]; then
  echo -e "\033[92mEnvironment verification PASSED! Ready for testing.\033[0m"
  echo "Environment verification PASSED at $(date)" >> "$RESULTS_FILE"
  exit 0
else
  echo -e "\033[91mEnvironment verification FAILED! See details above.\033[0m"
  echo "Environment verification FAILED at $(date)" >> "$RESULTS_FILE"
  exit 1
fi 