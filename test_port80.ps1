# Test Frontend on Port 80
Write-Host "=== Testing Frontend on Port 80 ===" -ForegroundColor Cyan

# Test 1: Port availability
Write-Host "
1. Testing port 80..." -ForegroundColor Yellow
$portTest = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue
if ($portTest.TcpTestSucceeded) {
    Write-Host "   Port 80: OK" -ForegroundColor Green
} else {
    Write-Host "   Port 80: NOT AVAILABLE" -ForegroundColor Red
    exit 1
}

# Test 2: Frontend response
Write-Host "
2. Testing Frontend response..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost" -UseBasicParsing -TimeoutSec 10
    Write-Host "   Status Code: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "   Content Length: $($response.Content.Length) bytes" -ForegroundColor Cyan
    
    if ($response.Content -match "root" -or $response.Content -match "html") {
        Write-Host "   Content: Valid HTML" -ForegroundColor Green
    } else {
        Write-Host "   Content: Unexpected" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 3: Test with IP address
Write-Host "
3. Testing with IP address..." -ForegroundColor Yellow
try {
    $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } | Select-Object -First 1).IPAddress
    $response = Invoke-WebRequest -Uri "http://$ip" -UseBasicParsing -TimeoutSec 10
    Write-Host "   IP Address: $ip" -ForegroundColor Cyan
    Write-Host "   Status Code: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Test API proxy (if Backend is running)
Write-Host "
4. Testing API proxy..." -ForegroundColor Yellow
try {
    $apiTest = Invoke-WebRequest -Uri "http://localhost/api/" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "   API Proxy: OK (Status: $($apiTest.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "   API Proxy: Backend not running or proxy not working" -ForegroundColor Yellow
}

Write-Host "
=== Tests Complete ===" -ForegroundColor Cyan
Write-Host "
Access URLs:" -ForegroundColor Yellow
Write-Host "   http://localhost" -ForegroundColor White
Write-Host "   http://191.101.113.163" -ForegroundColor White
Write-Host "   http://myaibaz.ir (via Cloudflare)" -ForegroundColor White
