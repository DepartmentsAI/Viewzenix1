#!/bin/bash
# Viewzenix1 Backend API Startup Script for Unix/Linux/MacOS
# 
# Usage:
#    ./start_backend.sh [--prod|--dev] [--port=PORT]
#
# Options:
#    --prod        Start in production mode
#    --dev         Start in development mode (default)
#    --port=PORT   Specify port to listen on (default: 5000)
#    --help        Show this help message

# Default configuration
MODE="development"
PORT=5000
HOST="0.0.0.0"
WORKERS=4

# Parse command line arguments
for arg in "$@"; do
  case $arg in
    --prod)
      MODE="production"
      shift
      ;;
    --dev)
      MODE="development"
      shift
      ;;
    --port=*)
      PORT="${arg#*=}"
      shift
      ;;
    --help)
      echo "Viewzenix1 Backend API Startup Script"
      echo ""
      echo "Usage:"
      echo "   ./start_backend.sh [--prod|--dev] [--port=PORT]"
      echo ""
      echo "Options:"
      echo "   --prod        Start in production mode"
      echo "   --dev         Start in development mode (default)"
      echo "   --port=PORT   Specify port to listen on (default: 5000)"
      echo "   --help        Show this help message"
      exit 0
      ;;
    *)
      # Unknown option
      echo "Unknown option: $arg"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Set working directory to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT" || { echo "Error: Could not navigate to project root"; exit 1; }

# Check for virtual environment
if [ -d ".venv" ]; then
  echo "Activating virtual environment..."
  source .venv/bin/activate || { echo "Error: Could not activate virtual environment"; exit 1; }
fi

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
  echo "Loading environment variables from .env file..."
  set -a
  source .env
  set +a
else
  echo "Warning: No .env file found. Using default environment variables."
  # Set default environment variables if not already set
  export FLASK_APP=${FLASK_APP:-src/backend/app.py}
  export FLASK_ENV=${FLASK_ENV:-$MODE}
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Check Flask app file exists
if [ ! -f "$FLASK_APP" ]; then
  echo "Error: Flask application file not found at $FLASK_APP"
  exit 1
fi

# Run environment check script if it exists
if [ -f "scripts/backend_environment_check.py" ]; then
  echo "Running environment check..."
  python scripts/backend_environment_check.py || { echo "Warning: Environment check reported issues"; }
fi

# Start server
echo "Starting Viewzenix1 Backend API server in $MODE mode on $HOST:$PORT..."

if [ "$MODE" = "production" ]; then
  # Production mode uses gunicorn
  echo "Starting with gunicorn (production mode)..."
  if command -v gunicorn &> /dev/null; then
    gunicorn --bind $HOST:$PORT --workers $WORKERS "src.backend.app:create_app()" \
      --access-logfile logs/access.log \
      --error-logfile logs/error.log \
      --capture-output
  else
    echo "Error: gunicorn not found. Install with 'pip install gunicorn'"
    exit 1
  fi
else
  # Development mode uses Flask's built-in server
  echo "Starting with Flask development server..."
  export FLASK_ENV=development
  export FLASK_DEBUG=1
  flask run --host=$HOST --port=$PORT 