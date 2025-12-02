# Start Frontend and Backend Services
Write-Host "=== Starting Services ===" -ForegroundColor Cyan

# Check if Frontend is running
Write-Host "`n1. Checking Frontend (Port 3000)..." -ForegroundColor Yellow
$port3000 = Test-NetConnection -ComputerName localhost -Port 3000 -WarningAction SilentlyContinue
if (-not $port3000.TcpTestSucceeded) {
    Write-Host "   Frontend not running. Starting..." -ForegroundColor Yellow
    
    # Start Frontend in background
    $frontendScript = @"
`$env:VITE_FRONTEND_PORT = "3000"
`$env:VITE_BACKEND_URL = "http://127.0.0.1:8000"
Set-Location "$PWD\frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run preview -- --port 3000 --host 0.0.0.0"
"@
    
    $tempScript = "$env:TEMP\start_frontend.ps1"
    Set-Content -Path $tempScript -Value $frontendScript
    Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-File", $tempScript -WindowStyle Minimized
    
    Write-Host "   Frontend starting in background..." -ForegroundColor Green
    Start-Sleep -Seconds 5
    
    # Check again
    $port3000Check = Test-NetConnection -ComputerName localhost -Port 3000 -WarningAction SilentlyContinue
    if ($port3000Check.TcpTestSucceeded) {
        Write-Host "   Frontend started successfully" -ForegroundColor Green
    } else {
        Write-Host "   Frontend might need more time or manual start" -ForegroundColor Yellow
        Write-Host "   Run manually: cd frontend && npm run preview -- --port 3000 --host 0.0.0.0" -ForegroundColor Cyan
    }
} else {
    Write-Host "   Frontend already running" -ForegroundColor Green
}

# Check if Backend is running
Write-Host "`n2. Checking Backend (Port 8000)..." -ForegroundColor Yellow
$port8000 = Test-NetConnection -ComputerName localhost -Port 8000 -WarningAction SilentlyContinue
if (-not $port8000.TcpTestSucceeded) {
    Write-Host "   Backend not running!" -ForegroundColor Red
    Write-Host "   Please start Backend manually:" -ForegroundColor Yellow
    Write-Host "   cd backend && .\venv\Scripts\Activate.ps1 && python manage.py runserver 0.0.0.0:8000" -ForegroundColor Cyan
} else {
    Write-Host "   Backend already running" -ForegroundColor Green
}

Write-Host "`n=== Services Check Complete ===" -ForegroundColor Cyan



