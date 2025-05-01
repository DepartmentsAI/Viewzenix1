"""
Run script for the Flask application.

This module provides a simple entry point to run the Flask application.
"""
import os
from src.backend.app import create_app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config.get('DEBUG', False)
    ) 