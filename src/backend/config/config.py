"""
Configuration module for the Flask application.

This module provides functions to configure the Flask application
based on environment variables and configuration files.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Base configuration class."""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///default.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', None)

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    # Production-specific configurations
    pass

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def configure_app(app, config_name=None):
    """
    Configure the Flask application.
    
    Args:
        app (Flask): The Flask application instance.
        config_name (str, optional): The configuration environment to use.
            Defaults to the value of FLASK_ENV environment variable or 'default'.
    """
    # Determine which configuration to use
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Optional: Load additional configuration from instance folder
    # app.config.from_pyfile('config.py', silent=True)
    
    app.config['ENV'] = config_name 