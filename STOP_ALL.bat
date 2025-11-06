@echo off
chcp 65001 >nul
title AI Forex Strategy Manager - Stopping All Services
color 0C

echo.
echo =========================================
echo   AI Forex Strategy Manager
echo   Stopping All Services
echo =========================================
echo.
echo Stopping all services...
echo.

REM Stop Node processes
echo [1/4] Stopping Node processes...
taskkill /F /IM node.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   ✓ Node processes stopped
) else (
    echo   ℹ No Node processes were running
)
echo.

REM Stop Python/Django processes
echo [2/4] Stopping Python (Django) processes...
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr "PID:"') do (
    taskkill /F /PID %%i >nul 2>&1
)
if %ERRORLEVEL% equ 0 (
    echo   ✓ Python processes stopped
) else (
    echo   ℹ No Python processes were running
)
echo.

REM Stop Celery processes
echo [3/4] Stopping Celery processes...
powershell -ExecutionPolicy Bypass -File "%~dp0stop_celery.ps1"
echo.

REM Optional: Stop Redis (commented out by default)
echo [4/4] Checking Redis...
echo   ℹ Redis is still running
echo   To stop Redis: docker stop redis
echo.

echo =========================================
echo   ✓ All services stopped!
echo =========================================
echo.
echo NOTE: Redis is still running.
echo To stop Redis: docker stop redis
echo.
pause
