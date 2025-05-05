# Backend API Troubleshooting Guide

This document provides detailed troubleshooting steps for common issues that may arise when running the Viewzenix1 Backend API.

## Table of Contents

1. [Quick Diagnostic Checklist](#quick-diagnostic-checklist)
2. [Connection Issues](#connection-issues)
3. [Database Problems](#database-problems)
4. [Authentication Errors](#authentication-errors)
5. [Webhook Processing Failures](#webhook-processing-failures)
6. [Performance Issues](#performance-issues)
7. [Broker Integration Failures](#broker-integration-failures)
8. [Environment Issues](#environment-issues)
9. [Docker-Specific Issues](#docker-specific-issues)
10. [Log Analysis](#log-analysis)
11. [Diagnostic Scripts](#diagnostic-scripts)
12. [Support Resources](#support-resources)

## Quick Diagnostic Checklist

Start with these basic checks when troubleshooting:

1. ✅ Verify the API service is running with `ps aux | grep flask` or Task Manager
2. ✅ Check if the server is listening on the expected port: `netstat -tlnp | grep 5000`
3. ✅ Confirm environment variables are set correctly with `printenv | grep FLASK`
4. ✅ Look for error messages in the logs: `tail -100 logs/api.log`
5. ✅ Verify database connectivity with the diagnostic script: `python scripts/check_db.py`
6. ✅ Check for disk space issues: `df -h` (Unix) or check Windows Explorer
7. ✅ Ensure required dependencies are installed: `pip list | grep flask`
8. ✅ Test endpoint access with `curl http://localhost:5000/api/health`

## Connection Issues

### API Service Not Accessible

**Symptoms:**
- Cannot connect to API at `http://localhost:5000`
- Connection timeout or connection refused errors

**Solutions:**

1. **Verify service is running:**
   ```bash
   # Check for process
   ps aux | grep flask
   # or on Windows
   tasklist | findstr python
   ```

2. **Check if process is bound to correct port:**
   ```bash
   # Linux
   netstat -tlnp | grep 5000
   # Windows
   netstat -ano | findstr :5000
   ```

3. **Check firewall settings:**
   ```bash
   # Linux
   sudo iptables -L | grep 5000
   # Windows
   netsh advfirewall firewall show rule name=all | findstr 5000
   ```

4. **Try different host binding:**
   ```bash
   # Instead of 0.0.0.0, try
   flask run --host=127.0.0.1 --port=5000
   ```

5. **Check if port is already in use:**
   ```bash
   # Linux
   sudo fuser -n tcp 5000
   # Kill the process if needed
   sudo fuser -k -n tcp 5000
   ```

### CORS Issues

**Symptoms:**
- Frontend receives CORS errors in browser console
- API requests work with tools like curl but not from the browser

**Solutions:**

1. **Check CORS configuration:**
   Ensure `CORS_ORIGINS` in your environment includes the frontend domain.

2. **Add frontend domain to allowed origins:**
   ```python
   # In your Flask app configuration
   CORS(app, origins=['http://localhost:3000', 'https://your-frontend-domain.com'])
   ```

3. **For development only - Allow all origins (not for production):**
   ```python
   CORS(app, origins=['*'])
   ```

## Database Problems

### Connection Failures

**Symptoms:**
- API returns 500 errors
- Logs show database connection errors
- `sqlalchemy.exc.OperationalError` in logs

**Solutions:**

1. **Verify database server is running:**
   ```bash
   # PostgreSQL
   pg_ctl status  # Or
   systemctl status postgresql
   ```

2. **Check connection parameters:**
   ```bash
   # Test PostgreSQL connection
   psql -U username -h localhost -d viewzenix
   # Should prompt for password and connect
   ```

3. **Validate DATABASE_URL environment variable:**
   ```bash
   echo $DATABASE_URL
   # Should be in format: postgresql://username:password@localhost:5432/viewzenix
   ```

4. **Check database permissions:**
   ```sql
   -- In PostgreSQL
   \du  -- List users and roles
   \l   -- List databases with owners
   ```

5. **Reset database connection pool:**
   ```python
   # In Python code
   from flask import current_app
   current_app.db.engine.dispose()
   ```

### Migration Errors

**Symptoms:**
- `Table X doesn't exist` errors
- Missing columns or tables
- Database schema version mismatch

**Solutions:**

1. **Check migration status:**
   ```bash
   flask db current  # Shows current migration
   flask db history  # Shows migration history
   ```

2. **Run missing migrations:**
   ```bash
   flask db upgrade
   ```

3. **Reset migrations (last resort):**
   ```bash
   flask db stamp head  # Mark all migrations as complete
   # If that doesn't work
   flask db stamp base  # Reset to base
   flask db migrate     # Generate migration
   flask db upgrade     # Apply migration
   ```

## Authentication Errors

### JWT Token Issues

**Symptoms:**
- "Invalid token" errors
- "Token expired" errors
- "Signature verification failed" errors

**Solutions:**

1. **Check JWT configuration:**
   ```python
   # JWT settings should include:
   app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
   app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))
   ```

2. **Verify token generation logic:**
   ```python
   # Debug token generation
   token = create_access_token(identity=user_id)
   print(f"Generated token: {token}")
   ```

3. **Test token decoding manually:**
   ```python
   from flask_jwt_extended import decode_token
   try:
       decoded = decode_token(token)
       print(f"Decoded token: {decoded}")
   except Exception as e:
       print(f"Error decoding token: {e}")
   ```

4. **Check system time synchronization:**
   Ensure server time is correct, as JWT token validation is time-sensitive.

## Webhook Processing Failures

### Payload Validation Errors

**Symptoms:**
- Webhook requests rejected with 400 Bad Request
- "Invalid payload schema" errors in logs
- Validation errors in webhook response

**Solutions:**

1. **Check webhook payload against schema:**
   ```bash
   # Review the expected schema
   cat src/backend/schemas/tradingview_alert.json
   
   # Compare with actual payload (from logs)
   ```

2. **Temporarily disable strict validation for debugging:**
   ```python
   # In webhook handler
   validate_webhook_payload(payload, strict=False)
   ```

3. **Log the full webhook payload (temporarily, for debugging only):**
   ```python
   app.logger.debug(f"Received webhook payload: {json.dumps(payload)}")
   ```

### Missing Webhook Events

**Symptoms:**
- Webhook requests received but not processed
- No errors in logs, but expected actions don't happen
- Orders not created from webhook signals

**Solutions:**

1. **Enable debug logging for webhook processor:**
   ```
   LOG_LEVEL=DEBUG
   ```

2. **Check webhook queue status if using queue processing:**
   ```python
   # In a debug endpoint or script
   queue_status = {
       "length": webhook_queue.qsize(),
       "is_processing": webhook_processor.is_running
   }
   ```

3. **Verify webhook handler registration:**
   Ensure webhook routes are properly registered in the Flask app.

## Performance Issues

### Slow Response Times

**Symptoms:**
- API endpoints take several seconds to respond
- Timeout errors from frontend or other clients
- High latency reported in metrics

**Solutions:**

1. **Check database query performance:**
   ```python
   # Enable query timing logs
   app.config['SQLALCHEMY_RECORD_QUERIES'] = True
   
   # After request, log slow queries
   @app.after_request
   def log_slow_queries(response):
       from flask_sqlalchemy import get_debug_queries
       for query in get_debug_queries():
           if query.duration >= 0.5:  # 500 ms
               app.logger.warning(f"Slow query: {query.statement} took {query.duration}s")
       return response
   ```

2. **Monitor system resources:**
   ```bash
   # Linux
   top -b -n 1 | head -n 20
   # Check memory usage
   free -m
   ```

3. **Optimize database with indexes:**
   Check for missing indexes on frequently queried columns.

4. **Implement caching for repetitive queries:**
   Use Flask-Caching for expensive operations.

### Memory Leaks

**Symptoms:**
- API performance degrades over time
- Memory usage steadily increases
- Application needs frequent restarts

**Solutions:**

1. **Monitor memory usage over time:**
   ```bash
   ps -o pid,user,%mem,command ax | grep flask
   ```

2. **Enable memory profiling:**
   ```python
   # Add memory profiling middleware
   from flask import Flask
   from memory_profiler import profile
   
   app = Flask(__name__)
   
   @profile
   def expensive_function():
       # Your function code
       pass
   ```

3. **Check for resource cleanup:**
   Ensure file handles, database connections, and other resources are properly closed.

## Broker Integration Failures

### Order Placement Failures

**Symptoms:**
- "Order placement failed" errors
- API returns 4xx or 5xx errors from broker
- Broker API rate limits exceeded

**Solutions:**

1. **Verify broker API credentials:**
   ```bash
   # Check environment variables
   echo $BROKER_API_KEY
   echo $BROKER_API_SECRET
   
   # Ensure they're not empty and are correctly formatted
   ```

2. **Test broker connection directly:**
   ```python
   # Example script
   from src.integration.adapters.alpaca_adapter import AlpacaAdapter
   
   adapter = AlpacaAdapter()
   connected = adapter.authenticate()
   print(f"Connected: {connected}")
   
   account = adapter.get_account_info()
   print(f"Account: {account}")
   ```

3. **Check broker API status:**
   Visit the broker's status page or API documentation to check for outages.

4. **Implement retry logic for transient failures:**
   ```python
   def place_order_with_retry(broker, order_params, max_retries=3):
       for attempt in range(max_retries):
           try:
               return broker.place_order(**order_params)
           except TransientError as e:
               if attempt < max_retries - 1:
                   time.sleep(2 ** attempt)  # Exponential backoff
                   continue
               raise
   ```

### Position Tracking Inconsistencies

**Symptoms:**
- Local position records don't match broker positions
- Duplicate orders for the same position
- Missing positions in local database

**Solutions:**

1. **Implement position reconciliation:**
   ```python
   def reconcile_positions(broker):
       # Get broker positions
       broker_positions = broker.get_all_positions()
       
       # Get local positions
       local_positions = Position.query.all()
       
       # Compare and fix discrepancies
       for bp in broker_positions:
           lp = next((p for p in local_positions if p.symbol == bp.symbol), None)
           if lp is None:
               # Missing position in local DB
               new_position = Position(symbol=bp.symbol, quantity=bp.qty)
               db.session.add(new_position)
           elif float(lp.quantity) != float(bp.qty):
               # Update quantity discrepancy
               lp.quantity = bp.qty
               db.session.add(lp)
               
       db.session.commit()
   ```

2. **Log all broker interactions for audit:**
   Ensure comprehensive logging of all broker API calls.

## Environment Issues

### Missing Environment Variables

**Symptoms:**
- `KeyError` exceptions when accessing environment variables
- Default values being used unexpectedly
- Configuration not applied correctly

**Solutions:**

1. **Check for missing variables:**
   ```bash
   # Linux/Mac
   printenv | grep FLASK
   printenv | grep DATABASE
   
   # Windows PowerShell
   Get-ChildItem Env: | Where-Object { $_.Name -like "FLASK*" -or $_.Name -like "DATABASE*" }
   ```

2. **Implement validation at startup:**
   ```python
   def validate_environment():
       required_vars = ['FLASK_APP', 'DATABASE_URL', 'SECRET_KEY', 'JWT_SECRET_KEY']
       missing = [var for var in required_vars if not os.environ.get(var)]
       
       if missing:
           raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")
   
   # Call at application startup
   validate_environment()
   ```

3. **Use a .env file for development:**
   Create a `.env` file with all required variables (see [Environment Template](backend_env_template.md)).

### Path and Import Issues

**Symptoms:**
- `ModuleNotFoundError` exceptions
- "No module named X" errors
- Import errors when running scripts

**Solutions:**

1. **Check Python path:**
   ```python
   import sys
   print(sys.path)
   ```

2. **Add project root to Python path:**
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
   ```

3. **Use proper relative imports:**
   ```python
   # Instead of
   from src.backend.models import User
   
   # Use relative import when appropriate
   from ..models import User
   ```

## Docker-Specific Issues

### Container Startup Failures

**Symptoms:**
- Container exits immediately after startup
- "Exited with code 1" in `docker ps -a`
- Flask app doesn't start inside container

**Solutions:**

1. **Check container logs:**
   ```bash
   docker logs <container_id>
   ```

2. **Verify Dockerfile permissions:**
   Ensure startup script has execute permissions:
   ```bash
   # In Dockerfile
   COPY start.sh /app/
   RUN chmod +x /app/start.sh
   ```

3. **Check environment variables:**
   ```bash
   # Ensure variables are passed to container
   docker run -e FLASK_APP=src/backend/app.py -e DATABASE_URL=... <image_name>
   ```

4. **Run with interactive shell for debugging:**
   ```bash
   docker run -it --entrypoint /bin/bash <image_name>
   ```

### Database Connection from Container

**Symptoms:**
- Container starts but can't connect to database
- "Connection refused" errors to database host

**Solutions:**

1. **Use proper network configuration:**
   ```bash
   # Create a network for containers
   docker network create viewzenix-network
   
   # Run database with network
   docker run --name postgres --network viewzenix-network -p 5432:5432 postgres
   
   # Run app connecting to database by container name
   docker run --network viewzenix-network -e DATABASE_URL=postgresql://username:password@postgres:5432/viewzenix <image_name>
   ```

2. **For external database, check host networking:**
   Ensure the container can resolve and reach the database host.

## Log Analysis

### Reading and Filtering Logs

Log analysis is crucial for diagnosing issues:

```bash
# View last 100 lines
tail -100 logs/api.log

# Filter for error messages
grep "ERROR" logs/api.log

# Find authentication errors
grep -i "auth" logs/api.log | grep "ERROR"

# View JSON logs in a readable format (if using JSON logging)
cat logs/api.log | jq '.'

# Monitor logs in real-time
tail -f logs/api.log
```

### Common Log Patterns and Their Meaning

| Log Pattern | Meaning | Potential Solution |
|-------------|---------|-------------------|
| `ConnectionError: (psycopg2.OperationalError) could not connect to server` | Database connection issue | Check database server is running and accessible |
| `ModuleNotFoundError: No module named 'x'` | Missing dependency | `pip install x` or check Python path |
| `TypeError: ... is not JSON serializable` | Object cannot be converted to JSON | Add custom JSON serializer or convert object to basic types |
| `RuntimeError: Working outside of application context` | Flask app context missing | Use `with app.app_context():` or `@app.route` |
| `ValidationError: ... is a required property` | Missing required field in webhook | Check incoming payload format |

## Diagnostic Scripts

### Database Connection Checker

Create a script at `scripts/check_db.py`:

```python
#!/usr/bin/env python
"""Database connection checker for Viewzenix1 API."""

import os
import sys
import time
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def check_database_connection():
    """Check if database is accessible with current environment variables."""
    # Load environment variables from .env file if present
    load_dotenv()
    
    # Get database URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False
    
    # Create engine
    try:
        engine = create_engine(database_url)
    except Exception as e:
        print(f"ERROR: Failed to create database engine: {e}")
        return False
    
    # Test connection
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.fetchone()[0] == 1:
                print("SUCCESS: Database connection successful")
                
                # Check for required tables
                table_query = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema='public'
                """)
                tables = [row[0] for row in conn.execute(table_query)]
                print(f"Found {len(tables)} tables: {', '.join(tables)}")
                
                # Check for critical tables
                critical_tables = ['users', 'orders', 'positions', 'webhooks']
                missing = [t for t in critical_tables if t not in tables]
                if missing:
                    print(f"WARNING: Missing critical tables: {', '.join(missing)}")
                
                return True
    except Exception as e:
        print(f"ERROR: Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("Viewzenix1 Database Connection Checker")
    print("-" * 40)
    print(f"Checking database connection at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = check_database_connection()
    sys.exit(0 if success else 1)
```

### API Health Inspector

Create a script at `scripts/check_api_health.py`:

```python
#!/usr/bin/env python
"""API health check script for Viewzenix1 API."""

import os
import sys
import requests
import time
import json
from dotenv import load_dotenv

def check_api_health(base_url=None):
    """Check if API is running and responsive."""
    # Load environment variables from .env file if present
    load_dotenv()
    
    # Get base URL
    if not base_url:
        host = os.environ.get('HOST', 'localhost')
        port = os.environ.get('PORT', '5000')
        base_url = f"http://{host}:{port}"
    
    print(f"Checking API health at: {base_url}")
    
    # Basic health check
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"SUCCESS: API is healthy")
            print(f"  Status: {health_data.get('status')}")
            print(f"  Uptime: {health_data.get('uptime_seconds', 'N/A')} seconds")
            print(f"  Version: {health_data.get('version', 'N/A')}")
            
            # Check detailed health if available
            try:
                details_response = requests.get(f"{base_url}/api/health/details", timeout=5)
                if details_response.status_code == 200:
                    details = details_response.json()
                    print("\nDetailed Health Check:")
                    print(f"  Database: {details.get('database', {}).get('status', 'N/A')}")
                    for service, status in details.get('services', {}).items():
                        print(f"  Service '{service}': {status.get('status', 'N/A')}")
            except requests.RequestException:
                print("Detailed health check not available")
                
            return True
        else:
            print(f"ERROR: API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"ERROR: Could not connect to API: {e}")
        return False

if __name__ == "__main__":
    print("Viewzenix1 API Health Checker")
    print("-" * 40)
    print(f"Running health check at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Allow base URL to be passed as command line argument
    base_url = sys.argv[1] if len(sys.argv) > 1 else None
    
    success = check_api_health(base_url)
    sys.exit(0 if success else 1)
```

## Support Resources

If you're still experiencing issues after going through this troubleshooting guide:

1. **Check the GitHub Issue Tracker**
   - Look for similar issues that might have already been resolved

2. **Contact the Backend Team**
   - Create a message in the BE team's inbox with details of your problem:
     `/workspace/Viewzenix1/communication/inbox/BE/`

3. **Join the Developer Chat**
   - Real-time assistance is available on the development Slack channel

4. **Review Advanced Documentation**
   - [Backend Architecture Documentation](../architecture/backend_architecture.md)
   - [API Specifications](api_specs.md)
   - [Database Schema](../architecture/database_schema.md)

## Reporting Issues

When reporting backend issues, please include:

1. Complete error messages from logs
2. Steps to reproduce the issue
3. Your environment details (OS, Python version, dependency versions)
4. Any recent changes made to the codebase
5. Results of running the diagnostic scripts 