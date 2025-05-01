"""
Risk Management API Blueprint

This module defines the risk management endpoints for configuring
risk parameters and monitoring risk metrics.
"""
import logging
from flask import Blueprint, request, jsonify, current_app
from jsonschema import validate, ValidationError

from src.backend.services.risk_manager import RiskManager

# Create blueprint
risk_bp = Blueprint('risk', __name__)

# Logger for this module
logger = logging.getLogger(__name__)

# Create an instance of the RiskManager
risk_manager = RiskManager()

# Risk parameters JSON schema
RISK_PARAMETERS_SCHEMA = {
    "type": "object",
    "properties": {
        "stop_loss_percent": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
        },
        "take_profit_percent": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
        },
        "max_position_size_percent": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
        },
        "max_daily_drawdown_percent": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
        },
        "max_open_positions": {
            "type": "integer",
            "minimum": 1
        },
        "orphaned_order_age_hours": {
            "type": "integer",
            "minimum": 1
        }
    },
    "additionalProperties": False
}

@risk_bp.route('/risk/parameters', methods=['GET'])
def get_risk_parameters():
    """
    Get current risk parameters.
    
    Returns:
        JSON response with current risk parameters
    """
    try:
        parameters = risk_manager.get_risk_parameters()
        return jsonify({
            "status": "success",
            "parameters": parameters
        }), 200
    except Exception as e:
        logger.exception("Error getting risk parameters: %s", str(e))
        return jsonify({
            "status": "error",
            "message": f"Error getting risk parameters: {str(e)}"
        }), 500

@risk_bp.route('/risk/parameters', methods=['PUT'])
def update_risk_parameters():
    """
    Update risk parameters.
    
    Returns:
        JSON response with updated risk parameters
    """
    # Check if content type is JSON
    if not request.is_json:
        logger.warning("Invalid content type, expected JSON")
        return jsonify({"error": "Content type must be application/json"}), 415
    
    # Get JSON data
    try:
        payload = request.get_json()
        logger.debug(f"Risk parameters update request: {payload}")
    except Exception as e:
        logger.error(f"Error parsing JSON: {str(e)}")
        return jsonify({"error": "Invalid JSON format"}), 400
    
    # Validate against schema
    try:
        validate(instance=payload, schema=RISK_PARAMETERS_SCHEMA)
    except ValidationError as e:
        logger.warning(f"Schema validation error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Invalid payload schema",
            "details": str(e)
        }), 400
    
    try:
        # Update risk parameters
        updated_params = risk_manager.update_risk_parameters(payload)
        
        return jsonify({
            "status": "success",
            "message": "Risk parameters updated successfully",
            "parameters": updated_params
        }), 200
    except Exception as e:
        logger.exception("Error updating risk parameters: %s", str(e))
        return jsonify({
            "status": "error",
            "message": f"Error updating risk parameters: {str(e)}"
        }), 500

@risk_bp.route('/risk/metrics', methods=['GET'])
def get_risk_metrics():
    """
    Get current risk metrics.
    
    Returns:
        JSON response with current risk metrics
    """
    try:
        metrics = risk_manager.get_risk_metrics()
        return jsonify({
            "status": "success",
            "metrics": metrics
        }), 200
    except Exception as e:
        logger.exception("Error getting risk metrics: %s", str(e))
        return jsonify({
            "status": "error",
            "message": f"Error getting risk metrics: {str(e)}"
        }), 500

@risk_bp.route('/risk/cleanup', methods=['POST'])
def cleanup_orphaned_orders():
    """
    Trigger cleanup of orphaned orders.
    
    Returns:
        JSON response with cleanup results
    """
    try:
        results = risk_manager.cleanup_orphaned_orders()
        return jsonify({
            "status": "success",
            "results": results
        }), 200
    except Exception as e:
        logger.exception("Error cleaning up orphaned orders: %s", str(e))
        return jsonify({
            "status": "error",
            "message": f"Error cleaning up orphaned orders: {str(e)}"
        }), 500

@risk_bp.route('/risk/webhook', methods=['POST'])
def process_webhook_with_risk():
    """
    Process a webhook with risk management applied.
    
    Returns:
        JSON response with order execution results
    """
    # Check if content type is JSON
    if not request.is_json:
        logger.warning("Invalid content type, expected JSON")
        return jsonify({"error": "Content type must be application/json"}), 415
    
    # Get JSON data
    try:
        payload = request.get_json()
        logger.debug(f"Webhook payload: {payload}")
    except Exception as e:
        logger.error(f"Error parsing JSON: {str(e)}")
        return jsonify({"error": "Invalid JSON format"}), 400
    
    try:
        # Process webhook with risk management
        result = risk_manager.process_order_with_risk_management(payload)
        
        # Return appropriate status based on result
        if result.get('status') == 'success':
            return jsonify(result), 200
        elif result.get('status') == 'rejected':
            return jsonify(result), 200  # Still return 200 for rejected orders
        else:
            return jsonify(result), 400  # Return 400 for errors
    except Exception as e:
        logger.exception("Error processing webhook with risk management: %s", str(e))
        return jsonify({
            "status": "error",
            "message": "Error processing webhook with risk management",
            "details": str(e)
        }), 500 