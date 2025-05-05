# Frontend Environment Verification Guide

This guide explains how to use the environment verification tools to diagnose and fix frontend setup issues.

## Overview

The frontend environment verification system consists of:

1. **Verification Scripts**: Command-line tools to check environment health
2. **Automated Tests**: Jest-based tests for CI/CD integration
3. **Runtime Checks**: Browser-side verification of requirements

## Getting Started

### Basic Verification

Run the verification script to get a comprehensive health check of your environment:

```bash
# In the frontend directory
npm run verify
```

This will:
- Check Node.js version compatibility
- Verify all required files exist
- Validate configuration settings
- Check environment variables
- Verify dependencies are installed
- Test Docker configuration
- Validate API connectivity (if available)

### Verification in CI/CD Pipelines

For CI/CD environments, use the silent mode:

```bash
npm run verify:ci
```

This runs the same checks but:
- Produces minimal output (errors only)
- Returns non-zero exit code on failure
- Skips API connectivity tests by default

### Running Environment Tests

To run the Jest-based tests:

```bash
npm run test:env
```

## Verification Results

The verification script produces a detailed report with three types of results:

1. **Passed**: Requirements that are correctly satisfied
2. **Warnings**: Non-critical issues that should be addressed
3. **Failures**: Critical issues that must be fixed

## Common Issues and Solutions

### Node.js Version Problems

**Issue**: `Node.js version v12.x is below recommended (>= 14.x)`

**Solution**: Install Node.js 14.x or later:
```bash
# Using nvm (recommended)
nvm install 14
nvm use 14

# Or download from nodejs.org
```

### Missing Configuration

**Issue**: `config.js not found` or `Configuration missing required properties`

**Solution**: 
1. Copy the template configuration: `cp config.template.js config.js`
2. Edit config.js to include required values
3. Ensure `api.baseUrl` is properly formatted as a URL

### Environment Variables

**Issue**: `Missing recommended environment variables`

**Solution**: Create or update your `.env` file:
```
REACT_APP_API_URL=http://localhost:5000/api
PORT=3000
HOST=0.0.0.0
```

### Package Dependencies

**Issue**: `Missing critical dependencies` or `node_modules directory not found`

**Solution**: Install dependencies:
```bash
npm install
```

### Docker Issues

**Issue**: Docker configuration missing or incomplete

**Solution**:
1. Ensure Docker is installed and running
2. Check that `Dockerfile`, `docker-compose.yml`, and `nginx.conf` exist
3. Run Docker with: `docker-compose up`

## Advanced Usage

### Custom Verification

You can customize the verification process:

```bash
# Skip API connectivity checks
SKIP_API_TESTS=true npm run verify

# Verify only specific parts
node verify-environment.js --module=dependencies,config

# Change exit behavior
node verify-environment.js --no-exit-on-error
```

### Integration with QA Tests

QA can incorporate the verification into test workflows:

```js
// In a test setup file
beforeAll(async () => {
  const { verifyEnvironment } = require('../verify-environment');
  const results = await verifyEnvironment({ silent: true });
  
  if (results.failed.length > 0) {
    console.error('Environment verification failed:', results.failed);
    throw new Error('Environment not properly configured');
  }
});
```

## Extending the Verification System

To add new checks:

1. Add a new verification function in `verify-environment.js`
2. Add corresponding Jest tests in `tests/environment.test.js`
3. Update this documentation with the new check details

## Troubleshooting

For detailed debugging, run:

```bash
DEBUG=verify:* npm run verify
```

If you need help interpreting results, contact the Frontend team. 