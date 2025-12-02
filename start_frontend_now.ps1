# Start Frontend Now
Write-Host "Starting Frontend..." -ForegroundColor Cyan

Set-Location frontend

# Check if dist exists
if (-not (Test-Path "dist")) {
    Write-Host "Building Frontend (this may take a few minutes)..." -ForegroundColor Yellow
    npm run build 2>&1 | Select-Object -Last 10
}

Write-Host "`nStarting preview server on port 3000..." -ForegroundColor Green
$env:VITE_FRONTEND_PORT = "3000"
$env:VITE_BACKEND_URL = "http://127.0.0.1:8000"

# Start in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; `$env:VITE_FRONTEND_PORT='3000'; `$env:VITE_BACKEND_URL='http://127.0.0.1:8000'; npm run preview -- --port 3000 --host 0.0.0.0"

Write-Host "Frontend starting in new window..." -ForegroundColor Green
Write-Host "Waiting for it to be ready..." -ForegroundColor Yellow

# Wait and check
for ($i = 1; $i -le 30; $i++) {
    Start-Sleep -Seconds 2
    $portCheck = Test-NetConnection -ComputerName localhost -Port 3000 -WarningAction SilentlyContinue
    if ($portCheck.TcpTestSucceeded) {
        Write-Host "Frontend is ready on port 3000!" -ForegroundColor Green
        break
    }
    Write-Host "." -NoNewline -ForegroundColor Gray
}

Write-Host "`nDone!" -ForegroundColor Cyan

Set-Location ..



