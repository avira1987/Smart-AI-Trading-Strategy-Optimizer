# Start Frontend Now (Development Mode - No build needed)
Write-Host "Starting Frontend Dev Server..." -ForegroundColor Cyan

Set-Location frontend

Write-Host "`nStarting dev server on port 3000..." -ForegroundColor Green
Write-Host "Mode: Development (No build required)" -ForegroundColor Yellow
$env:VITE_FRONTEND_PORT = "3000"
$env:VITE_BACKEND_URL = "http://127.0.0.1:8000"

# Start in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; `$env:VITE_FRONTEND_PORT='3000'; `$env:VITE_BACKEND_URL='http://127.0.0.1:8000'; npm run dev -- --port 3000 --host 0.0.0.0"

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



