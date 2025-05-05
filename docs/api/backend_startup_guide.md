# Backend API Startup Guide

## Overview

This guide provides comprehensive instructions for starting and troubleshooting the Viewzenix1 backend API services. Following these steps will ensure that the API is properly configured and running, making it available for testing and client applications.

## Prerequisites

Before starting the backend API, ensure you have the following:

- Python 3.9 or higher installed
- PostgreSQL 13 or higher (or access to a PostgreSQL instance)
- All required dependencies installed via `pip install -r requirements.txt`
- Appropriate environment variables configured (see [Environment Variables](#environment-variables))

## Quick Start

```bash
# Navigate to the project root
cd /path/to/Viewzenix1

# Activate virtual environment (if using one)
# Windows
.venv\Scripts\activate
# Unix/Mac
source .venv/bin/activate

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Set required environment variables
# Windows (PowerShell)
$env:FLASK_APP="src/backend/app.py"
$env:FLASK_ENV="development"
$env:DATABASE_URL="postgresql://username:password@localhost:5432/viewzenix"
$env:SECRET_KEY="your-secret-key"
$env:BROKER_API_KEY="your-broker-api-key"
$env:BROKER_API_SECRET="your-broker-api-secret"

# Unix/Mac
export FLASK_APP=src/backend/app.py
export FLASK_ENV=development
export DATABASE_URL=postgresql://username:password@localhost:5432/viewzenix
export SECRET_KEY=your-secret-key
export BROKER_API_KEY=your-broker-api-key
export BROKER_API_SECRET=your-broker-api-secret

# Initialize the database (first time only)
flask db upgrade

# Start the backend API server
flask run --host=0.0.0.0 --port=5000
```

## Detailed Installation Steps

### Step 1: Clone the Repository (If Not Already Done)

```bash
git clone https://github.com/DepartmentsAI/Viewzenix1.git
cd Viewzenix1
```

### Step 2: Set Up a Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Unix/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root with the following variables (adjust values as needed):

```
# Application Settings
FLASK_APP=src/backend/app.py
FLASK_ENV=development
DEBUG=True
SECRET_KEY=your-secure-secret-key

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/viewzenix

# Broker Integration
BROKER_API_KEY=your-broker-api-key
BROKER_API_SECRET=your-broker-api-secret
USE_PAPER_TRADING=True

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_DIR=logs

# Security Settings
JWT_SECRET_KEY=another-secure-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600
CORS_ORIGINS=http://localhost:3000,https://your-frontend-domain.com
```

Load these variables using:

```bash
# Windows (PowerShell)
Get-Content .env | ForEach-Object { 
    $key, $value = $_.Split('=', 2)
    if ($key -and $value) { 
        [Environment]::SetEnvironmentVariable($key, $value, 'Process')
    }
}

# Unix/Mac
export $(grep -v '^#' .env | xargs)
```

### Step 5: Initialize the Database

```bash
# Create database (if not already created)
createdb viewzenix  # Using PostgreSQL CLI

# Run migrations
flask db upgrade
```

### Step 6: Start the Backend API Server

```bash
# Development mode
flask run --host=0.0.0.0 --port=5000

# Production mode
gunicorn --bind 0.0.0.0:5000 --workers 4 'src.backend.app:create_app()'
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `FLASK_APP` | Path to the Flask application entry point | Yes | `src/backend/app.py` |
| `FLASK_ENV` | Environment mode (development, production) | No | `development` |
| `DATABASE_URL` | PostgreSQL connection string | Yes | None |
| `SECRET_KEY` | Secret key for Flask session encryption | Yes | None |
| `BROKER_API_KEY` | API key for the broker integration | Yes (for live trading) | None |
| `BROKER_API_SECRET` | API secret for the broker integration | Yes (for live trading) | None |
| `USE_PAPER_TRADING` | Whether to use paper trading mode | No | `True` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No | `INFO` |
| `LOG_FORMAT` | Log format (text, json) | No | `json` |
| `LOG_DIR` | Directory for log files | No | `logs` |
| `JWT_SECRET_KEY` | Secret key for JWT token encryption | Yes | None |
| `JWT_ACCESS_TOKEN_EXPIRES` | JWT token expiration time in seconds | No | `3600` |
| `CORS_ORIGINS` | Comma-separated list of allowed CORS origins | No | `http://localhost:3000` |

## Verification

Once the API server is running, you can verify it's working with:

```bash
# Using curl
curl http://localhost:5000/api/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2025-05-09T12:34:56.789Z",
  "uptime_seconds": 123,
  "version": "1.0.0"
}
```

## Common Issues and Solutions

### API Not Starting

**Symptoms:**
- Error messages when running `flask run`
- No response when accessing API endpoints

**Possible Causes and Solutions:**

1. **Port Already in Use**
   ```
   Error: [Errno 98] Address already in use
   ```
   Solution: Change the port or kill the process using the current port
   ```bash
   # Find the process using port 5000
   netstat -tlnp | grep 5000  # Linux
   netstat -ano | findstr :5000  # Windows
   
   # Kill the process
   kill <PID>  # Linux
   taskkill /F /PID <PID>  # Windows
   
   # Or use a different port
   flask run --port=5001
   ```

2. **Missing Dependencies**
   ```
   ModuleNotFoundError: No module named 'flask_sqlalchemy'
   ```
   Solution: Install required dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Connection Error**
   ```
   sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
   ```
   Solution: Check database connection settings and ensure PostgreSQL is running
   ```bash
   # Check PostgreSQL status
   pg_ctl status  # PostgreSQL command line
   systemctl status postgresql  # Linux
   # Ensure DATABASE_URL is correct in your environment
   ```

4. **Environment Variable Issues**
   ```
   KeyError: 'SECRET_KEY'
   ```
   Solution: Ensure all required environment variables are set
   ```bash
   # Check if variables are set
   echo $SECRET_KEY  # Unix/Mac
   echo %SECRET_KEY%  # Windows
   ```

### Database Migrations Failed

**Symptoms:**
- Error when running `flask db upgrade`
- Missing tables when accessing the database

**Solutions:**
```bash
# Reset migrations (caution: this will reset your database)
flask db stamp head  # Mark current as head 
flask db migrate     # Generate migration
flask db upgrade     # Apply migration
```

### Permission Issues

**Symptoms:**
- Permission denied errors
- Cannot write to log files

**Solutions:**
```bash
# Fix log directory permissions
mkdir -p logs
chmod 755 logs
```

## Advanced Configuration

### Running Behind Nginx

For production deployments, we recommend running the API behind Nginx:

```nginx
server {
    listen 80;
    server_name api.viewzenix1.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Supervisor Configuration

For automatic restart and monitoring:

```ini
[program:viewzenix1-api]
command=/path/to/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 'src.backend.app:create_app()'
directory=/path/to/Viewzenix1
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/viewzenix1/api-err.log
stdout_logfile=/var/log/viewzenix1/api-out.log
environment=
    FLASK_APP=src/backend/app.py,
    FLASK_ENV=production,
    DATABASE_URL=postgresql://username:password@localhost:5432/viewzenix,
    SECRET_KEY=your-secure-secret-key
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test modules
pytest tests/unit/backend/
```

### Linting

```bash
# Run linting
flake8 src/backend/
```

### API Documentation

API documentation is automatically generated and available at:
- Development: http://localhost:5000/api/docs
- Production: https://api.viewzenix1.com/docs

## Conclusion

The backend API should now be up and running. If you encounter any issues not covered in this guide, please refer to the [Backend Troubleshooting Guide](backend_troubleshooting.md) or contact the Backend Team for assistance.

## Additional Resources

- [Backend Architecture Documentation](../architecture/backend_architecture.md)
- [API Specifications](api_specs.md)
- [Database Schema](../architecture/database_schema.md)
- [Environment Variable Template](backend_env_template.md)
- [Deployment Guide](../deployment/backend_deployment.md) 