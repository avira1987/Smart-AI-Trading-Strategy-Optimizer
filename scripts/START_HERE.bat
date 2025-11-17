@echo off
echo =========================================
echo   AI Forex Strategy Manager
echo =========================================
echo.
echo Starting all services...
echo.

REM Check if Redis is running (optional warning)
echo Checking Redis connection...
timeout /t 1 /nobreak >nul 2>&1
powershell -Command "try { $null = [System.Net.Sockets.TcpClient]::new('localhost', 6379); Write-Host 'Redis is running' -ForegroundColor Green } catch { Write-Host 'WARNING: Redis may not be running on port 6379' -ForegroundColor Yellow; Write-Host 'Make sure Redis is started before using auto-trading!' -ForegroundColor Yellow }" 2>nul
echo.

REM Stop existing Celery processes
echo Checking for existing Celery processes...
powershell -Command "$processes = Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like '*celery*' }; if ($processes) { Write-Host 'Stopping existing Celery processes...' -ForegroundColor Yellow; $processes | ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {} }; Start-Sleep -Seconds 2 }"
echo.

REM Stop existing Node processes (if any)
echo Checking for existing Node processes...
taskkill /F /IM node.exe >nul 2>&1
timeout /t 1 /nobreak >nul 2>&1

REM Start Backend in background
echo Starting Backend Django Server...
start "Backend Django" cmd /k "cd /d %~dp0backend && python manage.py runserver"
timeout /t 3 /nobreak >nul

REM Start Frontend in background  
echo Starting Frontend React...
start "Frontend React" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 2 /nobreak >nul

REM Start Celery Worker in background
echo Starting Celery Worker...
start "Celery Worker" cmd /k "cd /d %~dp0backend && celery -A config worker --loglevel=info --pool=solo"
timeout /t 2 /nobreak >nul

REM Start Celery Beat in background
echo Starting Celery Beat...
start "Celery Beat" cmd /k "cd /d %~dp0backend && celery -A config beat --loglevel=info"
timeout /t 2 /nobreak >nul

echo.
echo =========================================
echo   All Services Started Successfully!
echo =========================================
echo.
echo Services running:
echo   - Frontend: http://localhost:3000
echo   - Backend:  http://localhost:8000
echo   - Admin:    http://localhost:8000/admin/
echo   - Celery Worker: Running
echo   - Celery Beat: Running (Auto-trading every 5 minutes)
echo.
echo Login Info:
echo   Username: admin
echo   Password: admin
echo.
echo IMPORTANT NOTES:
echo   - Make sure Redis is running on port 6379
echo   - Make sure MT5 is open and AutoTrading is enabled
echo   - Auto-trading will run every 5 minutes automatically
echo.
echo Press any key to exit...
pause >nul

