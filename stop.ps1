# Smart AI Trading Strategy Optimizer - Stop Script
# This script stops all services

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "========================================" -ForegroundColor Red
Write-Host "  Smart AI Trading Strategy Optimizer" -ForegroundColor Red
Write-Host "  Stopping All Services" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""

# ==========================================
# Step 1: Stop Node processes (Frontend)
# ==========================================
Write-Host "[1/5] Stopping Node processes (Frontend)..." -ForegroundColor Cyan
$nodeProcess = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcess) {
    $count = ($nodeProcess | Measure-Object).Count
    Stop-Process -Name "node" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "  [OK] $count Node processes stopped" -ForegroundColor Green
} else {
    Write-Host "  [OK] No Node processes were running" -ForegroundColor Gray
}

Write-Host ""

# ==========================================
# Step 2: Stop Nginx processes (Frontend Web Server)
# ==========================================
Write-Host "[2/5] Stopping Nginx processes (Frontend Web Server)..." -ForegroundColor Cyan
$nginxProcess = Get-Process -Name "nginx" -ErrorAction SilentlyContinue
if ($nginxProcess) {
    $count = ($nginxProcess | Measure-Object).Count
    Stop-Process -Name "nginx" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "  [OK] $count Nginx processes stopped" -ForegroundColor Green
} else {
    Write-Host "  [OK] No Nginx processes were running" -ForegroundColor Gray
}

Write-Host ""

# ==========================================
# Step 3: Stop Django processes (Backend)
# ==========================================
Write-Host "[3/5] Stopping Django processes (Backend)..." -ForegroundColor Cyan
$djangoProcesses = Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like "*manage.py*runserver*" }
if ($djangoProcesses) {
    $count = ($djangoProcesses | Measure-Object).Count
    $djangoProcesses | ForEach-Object { 
        try {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        } catch {}
    }
    Start-Sleep -Seconds 2
    Write-Host "  [OK] $count Django processes stopped" -ForegroundColor Green
} else {
    Write-Host "  [OK] No Django processes were running" -ForegroundColor Gray
}

Write-Host ""

# ==========================================
# Step 4: Stop Celery processes
# ==========================================
Write-Host "[4/5] Stopping Celery processes..." -ForegroundColor Cyan
$celeryProcesses = Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like "*celery*" }
if ($celeryProcesses) {
    $count = ($celeryProcesses | Measure-Object).Count
    $celeryProcesses | ForEach-Object { 
        try {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        } catch {}
    }
    Start-Sleep -Seconds 2
    Write-Host "  [OK] $count Celery processes stopped" -ForegroundColor Green
} else {
    Write-Host "  [OK] No Celery processes were running" -ForegroundColor Gray
}

Write-Host ""

# ==========================================
# Step 5: Check Redis status
# ==========================================
Write-Host "[5/5] Checking Redis status..." -ForegroundColor Cyan
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 6379)
    $tcpClient.Close()
    Write-Host "  [i] Redis is still running (Port 6379)" -ForegroundColor Yellow
    Write-Host "  Note: Redis is managed by Docker" -ForegroundColor Gray
    Write-Host "  To stop Redis: docker stop redis" -ForegroundColor Cyan
} catch {
    Write-Host "  [OK] Redis is not running" -ForegroundColor Gray
}

Write-Host ""

# ==========================================
# Final Summary
# ==========================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  [OK] All services stopped!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Note:" -ForegroundColor Yellow
Write-Host "  - Redis is still running (if it was previously started)" -ForegroundColor White
Write-Host "  - To stop Redis: docker stop redis" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host
