# Frontend Environment Troubleshooting Guide

This guide helps diagnose and fix common issues with the frontend environment setup.

## Quick Reference

| Issue | Solution |
|-------|----------|
| Application won't start | Run `npm run verify` to diagnose the issue |
| Missing configuration files | Run `node scripts/migrate-environment.js` to restore them |
| API connectivity issues | Check `config.js` and verify `api.baseUrl` setting |
| Version compatibility | Ensure Node.js 14+ and npm 6+ are installed |
| Docker issues | Check Docker is running and ports are available |

## Diagnostic Tools

### Environment Verification

The verification script is your first line of defense:

```bash
# Run basic verification
npm run verify

# Detailed verification with debugging
DEBUG=verify:* npm run verify
```

### Health Check

For runtime verification:

```bash
npm run health-check
```

## Common Issues and Solutions

### 1. Frontend Application Won't Start

**Symptoms:**
- Blank screen when visiting frontend URL
- Terminal errors when running `npm start`
- "Cannot connect" browser message

**Possible Causes and Solutions:**

a) **Wrong Port Configuration**
   - Check `config.js` and `.env` for the correct port
   - Ensure the port isn't already in use by another application
   - Solution: Change the port in `.env` (e.g., `PORT=3001`)

b) **Missing Dependencies**
   - Run `npm install` to restore missing packages
   - Check for errors in the npm output

c) **Incorrect Environment Variables**
   - Verify `.env` file exists and has the correct values
   - Regenerate if needed: `cp .env.template .env`

d) **Configuration Issues**
   - Run `npm run verify` to identify specific problems
   - Restore default configuration: `cp config.template.js config.js`

### 2. API Connectivity Problems

**Symptoms:**
- UI loads but data doesn't appear
- Console errors mentioning API requests
- Timeout or CORS errors

**Possible Causes and Solutions:**

a) **Incorrect API URL**
   - Check `config.js` and verify `api.baseUrl` setting
   - Ensure the backend is running at the specified URL
   - Try accessing the API directly in a browser or with curl/Postman

b) **Backend Not Running**
   - Start the backend application
   - Verify backend health endpoints respond

c) **CORS Issues**
   - Check browser console for CORS errors
   - Ensure backend has correct CORS configuration
   - For local development, both should run on the same host

d) **Network/Firewall Issues**
   - Check if a firewall is blocking connections
   - Try disabling VPNs or network tools temporarily

### 3. Docker Environment Issues

**Symptoms:**
- Docker containers fail to start
- Port binding errors
- Missing files in Docker container

**Possible Causes and Solutions:**

a) **Docker Not Running**
   - Ensure Docker daemon is running
   - Check Docker status: `docker info`

b) **Port Conflicts**
   - Change ports in `docker-compose.yml`
   - Stop other containers or services using the same ports

c) **Incorrect Docker Configuration**
   - Restore default configurations:
     ```bash
     cp templates/Dockerfile.template Dockerfile
     cp templates/docker-compose.yml.template docker-compose.yml
     cp templates/nginx.conf.template nginx.conf
     ```

d) **Volume Mount Issues**
   - Check volume paths in `docker-compose.yml`
   - Ensure the specified directories exist

### 4. Configuration Corruption

**Symptoms:**
- Verification fails with file format errors
- Strange behavior that doesn't match code
- Environment values not being recognized

**Possible Causes and Solutions:**

a) **Damaged Configuration Files**
   - Use the migration script to restore proper configuration:
     ```bash
     node scripts/migrate-environment.js
     ```

b) **Missing Configuration Files**
   - Create them from templates:
     ```bash
     cp templates/config.template.js config.js
     cp templates/.env.template .env
     ```

c) **Invalid JSON or JavaScript Syntax**
   - Check for syntax errors in configuration files
   - Validate JSON files with a linter or validator

### 5. Cross-Platform Issues

**Symptoms:**
- Works on one OS but not another
- Path-related errors
- Script execution problems

**Possible Causes and Solutions:**

a) **Windows-specific Issues**
   - Use `npm run start:win` instead of `npm start`
   - Check line endings (CRLF vs LF)
   - Use backslashes in Windows paths

b) **macOS/Linux Issues**
   - Use `npm run start:unix` instead of `npm start`
   - Ensure scripts are executable: `chmod +x *.sh`
   - Use forward slashes in paths

c) **Path Separator Issues**
   - Use `path.join()` or `path.resolve()` in Node.js scripts
   - Avoid hardcoded path separators

## When All Else Fails

If the above solutions don't resolve your issue:

1. **Clean Reinstall**
   ```bash
   rm -rf node_modules
   npm cache clean --force
   npm install
   ```

2. **Reset Configuration**
   ```bash
   node scripts/migrate-environment.js --force
   ```

3. **Check System Requirements**
   - Node.js 14+
   - npm 6+
   - Supported browser (Chrome, Firefox, Edge, Safari)
   - Docker 19+ (if using Docker)

4. **Contact Support**
   - Provide the output of `npm run verify`
   - Share any error messages from the console
   - Describe your environment (OS, Node version, etc.)

## Advanced Diagnostic Information

### Collecting Logs

To gather detailed logs for troubleshooting:

```bash
# Enable debug logging
DEBUG=* npm start > frontend.log 2>&1
```

### External Connectivity Test

To test API connectivity separate from the frontend:

```bash
curl -v http://localhost:5000/api/health
```

### System Environment Check

```bash
# Node.js Version
node -v

# npm Version
npm -v

# Operating System
uname -a  # Linux/macOS
systeminfo | findstr /B /C:"OS"  # Windows
``` 