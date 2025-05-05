# Frontend Configuration Templates

This directory contains template configuration files for the frontend environment.

## Available Templates

- `config.template.js` - Application configuration template
- `.env.template` - Environment variables template
- `Dockerfile.template` - Docker configuration template
- `docker-compose.yml.template` - Docker Compose configuration template
- `nginx.conf.template` - Nginx configuration template for production
- `start.ps1.template` - PowerShell startup script template
- `start.bat.template` - Windows Batch startup script template
- `start.sh.template` - Shell startup script template

## Usage

To use these templates:

1. Copy them to the frontend root directory
2. Remove the `.template` suffix
3. Customize them as needed

Example:

```bash
# Copy a template
cp templates/config.template.js ../config.js

# Customize it (optional)
nano ../config.js
```

Alternatively, use the migration script to copy and configure all templates automatically:

```bash
node scripts/migrate-environment.js
```

## Extending Templates

To add a new template:

1. Create the template file with a `.template` suffix
2. Add it to this directory
3. Update this README to include the new template
4. Update the migration script to handle the new template 