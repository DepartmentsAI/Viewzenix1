# Environment Verification Troubleshooting Guide

This guide provides quick solutions for common issues that may occur during environment verification testing. Refer to this document if you encounter problems during the May 10, 2025 verification process.

## Backend Issues

### Backend Server Won't Start

**Symptoms:**
- Error messages during startup
- Process terminates immediately
- Port 5000 unavailable

**Quick Fixes:**
1. **Check for port conflicts:**
   ```bash
   # Windows
   netstat -ano | findstr 5000
   
   # Linux/macOS
   lsof -i :5000
   ```
   If another process is using the port, terminate it or change the backend port.

2. **Verify environment variables:**
   Make sure all required environment variables are set properly (check `.env` file).

3. **Check database connection:**
   Ensure the database is running and connection parameters are correct.

4. **Inspect logs:**
   Look for startup errors in the backend logs.

5. **Restore from backup:**
   Use the backup configuration if available:
   ```bash
   cp .env.backup .env
   ```

### Database Connection Failure

**Symptoms:**
- "Connection refused" errors
- Database component shows "disconnected" in health check
- Timeout errors

**Quick Fixes:**
1. **Verify database is running:**
   ```bash
   # For SQLite
   ls -l data/database.db
   
   # For MySQL
   mysql -u root -p -e "show databases"
   
   # For PostgreSQL
   pg_isready
   ```

2. **Check credentials:**
   Verify username/password in configuration file.

3. **Test connection manually:**
   Use database client to attempt connection with same parameters.

4. **Switch to SQLite:**
   If configured to use external database, modify backend config to use SQLite:
   ```
   DATABASE_TYPE=sqlite
   DATABASE_PATH=./data/database.db
   ```

### Health Endpoint Failing

**Symptoms:**
- HTTP 500 errors
- Timeout on health endpoints
- Missing components in health response

**Quick Fixes:**
1. **Restart backend service:**
   ```bash
   # Ctrl+C to stop current process, then
   python app.py
   ```

2. **Check component dependencies:**
   Ensure all dependent services are running.

3. **Verify configuration:**
   ```bash
   cat config/healthcheck.json
   ```

4. **Disable problematic checks:**
   If specific component is causing issues, disable it in config temporarily.

## Frontend Issues

### Frontend Won't Build/Start

**Symptoms:**
- Build errors in terminal
- Webpack/NPM errors
- Port 3000 unavailable

**Quick Fixes:**
1. **Clear node_modules and reinstall:**
   ```bash
   rm -rf node_modules
   npm install
   ```

2. **Check for port conflicts:**
   ```bash
   # Windows
   netstat -ano | findstr 3000
   
   # Linux/macOS
   lsof -i :3000
   ```

3. **Verify Node.js version:**
   ```bash
   node -v # Should be v16+
   ```

4. **Try production build:**
   ```bash
   npm run build
   npx serve -s build
   ```

### Frontend Loads Blank Page

**Symptoms:**
- White screen, no errors visible
- Console shows JavaScript errors
- API endpoints not being called

**Quick Fixes:**
1. **Check browser console:**
   Open DevTools (F12) and look for errors.

2. **Verify API base URL:**
   ```javascript
   // Should point to correct backend URL
   console.log(process.env.REACT_APP_API_URL);
   ```

3. **Clear browser cache and cookies:**
   CTRL+SHIFT+DEL in most browsers.

4. **Try different browser:**
   Test in Chrome, Firefox, and Edge.

5. **Run with verbose logs:**
   ```bash
   BROWSER=none DEBUG=* npm start
   ```

### Login Screen Errors

**Symptoms:**
- Can't log in with test credentials
- Authentication errors
- Redirect loops

**Quick Fixes:**
1. **Verify credentials:**
   Check test user accounts in fixtures.

2. **Inspect network requests:**
   Look for 401/403 errors in network tab.

3. **Clear local storage:**
   ```javascript
   // In browser console
   localStorage.clear();
   ```

4. **Check token expiration:**
   Authentication tokens may be expired.

5. **Bypass authentication (for testing only):**
   If available, use test backdoor routes.

## Integration Issues

### Broker API Connection Failure

**Symptoms:**
- "Connection refused" when connecting to broker
- Authentication failures
- Timeout errors

**Quick Fixes:**
1. **Verify API credentials:**
   Check broker_config.json credentials.

2. **Test with curl:**
   ```bash
   curl -X GET "https://paper-api.alpaca.markets/v2/account" \
     -H "APCA-API-KEY-ID: YOUR_API_KEY" \
     -H "APCA-API-SECRET-KEY: YOUR_SECRET_KEY"
   ```

3. **Check for API rate limiting:**
   Broker may be limiting requests.

4. **Use alternate broker endpoint:**
   Try backup server if available.

