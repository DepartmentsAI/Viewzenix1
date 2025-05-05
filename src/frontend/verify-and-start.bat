@echo off
echo Viewzenix1 Frontend Verification and Auto-Start
echo ==============================================
echo.

:: Check if Node.js is installed
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo Error: Node.js is not installed or not in PATH.
  echo Please install Node.js from https://nodejs.org/
  exit /b 1
)

:: Run the verification and auto-start script
node verify-and-start.js

:: If the script fails, print a message
if %ERRORLEVEL% NEQ 0 (
  echo.
  echo Error: Frontend verification failed with error code %ERRORLEVEL%.
  echo Please check the log output above for details.
  exit /b %ERRORLEVEL%
)

exit /b 0 