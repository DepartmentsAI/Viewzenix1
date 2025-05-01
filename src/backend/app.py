"""
Trading Webhook Platform - Flask Application

This module initializes the Flask application with its configuration
and registers all blueprints and extensions.
"""
import os
import logging
from flask import Flask

from src.backend.api.webhook import webhook_bp
from src.backend.api.risk import risk_bp
from src.backend.config.config import configure_app

def create_app(config_name=None):
    """
    Factory function to create and configure the Flask application.
    
    Args:
        config_name (str, optional): The configuration environment to use.
            Defaults to the value of FLASK_ENV environment variable or 'development'.
    
    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)
    
    # Configure app from environment variables and config files
    configure_app(app, config_name)
    
    # Configure logging
    configure_logging(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def configure_logging(app):
    """Configure application logging."""
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    
    # Configure basic logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add file handler if configured
    log_file = app.config.get('LOG_FILE')
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        app.logger.addHandler(file_handler)
    
    app.logger.info('Logging configured')

def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(webhook_bp, url_prefix='/api')
    app.register_blueprint(risk_bp, url_prefix='/api')
    
    app.logger.info('Blueprints registered')

def register_error_handlers(app):
    """Register error handlers."""
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found"}, 404
    
    @app.errorhandler(500)
    def server_error(error):
        app.logger.error(f"Server error: {error}")
        return {"error": "Internal server error"}, 500
    
    app.logger.info('Error handlers registered')

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 