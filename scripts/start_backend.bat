@echo off
REM Viewzenix1 Backend Startup Script for Windows
REM This script starts the Viewzenix1 backend API service

ECHO Starting Viewzenix1 Backend API...

REM Set environment variables if .env file doesn't exist
IF NOT EXIST "%~dp0..\.env" (
    ECHO No .env file found, using default environment variables
    SET FLASK_APP=src.backend.app
    SET FLASK_ENV=development
    SET DEBUG=True
    SET PORT=5000
)

REM Create logs directory if it doesn't exist
IF NOT EXIST "%~dp0..\logs" (
    ECHO Creating logs directory...
    mkdir "%~dp0..\logs"
)

REM Check if Python is installed
python --version > NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO Python is not installed or not in PATH. Please install Python 3.9 or higher.
    EXIT /B 1
)

REM Move to project root
CD /D "%~dp0.."

REM Install required packages if not already installed
ECHO Checking required packages...
pip install -r requirements.txt

ECHO Starting Backend API server on port %PORT%...
ECHO Access the health check endpoint at: http://localhost:%PORT%/api/health

REM Start the Flask application
python -m src.backend.run

ECHO If the server failed to start, check the logs directory for error information. 