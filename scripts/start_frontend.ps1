# Start React Frontend Server
Write-Host "Starting React Frontend Server..." -ForegroundColor Green
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
cd "$scriptPath\..\frontend"
npm run dev
cd "$scriptPath\.."

