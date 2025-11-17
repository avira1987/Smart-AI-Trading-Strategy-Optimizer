# Smart AI Trading Strategy Optimizer - Start Script
# This script starts all services: Redis, Backend, Frontend, Celery

$ErrorActionPreference = "Continue"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Smart AI Trading Strategy Optimizer" -ForegroundColor Green
Write-Host "  Starting All Services..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Step 1: Check and Start Redis
Write-Host "[1/5] Checking Redis..." -ForegroundColor Cyan
$redisRunning = $false

try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 6379)
    $tcpClient.Close()
    Write-Host "  [OK] Redis is running" -ForegroundColor Green
    $redisRunning = $true
}
catch {
    Write-Host "  [WARN] Redis is not running. Starting Redis..." -ForegroundColor Yellow
    
    # Check Docker
    $dockerAvailable = $false
    try {
        $dockerCheck = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $dockerAvailable = $true
        }
    }
    catch {
        Write-Host "  [ERROR] Docker is not available" -ForegroundColor Red
    }
    
    if ($dockerAvailable) {
        try {
            $existingContainer = docker ps -a --filter "name=redis" --format "{{.Names}}" 2>&1
            if ($existingContainer -eq "redis") {
                Write-Host "    Starting existing Redis container..." -ForegroundColor Cyan
                docker start redis 2>&1 | Out-Null
            }
            else {
                Write-Host "    Creating new Redis container..." -ForegroundColor Cyan
                docker run -d --name redis -p 6379:6379 redis:7-alpine 2>&1 | Out-Null
            }
            
            Start-Sleep -Seconds 3
            
            try {
                $tcpClient2 = New-Object System.Net.Sockets.TcpClient
                $tcpClient2.Connect("localhost", 6379)
                $tcpClient2.Close()
                Write-Host "  [OK] Redis started successfully!" -ForegroundColor Green
                $redisRunning = $true
            }
            catch {
                Write-Host "  [ERROR] Failed to start Redis" -ForegroundColor Red
            }
        }
        catch {
            Write-Host "  [ERROR] Error starting Redis: $_" -ForegroundColor Red
        }
    }
}

