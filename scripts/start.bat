@echo off
docker compose up --build -d
if errorlevel 1 exit /b %errorlevel%
echo App started at http://127.0.0.1:8000
