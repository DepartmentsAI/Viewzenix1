#!/usr/bin/env node
/**
 * Frontend Environment Migration Script
 * 
 * This script helps migrate from older environment setups to the new
 * standardized environment configuration system.
 * 
 * Usage:
 *   node scripts/migrate-environment.js [--force]
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// CLI arguments
const args = process.argv.slice(2);
const FORCE_MODE = args.includes('--force');

// Colors for output
const colors = {
  reset: "\x1b[0m",
  bright: "\x1b[1m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m"
};

// Log functions
function log(message, type = 'info') {
  switch (type) {
    case 'error':
      console.error(`${colors.red}✘ Error: ${message}${colors.reset}`);
      break;
    case 'warning':
      console.warn(`${colors.yellow}⚠ Warning: ${message}${colors.reset}`);
      break;
    case 'success':
      console.log(`${colors.green}✓ ${message}${colors.reset}`);
      break;
    case 'header':
      console.log(`\n${colors.bright}${message}${colors.reset}`);
      break;
    case 'step':
      console.log(`${colors.blue}→ ${message}${colors.reset}`);
      break;
    default:
      console.log(`  ${message}`);
  }
}

// Main migration function
async function migrateEnvironment() {
  log('FRONTEND ENVIRONMENT MIGRATION', 'header');
  log(`This script will migrate your environment to the latest configuration system.`);
  log(`Working directory: ${process.cwd()}`);
  
  // Step 1: Check if we're in the right directory
  checkDirectory();
  
  // Step 2: Backup existing files
  backupExistingFiles();
  
  // Step 3: Copy new template files
  copyTemplateFiles();
  
  // Step 4: Migrate existing environment variables
  migrateEnvironmentVariables();
  
  // Step 5: Install dependencies
  installDependencies();
  
  // Step 6: Run verification
  runVerification();
  
  // Done!
  log('MIGRATION COMPLETE', 'header');
  log('Your frontend environment has been migrated to the new configuration system.', 'success');
  log('Please run the verification script to ensure everything is working correctly:');
  log('  npm run verify');
}

// Check if we're in the right directory
function checkDirectory() {
  log('Checking working directory...', 'step');
  
  const packageJsonPath = path.resolve(process.cwd(), 'package.json');
  if (!fs.existsSync(packageJsonPath)) {
    log('package.json not found. Make sure you are in the frontend directory.', 'error');
    log('Migration aborted.');
    process.exit(1);
  }
  
  try {
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    if (packageJson.name !== 'trading-webhook-platform') {
      log(`Unexpected package name: ${packageJson.name}`, 'warning');
      if (!FORCE_MODE) {
        log('This does not appear to be the frontend directory. Use --force to continue anyway.', 'error');
        log('Migration aborted.');
        process.exit(1);
      }
    }
  } catch (error) {
    log(`Error reading package.json: ${error.message}`, 'error');
    log('Migration aborted.');
    process.exit(1);
  }
  
  log('Working directory verified.', 'success');
}

// Backup existing files
function backupExistingFiles() {
  log('Backing up existing files...', 'step');
  
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const backupDir = path.resolve(process.cwd(), `backup-${timestamp}`);
  
  // Create backup directory
  if (!fs.existsSync(backupDir)) {
    fs.mkdirSync(backupDir);
  }
  
  // Files to backup
  const filesToBackup = [
    'config.js',
    '.env',
    'start.ps1',
    'start.bat',
    'start.sh',
    'health-check.js',
    'docker-compose.yml',
    'Dockerfile',
    'nginx.conf'
  ];
  
  let backupCount = 0;
  
  // Copy files to backup directory
  filesToBackup.forEach(file => {
    const filePath = path.resolve(process.cwd(), file);
    if (fs.existsSync(filePath)) {
      const destPath = path.resolve(backupDir, file);
      fs.copyFileSync(filePath, destPath);
      backupCount++;
      log(`Backed up ${file}`);
    }
  });
  
  if (backupCount === 0) {
    log('No files found to backup.', 'warning');
  } else {
    log(`Backed up ${backupCount} files to ${backupDir}`, 'success');
  }
}

// Copy template files
function copyTemplateFiles() {
  log('Copying template files...', 'step');
  
  // Check if template files exist
  const templateDir = path.resolve(__dirname, '../templates');
  if (!fs.existsSync(templateDir)) {
    // If templates directory doesn't exist, we'll look for template files in the current directory
    log('Templates directory not found, looking for template files in current directory...', 'warning');
    
    // Files to check for
    const templateFiles = [
      'config.template.js',
      'start.ps1',
      'start.bat',
      'start.sh',
      'health-check.js',
      'verify-environment.js',
      'docker-compose.yml',
      'Dockerfile',
      'nginx.conf'
    ];
    
    let templateCount = 0;
    
    // Check if template files exist
    templateFiles.forEach(file => {
      const templatePath = path.resolve(process.cwd(), file);
      const targetFile = file.replace('.template', '');
      const targetPath = path.resolve(process.cwd(), targetFile);
      
      if (fs.existsSync(templatePath) && !fs.existsSync(targetPath)) {
        fs.copyFileSync(templatePath, targetPath);
        templateCount++;
        log(`Created ${targetFile}`);
      }
    });
    
    if (templateCount === 0) {
      log('No template files found.', 'warning');
      log('You may need to manually copy configuration files.', 'warning');
    } else {
      log(`Copied ${templateCount} template files`, 'success');
    }
  } else {
    // Copy from templates directory
    const templateFiles = fs.readdirSync(templateDir);
    let templateCount = 0;
    
    templateFiles.forEach(file => {
      const templatePath = path.resolve(templateDir, file);
      const targetFile = file.replace('.template', '');
      const targetPath = path.resolve(process.cwd(), targetFile);
      
      fs.copyFileSync(templatePath, targetPath);
      templateCount++;
      log(`Created ${targetFile}`);
    });
    
    log(`Copied ${templateCount} template files`, 'success');
  }
}

// Migrate environment variables
function migrateEnvironmentVariables() {
  log('Migrating environment variables...', 'step');
  
  // Check if .env file exists
  const envPath = path.resolve(process.cwd(), '.env');
  const newEnvPath = path.resolve(process.cwd(), '.env.new');
  
  if (!fs.existsSync(envPath)) {
    // Create new .env file from template
    const envTemplatePath = path.resolve(process.cwd(), '.env.template');
    if (fs.existsSync(envTemplatePath)) {
      fs.copyFileSync(envTemplatePath, envPath);
      log('Created new .env file from template', 'success');
    } else {
      // Create basic .env file
      const basicEnv = 
`# Frontend Environment Variables
REACT_APP_API_URL=http://localhost:5000/api
PORT=3000
HOST=0.0.0.0
`;
      fs.writeFileSync(envPath, basicEnv);
      log('Created new basic .env file', 'success');
    }
    return;
  }
  
  // Read existing .env file
  const envContent = fs.readFileSync(envPath, 'utf8');
  const envLines = envContent.split('\n');
  
  // Required variables
  const requiredVars = ['REACT_APP_API_URL', 'PORT', 'HOST'];
  const foundVars = [];
  const newEnvLines = [];
  
  // Check for existing variables
  envLines.forEach(line => {
    // Keep comments and blank lines
    if (line.trim() === '' || line.trim().startsWith('#')) {
      newEnvLines.push(line);
      return;
    }
    
    const match = line.match(/^\s*([\w.-]+)\s*=\s*(.*)?\s*$/);
    if (match) {
      const key = match[1];
      if (requiredVars.includes(key)) {
        foundVars.push(key);
      }
      newEnvLines.push(line);
    }
  });
  
  // Add missing required variables
  const missingVars = requiredVars.filter(v => !foundVars.includes(v));
  if (missingVars.length > 0) {
    newEnvLines.push('');
    newEnvLines.push('# Added by migration script');
    
    missingVars.forEach(v => {
      switch (v) {
        case 'REACT_APP_API_URL':
          newEnvLines.push('REACT_APP_API_URL=http://localhost:5000/api');
          break;
        case 'PORT':
          newEnvLines.push('PORT=3000');
          break;
        case 'HOST':
          newEnvLines.push('HOST=0.0.0.0');
          break;
      }
    });
    
    // Write new .env file
    fs.writeFileSync(envPath, newEnvLines.join('\n'));
    log(`Added ${missingVars.length} missing environment variables.`, 'success');
  } else {
    log('All required environment variables found.', 'success');
  }
}

// Install dependencies
function installDependencies() {
  log('Checking dependencies...', 'step');
  
  // Check if node_modules exists
  const nodeModulesPath = path.resolve(process.cwd(), 'node_modules');
  if (!fs.existsSync(nodeModulesPath)) {
    log('node_modules directory not found, running npm install...', 'warning');
    try {
      execSync('npm install', { stdio: 'inherit' });
      log('Dependencies installed successfully.', 'success');
    } catch (error) {
      log(`Error installing dependencies: ${error.message}`, 'error');
      log('You may need to manually run npm install.', 'warning');
    }
  } else {
    log('Dependencies already installed.', 'success');
  }
}

// Run verification
function runVerification() {
  log('Running environment verification...', 'step');
  
  // Check if verification script exists
  const verifyPath = path.resolve(process.cwd(), 'verify-environment.js');
  if (!fs.existsSync(verifyPath)) {
    log('Verification script not found.', 'warning');
    log('You should run verification manually after migration.', 'warning');
    return;
  }
  
  try {
    log('Running verification script...');
    execSync('node verify-environment.js', { stdio: 'inherit' });
    log('Verification complete.', 'success');
  } catch (error) {
    log(`Verification failed: ${error.message}`, 'error');
    log('Please address the issues reported by the verification script.', 'warning');
  }
}

// Run migration
migrateEnvironment().catch(error => {
  log(`Migration failed: ${error.message}`, 'error');
  log('Please check the error message and try again.', 'warning');
}); 