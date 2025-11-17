@echo off
REM Smart AI Trading Strategy Optimizer - Start Script (Batch)
REM This is a wrapper that calls the PowerShell script

echo.
echo ========================================
echo   Smart AI Trading Strategy Optimizer
echo   Starting All Services...
echo ========================================
echo.

REM Check if PowerShell is available
where powershell >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PowerShell is not available!
    echo Please install PowerShell or use start.ps1 directly
    pause
    exit /b 1
)

REM Call PowerShell script
powershell -ExecutionPolicy Bypass -File "%~dp0start.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to start services
    pause
    exit /b 1
)

