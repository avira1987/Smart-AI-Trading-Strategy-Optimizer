# Check Port 80 Availability
Write-Host "Checking port 80 availability..." -ForegroundColor Cyan
$port80 = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue
if (-not $port80.TcpTestSucceeded) {
    Write-Host "Port 80 is available - Ready to start!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Port 80 is in use - Need to stop IIS first" -ForegroundColor Red
    Write-Host "Run: iisreset /stop" -ForegroundColor Yellow
    exit 1
}



