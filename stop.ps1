# Smart AI Trading Strategy Optimizer - Stop Script
# This script stops all running services

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "========================================" -ForegroundColor Red
Write-Host "  Smart AI Trading Strategy Optimizer" -ForegroundColor Red
Write-Host "  Stopping All Services..." -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""

# Stop Node processes
Write-Host "[1/4] Stopping Node processes (Frontend)..." -ForegroundColor Cyan
$nodeProcess = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcess) {
    Stop-Process -Name "node" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "  ✓ Node processes stopped" -ForegroundColor Green
} else {
    Write-Host "  ℹ No Node processes were running" -ForegroundColor Gray
}

Write-Host ""

# Stop Celery processes
Write-Host "[2/4] Stopping Celery processes..." -ForegroundColor Cyan
$celeryProcesses = Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like "*celery*" }
if ($celeryProcesses) {
    $celeryProcesses | ForEach-Object { 
        try {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        } catch {}
    }
    Start-Sleep -Seconds 2
    Write-Host "  ✓ Celery processes stopped" -ForegroundColor Green
} else {
    Write-Host "  ℹ No Celery processes were running" -ForegroundColor Gray
}

Write-Host ""

# Stop Python Django processes (manage.py runserver)
Write-Host "[3/4] Stopping Django processes (Backend)..." -ForegroundColor Cyan
$djangoProcesses = Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like "*manage.py*runserver*" }
if ($djangoProcesses) {
    $djangoProcesses | ForEach-Object { 
        try {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        } catch {}
    }
    Start-Sleep -Seconds 2
    Write-Host "  ✓ Django processes stopped" -ForegroundColor Green
} else {
    Write-Host "  ℹ No Django processes were running" -ForegroundColor Gray
}

Write-Host ""

# Stop Redis (optional - ask user)
Write-Host "[4/4] Redis status..." -ForegroundColor Cyan
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 6379)
    $tcpClient.Close()
    Write-Host "  ℹ Redis is still running (port 6379)" -ForegroundColor Yellow
    Write-Host "  Note: Redis is managed by Docker. To stop it, run: docker stop redis" -ForegroundColor Gray
} catch {
    Write-Host "  ℹ Redis is not running" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ All Services Stopped Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host

