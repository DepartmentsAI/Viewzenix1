# Backend Environment Variables Template

This document provides a comprehensive template and explanation for all environment variables used by the Viewzenix1 backend API.

## Environment Variables Template

Copy and paste this template into a `.env` file in your project root, then modify the values according to your environment:

```bash
# ======================================================
# Viewzenix1 Backend API Environment Variables
# ======================================================

# ----------------------
# Application Settings
# ----------------------
FLASK_APP=src/backend/app.py
FLASK_ENV=development  # Use 'production' for production environments
DEBUG=True  # Set to False in production
SECRET_KEY=your-secure-secret-key-replace-this
APP_NAME=Viewzenix1
VERSION=1.0.0

# ----------------------
# Server Configuration
# ----------------------
HOST=0.0.0.0
PORT=5000
WORKERS=4  # Number of Gunicorn workers for production

# ----------------------
# Database Configuration
# ----------------------
DATABASE_URL=postgresql://username:password@localhost:5432/viewzenix
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30
DATABASE_ECHO=False  # Set to True for SQL query logging

# ----------------------
# Broker Integration
# ----------------------
BROKER_API_KEY=your-broker-api-key-replace-this
BROKER_API_SECRET=your-broker-api-secret-replace-this
USE_PAPER_TRADING=True  # Set to False for live trading
BROKER_BASE_URL=https://paper-api.alpaca.markets/v2  # Paper trading URL
# BROKER_BASE_URL=https://api.alpaca.markets/v2  # Live trading URL

# ----------------------
# Logging Configuration
# ----------------------
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json  # json or text
LOG_DIR=logs
LOG_FILENAME=api.log
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5  # Number of backup log files to keep

# ----------------------
# Security Settings
# ----------------------
JWT_SECRET_KEY=another-secure-secret-key-replace-this
JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour in seconds
JWT_REFRESH_TOKEN_EXPIRES=2592000  # 30 days in seconds
CORS_ORIGINS=http://localhost:3000,https://your-frontend-domain.com
RATE_LIMITING_ENABLED=True
RATE_LIMIT_DEFAULT=100  # requests per hour

# ----------------------
# Webhook Configuration
# ----------------------
WEBHOOK_SECRET=webhook-secret-key-replace-this
WEBHOOK_RATE_LIMIT=60  # requests per minute
WEBHOOK_VALIDATION_ENABLED=True

# ----------------------
# Risk Management
# ----------------------
MAX_ORDER_VALUE=5000  # Maximum value of a single order in USD
MAX_DAILY_DRAWDOWN_PERCENT=5  # Maximum allowed daily drawdown percentage
MAX_POSITIONS=10  # Maximum number of concurrent open positions
STOP_LOSS_DEFAULT_PERCENT=2  # Default stop loss percentage

# ----------------------
# Cache Configuration
# ----------------------
CACHE_TYPE=simple  # simple, redis, memcached
CACHE_DEFAULT_TIMEOUT=300  # seconds
# Uncomment for Redis cache:
# CACHE_REDIS_URL=redis://localhost:6379/0

# ----------------------
# Testing Configuration
# ----------------------
TESTING=False  # Set to True in testing environments
TEST_DATABASE_URL=postgresql://username:password@localhost:5432/viewzenix_test
```

## Environment Variable Descriptions

### Application Settings

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `FLASK_APP` | Python path to your Flask application | Yes | `src/backend/app.py` |
| `FLASK_ENV` | Environment type (development, production) | No | `development` |
| `DEBUG` | Enable/disable debug mode | No | `True` in development, `False` in production |
| `SECRET_KEY` | Secret key for session encryption | Yes | None |
| `APP_NAME` | Application name for metadata | No | `Viewzenix1` |
| `VERSION` | Application version for metadata | No | `1.0.0` |

### Server Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `HOST` | Host IP to bind the server to | No | `0.0.0.0` (all interfaces) |
| `PORT` | Port to run the server on | No | `5000` |
| `WORKERS` | Number of worker processes (Gunicorn) | No | `4` |

### Database Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | SQLAlchemy connection string | Yes | None |
| `DATABASE_POOL_SIZE` | Connection pool size | No | `10` |
| `DATABASE_MAX_OVERFLOW` | Maximum overflow connections | No | `20` |
| `DATABASE_POOL_TIMEOUT` | Pool timeout in seconds | No | `30` |
| `DATABASE_ECHO` | Echo SQL queries to console | No | `False` |

