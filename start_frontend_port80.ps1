# Start Frontend on Port 80
$env:VITE_FRONTEND_PORT = "80"
$env:VITE_BACKEND_URL = "http://127.0.0.1:8000"

Write-Host "Starting Frontend on port 80..." -ForegroundColor Green
Write-Host "Backend URL: $env:VITE_BACKEND_URL" -ForegroundColor Cyan

Set-Location frontend
npm run preview -- --port 80 --host 0.0.0.0