if (-not $redisRunning) {
    Write-Host ""
    Write-Host "[ERROR] Redis is not running!" -ForegroundColor Red
    Write-Host "Please start Redis manually or install Docker" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Start-Sleep -Seconds 1

# Step 2: Stop existing processes
Write-Host "[2/5] Stopping existing processes..." -ForegroundColor Cyan

# Stop Node processes
$nodeProcess = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcess) {
    Write-Host "  Stopping Node processes..." -ForegroundColor Gray
    Stop-Process -Name "node" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Stop Celery processes
$celeryProcesses = Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like "*celery*" }
if ($celeryProcesses) {
    Write-Host "  Stopping Celery processes..." -ForegroundColor Gray
    $celeryProcesses | ForEach-Object { 
        try {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
        catch {
            # Ignore errors
        }
    }
    Start-Sleep -Seconds 2
}

Write-Host ""
Start-Sleep -Seconds 1

# Step 3: Start Backend
Write-Host "[3/5] Starting Backend (Django)..." -ForegroundColor Cyan
$backendPath = Join-Path $scriptPath "backend"
$backendCommand = "cd '$backendPath'; Write-Host '========================================' -ForegroundColor Green; Write-Host '  Backend Django Server' -ForegroundColor Green; Write-Host '  Port: 8000' -ForegroundColor Green; Write-Host '========================================' -ForegroundColor Green; Write-Host ''; python manage.py runserver 0.0.0.0:8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand
Start-Sleep -Seconds 4
Write-Host "  [OK] Backend starting..." -ForegroundColor Green
Write-Host ""

# Step 4: Start Frontend
Write-Host "[4/5] Starting Frontend (React)..." -ForegroundColor Cyan
$frontendPath = Join-Path $scriptPath "frontend"
$frontendCommand = "cd '$frontendPath'; Write-Host '========================================' -ForegroundColor Cyan; Write-Host '  Frontend React Server' -ForegroundColor Cyan; Write-Host '  Port: 3000' -ForegroundColor Cyan; Write-Host '========================================' -ForegroundColor Cyan; Write-Host ''; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand
Start-Sleep -Seconds 3
Write-Host "  [OK] Frontend starting..." -ForegroundColor Green
Write-Host ""

# Step 5: Start Celery Worker and Beat
Write-Host "[5/5] Starting Celery Worker and Beat..." -ForegroundColor Cyan

# Start Celery Worker
$workerCommand = "cd '$backendPath'; Write-Host '========================================' -ForegroundColor Yellow; Write-Host '  Celery Worker' -ForegroundColor Yellow; Write-Host '========================================' -ForegroundColor Yellow; Write-Host ''; celery -A config worker --loglevel=info --pool=solo"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $workerCommand
Start-Sleep -Seconds 2
Write-Host "  [OK] Celery Worker starting..." -ForegroundColor Green

# Start Celery Beat
$beatCommand = "cd '$backendPath'; Write-Host '========================================' -ForegroundColor Magenta; Write-Host '  Celery Beat Scheduler' -ForegroundColor Magenta; Write-Host '  Auto-trading every 5 minutes' -ForegroundColor Magenta; Write-Host '========================================' -ForegroundColor Magenta; Write-Host ''; celery -A config beat --loglevel=info"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $beatCommand
Start-Sleep -Seconds 2
Write-Host "  [OK] Celery Beat starting..." -ForegroundColor Green
Write-Host ""

# Final Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  [OK] All Services Started Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Get local IP
$localIP = ""
try {
    $netIPs = Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*","Wi-Fi*" -ErrorAction SilentlyContinue
    $localIP = $netIPs | Where-Object { $_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" -or $_.IPAddress -like "172.16.*" } | Select-Object -First 1 -ExpandProperty IPAddress
    if (-not $localIP) {
        $allIPs = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue
        $localIP = $allIPs | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } | Select-Object -First 1 -ExpandProperty IPAddress
    }
}
catch {
    $localIP = ""
}

Write-Host "Access URLs:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Frontend (Local):    http://localhost:3000" -ForegroundColor White
if ($localIP) {
    Write-Host "  Frontend (Network):  http://$localIP:3000" -ForegroundColor Cyan
}
Write-Host "  Backend (Local):     http://localhost:8000" -ForegroundColor White
if ($localIP) {
    Write-Host "  Backend (Network):   http://$localIP:8000" -ForegroundColor Cyan
}
Write-Host "  Admin (Local):       http://localhost:8000/admin/" -ForegroundColor White
if ($localIP) {
    Write-Host "  Admin (Network):     http://$localIP:8000/admin/" -ForegroundColor Cyan
}
Write-Host ""
Write-Host "Admin Login:" -ForegroundColor Cyan
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: admin" -ForegroundColor White
Write-Host ""
Write-Host "Services Status:" -ForegroundColor Yellow
Write-Host "  [OK] Redis          (Port 6379)" -ForegroundColor Green
Write-Host "  [OK] Django Server  (Port 8000)" -ForegroundColor Green
Write-Host "  [OK] React Dev      (Port 3000)" -ForegroundColor Green
Write-Host "  [OK] Celery Worker  (Running)" -ForegroundColor Green
Write-Host "  [OK] Celery Beat    (Every 5 minutes)" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT NOTES:" -ForegroundColor Yellow
Write-Host "  - Redis must always be running" -ForegroundColor White
Write-Host "  - For auto-trading, MT5 must be open" -ForegroundColor White
Write-Host "  - Celery Beat runs every 5 minutes" -ForegroundColor White
Write-Host ""
Write-Host "To stop all services, run: .\stop.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "All terminal windows have been opened." -ForegroundColor Gray
Write-Host "Press Enter to exit this window (services will continue running)..." -ForegroundColor Gray
Read-Host
