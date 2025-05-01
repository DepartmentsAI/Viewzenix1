"""
Webhook API Blueprint

This module defines the webhook endpoint for receiving TradingView alerts
and validates the JSON payload against the expected schema.
"""
import json
import logging
from flask import Blueprint, request, jsonify, current_app
from jsonschema import validate, ValidationError

from src.backend.services.order_engine import OrderEngine

# Create blueprint
webhook_bp = Blueprint('webhook', __name__)

# Logger for this module
logger = logging.getLogger(__name__)

# TradingView alert JSON schema
TRADINGVIEW_SCHEMA = {
    "type": "object",
    "required": [
        "symbol",
        "strategy_order_id",
        "strategy_order_action",
        "strategy_order_price",
        "time"
    ],
    "properties": {
        "symbol": {"type": "string"},
        "strategy_order_id": {
            "type": "string",
            "enum": ["long", "sell"]
        },
        "strategy_order_action": {
            "type": "string",
            "enum": ["buy", "sell"]
        },
        "strategy_order_contracts": {"type": "number"},
        "strategy_order_price": {"type": "number"},
        "strategy_order_comment": {"type": "string"},
        "time": {"type": "number"}
    },
    "additionalProperties": False
}

# Create an instance of the OrderEngine
order_engine = OrderEngine()

@webhook_bp.route('/webhook', methods=['POST'])
def receive_webhook():
    """
    Endpoint to receive TradingView webhook alerts.
    
    Validates the JSON payload against the expected schema and returns
    appropriate HTTP status codes.
    
    Returns:
        tuple: JSON response and HTTP status code
    """
    # Log the incoming request
    logger.info(f"Received webhook request: {request.remote_addr}")
    
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
    
    # Validate against schema
    try:
        validate(instance=payload, schema=TRADINGVIEW_SCHEMA)
    except ValidationError as e:
        logger.warning(f"Schema validation error: {str(e)}")
        return jsonify({
            "error": "Invalid payload schema",
            "details": str(e)
        }), 400
    
    # Process the webhook using the OrderEngine
    try:
        # Use the OrderEngine to process the webhook data
        result = order_engine.process_webhook_data(payload)
        
        # Log the result
        logger.info(f"Webhook processed: {result}")
        
        # Return the result
        if result.get('status') == 'success':
            return jsonify(result), 200
        elif result.get('status') == 'warning':
            return jsonify(result), 200  # Still return 200 for warnings
        else:
            return jsonify(result), 400  # Return 400 for errors
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "Error processing webhook",
            "details": str(e)
        }), 500

@webhook_bp.route('/webhook/status', methods=['GET'])
def webhook_status():
    """
    Endpoint to check webhook service status.
    
    Returns:
        tuple: JSON response with service status and HTTP status code
    """
    return jsonify({
        "status": "active",
        "service": "TradingView Webhook Receiver",
        "version": "1.0.0"
    }), 200 