# Start Frontend on Port 80 (Complete Setup)
Write-Host "=== Starting Frontend on Port 80 ===" -ForegroundColor Cyan

# 1. Stop IIS
Write-Host "`n1. Stopping IIS..." -ForegroundColor Yellow
iisreset /stop
Start-Sleep -Seconds 3

# 2. Stop any existing Node processes (Frontend on 3000)
Write-Host "`n2. Stopping existing Frontend processes..." -ForegroundColor Yellow
$nodeProcesses = Get-Process | Where-Object {$_.ProcessName -eq 'node'}
if ($nodeProcesses) {
    $nodeProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "   Stopped $($nodeProcesses.Count) Node process(es)" -ForegroundColor Green
} else {
    Write-Host "   No Node processes found" -ForegroundColor Gray
}

# 3. Check port 80
Write-Host "`n3. Checking port 80..." -ForegroundColor Yellow
$port80Check = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue
if ($port80Check.TcpTestSucceeded) {
    Write-Host "   Port 80 is still in use!" -ForegroundColor Red
    Write-Host "   Please check what's using it and stop it" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "   Port 80 is available" -ForegroundColor Green
}

# 4. Check if Frontend is built
Write-Host "`n4. Checking Frontend build..." -ForegroundColor Yellow
$distPath = "frontend\dist"
if (-not (Test-Path $distPath) -or (Get-ChildItem $distPath -File -ErrorAction SilentlyContinue).Count -eq 0) {
    Write-Host "   Building Frontend..." -ForegroundColor Yellow
    Set-Location frontend
    npm run build 2>&1 | Out-Null
    Set-Location ..
    Write-Host "   Build complete" -ForegroundColor Green
} else {
    Write-Host "   Frontend is already built" -ForegroundColor Green
}

# 5. Set environment variables
$env:VITE_FRONTEND_PORT = "80"
$env:VITE_BACKEND_URL = "http://127.0.0.1:8000"

Write-Host "`n5. Starting Frontend on port 80..." -ForegroundColor Yellow
Write-Host "   Backend URL: $env:VITE_BACKEND_URL" -ForegroundColor Cyan
Write-Host "   Frontend Port: $env:VITE_FRONTEND_PORT" -ForegroundColor Cyan
Write-Host ""

# 6. Start Frontend
Set-Location frontend
Write-Host "=== Frontend Starting ===" -ForegroundColor Green
Write-Host "Access URLs:" -ForegroundColor Yellow
Write-Host "  - http://localhost" -ForegroundColor White
Write-Host "  - http://191.101.113.163" -ForegroundColor White
Write-Host "  - http://myaibaz.ir (via Cloudflare)" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

npm run preview -- --port 80 --host 0.0.0.0

