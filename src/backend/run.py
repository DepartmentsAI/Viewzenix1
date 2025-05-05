"""
Run script for the Flask application.

This module provides a simple entry point to run the Flask application.
"""
import os
import logging
from pathlib import Path

# Configure basic logging before importing app
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger("backend.startup")

# Ensure we're in the correct directory context
os.chdir(Path(__file__).parent.parent.parent)
logger.info(f"Working directory: {os.getcwd()}")

# Check if .env file exists
env_file = '.env'
if os.path.exists(env_file):
    logger.info(f"Found .env file at {os.path.abspath(env_file)}")
else:
    logger.warning(f"No .env file found at {os.path.abspath(env_file)}")
    
# Import the app after directory setup
from src.backend.app import create_app

if __name__ == '__main__':
    logger.info("Initializing Flask application...")
    app = create_app()
    
    # Get port from environment variable with fallback to 5000
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting server on port {port}")
    
    # Get debug setting from environment with app config fallback
    debug = os.environ.get('FLASK_DEBUG', str(app.config.get('DEBUG', False))).lower() in ('true', '1', 't')
    
    # Log all registered routes
    logger.info("Registered routes:")
    for rule in app.url_map.iter_rules():
        logger.info(f"Route: {rule.endpoint} - {rule.rule} - {rule.methods}")
    
    # Start the server
    logger.info(f"API server starting in {'debug' if debug else 'production'} mode")
    app.run(
        host='0.0.0.0',  # Listen on all network interfaces
        port=port,
        debug=debug
    ) 