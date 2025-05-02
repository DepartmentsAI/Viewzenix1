"""
Trading Webhook Platform - Flask Application

This module initializes the Flask application with its configuration
and registers all blueprints and extensions.
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask

from src.backend.api.webhook import webhook_bp
from src.backend.api.risk import risk_bp
from src.backend.api.health import health_bp
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
    """
    Configure application logging.
    
    Args:
        app: Flask application instance
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(module)s: %(message)s'
    )
    
    # Configure file handler
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Configure stdout handler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    
    # Add handlers to app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)
    
    # Set root logger level
    logging.getLogger().setLevel(logging.INFO)

def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(webhook_bp, url_prefix='/api')
    app.register_blueprint(risk_bp, url_prefix='/api')
    app.register_blueprint(health_bp, url_prefix='/api')
    
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