5. **Switch to mock mode:**
   Enable mock broker mode in configuration.

### WebSocket Connection Issues

**Symptoms:**
- WebSocket connection fails to establish
- Frequent disconnections
- No data streaming

**Quick Fixes:**
1. **Verify WebSocket URL:**
   Check configuration for correct WebSocket endpoint.

2. **Test with simple client:**
   ```bash
   # Using websocat tool
   websocat wss://stream.data.alpaca.markets/v2/iex -H "Authorization: Bearer YOUR_TOKEN"
   ```

3. **Check network restrictions:**
   WebSockets may be blocked by firewalls.

4. **Increase reconnect attempts:**
   Modify reconnection parameters in WebSocket client config.

5. **Use polling fallback:**
   If WebSocket cannot be fixed, switch to REST polling.

### Market Data Not Available

**Symptoms:**
- Empty market data responses
- "Symbol not found" errors
- Price data missing

**Quick Fixes:**
1. **Verify market hours:**
   Check if market is open for requested symbols.

2. **Verify symbol list:**
   Ensure symbols being requested are valid.

3. **Check subscription level:**
   Some data may require higher tier API access.

4. **Use historical data instead:**
   If real-time data unavailable, fall back to historical endpoints.

5. **Check for API announcement/status:**
   Check broker status page for outages.

## Test Fixture Issues

### Missing or Invalid Fixtures

**Symptoms:**
- "File not found" errors when running tests
- JSON parsing errors
- Verification script fails with fixture errors

**Quick Fixes:**
1. **Check fixture location:**
   Fixtures should be in `tests/e2e/fixtures/`.

2. **Validate JSON format:**
   ```bash
   # For each fixture file
   cat fixture.json | jq
   ```

3. **Recreate from templates:**
   Use default templates to recreate missing fixtures.

4. **Fix permissions:**
   ```bash
   chmod 644 tests/e2e/fixtures/*
   ```

5. **Generate sample data:**
   If fixtures cannot be restored, use verification script's generator mode:
   ```bash
   python environment_verification.py --generate-fixtures
   ```

## Script and Tool Issues

### Verification Script Failures

**Symptoms:**
- Script crashes during execution
- Timeout errors
- Import errors

**Quick Fixes:**
1. **Check Python version:**
   ```bash
   python --version  # Should be 3.6+
   ```

2. **Install dependencies:**
   ```bash
   pip install requests
   ```

3. **Run with verbose logging:**
   ```bash
   python environment_verification.py -v
   ```

4. **Test individual components:**
   ```bash
   python environment_verification.py --test-backend-only
   ```

5. **Check script permissions:**
   ```bash
   chmod +x environment_verification.py
   ```

### Shell/PowerShell Script Issues

**Symptoms:**
- "Permission denied" errors
- Command not found
- Script terminates prematurely

**Quick Fixes:**
1. **Fix permissions:**
   ```bash
   # Linux/macOS
   chmod +x run_environment_verification.sh
   
   # Windows (PowerShell)
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```

2. **Check for line ending issues:**
   If transferring between Windows/Unix, line endings may be incorrect.

3. **Run with debugging:**
   ```bash
   # Bash
   bash -x run_environment_verification.sh
   
   # PowerShell
   ./run_environment_verification.ps1 -Debug
   ```

4. **Run commands manually:**
   Execute each command from the script individually to identify issues.

## Network and Connectivity Issues

### General Connection Problems

**Symptoms:**
- Timeout errors across multiple components
- Intermittent connectivity
- DNS resolution failures

**Quick Fixes:**
1. **Check network connectivity:**
   ```bash
   ping google.com
   ```

2. **Verify DNS resolution:**
   ```bash
   nslookup paper-api.alpaca.markets
   ```

3. **Check proxy settings:**
   Ensure HTTP_PROXY/HTTPS_PROXY environment variables are set correctly if required.

4. **Test with curl:**
   ```bash
   curl -v http://localhost:5000/api/health
   ```

5. **Check firewall settings:**
   Ensure required ports are open.

## Emergency Contact Information

If troubleshooting steps do not resolve the issue:

| Role | Name | Contact |
|------|------|---------|
| QA Lead | | |
| BE Lead | | |
| FE Lead | | |
| INT Lead | | |
| PM | | |

## Command Reference

```bash
# Start backend (standard)
cd /path/to/backend
python app.py

# Start frontend (standard)
cd /path/to/frontend
npm start

# Check running processes
ps aux | grep python
ps aux | grep node

# Check open ports
netstat -tuln

# Test HTTP endpoint
curl -v http://localhost:5000/api/health

# Validate JSON file
cat file.json | jq

# Run verification script
cd /path/to/tests/e2e
python environment_verification.py

# Run verification script with options
python environment_verification.py --backend-url http://localhost:5000 --frontend-url http://localhost:3000 --verbose
``` 