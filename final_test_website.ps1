# Final Website Test
Write-Host "=== Final Website Test ===" -ForegroundColor Cyan

Start-Sleep -Seconds 3

# Test 1: IP Address
Write-Host "`n1. Testing IP Address (http://191.101.113.163)..." -ForegroundColor Yellow
try {
    $ipResponse = Invoke-WebRequest -Uri "http://191.101.113.163" -UseBasicParsing -TimeoutSec 15
    Write-Host "   SUCCESS!" -ForegroundColor Green
    Write-Host "   Status Code: $($ipResponse.StatusCode)" -ForegroundColor Cyan
    Write-Host "   Content Length: $($ipResponse.Content.Length) bytes" -ForegroundColor Cyan
    
    if ($ipResponse.Content -match "root" -or $ipResponse.Content -match "html" -or $ipResponse.Content.Length -gt 1000) {
        Write-Host "   Content: Valid" -ForegroundColor Green
    }
} catch {
    Write-Host "   FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Domain
Write-Host "`n2. Testing Domain (http://myaibaz.ir)..." -ForegroundColor Yellow
try {
    $domainResponse = Invoke-WebRequest -Uri "http://myaibaz.ir" -UseBasicParsing -TimeoutSec 15
    Write-Host "   SUCCESS!" -ForegroundColor Green
    Write-Host "   Status Code: $($domainResponse.StatusCode)" -ForegroundColor Cyan
    Write-Host "   Content Length: $($domainResponse.Content.Length) bytes" -ForegroundColor Cyan
} catch {
    Write-Host "   FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Note: DNS might need time to propagate" -ForegroundColor Yellow
}

# Test 3: Check Services
Write-Host "`n3. Service Status:" -ForegroundColor Yellow
$p3000 = Test-NetConnection -ComputerName localhost -Port 3000 -WarningAction SilentlyContinue
$p8000 = Test-NetConnection -ComputerName localhost -Port 8000 -WarningAction SilentlyContinue

Write-Host "   Frontend (3000): " -NoNewline
Write-Host $(if ($p3000.TcpTestSucceeded) { "RUNNING" } else { "NOT RUNNING" }) -ForegroundColor $(if ($p3000.TcpTestSucceeded) { "Green" } else { "Red" })

Write-Host "   Backend (8000): " -NoNewline
Write-Host $(if ($p8000.TcpTestSucceeded) { "RUNNING" } else { "NOT RUNNING" }) -ForegroundColor $(if ($p8000.TcpTestSucceeded) { "Green" } else { "Red" })

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan



