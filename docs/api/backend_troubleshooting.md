# Backend API Troubleshooting Guide

This document provides quick solutions for common issues encountered when running the Viewzenix1 backend API.

## Quick Reference

| Issue | Common Causes | Solution |
|-------|--------------|----------|
| API won't start | Environment configuration, port in use, missing dependencies | Run `scripts/backend_environment_check.py` |
| "Connection refused" | Service not running, wrong port, firewall | Check service status, port config, firewall settings |
| Database errors | PostgreSQL not running, wrong credentials | Verify PostgreSQL status, check DATABASE_URL |
| Authentication failures | Invalid/expired tokens, wrong credentials | Check JWT configuration, verify credentials |
| Missing modules | Incomplete installation | Run `pip install -r requirements.txt` |
| 500 Internal Server Error | Application error, database issue | Check application logs |

## Common Issues and Solutions

### 1. API Service Won't Start

**Symptoms:**
- Error messages when starting the service
- No response from the API endpoints
- The process exits immediately after starting

**Common Causes and Solutions:**

- **Missing dependencies**
  ```bash
  # Install required packages
  pip install -r requirements.txt
  ```

- **Port already in use**
  ```bash
  # Check for processes using port 5000
  # Windows:
  netstat -ano | findstr :5000
  
  # Linux/macOS:
  lsof -i :5000
  
  # Change the port in .env file
  PORT=5001
  ```

- **Incorrect environment configuration**
  ```bash
  # Verify environment variables
  # Windows:
  echo %FLASK_APP%
  
  # Linux/macOS:
  echo $FLASK_APP
  
  # Set correct environment variables
  # Windows:
  set FLASK_APP=src.backend.app
  
  # Linux/macOS:
  export FLASK_APP=src.backend.app
  ```

- **Python path issues**
  ```bash
  # Add project root to PYTHONPATH
  # Windows:
  set PYTHONPATH=%PYTHONPATH%;C:\path\to\Viewzenix1
  
  # Linux/macOS:
  export PYTHONPATH=$PYTHONPATH:/path/to/Viewzenix1
  ```

### 2. Database Connection Issues

**Symptoms:**
- "Could not connect to server" errors
- "Authentication failed" messages
- API starts but API calls fail with database errors

**Common Causes and Solutions:**

- **PostgreSQL not running**
  ```bash
  # Check if PostgreSQL is running
  # Windows:
  pg_isready -h localhost
  
  # Linux:
  sudo systemctl status postgresql
  
  # macOS:
  brew services list | grep postgresql
  ```

- **Wrong database credentials**
  ```bash
  # Verify your DATABASE_URL in .env
  # Format: postgresql://username:password@hostname:port/database
  
  # Test connection manually with psql
  psql postgresql://username:password@hostname:port/database
  ```

- **Database doesn't exist**
  ```bash
  # Create the database
  createdb viewzenix1
  
  # Or with psql:
  psql -c "CREATE DATABASE viewzenix1;" -U username
  ```

- **Schema migration issues**
  ```bash
  # Run database migrations
  cd /path/to/Viewzenix1
  flask db upgrade
  ```

### 3. Authentication Failures

**Symptoms:**
- "Unauthorized" (401) responses
- "JWT verification failed" messages
- Unable to access protected endpoints

**Common Causes and Solutions:**

- **Incorrect JWT configuration**
  ```bash
  # Verify JWT configuration in .env
  # Ensure SECRET_KEY and JWT_SECRET_KEY are set correctly
  ```

- **Token expired**
  ```bash
  # Check token expiration configuration
  # Increase JWT_ACCESS_TOKEN_EXPIRES in .env if needed
  ```

- **Client using incorrect authentication process**
  ```bash
  # Correct authentication flow:
  # 1. POST /auth/login with credentials
  # 2. Receive token in response
  # 3. Include token in Authorization header:
  #    Authorization: Bearer <token>
  ```

### 4. Webhook Processing Issues

**Symptoms:**
- Webhooks received but not processed
- Signature verification failures
- Missing webhook data

**Common Causes and Solutions:**

- **Incorrect webhook secret**
  ```bash
  # Verify WEBHOOK_SECRET in .env matches what's configured at the source
  ```

- **Malformed webhook payloads**
  ```bash
  # Check the webhook payload format:
  # - Ensure Content-Type is set correctly (usually application/json)
  # - Verify the payload structure matches what the API expects
  ```

- **Logging configuration**
  ```bash
  # Enable debug logging for webhooks
  LOG_LEVEL=DEBUG
  ```

### 5. API Performance Issues

**Symptoms:**
- Slow response times
- Timeouts
- High CPU/memory usage

**Common Causes and Solutions:**

- **Database query performance**
  ```bash
  # Check for missing indexes
  # Review large queries
  # Consider adding database monitoring
  ```

- **Missing caching**
  ```bash
  # Implement caching for frequently accessed data
  # Consider using Redis or an in-memory cache
  ```

- **Connection pooling issues**
  ```bash
  # Verify database connection pooling configuration
  # Adjust max_connections in PostgreSQL if needed
  ```

- **Resource constraints**
  ```bash
  # Check system resources
  # Windows:
  Task Manager
  
  # Linux:
  htop
  
  # macOS:
  Activity Monitor
  ```

### 6. Logging and Monitoring Issues

**Symptoms:**
- Missing logs
- Insufficient information in logs
- Unable to troubleshoot issues

**Common Causes and Solutions:**

- **Log level too high**
  ```bash
  # Set lower log level for more verbose output
  LOG_LEVEL=DEBUG
  ```

- **Log directory permissions**
  ```bash
  # Ensure the logs directory exists and is writable
  mkdir -p logs
  chmod 755 logs
  ```

- **Log rotation issues**
  ```bash
  # Check log_file_max_bytes and log_file_backup_count settings
  # Ensure there's enough disk space
  ```

## Using the Environment Checker

The backend environment checker script can automatically detect and diagnose many common issues:

```bash
# Run the environment checker script
cd /path/to/Viewzenix1
python scripts/backend_environment_check.py
```

## Advanced Debugging

For more complex issues:

1. **Enable debug mode in Flask**
   ```bash
   export FLASK_ENV=development
   export DEBUG=True
   ```

2. **Use the Flask debugger**
   ```bash
   flask run --debugger
   ```

3. **Use logging to trace execution**
   ```python
   import logging
   logging.debug("Variable value: %s", some_variable)
   ```

4. **Inspect database state**
   ```bash
   psql -U username -d viewzenix1
   # Then run SQL queries to inspect data
   ```

5. **Check network issues**
   ```bash
   # Test API endpoint
   curl http://localhost:5000/api/health
   
   # Check network connections
   netstat -an | grep 5000
   ```

## Getting Help

If you're still experiencing issues after trying these troubleshooting steps:

1. Check the application logs in the `logs` directory
2. Review the documentation in `docs/api/`
3. Contact the Backend Team via GitHub Issues
4. Include:
   - Exact error messages
   - Steps to reproduce the issue
   - Environment details (OS, Python version, etc.)
   - Logs and configuration (with sensitive information removed) 