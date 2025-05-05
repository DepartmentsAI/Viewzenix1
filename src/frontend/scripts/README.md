# Frontend Utility Scripts

This directory contains utility scripts for the frontend environment.

## Available Scripts

- `migrate-environment.js` - Migrates your environment to the new configuration system

## Migration Script

The migration script helps you upgrade your frontend environment to the latest configuration system, which includes standardized:

- Configuration files
- Environment variables
- Startup scripts
- Docker configuration
- Verification tools

### Usage

```bash
# Basic migration
node scripts/migrate-environment.js

# Force migration (skip checks)
node scripts/migrate-environment.js --force
```

### What the Migration Script Does

1. **Backup** - Backs up all existing configuration files
2. **Copy Templates** - Copies new template files to their proper locations
3. **Migrate Environment Variables** - Preserves existing environment variables and adds missing ones
4. **Check Dependencies** - Verifies that all required dependencies are installed
5. **Run Verification** - Runs the verification script to check for any issues

### Exit Codes

- `0` - Migration completed successfully
- `1` - Migration failed (check error message)

## Extending Scripts

To add a new script:

1. Create the script file in this directory
2. Make it executable (`chmod +x script.js`) if needed
3. Update this README to include the new script
4. Add any necessary documentation 