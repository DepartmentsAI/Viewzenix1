#!/usr/bin/env python
"""
Viewzenix1 Backend Environment Checker

This diagnostic script checks for common configuration issues that might prevent
the Viewzenix1 backend API from starting correctly.

Usage:
    python backend_environment_check.py [--fix]

Options:
    --fix    Attempt to fix some common issues automatically
"""

import os
import sys
import platform
import subprocess
import importlib.util
import json
import socket
from pathlib import Path

# Define colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def disable_if_not_supported():
        """Disable colors if not supported by the terminal"""
        if sys.platform == 'win32':
            try:
                # Enable VT processing on Windows
                from ctypes import windll
                kernel32 = windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except:
                # If it fails, disable colors
                for attr in dir(Colors):
                    if not attr.startswith('_') and isinstance(getattr(Colors, attr), str):
                        setattr(Colors, attr, '')


class EnvironmentChecker:
    """Check Viewzenix1 backend environment for common issues"""
    
    def __init__(self, fix_issues=False):
        """Initialize the environment checker
        
        Args:
            fix_issues: Whether to attempt automatic fixes for some issues
        """
        Colors.disable_if_not_supported()
        self.fix_issues = fix_issues
        self.issues_found = 0
        self.issues_fixed = 0
        self.required_packages = [
            "flask",
            "sqlalchemy",
            "psycopg2",
            "flask_sqlalchemy",
            "flask_migrate",
            "flask_jwt_extended",
            "flask_cors",
            "pydantic",
            "gunicorn",
            "python-dotenv",
            "requests"
        ]
        self.required_env_vars = [
            "FLASK_APP",
            "DATABASE_URL",
            "SECRET_KEY",
            "JWT_SECRET_KEY"
        ]
        # Try to detect project root (where this script is running from)
        try:
            # Assume script is in /scripts directory
            self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        except:
            # Fallback to current working directory
            self.project_root = os.getcwd()
            
    def run_checks(self):
        """Run all environment checks"""
        print(f"{Colors.HEADER}{Colors.BOLD}Viewzenix1 Backend Environment Checker{Colors.ENDC}")
        print(f"{Colors.BOLD}{'=' * 50}{Colors.ENDC}")
        print(f"Running diagnostics at: {self.project_root}\n")
        
        self.check_python_version()
        self.check_dependencies()
        self.check_environment_variables()
        self.check_flask_app_file()
        self.check_database_connection()
        self.check_network_ports()
        self.check_file_permissions()
        self.check_directory_structure()
        
        # Print summary
        print(f"\n{Colors.BOLD}{'=' * 50}{Colors.ENDC}")
        if self.issues_found == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ All checks passed! Environment looks good.{Colors.ENDC}")
        else:
            print(f"{Colors.YELLOW}{Colors.BOLD}! Found {self.issues_found} issue(s), fixed {self.issues_fixed}.{Colors.ENDC}")
            if self.issues_found > self.issues_fixed:
                print(f"{Colors.YELLOW}Please fix the remaining issues manually.{Colors.ENDC}")
                return 1
        return 0
    
    def check_python_version(self):
        """Check Python version"""
        print(f"{Colors.BOLD}Checking Python version...{Colors.ENDC}")
        python_version = platform.python_version()
        python_implementation = platform.python_implementation()
        
        print(f"  Python version: {python_version}")
        print(f"  Implementation: {python_implementation}")
        
        major, minor, _ = [int(n) for n in python_version.split('.')]
        
        if major < 3 or (major == 3 and minor < 9):
            self.issues_found += 1
            print(f"{Colors.RED}✗ Python 3.9+ required, but {python_version} found.{Colors.ENDC}")
            print(f"  Recommendation: Install Python 3.9 or newer.")
        else:
            print(f"{Colors.GREEN}✓ Python version {python_version} is compatible.{Colors.ENDC}")
    
    def check_dependencies(self):
        """Check if required Python packages are installed"""
        print(f"\n{Colors.BOLD}Checking Python dependencies...{Colors.ENDC}")
        
        missing_packages = []
        
        for package in self.required_packages:
            spec = importlib.util.find_spec(package.split('[')[0])  # Handle packages with extras
            if spec is None:
                missing_packages.append(package)
                self.issues_found += 1
                print(f"{Colors.RED}✗ Missing required package: {package}{Colors.ENDC}")
            else:
                try:
                    module = importlib.import_module(package.split('[')[0])
                    version = getattr(module, '__version__', 'unknown')
                    print(f"{Colors.GREEN}✓ {package} (version: {version}){Colors.ENDC}")
                except ImportError:
                    missing_packages.append(package)
                    self.issues_found += 1
                    print(f"{Colors.RED}✗ Error importing package: {package}{Colors.ENDC}")
        
        if missing_packages and self.fix_issues:
            print(f"\n{Colors.YELLOW}Attempting to install missing packages...{Colors.ENDC}")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
                self.issues_fixed += len(missing_packages)
                print(f"{Colors.GREEN}✓ Successfully installed missing packages.{Colors.ENDC}")
            except subprocess.CalledProcessError:
                print(f"{Colors.RED}✗ Failed to install missing packages.{Colors.ENDC}")
                print(f"  Recommendation: Run 'pip install {' '.join(missing_packages)}'")
    
    def check_environment_variables(self):
        """Check if required environment variables are set"""
        print(f"\n{Colors.BOLD}Checking environment variables...{Colors.ENDC}")
        
        # Check for presence of .env file
        dotenv_path = os.path.join(self.project_root, '.env')
        has_dotenv = os.path.isfile(dotenv_path)
        env_vars_from_dotenv = {}
        
        if has_dotenv:
            print(f"{Colors.GREEN}✓ .env file found at {dotenv_path}{Colors.ENDC}")
            # Parse .env file content
            try:
                with open(dotenv_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#') or '=' not in line:
                            continue
                        key, value = line.split('=', 1)
                        env_vars_from_dotenv[key.strip()] = value.strip()
            except Exception as e:
                print(f"{Colors.RED}✗ Error reading .env file: {e}{Colors.ENDC}")
        else:
            print(f"{Colors.YELLOW}! No .env file found at {dotenv_path}{Colors.ENDC}")
            print(f"  Recommendation: Create a .env file with required environment variables.")
            self.issues_found += 1
            
            if self.fix_issues:
                try:
                    self._create_sample_env_file(dotenv_path)
                    print(f"{Colors.GREEN}✓ Created sample .env file at {dotenv_path}{Colors.ENDC}")
                    self.issues_fixed += 1
                    has_dotenv = True
                    # Read the newly created file
                    with open(dotenv_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith('#') or '=' not in line:
                                continue
                            key, value = line.split('=', 1)
                            env_vars_from_dotenv[key.strip()] = value.strip()
                except Exception as e:
                    print(f"{Colors.RED}✗ Failed to create .env file: {e}{Colors.ENDC}")
        
        # Check for required environment variables
        for var in self.required_env_vars:
            if var in os.environ:
                value = os.environ[var]
                # Mask sensitive values
                if var in ['SECRET_KEY', 'JWT_SECRET_KEY', 'BROKER_API_SECRET']:
                    value = value[:3] + '****' if len(value) > 3 else '****'
                print(f"{Colors.GREEN}✓ {var} is set in environment to: {value}{Colors.ENDC}")
            elif var in env_vars_from_dotenv:
                value = env_vars_from_dotenv[var]
                # Mask sensitive values
                if var in ['SECRET_KEY', 'JWT_SECRET_KEY', 'BROKER_API_SECRET']:
                    value = value[:3] + '****' if len(value) > 3 else '****'
                print(f"{Colors.YELLOW}! {var} found in .env file but not in environment: {value}{Colors.ENDC}")
                print(f"  Note: You may need to load these variables using python-dotenv or export them")
            else:
                print(f"{Colors.RED}✗ Required variable {var} not found in environment or .env file{Colors.ENDC}")
                self.issues_found += 1
                if self.fix_issues and has_dotenv:
                    # Only try to fix if we have a .env file (either existing or just created)
                    default_values = {
                        'FLASK_APP': 'src/backend/app.py',
                        'DATABASE_URL': 'postgresql://postgres:postgres@localhost:5432/viewzenix',
                        'SECRET_KEY': 'dev-' + os.urandom(8).hex(),
                        'JWT_SECRET_KEY': 'dev-' + os.urandom(8).hex(),
                    }
                    if var in default_values:
                        try:
                            with open(dotenv_path, 'a') as f:
                                f.write(f"\n{var}={default_values[var]}\n")
                            print(f"{Colors.GREEN}✓ Added {var} to .env file with default value{Colors.ENDC}")
                            self.issues_fixed += 1
                        except Exception as e:
                            print(f"{Colors.RED}✗ Failed to update .env file: {e}{Colors.ENDC}")
                    
        # Check FLASK_APP points to a valid file
        flask_app = os.environ.get('FLASK_APP') or env_vars_from_dotenv.get('FLASK_APP')
        if flask_app:
            flask_app_path = os.path.join(self.project_root, flask_app)
            if os.path.isfile(flask_app_path):
                print(f"{Colors.GREEN}✓ FLASK_APP points to valid file: {flask_app_path}{Colors.ENDC}")
            else:
                print(f"{Colors.RED}✗ FLASK_APP file not found at: {flask_app_path}{Colors.ENDC}")
                self.issues_found += 1
                print(f"  Recommendation: Set FLASK_APP to the correct path to your Flask application.")
    
    def check_flask_app_file(self):
        """Check if Flask app file is valid and can be imported"""
        print(f"\n{Colors.BOLD}Checking Flask application file...{Colors.ENDC}")
        
        # Get FLASK_APP from environment or .env
        flask_app = os.environ.get('FLASK_APP')
        dotenv_path = os.path.join(self.project_root, '.env')
        if not flask_app and os.path.isfile(dotenv_path):
            try:
                with open(dotenv_path, 'r') as f:
                    for line in f:
                        if line.strip().startswith('FLASK_APP='):
                            flask_app = line.strip().split('=', 1)[1]
                            break
            except:
                pass
        
        if not flask_app:
            print(f"{Colors.RED}✗ FLASK_APP not defined{Colors.ENDC}")
            self.issues_found += 1
            return
        
        # Check if file exists
        flask_app_path = os.path.join(self.project_root, flask_app)
        if not os.path.isfile(flask_app_path):
            print(f"{Colors.RED}✗ Flask application file not found at: {flask_app_path}{Colors.ENDC}")
            self.issues_found += 1
            return
        
        print(f"{Colors.GREEN}✓ Flask application file exists{Colors.ENDC}")
        
        # Try to parse Python file
        try:
            with open(flask_app_path, 'r') as f:
                content = f.read()
            compile(content, flask_app_path, 'exec')
            print(f"{Colors.GREEN}✓ Flask application file has valid Python syntax{Colors.ENDC}")
        except SyntaxError as e:
            print(f"{Colors.RED}✗ Flask application file has syntax errors: {e}{Colors.ENDC}")
            self.issues_found += 1
            return
        
        # Check for common Flask patterns
        try:
            with open(flask_app_path, 'r') as f:
                content = f.read()
            
            has_app = 'app = ' in content or 'def create_app' in content
            if has_app:
                print(f"{Colors.GREEN}✓ Flask application file contains app definition{Colors.ENDC}")
            else:
                print(f"{Colors.YELLOW}! Flask application file might not contain app definition{Colors.ENDC}")
                print(f"  Recommendation: Check if app is defined in another module.")
                self.issues_found += 1
        except:
            print(f"{Colors.YELLOW}! Could not analyze Flask application file content{Colors.ENDC}")
    
    def check_database_connection(self):
        """Check if database connection is possible"""
        print(f"\n{Colors.BOLD}Checking database connection...{Colors.ENDC}")
        
        # Get DATABASE_URL from environment or .env
        database_url = os.environ.get('DATABASE_URL')
        dotenv_path = os.path.join(self.project_root, '.env')
        if not database_url and os.path.isfile(dotenv_path):
            try:
                with open(dotenv_path, 'r') as f:
                    for line in f:
                        if line.strip().startswith('DATABASE_URL='):
                            database_url = line.strip().split('=', 1)[1]
                            break
            except:
                pass
        
        if not database_url:
            print(f"{Colors.RED}✗ DATABASE_URL not defined{Colors.ENDC}")
            self.issues_found += 1
            return
        
        # Mask password in URL for display
        display_url = database_url
        if '://' in database_url:
            parts = database_url.split('://')
            if '@' in parts[1]:
                auth_part = parts[1].split('@')[0]
                if ':' in auth_part:
                    username = auth_part.split(':')[0]
                    display_url = f"{parts[0]}://{username}:****@{parts[1].split('@')[1]}"
        
        print(f"  Database URL: {display_url}")
        
        # Check if required modules are installed
        try:
            import sqlalchemy
            from sqlalchemy import create_engine
            from sqlalchemy.sql import text
        except ImportError:
            print(f"{Colors.RED}✗ Required modules for database check not installed{Colors.ENDC}")
            print(f"  Recommendation: Install SQLAlchemy with 'pip install sqlalchemy'")
            self.issues_found += 1
            return
        
        # Try to connect to database
        try:
            # Create engine without pool to just test connection
            engine = create_engine(database_url, pool_size=1, max_overflow=0)
            with engine.connect() as conn:
                # Try a simple query
                result = conn.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    print(f"{Colors.GREEN}✓ Database connection successful{Colors.ENDC}")
                else:
                    print(f"{Colors.RED}✗ Database connection test returned unexpected result{Colors.ENDC}")
                    self.issues_found += 1
        except Exception as e:
            print(f"{Colors.RED}✗ Database connection failed: {e}{Colors.ENDC}")
            self.issues_found += 1
            
            # Check PostgreSQL-specific issues
            if 'postgresql' in database_url.lower() or 'postgres' in database_url.lower():
                try:
                    parts = database_url.split('/')
                    db_name = parts[-1].split('?')[0]  # Extract database name
                    host = parts[2].split('@')[-1].split(':')[0]  # Extract host
                    
                    print(f"\n{Colors.YELLOW}PostgreSQL-specific recommendations:{Colors.ENDC}")
                    print(f"  1. Check if PostgreSQL is running:")
                    if sys.platform == 'win32':
                        print(f"     - Check Services in Windows: PostgreSQL should be running")
                    else:
                        print(f"     - Run: systemctl status postgresql")
                    
                    print(f"  2. Check if database '{db_name}' exists:")
                    print(f"     - Run: psql -U postgres -c \"\\l\" | grep {db_name}")
                    
                    print(f"  3. Check if host '{host}' is allowed in pg_hba.conf")
                    print(f"  4. If using local database, try:")
                    print(f"     - DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/{db_name}")
                except:
                    # If parsing fails, just provide general advice
                    print(f"\n{Colors.YELLOW}Check PostgreSQL configuration:{Colors.ENDC}")
                    print(f"  - Ensure PostgreSQL is running")
                    print(f"  - Check database name, username and password")
                    print(f"  - Verify host and port accessibility")
    
    def check_network_ports(self):
        """Check if required network ports are available"""
        print(f"\n{Colors.BOLD}Checking network ports...{Colors.ENDC}")
        
        # Get PORT from environment or .env, default to 5000
        port = os.environ.get('PORT', '5000')
        dotenv_path = os.path.join(self.project_root, '.env')
        if os.path.isfile(dotenv_path):
            try:
                with open(dotenv_path, 'r') as f:
                    for line in f:
                        if line.strip().startswith('PORT='):
                            port = line.strip().split('=', 1)[1]
                            break
            except:
                pass
        
        try:
            port = int(port)
        except ValueError:
            print(f"{Colors.RED}✗ Invalid PORT value: {port}{Colors.ENDC}")
            self.issues_found += 1
            port = 5000  # Use default for testing
        
        print(f"  Checking if port {port} is available...")
        
        # Try to bind to the port
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', port))
            sock.close()
            print(f"{Colors.GREEN}✓ Port {port} is available{Colors.ENDC}")
        except socket.error:
            print(f"{Colors.RED}✗ Port {port} is already in use{Colors.ENDC}")
            self.issues_found += 1
            print(f"  Recommendation: Change PORT environment variable or stop the process using this port.")
            
            # Find what's using the port
            if sys.platform == 'win32':
                try:
                    result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
                    for line in result.stdout.splitlines():
                        if f":{port}" in line and "LISTENING" in line:
                            parts = line.split()
                            if len(parts) >= 5:
                                pid = parts[4]
                                print(f"  Process using port {port}: PID {pid}")
                                try:
                                    result = subprocess.run(['tasklist', '/FI', f"PID eq {pid}"], capture_output=True, text=True)
                                    process_info = result.stdout.splitlines()
                                    if len(process_info) > 1:
                                        print(f"  Process name: {process_info[1].split()[0]}")
                                except:
                                    pass
                except:
                    pass
            else:
                try:
                    result = subprocess.run(['lsof', '-i', f':{port}'], capture_output=True, text=True)
                    if result.stdout:
                        print(f"  Process using port {port}:")
                        print(f"  {result.stdout}")
                except:
                    pass
    
    def check_file_permissions(self):
        """Check file permissions for logs directory"""
        print(f"\n{Colors.BOLD}Checking file permissions...{Colors.ENDC}")
        
        logs_dir = os.path.join(self.project_root, 'logs')
        
        # Check if logs directory exists
        if os.path.isdir(logs_dir):
            print(f"{Colors.GREEN}✓ Logs directory exists: {logs_dir}{Colors.ENDC}")
            
            # Check if writable
            if os.access(logs_dir, os.W_OK):
                print(f"{Colors.GREEN}✓ Logs directory is writable{Colors.ENDC}")
            else:
                print(f"{Colors.RED}✗ Logs directory is not writable{Colors.ENDC}")
                self.issues_found += 1
                if self.fix_issues:
                    try:
                        if sys.platform != 'win32':
                            os.chmod(logs_dir, 0o755)
                            print(f"{Colors.GREEN}✓ Fixed logs directory permissions{Colors.ENDC}")
                            self.issues_fixed += 1
                        else:
                            # On Windows, permissions work differently
                            print(f"{Colors.YELLOW}! Cannot automatically fix permissions on Windows{Colors.ENDC}")
                    except Exception as e:
                        print(f"{Colors.RED}✗ Failed to fix logs directory permissions: {e}{Colors.ENDC}")
        else:
            print(f"{Colors.YELLOW}! Logs directory does not exist: {logs_dir}{Colors.ENDC}")
            print(f"  This might be normal if the app creates it on first run.")
            
            # Try to create logs directory
            if self.fix_issues:
                try:
                    os.makedirs(logs_dir, exist_ok=True)
                    print(f"{Colors.GREEN}✓ Created logs directory{Colors.ENDC}")
                    self.issues_fixed += 1
                except Exception as e:
                    print(f"{Colors.RED}✗ Failed to create logs directory: {e}{Colors.ENDC}")
                    self.issues_found += 1
    
    def check_directory_structure(self):
        """Check if required directories and files exist"""
        print(f"\n{Colors.BOLD}Checking directory structure...{Colors.ENDC}")
        
        # Add expected directory structure here
        required_paths = [
            'src/backend',
            'src/backend/api',
            'src/backend/models',
            'src/backend/services',
            'src/backend/utils',
            'tests/unit/backend'
        ]
        
        # Files that should exist
        required_files = [
            'requirements.txt'
        ]
        
        # Flask app file (from environment or default)
        flask_app = os.environ.get('FLASK_APP', 'src/backend/app.py')
        if flask_app:
            required_files.append(flask_app)
        
        # Check required directories
        for path in required_paths:
            full_path = os.path.join(self.project_root, path)
            if os.path.isdir(full_path):
                print(f"{Colors.GREEN}✓ Directory exists: {path}{Colors.ENDC}")
            else:
                print(f"{Colors.YELLOW}! Directory not found: {path}{Colors.ENDC}")
                self.issues_found += 1
                
                if self.fix_issues:
                    try:
                        os.makedirs(full_path, exist_ok=True)
                        print(f"{Colors.GREEN}✓ Created directory: {path}{Colors.ENDC}")
                        self.issues_fixed += 1
                    except Exception as e:
                        print(f"{Colors.RED}✗ Failed to create directory {path}: {e}{Colors.ENDC}")
        
        # Check required files
        for filepath in required_files:
            full_path = os.path.join(self.project_root, filepath)
            if os.path.isfile(full_path):
                print(f"{Colors.GREEN}✓ File exists: {filepath}{Colors.ENDC}")
            else:
                print(f"{Colors.RED}✗ File not found: {filepath}{Colors.ENDC}")
                self.issues_found += 1
    
    def _create_sample_env_file(self, dotenv_path):
        """Create a sample .env file with default values
        
        Args:
            dotenv_path: Path to the .env file to create
        """
        with open(dotenv_path, 'w') as f:
            f.write("""# Viewzenix1 Backend API Environment Variables
# Created by backend_environment_check.py

# Application Settings
FLASK_APP=src/backend/app.py
FLASK_ENV=development
DEBUG=True
SECRET_KEY=dev-""" + os.urandom(16).hex() + """

# Server Configuration
HOST=0.0.0.0
PORT=5000

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/viewzenix

# Security Settings
JWT_SECRET_KEY=dev-""" + os.urandom(16).hex() + """
JWT_ACCESS_TOKEN_EXPIRES=3600

# Logging Configuration
LOG_LEVEL=DEBUG
LOG_FORMAT=json
LOG_DIR=logs
""")


def main():
    """Main entry point of the script"""
    fix_issues = '--fix' in sys.argv
    checker = EnvironmentChecker(fix_issues=fix_issues)
    exit_code = checker.run_checks()
    
    if exit_code == 0:
        print(f"\nAll checks completed successfully. Your environment should be ready to run the backend API.")
        print(f"\nTo start the backend API, run:")
        print(f"  flask run --host=0.0.0.0 --port=5000")
    else:
        print(f"\nSome issues were found. Please fix them and run this script again.")
        print(f"\nFor detailed setup instructions, refer to:")
        print(f"  /docs/api/backend_startup_guide.md")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main() 