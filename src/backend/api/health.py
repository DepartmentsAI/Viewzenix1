"""
Health check endpoint for the backend service.
"""
from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)

@health_bp.route('/v1/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the service is running.
    
    Returns:
        dict: Health status information
    """
    return jsonify({
        'status': 'ok',
        'service': 'backend-api',
        'version': '1.0.0'
    }) 