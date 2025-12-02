# Final Test - IP and Domain
Write-Host "=== Final Test ===" -ForegroundColor Cyan
Start-Sleep -Seconds 5

# Test 1: IP Address
Write-Host "`n1. Testing IP Address (http://191.101.113.163)..." -ForegroundColor Yellow
try {
    $ipResponse = Invoke-WebRequest -Uri "http://191.101.113.163" -UseBasicParsing -TimeoutSec 10
    Write-Host "   SUCCESS! Status: $($ipResponse.StatusCode)" -ForegroundColor Green
    Write-Host "   Content Length: $($ipResponse.Content.Length) bytes" -ForegroundColor Cyan
    if ($ipResponse.Content -match "root" -or $ipResponse.Content -match "html") {
        Write-Host "   Content: Valid HTML" -ForegroundColor Green
    }
} catch {
    Write-Host "   FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Domain
Write-Host "`n2. Testing Domain (https://myaibaz.ir)..." -ForegroundColor Yellow
try {
    $domainResponse = Invoke-WebRequest -Uri "https://myaibaz.ir" -UseBasicParsing -TimeoutSec 15
    Write-Host "   SUCCESS! Status: $($domainResponse.StatusCode)" -ForegroundColor Green
    Write-Host "   Content Length: $($domainResponse.Content.Length) bytes" -ForegroundColor Cyan
} catch {
    Write-Host "   FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Note: This might be a Cloudflare timeout issue" -ForegroundColor Yellow
}

# Test 3: Localhost
Write-Host "`n3. Testing Localhost (http://localhost)..." -ForegroundColor Yellow
try {
    $localResponse = Invoke-WebRequest -Uri "http://localhost" -UseBasicParsing -TimeoutSec 10
    Write-Host "   SUCCESS! Status: $($localResponse.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan

