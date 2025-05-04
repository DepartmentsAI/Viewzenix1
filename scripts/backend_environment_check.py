#!/usr/bin/env python3
"""
Viewzenix1 Backend Environment Checker

This script checks the environment for common issues that may prevent
the Viewzenix1 backend API from starting or running correctly.
"""

import os
import sys
import socket
import platform
import subprocess
import importlib.util
from pathlib import Path


class EnvironmentChecker:
    """Checks the environment for potential issues with the backend API."""

    def __init__(self):
        """Initialize the environment checker."""
        self.project_root = self._find_project_root()
        self.issues_found = 0
        self.warnings_found = 0
        
        print(f"Viewzenix1 Backend Environment Checker")
        print(f"======================================")
        print(f"Project root: {self.project_root}\n")
        
    def _find_project_root(self):
        """Find the project root directory."""
        # Start with the directory this script is in
        current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        
        # Go up one level (assuming script is in /scripts directory)
        return current_dir.parent
    
    def check_environment(self):
        """Run all environment checks."""
        self.check_python_version()
        self.check_required_modules()
        self.check_file_structure()
        self.check_environment_variables()
        self.check_database_connection()
        self.check_port_availability()
        self.check_directory_permissions()
        
        # Print summary
        print("\nCheck completed!")
        if self.issues_found == 0 and self.warnings_found == 0:
            print("✅ No issues found! The environment appears to be correctly configured.")
        else:
            print(f"❌ Found {self.issues_found} critical issues and {self.warnings_found} warnings.")
            print("Please address these issues before starting the backend API.")
    
    def check_python_version(self):
        """Check if Python version is compatible."""
        print("Checking Python version...")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 9):
            self.issues_found += 1
            print(f"❌ Python version {version.major}.{version.minor}.{version.micro} is not supported.")
            print("   Please use Python 3.9 or higher.\n")
        else:
            print(f"✅ Python version {version.major}.{version.minor}.{version.micro} is supported.\n")
    
    def check_required_modules(self):
        """Check if required Python modules are installed."""
        print("Checking required Python modules...")
        
        required_modules = [
            'flask', 
            'sqlalchemy', 
            'psycopg2-binary', 
            'pyjwt', 
            'python-dotenv',
            'requests'
        ]
        
        missing_modules = []
        
        for module in required_modules:
            if importlib.util.find_spec(module.split('-')[0]) is None:
                missing_modules.append(module)
        
        if missing_modules:
            self.issues_found += 1
            print(f"❌ Missing required Python modules: {', '.join(missing_modules)}")
            print("   Please install them using:")
            print(f"   pip install {' '.join(missing_modules)}\n")
        else:
            print(f"✅ All required Python modules are installed.\n")
    
    def check_file_structure(self):
        """Check if the project file structure is correct."""
        print("Checking project file structure...")
        
        required_files = [
            'src/backend/app.py',
            'src/backend/run.py',
            'src/backend/__init__.py',
            'src/backend/api/health.py',
            'requirements.txt'
        ]
        
        missing_files = []
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.issues_found += 1
            print(f"❌ Missing required files: {', '.join(missing_files)}")
            print("   The project structure appears to be incomplete.\n")
        else:
            print(f"✅ Project file structure appears to be correct.\n")
    
    def check_environment_variables(self):
        """Check if required environment variables are set."""
        print("Checking environment variables...")
        
        required_vars = [
            'FLASK_APP',
            'PORT'
        ]
        
        recommended_vars = [
            'FLASK_ENV',
            'DEBUG',
            'DATABASE_URL',
            'SECRET_KEY'
        ]
        
        missing_required = []
        missing_recommended = []
        
        for var in required_vars:
            if var not in os.environ:
                missing_required.append(var)
        
        for var in recommended_vars:
            if var not in os.environ:
                missing_recommended.append(var)
        
        if missing_required:
            self.issues_found += 1
            print(f"❌ Missing required environment variables: {', '.join(missing_required)}")
            print("   These variables must be set for the application to run correctly.\n")
        else:
            print(f"✅ All required environment variables are set.")
        
        if missing_recommended:
            self.warnings_found += 1
            print(f"⚠️ Missing recommended environment variables: {', '.join(missing_recommended)}")
            print("   The application may use default values which might not be suitable for your environment.\n")
        else:
            print(f"✅ All recommended environment variables are set.\n")
        
        # Check .env file
        env_file = self.project_root / '.env'
        if not env_file.exists():
            self.warnings_found += 1
            print(f"⚠️ No .env file found at {env_file}")
            print("   Consider creating one to store your environment variables.\n")
        else:
            print(f"✅ Found .env file: {env_file}\n")
    
    def check_database_connection(self):
        """Check database connection if DATABASE_URL is set."""
        print("Checking database connection...")
        
        if 'DATABASE_URL' not in os.environ:
            self.warnings_found += 1
            print("⚠️ DATABASE_URL environment variable is not set.")
            print("   Skipping database connection check.\n")
            return
        
        db_url = os.environ['DATABASE_URL']
        
        # Check if it's PostgreSQL
        if 'postgresql' in db_url:
            try:
                # Try to import psycopg2
                import psycopg2
                
                # Check if pg_isready is available on the system
                pg_isready_available = False
                
                try:
                    if sys.platform == 'win32':
                        subprocess.run(['where', 'pg_isready'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    else:
                        subprocess.run(['which', 'pg_isready'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    pg_isready_available = True
                except subprocess.CalledProcessError:
                    pass
                
                if pg_isready_available:
                    # Extract host and port from DATABASE_URL
                    import re
                    match = re.search(r'postgresql://.*?@([^:]+):(\d+)/', db_url)
                    
                    if match:
                        host, port = match.groups()
                        
                        # Check if PostgreSQL is running
                        try:
                            if sys.platform == 'win32':
                                result = subprocess.run(['pg_isready', '-h', host, '-p', port], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            else:
                                result = subprocess.run(['pg_isready', '-h', host, '-p', port], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            
                            if result.returncode == 0:
                                print(f"✅ PostgreSQL server is running on {host}:{port}.\n")
                            else:
                                self.issues_found += 1
                                print(f"❌ PostgreSQL server is not running on {host}:{port}.")
                                print("   Please start your PostgreSQL server.\n")
                        except Exception as e:
                            self.warnings_found += 1
                            print(f"⚠️ Error checking PostgreSQL server: {str(e)}")
                            print("   Please ensure your PostgreSQL server is running.\n")
                    else:
                        self.warnings_found += 1
                        print(f"⚠️ Could not parse host and port from DATABASE_URL.")
                        print("   Please ensure your DATABASE_URL is correctly formatted.\n")
                else:
                    self.warnings_found += 1
                    print("⚠️ pg_isready command not found. Cannot check PostgreSQL server status.")
                    print("   Please ensure your PostgreSQL server is running.\n")
            
            except ImportError:
                self.issues_found += 1
                print("❌ psycopg2 module is not installed.")
                print("   Please install it using: pip install psycopg2-binary\n")
        else:
            self.warnings_found += 1
            print(f"⚠️ Non-PostgreSQL database URL detected: {db_url[:10]}...")
            print("   This script only supports checking PostgreSQL connections.\n")
    
    def check_port_availability(self):
        """Check if the specified port is available."""
        print("Checking port availability...")
        
        port = int(os.environ.get('PORT', 5000))
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:
            self.issues_found += 1
            print(f"❌ Port {port} is already in use.")
            print(f"   Please either stop the process using port {port} or set a different port.")
            
            # Try to identify the process using the port
            try:
                if sys.platform == 'win32':
                    print("   You can use this command to find the process:")
                    print(f"   netstat -ano | findstr :{port}")
                else:
                    print("   You can use these commands to find and kill the process:")
                    print(f"   lsof -i :{port}")
                    print(f"   kill $(lsof -t -i :{port})")
                print("\n")
            except Exception:
                pass
        else:
            print(f"✅ Port {port} is available.\n")
    
    def check_directory_permissions(self):
        """Check if the application has permission to write to key directories."""
        print("Checking directory permissions...")
        
        directories_to_check = [
            'logs',
            'src/backend',
            'src/backend/api'
        ]
        
        for directory in directories_to_check:
            dir_path = self.project_root / directory
            
            # Create directory if it doesn't exist (especially for logs)
            if not dir_path.exists() and directory == 'logs':
                try:
                    dir_path.mkdir(parents=True)
                    print(f"✅ Created logs directory: {dir_path}")
                except Exception as e:
                    self.issues_found += 1
                    print(f"❌ Failed to create logs directory: {dir_path}")
                    print(f"   Error: {str(e)}")
                    continue
            
            # Skip if directory doesn't exist
            if not dir_path.exists():
                continue
            
            # Check read permission
            if not os.access(dir_path, os.R_OK):
                self.issues_found += 1
                print(f"❌ No read permission for directory: {dir_path}")
            
            # Check write permission for logs directory
            if directory == 'logs' and not os.access(dir_path, os.W_OK):
                self.issues_found += 1
                print(f"❌ No write permission for logs directory: {dir_path}")
                print("   The application needs to write to this directory.")
        
        print("✅ Directory permissions check completed.\n")


if __name__ == "__main__":
    checker = EnvironmentChecker()
    checker.check_environment() 