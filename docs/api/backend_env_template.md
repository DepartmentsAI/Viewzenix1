# Backend Environment Configuration

This document provides a template for the environment variables required to run the Viewzenix1 backend API service.

## Environment Variables Template

Create a file named `.env` in the project root directory with the following content, adjusting the values as needed for your environment:

```bash
# Viewzenix1 Backend API - Environment Variables
# Update the values as needed for your environment

# Core configuration
FLASK_APP=src.backend.app
FLASK_ENV=development  # Use 'production' for production environment
DEBUG=True  # Set to False in production
PORT=5000  # The port the API will listen on

# Database configuration
DATABASE_URL=postgresql://username:password@localhost:5432/viewzenix1

# Security configuration 
SECRET_KEY=your_secret_key_here  # Change this to a random string
JWT_SECRET_KEY=your_jwt_secret_key_here  # Change this to a random string
JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour (in seconds)

# Broker API configuration
ALPACA_API_KEY=your_alpaca_api_key  # Get from Alpaca dashboard
ALPACA_API_SECRET=your_alpaca_api_secret  # Get from Alpaca dashboard
ALPACA_PAPER_TRADING=True  # Set to False for live trading

# Webhook configuration
WEBHOOK_SECRET=your_webhook_secret_here  # Used for webhook signature verification

# Logging configuration
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE_MAX_BYTES=10485760  # 10MB
LOG_FILE_BACKUP_COUNT=5
```

## Security Recommendations

1. **Never commit your `.env` file to version control**
   - Add `.env` to your `.gitignore` file
   - Use separate `.env` files for different environments (development, testing, production)

2. **Use strong, unique values for security keys**
   - Generate random strings for `SECRET_KEY` and `JWT_SECRET_KEY`
   - You can use Python to generate secure random strings:

   ```python
   import secrets
   print(secrets.token_hex(32))  # 32 bytes = 64 hex characters
   ```

3. **Protect sensitive API credentials**
   - Use environment-specific credentials for APIs like Alpaca
   - Consider using a secrets management solution for production environments

## Environment-Specific Configuration

### Development

```bash
FLASK_ENV=development
DEBUG=True
LOG_LEVEL=DEBUG
ALPACA_PAPER_TRADING=True
```

### Testing

```bash
FLASK_ENV=testing
DEBUG=False
LOG_LEVEL=INFO
ALPACA_PAPER_TRADING=True
# Use a separate test database
DATABASE_URL=postgresql://username:password@localhost:5432/viewzenix1_test
```

### Production

```bash
FLASK_ENV=production
DEBUG=False
LOG_LEVEL=WARNING
# Consider using a different port in production
PORT=8000
# Use appropriate connection strings for production databases
DATABASE_URL=postgresql://username:password@production-db-host:5432/viewzenix1_prod
# Set to False only when ready to trade with real money
ALPACA_PAPER_TRADING=False
```

## Loading Environment Variables

The backend application loads environment variables in the following order of precedence:

1. Variables explicitly set in the environment (e.g., `export FLASK_APP=...`)
2. Variables in the `.env` file
3. Default values in the application code

When running the application with one of the startup scripts in `/scripts/`, the script will automatically load the `.env` file if present. 