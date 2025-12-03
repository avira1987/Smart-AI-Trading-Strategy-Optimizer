@echo off
REM Smart AI Trading Strategy Optimizer - Site Test Script (Batch)
REM This is a wrapper that calls the PowerShell test script

echo.
echo ========================================
echo   Smart AI Trading Strategy Optimizer
echo   Site Health Check & Test
echo ========================================
echo.

REM Check if PowerShell is available
where powershell >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PowerShell is not available!
    echo Please install PowerShell or use test_site.ps1 directly
    pause
    exit /b 1
)

REM Call PowerShell script
powershell -ExecutionPolicy Bypass -File "%~dp0test_site.ps1"

pause

