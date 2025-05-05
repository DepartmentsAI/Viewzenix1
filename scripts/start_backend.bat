@echo off
:: Viewzenix1 Backend API Startup Script for Windows
:: 
:: Usage:
::    start_backend.bat [--prod|--dev] [--port=PORT]
::
:: Options:
::    --prod        Start in production mode
::    --dev         Start in development mode (default)
::    --port=PORT   Specify port to listen on (default: 5000)
::    --help        Show this help message

:: Default configuration
set MODE=development
set PORT=5000
set HOST=0.0.0.0
set WORKERS=4

:: Parse command line arguments
:parse_args
if "%~1"=="" goto :done_args
if "%~1"=="--prod" (
    set MODE=production
    shift
    goto :parse_args
)
if "%~1"=="--dev" (
    set MODE=development
    shift
    goto :parse_args
)
if "%~1"=="--help" (
    echo Viewzenix1 Backend API Startup Script
    echo.
    echo Usage:
    echo    start_backend.bat [--prod^|--dev] [--port=PORT]
    echo.
    echo Options:
    echo    --prod        Start in production mode
    echo    --dev         Start in development mode (default)
    echo    --port=PORT   Specify port to listen on (default: 5000)
    echo    --help        Show this help message
    exit /b 0
)
set arg=%~1
if "%arg:~0,7%"=="--port=" (
    set PORT=%arg:~7%
    shift
    goto :parse_args
)
echo Unknown option: %~1
echo Use --help for usage information
exit /b 1
:done_args

:: Set working directory to project root
pushd %~dp0..
set PROJECT_ROOT=%CD%
echo Working directory: %PROJECT_ROOT%

:: Check for virtual environment
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
    if errorlevel 1 (
        echo Error: Could not activate virtual environment
        exit /b 1
    )
)

:: Load environment variables from .env file if it exists
if exist .env (
    echo Loading environment variables from .env file...
    for /F "tokens=*" %%A in (.env) do (
        set line=%%A
        if not "!line:~0,1!"=="#" (
            for /F "tokens=1,2 delims==" %%B in ("!line!") do (
                if not "%%B"=="" if not "%%C"=="" (
                    set %%B=%%C
                )
            )
        )
    )
) else (
    echo Warning: No .env file found. Using default environment variables.
    :: Set default environment variables if not already set
    if not defined FLASK_APP set FLASK_APP=src\backend\app.py
    if not defined FLASK_ENV set FLASK_ENV=%MODE%
)

:: Create logs directory if it doesn't exist
if not exist logs mkdir logs

:: Check Flask app file exists
if not exist "%FLASK_APP%" (
    echo Error: Flask application file not found at %FLASK_APP%
    exit /b 1
)

:: Run environment check script if it exists
if exist scripts\backend_environment_check.py (
    echo Running environment check...
    python scripts\backend_environment_check.py
    if errorlevel 1 (
        echo Warning: Environment check reported issues
    )
)

:: Start server
echo Starting Viewzenix1 Backend API server in %MODE% mode on %HOST%:%PORT%...

if "%MODE%"=="production" (
    :: Production mode uses waitress (a WSGI server for Windows)
    echo Starting with waitress (production mode)...
    where waitress-serve >nul 2>&1
    if errorlevel 1 (
        echo Error: waitress not found. Install with 'pip install waitress'
        exit /b 1
    )
    waitress-serve --host=%HOST% --port=%PORT% "src.backend.app:create_app()" > logs\server.log 2>&1
) else (
    :: Development mode uses Flask's built-in server
    echo Starting with Flask development server...
    set FLASK_ENV=development
    set FLASK_DEBUG=1
    flask run --host=%HOST% --port=%PORT%
)

popd 