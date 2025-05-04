# Backend API Startup Guide

## Overview

This document provides instructions for starting the Viewzenix1 backend API service and troubleshooting common connection issues. The backend service provides essential trading APIs, webhook endpoints, and monitoring capabilities.

## Prerequisites

- Python 3.9+ installed
- Required Python packages installed (`pip install -r requirements.txt`)
- PostgreSQL database configured and running
- Appropriate environment variables set

## Environment Variables

The backend service requires the following environment variables:

```
# Core configuration
FLASK_APP=src.backend.app
FLASK_ENV=development  # Use 'production' for production environment
DEBUG=True  # Set to False in production
PORT=5000  # The port the API will listen on

# Database configuration
DATABASE_URL=postgresql://username:password@localhost:5432/viewzenix1

# Security configuration 
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret_key

# Broker API configuration
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_API_SECRET=your_alpaca_api_secret
ALPACA_PAPER_TRADING=True  # Set to False for live trading
```

You can set these variables in a `.env` file in the root directory or export them directly in your terminal.

## Starting the Backend Service

### Method 1: Using Python Directly

```bash
# Navigate to the project root
cd /path/to/Viewzenix1

# Set environment variables (if not using .env file)
export FLASK_APP=src.backend.app
export FLASK_ENV=development
export PORT=5000

# Start the Flask application
python -m src.backend.run
```

### Method 2: Using Flask CLI

```bash
# Navigate to the project root
cd /path/to/Viewzenix1

# Set environment variables (if not using .env file)
export FLASK_APP=src.backend.app
export FLASK_ENV=development
export PORT=5000

# Start the Flask application with the Flask CLI
flask run --host=0.0.0.0 --port=5000
```

### Method 3: Using the Startup Script (Windows)

```powershell
# Navigate to the project root
cd C:\path\to\Viewzenix1

# Run the startup script
.\scripts\start_backend.bat
```

### Method 4: Using the Startup Script (Linux/macOS)

```bash
# Navigate to the project root
cd /path/to/Viewzenix1

# Ensure the script is executable
chmod +x ./scripts/start_backend.sh

# Run the startup script
./scripts/start_backend.sh
```

## Verifying the Service is Running

After starting the service, you can verify it's running correctly by:

1. Checking the console output for any errors
2. Making a request to the health endpoint:

```bash
curl http://localhost:5000/api/health
```

You should receive a JSON response with status "healthy" if the service is running correctly.

## Troubleshooting Connection Issues

### Issue: "Connection refused" error

**Possible causes and solutions:**

1. **Service not running**
   - Check if the process is running: `ps aux | grep python` (Linux/macOS) or `tasklist | findstr python` (Windows)
   - Look for error messages in the console output
   - Restart the service

2. **Wrong port configuration**
   - Verify the PORT environment variable is set correctly
   - Check if another process is using port 5000: 
     - Linux/macOS: `sudo lsof -i :5000`
     - Windows: `netstat -ano | findstr :5000`
   - If port 5000 is in use, configure the service to use a different port

3. **Firewall blocking connections**
   - Check firewall settings to ensure they allow connections to port 5000
   - Windows: Check Windows Defender Firewall
   - Linux: Check iptables or ufw (`sudo ufw status`)

4. **Wrong host binding**
   - Ensure the Flask app is binding to `0.0.0.0` (all interfaces) and not just `127.0.0.1` (localhost)
   - Check the `host` parameter in `app.run()` or the `--host` option with the Flask CLI

### Issue: Service starts but crashes immediately

**Possible causes and solutions:**

1. **Database connection issues**
   - Verify PostgreSQL is running: `pg_isready -h localhost -p 5432`
   - Check database credentials in environment variables
   - Look for database-related errors in the logs

2. **Missing dependencies**
   - Ensure all required packages are installed: `pip install -r requirements.txt`
   - Check for ImportError messages in the logs

3. **Configuration errors**
   - Validate all required environment variables are set correctly
   - Check for syntax errors in configuration files

4. **File permission issues**
   - Ensure the application has permission to write to the logs directory
   - Check for permission-related errors in the console output

### Issue: 500 Internal Server Error responses

**Possible causes and solutions:**

1. **Application errors**
   - Check the application logs in the `logs` directory
   - Look for traceback information in the console output
   - Enable debug mode temporarily to get more detailed error information: `export DEBUG=True`

2. **Database query errors**
   - Check that database migrations have been applied: `flask db upgrade`
   - Verify the database schema is up to date
   - Look for SQL-related errors in the logs

## Log Files

The backend service generates the following log files:

- `logs/app.log`: General application logs
- `logs/webhook.log`: Webhook processing logs
- `logs/error.log`: Error-specific logs

Check these files for detailed information when troubleshooting issues.

## Common Error Messages and Solutions

### "ModuleNotFoundError: No module named 'src'"

**Solution**: Ensure you're running the commands from the project root directory, or add the project root to your PYTHONPATH:

```bash
export PYTHONPATH=$PYTHONPATH:/path/to/Viewzenix1
```

### "Error: Could not locate a Flask application"

**Solution**: Ensure the FLASK_APP environment variable is set correctly:

```bash
export FLASK_APP=src.backend.app
```

### "psycopg2.OperationalError: could not connect to server"

**Solution**: Check that PostgreSQL is running and your DATABASE_URL is correct:

```bash
# Verify PostgreSQL is running
pg_isready -h localhost -p 5432

# Check your DATABASE_URL environment variable
echo $DATABASE_URL
```

### "Address already in use"

**Solution**: Either kill the process using port 5000 or configure the application to use a different port:

```bash
# Find and kill the process using port 5000
lsof -i :5000  # On Linux/macOS
kill <PID>

# Or use a different port
export PORT=5001
```

## Contact Information

If you continue to experience issues after trying these troubleshooting steps, please contact the Backend Team or submit an issue on GitHub with:

1. The exact command used to start the service
2. Any error messages or logs
3. Your environment (OS, Python version, etc.)
4. Steps you've already tried 