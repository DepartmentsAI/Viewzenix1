#!/bin/bash
# Script to start the Flask application

# Export environment variables from .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Set default values if not provided in environment
export FLASK_APP=${FLASK_APP:-"src.backend.app:create_app"}
export FLASK_ENV=${FLASK_ENV:-"development"}
export PORT=${PORT:-5000}

# Create log directory if it doesn't exist
mkdir -p logs

# Run the application
python -m src.backend.run 