# Test and Fix Website
Write-Host "=== Testing and Fixing Website ===" -ForegroundColor Cyan

# Test 1: IP Address
Write-Host "`n1. Testing IP Address (http://191.101.113.163)..." -ForegroundColor Yellow
try {
    $ipResponse = Invoke-WebRequest -Uri "http://191.101.113.163" -UseBasicParsing -TimeoutSec 10
    Write-Host "   SUCCESS - Status: $($ipResponse.StatusCode)" -ForegroundColor Green
    Write-Host "   Content Length: $($ipResponse.Content.Length) bytes" -ForegroundColor Cyan
} catch {
    Write-Host "   FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Domain
Write-Host "`n2. Testing Domain (https://myaibaz.ir)..." -ForegroundColor Yellow
try {
    $domainResponse = Invoke-WebRequest -Uri "https://myaibaz.ir" -UseBasicParsing -TimeoutSec 10
    Write-Host "   SUCCESS - Status: $($domainResponse.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Check what's on port 80
Write-Host "`n3. Checking port 80..." -ForegroundColor Yellow
$port80 = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue
if ($port80.TcpTestSucceeded) {
    Write-Host "   Port 80 is listening" -ForegroundColor Green
    
    # Try to get response from localhost
    try {
        $localResponse = Invoke-WebRequest -Uri "http://localhost" -UseBasicParsing -TimeoutSec 5
        Write-Host "   Localhost response: Status $($localResponse.StatusCode)" -ForegroundColor Cyan
    } catch {
        Write-Host "   Localhost error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   Port 80 is NOT listening" -ForegroundColor Red
}

# Test 4: Check port 3000
Write-Host "`n4. Checking port 3000 (Frontend)..." -ForegroundColor Yellow
$port3000 = Test-NetConnection -ComputerName localhost -Port 3000 -WarningAction SilentlyContinue
if ($port3000.TcpTestSucceeded) {
    Write-Host "   Port 3000 is listening" -ForegroundColor Green
    try {
        $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5
        Write-Host "   Frontend response: Status $($frontendResponse.StatusCode)" -ForegroundColor Cyan
    } catch {
        Write-Host "   Frontend error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   Port 3000 is NOT listening" -ForegroundColor Red
}

Write-Host "`n=== Tests Complete ===" -ForegroundColor Cyan

