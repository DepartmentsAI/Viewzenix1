"""
Risk Management API Blueprint

This module defines the API endpoints for risk management features.
"""
import logging
import json
from flask import Blueprint, request, jsonify, current_app
from src.backend.services.risk_manager import RiskManager
from src.backend.models.risk_models import RiskParameters

logger = logging.getLogger(__name__)

# Create Blueprint
risk_bp = Blueprint('risk', __name__)

# Initialize risk manager (will be properly initialized when app starts)
risk_manager = None

@risk_bp.before_app_first_request
def initialize_risk_manager():
    """Initialize the RiskManager before first request."""
    global risk_manager
    risk_manager = RiskManager()
    logger.info("RiskManager initialized in API blueprint")

@risk_bp.route('/risk/parameters', methods=['GET'])
def get_risk_parameters():
    """
    Get current risk parameters.
    
    Returns:
        JSON with current risk parameters
    """
    try:
        parameters = risk_manager.get_risk_parameters()
        return jsonify({
            'status': 'success',
            'parameters': parameters
        })
    except Exception as e:
        logger.exception("Error getting risk parameters: %s", str(e))
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@risk_bp.route('/risk/parameters', methods=['PUT'])
def update_risk_parameters():
    """
    Update risk parameters.
    
    Returns:
        JSON with updated risk parameters
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Validate the data schema
        try:
            # Try constructing a RiskParameters object to validate
            RiskParameters.from_dict(data)
        except Exception as validation_error:
            return jsonify({
                'status': 'error',
                'message': f'Invalid parameter schema: {str(validation_error)}'
            }), 400
        
        updated_params = risk_manager.update_risk_parameters(data)
        return jsonify({
            'status': 'success',
            'parameters': updated_params
        })
    except Exception as e:
        logger.exception("Error updating risk parameters: %s", str(e))
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@risk_bp.route('/risk/metrics', methods=['GET'])
def get_risk_metrics():
    """
    Get current risk metrics.
    
    Returns:
        JSON with current risk metrics
    """
    try:
        metrics = risk_manager.get_risk_metrics()
        return jsonify({
            'status': 'success',
            'metrics': metrics
        })
    except Exception as e:
        logger.exception("Error getting risk metrics: %s", str(e))
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@risk_bp.route('/risk/webhook', methods=['POST'])
def process_webhook_with_risk():
    """
    Process a webhook with risk management applied.
    
    Returns:
        JSON with order results and risk management information
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        result = risk_manager.process_order_with_risk_management(data)
        return jsonify(result)
    except Exception as e:
        logger.exception("Error processing webhook with risk management: %s", str(e))
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@risk_bp.route('/risk/cleanup', methods=['POST'])
def cleanup_orphaned_orders():
    """
    Manually trigger cleanup of orphaned orders.
    
    Returns:
        JSON with cleanup results
    """
    try:
        result = risk_manager.cleanup_orphaned_orders()
        return jsonify(result)
    except Exception as e:
        logger.exception("Error during manual cleanup: %s", str(e))
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 