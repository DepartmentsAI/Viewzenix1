import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

class IntegrationLogger:
    """Logger for integration operations.
    
    Handles both machine-readable (JSON) and human-readable logging.
    """
    
    def __init__(self, 
                 log_dir: str = "logs", 
                 json_log_file: str = "logs.jsonl", 
                 activity_log_file: str = "activity.log"):
        """Initialize the integration logger.
        
        Args:
            log_dir: Directory for log files
            json_log_file: Filename for machine-readable logs
            activity_log_file: Filename for human-readable logs
        """
        self.log_dir = log_dir
        self.json_log_path = os.path.join(log_dir, json_log_file)
        self.activity_log_path = os.path.join(log_dir, activity_log_file)
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup Python logger for activity.log
        self.logger = logging.getLogger("integration")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            # Add file handler for activity.log
            file_handler = logging.FileHandler(self.activity_log_path)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            # Add console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def log_info(self, log_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log informational messages.
        
        Args:
            log_type: Type of information being logged
            message: Informational message
            details: Optional additional details
        """
        self._log_json_event(
            event_type="info",
            data={
                "log_type": log_type,
                "message": message,
                "details": details or {}
            }
        )
        self.logger.info(f"{log_type}: {message}")
    
    def log_webhook(self, payload: Dict[str, Any], status_code: int, response: Dict[str, Any]) -> None:
        """Log incoming webhook request and response.
        
        Args:
            payload: The webhook payload
            status_code: HTTP status code of the response
            response: The response data
        """
        self._log_json_event(
            event_type="webhook",
            data={
                "payload": payload,
                "status_code": status_code,
                "response": response
            }
        )
        self.logger.info(f"Webhook received: {payload.get('symbol', 'unknown')} - Status: {status_code}")
    
    def log_broker_request(self, broker: str, endpoint: str, method: str, 
                          params: Dict[str, Any], 
                          order_id: Optional[str] = None) -> None:
        """Log outgoing broker API request.
        
        Args:
            broker: Name of the broker (e.g., 'alpaca')
            endpoint: API endpoint
            method: HTTP method (GET, POST, etc.)
            params: Request parameters
            order_id: Optional order ID for tracking
        """
        self._log_json_event(
            event_type="broker_request",
            data={
                "broker": broker,
                "endpoint": endpoint,
                "method": method,
                "params": params,
                "order_id": order_id
            }
        )
        self.logger.info(f"Broker request: {broker} - {method} {endpoint} - Order ID: {order_id}")
    
    def log_broker_response(self, broker: str, endpoint: str, 
                           status_code: int, response_data: Dict[str, Any],
                           order_id: Optional[str] = None) -> None:
        """Log broker API response.
        
        Args:
            broker: Name of the broker
            endpoint: API endpoint
            status_code: HTTP status code
            response_data: Response data from broker
            order_id: Optional order ID for tracking
        """
        # Remove sensitive data from logs
        sanitized_response = self._sanitize_response(response_data)
        
        self._log_json_event(
            event_type="broker_response",
            data={
                "broker": broker,
                "endpoint": endpoint,
                "status_code": status_code,
                "response": sanitized_response,
                "order_id": order_id
            }
        )
        self.logger.info(f"Broker response: {broker} - Status: {status_code} - Order ID: {order_id}")
    
    def log_error(self, error_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log error information.
        
        Args:
            error_type: Type of error
            message: Error message
            details: Optional additional details
        """
        self._log_json_event(
            event_type="error",
            data={
                "error_type": error_type,
                "message": message,
                "details": details or {}
            }
        )
        self.logger.error(f"Error - {error_type}: {message}")
    
    def _log_json_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Write an event to the JSON log file.
        
        Args:
            event_type: Type of event (webhook, broker_request, etc.)
            data: Event data
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            **data
        }
        
        try:
            with open(self.json_log_path, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            # Fallback to console if file writing fails
            print(f"Error writing to log file: {e}")
            print(json.dumps(event))
    
    def _sanitize_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from response data.
        
        Args:
            response_data: Original response data
            
        Returns:
            Dict with sensitive information removed or masked
        """
        if not response_data:
            return {}
            
        # Create a copy to avoid modifying the original
        sanitized = response_data.copy()
        
        # List of sensitive fields to mask
        sensitive_fields = ['key_id', 'secret_key', 'token', 'password', 'secret']
        
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = "******"
        
        return sanitized 