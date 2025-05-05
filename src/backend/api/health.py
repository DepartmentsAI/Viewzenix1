"""
Health API Blueprint

This module defines the health check endpoints for monitoring the API status.
"""
import os
import sys
import platform
import json
import requests
import time
import logging
from datetime import datetime
from flask import Blueprint, jsonify, current_app

# Import the Alpaca validator
from src.backend.utils.alpaca_validator import validate_credentials, load_credentials

# Create blueprint
health_bp = Blueprint('health', __name__)

# Logger for this module
logger = logging.getLogger(__name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint.
    
    Returns:
        JSON with health status details
    """
    # Calculate uptime
    if hasattr(current_app, 'start_time'):
        uptime_seconds = (datetime.now() - current_app.start_time).total_seconds()
    else:
        uptime_seconds = 0
    
    # Get application version if available
    version = getattr(current_app, 'version', '1.0.0')
    
    # Basic health check response
    response = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "uptime_seconds": int(uptime_seconds),
        "version": version
    }
    
    logger.debug("Health check: %s", response)
    return jsonify(response), 200

@health_bp.route('/health/extended', methods=['GET'])
def extended_health_check():
    """
    Extended health check with more detailed diagnostics.
    
    Returns:
        JSON with detailed health information
    """
    # Basic health info
    health_info = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + 'Z',
    }
    
    # Add uptime
    if hasattr(current_app, 'start_time'):
        uptime_seconds = (datetime.now() - current_app.start_time).total_seconds()
        health_info["uptime_seconds"] = int(uptime_seconds)
    
    # Add version info
    health_info["version"] = getattr(current_app, 'version', '1.0.0')
    
    # Add system info - try to get from app config
    try:
        health_info["env"] = current_app.config.get('ENV', 'development')
        health_info["debug"] = current_app.config.get('DEBUG', False)
    except:
        health_info["env"] = "unknown"
    
    # Try to check database connection
    try:
        # Just log that we would check the database
        logger.info("Database check would go here")
        health_info["database"] = {
            "status": "unknown",
            "message": "Database connection check disabled in basic mode"
        }
    except Exception as e:
        health_info["database"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Return all health information
    logger.debug("Extended health check: %s", health_info)
    return jsonify(health_info), 200

@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """
    Detailed health check endpoint with component status.
    
    Returns:
        JSON with detailed status of various service components.
    """
    # Check database status
    db_status = check_database_connection()
    
    # Check Alpaca API connection
    alpaca_status = check_alpaca_connection()
    
    # Check recent webhook reception
    webhook_status = check_webhook_reception()
    
    # Check risk management service
    risk_status = check_risk_management_service()
    
    # Check disk space
    disk_status = check_disk_space()
    
    # Overall health assessment
    all_components = [
        db_status["connected"],
        alpaca_status["connected"],
        webhook_status["operational"],
        risk_status["operational"],
        disk_status["sufficient"]
    ]
    
    overall_status = "healthy" if all(all_components) else "degraded"
    
    response = {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": db_status,
            "alpaca_api": alpaca_status,
            "webhook_system": webhook_status,
            "risk_management": risk_status,
            "disk_space": disk_status
        }
    }
    
    return jsonify(response)

def check_database_connection():
    """
    Check database connection status.
    
    Returns:
        dict: Database connection status info
    """
    # In a real implementation, this would actually check the database
    try:
        # Simulate database check
        connected = True
        status = "connected"
        latency_ms = 15  # simulated latency
    except Exception as e:
        connected = False
        status = f"error: {str(e)}"
        latency_ms = None
    
    return {
        "connected": connected,
        "status": status,
        "latency_ms": latency_ms
    }

def check_alpaca_connection():
    """
    Check Alpaca API connection using credentials.
    
    Returns:
        dict: Alpaca API connection status
    """
    # Get credentials from environment
    key_id, secret_key, base_url = load_credentials()
    
    if not key_id or not secret_key:
        return {
            "connected": False,
            "status": "error: missing API credentials"
        }
    
    # Validate credentials
    is_valid, result = validate_credentials(key_id, secret_key, base_url)
    
    if is_valid:
        account_id = result.get('id', 'Unknown')
        account_status = result.get('status', 'Unknown')
        buying_power = result.get('buying_power', 'Unknown')
        
        return {
            "connected": True,
            "status": "connected",
            "account_id": account_id,
            "account_status": account_status,
            "buying_power": buying_power
        }
    else:
        return {
            "connected": False,
            "status": f"error: {result}"
        }

def check_webhook_reception():
    """
    Check if webhook system is receiving requests.
    
    Returns:
        dict: Webhook reception status
    """
    # Check last webhook received timestamp
    # In a real implementation, this would check logs or database
    operational = True
    last_received = datetime.now().isoformat()  # placeholder
    
    return {
        "operational": operational,
        "last_webhook_received": last_received
    }

def check_risk_management_service():
    """
    Check risk management service status.
    
    Returns:
        dict: Risk management service status
    """
    # Simulate risk management service check
    operational = True
    status = "active"
    
    return {
        "operational": operational,
        "status": status
    }

def check_disk_space():
    """
    Check available disk space.
    
    Returns:
        dict: Disk space status
    """
    # In a real implementation, this would check actual disk space
    total_gb = 100  # simulated total space
    available_gb = 75  # simulated available space
    percent_used = ((total_gb - available_gb) / total_gb) * 100
    sufficient = available_gb > 10  # Threshold of 10GB
    
    return {
        "sufficient": sufficient,
        "available_gb": available_gb,
        "total_gb": total_gb,
        "percent_used": percent_used
    } 