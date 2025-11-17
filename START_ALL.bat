@echo off
chcp 65001 >nul
title AI Forex Strategy Manager - Starting All Services
color 0A

echo.
echo =========================================
echo   AI Forex Strategy Manager
echo   Starting All Services Automatically
echo =========================================
echo.
echo Starting all services...
echo.

REM ==========================================
REM Step 1: Check and Start Redis
REM ==========================================
echo [1/5] Checking and starting Redis...
echo.

powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0check_redis.ps1" 2>nul

if %ERRORLEVEL% neq 0 (
    echo.
    echo ✗ Error starting Redis!
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)

echo.
timeout /t 2 /nobreak >nul

REM ==========================================
REM Step 2: Stop existing processes
REM ==========================================
echo [2/5] Stopping existing processes...
echo.

echo   Checking Node processes...
taskkill /F /IM node.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   ✓ Node processes stopped
) else (
    echo   ℹ No Node processes were running
)

echo   Checking Celery processes...
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0stop_celery.ps1" 2>nul

echo.
timeout /t 2 /nobreak >nul

REM ==========================================
REM Step 3: Start Backend (Django)
REM ==========================================
echo [3/5] Starting Backend (Django)...
echo.
start "Backend Django - Port 8000" cmd /k "cd /d %~dp0backend && echo ========================================= && echo   Backend Django Server && echo   Port: 8000 && echo ========================================= && echo. && python manage.py runserver"
timeout /t 4 /nobreak >nul
echo   ✓ Backend is starting...
echo.

REM ==========================================
REM Step 4: Start Frontend (React)
REM ==========================================
echo [4/5] Starting Frontend (React)...
echo.
start "Frontend React - Port 3000" cmd /k "cd /d %~dp0frontend && echo ========================================= && echo   Frontend React Server && echo   Port: 3000 && echo ========================================= && echo. && npm run dev"
timeout /t 3 /nobreak >nul
echo   ✓ Frontend is starting...
echo.

REM ==========================================
REM Step 5: Start Celery Worker
REM ==========================================
echo [5/5] Starting Celery Worker and Beat...
echo.
start "Celery Worker" cmd /k "cd /d %~dp0backend && echo ========================================= && echo   Celery Worker && echo ========================================= && echo. && celery -A config worker --loglevel=info --pool=solo"
timeout /t 2 /nobreak >nul
echo   ✓ Celery Worker is starting...
echo.

REM ==========================================
REM Step 6: Start Celery Beat
REM ==========================================
start "Celery Beat" cmd /k "cd /d %~dp0backend && echo ========================================= && echo   Celery Beat Scheduler && echo   Auto-trading every 5 minutes && echo ========================================= && echo. && celery -A config beat --loglevel=info"
timeout /t 2 /nobreak >nul
echo   ✓ Celery Beat is starting...
echo.

REM ==========================================
REM Final Summary
REM ==========================================
echo.
echo =========================================
echo   ✓ All services started successfully!
echo =========================================
echo.
echo Access URLs:
echo.
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8000
echo   Admin:     http://localhost:8000/admin/
echo.
echo Admin Login Info:
echo   Username: admin
echo   Password: admin
echo.
echo Service Status:
echo   ✓ Redis          (Port 6379)
echo   ✓ Django Server  (Port 8000)
echo   ✓ React Dev      (Port 3000)
echo   ✓ Celery Worker  (Running)
echo   ✓ Celery Beat    (Every 5 minutes)
echo.
echo IMPORTANT NOTES:
echo   - Redis must always be running
echo   - For auto-trading, MT5 must be open
echo   - Celery Beat runs every 5 minutes
echo.
echo To stop all services:
echo   Run STOP_ALL.bat
echo.
echo =========================================
echo.
echo All terminal windows have been opened.
echo Press any key to close this window...
pause >nul
