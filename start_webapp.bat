@echo off
title NAB Skills Intelligence Platform - Startup
color 0B

echo.
echo ========================================================================
echo                    NAB SKILLS INTELLIGENCE PLATFORM
echo                          Local Development Server
echo ========================================================================
echo.

REM Get the current user's username
set USERNAME=%USERNAME%

REM Set the project directory (assuming bat file is in project root)
set PROJECT_DIR=%~dp0

REM Change to project directory
cd /d "%PROJECT_DIR%"

echo [INFO] Starting NAB Skills Intelligence Platform...
echo [INFO] User: %USERNAME%
echo [INFO] Project Directory: %PROJECT_DIR%
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo [ERROR] Please install Python 3.8+ and add it to your PATH
    echo.
    pause
    exit /b 1
)

REM Skip virtual environment - use system Python directly
echo [INFO] Using system Python installation...
echo [INFO] Package installation will be handled by the webapp script...

echo.
echo [SUCCESS] Environment ready!
echo [INFO] Starting NAB Skills Intelligence Platform webapp...
echo.
echo ========================================================================
echo                          *** IMPORTANT WARNING ***
echo.
echo              DO NOT CLOSE THIS WINDOW WHILE USING THE WEBAPP!
echo.
echo   Closing this window will stop the NAB Skills Intelligence Platform
echo   Your browser will continue to show the page but it will stop working
echo.
echo   To stop the webapp: Press Ctrl+C in this window, then close it
echo ========================================================================
echo.
echo [INFO] Webapp is starting... Please wait for browser to open...

REM Run the webapp
python run_webapp.py

echo.
echo ========================================================================
echo [INFO] NAB Skills Intelligence Platform has stopped
echo [INFO] You can now safely close this window
echo ========================================================================
echo.
pause 