# Setup IIS to work with Frontend on Port 80
Write-Host "=== Setting up IIS for Port 80 ===" -ForegroundColor Cyan

Import-Module WebAdministration -ErrorAction SilentlyContinue

# Option 1: Stop IIS and use Frontend directly on port 80
Write-Host "`nOption 1: Stop IIS and run Frontend on port 80" -ForegroundColor Yellow
Write-Host "This is simpler and recommended for testing" -ForegroundColor Cyan

# Stop IIS
Write-Host "`nStopping IIS..." -ForegroundColor Yellow
iisreset /stop
Start-Sleep -Seconds 3

# Verify port 80 is free
$port80Check = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue
if (-not $port80Check.TcpTestSucceeded) {
    Write-Host "Port 80 is now free" -ForegroundColor Green
} else {
    Write-Host "Port 80 is still in use!" -ForegroundColor Red
    exit 1
}

# Check if Frontend is running on port 3000
$port3000Check = Test-NetConnection -ComputerName localhost -Port 3000 -WarningAction SilentlyContinue
if ($port3000Check.TcpTestSucceeded) {
    Write-Host "`nFrontend is running on port 3000" -ForegroundColor Green
    Write-Host "You need to:" -ForegroundColor Yellow
    Write-Host "1. Stop Frontend on port 3000" -ForegroundColor White
    Write-Host "2. Run: .\start_frontend_port80.ps1" -ForegroundColor White
} else {
    Write-Host "`nFrontend is not running on port 3000" -ForegroundColor Yellow
    Write-Host "You can start it on port 80 with: .\start_frontend_port80.ps1" -ForegroundColor White
}

Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Start Frontend on port 80: .\start_frontend_port80.ps1" -ForegroundColor White
Write-Host "2. Test with IP: http://191.101.113.163" -ForegroundColor White
Write-Host "3. Test with domain: http://myaibaz.ir (via Cloudflare)" -ForegroundColor White

