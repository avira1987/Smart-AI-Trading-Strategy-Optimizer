# Start Frontend Dev Server on Port 80 (No build needed)
$env:VITE_FRONTEND_PORT = "80"
$env:VITE_BACKEND_URL = "http://127.0.0.1:8000"

Write-Host "=== Starting Frontend Dev Server on Port 80 ===" -ForegroundColor Cyan
Write-Host "Backend URL: $env:VITE_BACKEND_URL" -ForegroundColor Cyan
Write-Host "Frontend Port: $env:VITE_FRONTEND_PORT" -ForegroundColor Cyan
Write-Host ""

# Check if port 80 is available
$portCheck = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue
if ($portCheck.TcpTestSucceeded) {
    Write-Host "WARNING: Port 80 is already in use!" -ForegroundColor Red
    Write-Host "Please stop IIS or other services using port 80" -ForegroundColor Yellow
    exit 1
}

Set-Location frontend

Write-Host "Starting dev server on port 80..." -ForegroundColor Green
Write-Host "Access at: http://localhost or http://191.101.113.163" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

npm run dev -- --port 80 --host 0.0.0.0



