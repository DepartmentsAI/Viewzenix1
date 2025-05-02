"""
Health check API endpoint for the Viewzenix1 backend.
Provides system status information and monitoring capabilities.
"""

from flask import Blueprint, jsonify
from datetime import datetime
import psutil
import os
import sys

# Initialize blueprint
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    API endpoint for checking backend health status.
    Returns system information, memory usage, and component statuses.
    """
    try:
        # Get system info
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Check component status
        db_status = check_db_connection()
        
        return jsonify({
            'status': 'operational',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',  # Should match application version
            'environment': os.environ.get('FLASK_ENV', 'development'),
            'system': {
                'python_version': sys.version,
                'memory_usage_percent': memory.percent,
                'disk_usage_percent': disk.percent
            },
            'components': {
                'database': db_status,
                'api': 'available',
            }
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health():
    """
    Detailed health check endpoint for system administrators.
    Provides comprehensive system diagnostics.
    """
    try:
        # System information
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disk = psutil.disk_usage('/')
        cpu_info = psutil.cpu_percent(interval=1, percpu=True)
        
        # Component checks
        db_status = check_db_connection()
        
        return jsonify({
            'status': 'operational',
            'timestamp': datetime.utcnow().isoformat(),
            'system': {
                'cpu': {
                    'usage_percent': cpu_info,
                    'cores': psutil.cpu_count(logical=True)
                },
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'used_percent': memory.percent
                },
                'swap': {
                    'total_gb': round(swap.total / (1024**3), 2),
                    'used_percent': swap.percent
                },
                'disk': {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'used_percent': disk.percent
                }
            },
            'components': {
                'database': db_status,
                'api': {
                    'status': 'available',
                    'uptime': get_uptime()
                }
            },
            'environment': {
                'python_version': sys.version,
                'environment': os.environ.get('FLASK_ENV', 'development'),
                'host': os.environ.get('HOSTNAME', 'unknown')
            }
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

def check_db_connection():
    """
    Check database connection status.
    Returns status information or error message.
    """
    try:
        # Placeholder for actual database connection check
        # In a real implementation, you would import your db module
        # and perform an actual connection test
        
        # from database import db_session
        # db_session.execute("SELECT 1")
        
        return {
            'status': 'connected',
            'latency_ms': 15  # Placeholder, should measure actual latency
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

def get_uptime():
    """Get application uptime"""
    # This is a placeholder implementation
    # In a real system, you'd track the application start time
    return "1 day, 3 hours"  # Placeholder 