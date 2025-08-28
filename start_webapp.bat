@echo off
title NAB Skills Intelligence Platform - Startup
color 0B

REM Set the project directory and change to it
set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

REM Simple Python availability check
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ========================================================================
    echo                          ERROR: PYTHON NOT FOUND
    echo ========================================================================
    echo.
    echo Python is not installed or not in your system PATH.
    echo.
    echo Please install Python 3.8+ from: https://python.org/downloads
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    echo ========================================================================
    pause
    exit /b 1
)

REM Launch the webapp (all setup handled by Python script)
python run_webapp.py

REM Cleanup message after webapp stops
echo.
echo ========================================================================
echo [INFO] NAB Skills Intelligence Platform has stopped
echo [INFO] You can now safely close this window
echo ========================================================================
echo.
pause 