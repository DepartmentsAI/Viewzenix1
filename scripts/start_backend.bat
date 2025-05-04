@echo off
echo ================================================
echo Starting Viewzenix1 Backend API Server
echo ================================================

:: Set the current directory to the repo root
cd %~dp0\..

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python and ensure it's added to your PATH
    pause
    exit /b 1
)

:: Check if .env file exists
if not exist .env (
    echo WARNING: .env file not found in %CD%
    echo Creating a default .env file with required settings...
    
    echo # Flask Application Settings > .env
    echo FLASK_APP=src/backend/app.py >> .env
    echo FLASK_ENV=development >> .env
    echo FLASK_DEBUG=True >> .env
    echo PORT=5000 >> .env
    echo # Alpaca API Credentials >> .env
    echo APCA_API_KEY_ID=PKG1F8EEMI2HWAFFWSD7 >> .env
    echo APCA_API_SECRET_KEY=PKG1F8EEMI2HWAFFWSD7 >> .env
    echo APCA_API_BASE_URL=https://paper-api.alpaca.markets/v2 >> .env
    
    echo Created .env file with default settings
)

:: Create logs directory if it doesn't exist
if not exist logs mkdir logs

echo Validating environment setup...
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'Environment loaded: FLASK_APP={os.environ.get(\"FLASK_APP\", \"Not set\")}'); print(f'Alpaca API Key: {os.environ.get(\"APCA_API_KEY_ID\", \"Not set\")[:5]}...')"

echo Validating Alpaca API credentials...
python src/backend/utils/alpaca_validator.py

echo Starting backend API server...
echo Server output will be logged to logs/backend.log
python src/backend/run.py > logs/backend.log 2>&1

echo If the server doesn't start, check logs/backend.log for errors
pause 