@echo off
echo Starting Frontend Application on port 3000...
cd /d %~dp0
SET PORT=3000
SET HOST=0.0.0.0
SET REACT_APP_API_URL=http://localhost:5000/api/v1
echo Environment variables set:
echo Port: %PORT%
echo Host: %HOST%
echo API URL: %REACT_APP_API_URL%
call npm start 