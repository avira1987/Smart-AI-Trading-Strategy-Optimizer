# Start Frontend on Port 80 (Development Mode - No build needed)
$env:VITE_FRONTEND_PORT = "80"
$env:VITE_BACKEND_URL = "http://127.0.0.1:8000"

Write-Host "Starting Frontend Dev Server on port 80..." -ForegroundColor Green
Write-Host "Backend URL: $env:VITE_BACKEND_URL" -ForegroundColor Cyan
Write-Host "Mode: Development (No build required)" -ForegroundColor Yellow

Set-Location frontend
npm run dev -- --port 80 --host 0.0.0.0