### Broker Integration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `BROKER_API_KEY` | API key for trading broker | Yes (for live trading) | None |
| `BROKER_API_SECRET` | API secret for trading broker | Yes (for live trading) | None |
| `USE_PAPER_TRADING` | Use paper trading instead of live | No | `True` |
| `BROKER_BASE_URL` | Base URL for broker API | No | Paper trading URL |

### Logging Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `LOG_LEVEL` | Minimum log level to record | No | `INFO` |
| `LOG_FORMAT` | Log format (json or text) | No | `json` |
| `LOG_DIR` | Directory for log files | No | `logs` |
| `LOG_FILENAME` | Name of the log file | No | `api.log` |
| `LOG_MAX_BYTES` | Max size of log file before rotation | No | `10485760` (10MB) |
| `LOG_BACKUP_COUNT` | Number of backup log files | No | `5` |

### Security Settings

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `JWT_SECRET_KEY` | Secret key for JWT tokens | Yes | None |
| `JWT_ACCESS_TOKEN_EXPIRES` | Access token expiration (seconds) | No | `3600` (1 hour) |
| `JWT_REFRESH_TOKEN_EXPIRES` | Refresh token expiration (seconds) | No | `2592000` (30 days) |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | No | `http://localhost:3000` |
| `RATE_LIMITING_ENABLED` | Enable rate limiting | No | `True` |
| `RATE_LIMIT_DEFAULT` | Default rate limit (requests per hour) | No | `100` |

### Webhook Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `WEBHOOK_SECRET` | Secret key for webhook verification | Yes | None |
| `WEBHOOK_RATE_LIMIT` | Rate limit for webhooks (per minute) | No | `60` |
| `WEBHOOK_VALIDATION_ENABLED` | Enable webhook payload validation | No | `True` |

### Risk Management

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `MAX_ORDER_VALUE` | Maximum value of a single order (USD) | No | `5000` |
| `MAX_DAILY_DRAWDOWN_PERCENT` | Max daily drawdown percentage | No | `5` |
| `MAX_POSITIONS` | Maximum number of concurrent positions | No | `10` |
| `STOP_LOSS_DEFAULT_PERCENT` | Default stop loss percentage | No | `2` |

### Cache Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `CACHE_TYPE` | Type of cache to use | No | `simple` |
| `CACHE_DEFAULT_TIMEOUT` | Default cache timeout (seconds) | No | `300` |
| `CACHE_REDIS_URL` | Redis URL for Redis cache | Only if using Redis | None |

### Testing Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `TESTING` | Enable testing mode | No | `False` |
| `TEST_DATABASE_URL` | Database URL for testing | Only in testing | None |

## Environment-Specific Configurations

### Development Environment

```bash
FLASK_ENV=development
DEBUG=True
LOG_LEVEL=DEBUG
DATABASE_ECHO=True
```

### Testing Environment

```bash
FLASK_ENV=testing
TESTING=True
TEST_DATABASE_URL=postgresql://username:password@localhost:5432/viewzenix_test
```

### Production Environment

```bash
FLASK_ENV=production
DEBUG=False
LOG_LEVEL=WARNING
WORKERS=4
RATE_LIMITING_ENABLED=True
```

## Loading Environment Variables

### Using python-dotenv

For development, the recommended approach is to use `python-dotenv`:

```python
# In app.py or config.py
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access environment variables
database_url = os.getenv("DATABASE_URL")
```

### Using Docker

For containerized deployments, pass environment variables in your `docker-compose.yml`:

```yaml
services:
  api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_APP=src/backend/app.py
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://username:password@db:5432/viewzenix
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    volumes:
      - ./logs:/app/logs
```

## Security Considerations

- **NEVER** commit your `.env` file with real credentials to version control
- Use secrets management systems for production environments
- Rotate secrets (JWT_SECRET_KEY, SECRET_KEY) periodically
- Use different secrets for development, testing, and production environments

## Troubleshooting

- If environment variables aren't being recognized, check your loading method
- For Docker, verify variables are properly passed in your configuration
- Use `printenv` or `os.environ` to debug environment variable loading

## Best Practices

1. **Use Descriptive Names**: Prefix variables with the application name to avoid conflicts
2. **Documentation**: Keep this template updated with any new variables
3. **Default Values**: Provide sensible defaults for optional variables
4. **Validation**: Validate critical environment variables at application startup
5. **Secrets**: Treat all API keys and secrets as sensitive information 