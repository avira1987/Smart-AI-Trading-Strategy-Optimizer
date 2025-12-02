# Setup Frontend on Port 80
Write-Host "=== Setting up Frontend on Port 80 ===" -ForegroundColor Cyan

# 1. Stop IIS to free port 80
Write-Host "`n1. Stopping IIS..." -ForegroundColor Yellow
Import-Module WebAdministration -ErrorAction SilentlyContinue

# Check if IIS is using port 80
$iisBindings = Get-WebBinding -Name "MyWebsite" -ErrorAction SilentlyContinue
if ($iisBindings) {
    Write-Host "   IIS is using port 80. Stopping..." -ForegroundColor Yellow
    iisreset /stop
    Start-Sleep -Seconds 3
    Write-Host "   IIS stopped" -ForegroundColor Green
} else {
    Write-Host "   IIS not using port 80 or site not found" -ForegroundColor Gray
}

# 2. Check if port 80 is available
Write-Host "`n2. Checking port 80 availability..." -ForegroundColor Yellow
$port80Check = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue
if (-not $port80Check.TcpTestSucceeded) {
    Write-Host "   Port 80 is available" -ForegroundColor Green
} else {
    Write-Host "   Port 80 is still in use!" -ForegroundColor Red
    Write-Host "   Trying to find and stop the process..." -ForegroundColor Yellow
    
    $process = Get-NetTCPConnection -LocalPort 80 -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($process) {
        $pid = $process.OwningProcess
        $procName = (Get-Process -Id $pid -ErrorAction SilentlyContinue).ProcessName
        Write-Host "   Process using port 80: $procName (PID: $pid)" -ForegroundColor Yellow
        Write-Host "   Please stop this process manually or run as Administrator" -ForegroundColor Red
    }
    exit 1
}

# 3. Check if Frontend is built
Write-Host "`n3. Checking Frontend build..." -ForegroundColor Yellow
$frontendDist = "frontend\dist"
if (Test-Path $frontendDist) {
    $distFiles = Get-ChildItem $frontendDist -File
    if ($distFiles.Count -gt 0) {
        Write-Host "   Frontend is built ($($distFiles.Count) files)" -ForegroundColor Green
    } else {
        Write-Host "   Frontend dist folder is empty. Building..." -ForegroundColor Yellow
        Set-Location frontend
        npm run build
        Set-Location ..
    }
} else {
    Write-Host "   Frontend not built. Building..." -ForegroundColor Yellow
    Set-Location frontend
    npm run build
    Set-Location ..
}

# 4. Create startup script for Frontend on port 80
Write-Host "`n4. Creating startup script..." -ForegroundColor Yellow
$startScript = @"
# Start Frontend on Port 80
`$env:VITE_FRONTEND_PORT = "80"
`$env:VITE_BACKEND_URL = "http://127.0.0.1:8000"

Write-Host "Starting Frontend on port 80..." -ForegroundColor Green
Write-Host "Backend URL: `$env:VITE_BACKEND_URL" -ForegroundColor Cyan

Set-Location frontend
npm run preview -- --port 80 --host 0.0.0.0
"@

Set-Content -Path "start_frontend_port80.ps1" -Value $startScript -Encoding UTF8
Write-Host "   Script created: start_frontend_port80.ps1" -ForegroundColor Green

# 5. Create test script
Write-Host "`n5. Creating test script..." -ForegroundColor Yellow
$testScript = @"
# Test Frontend on Port 80
Write-Host "=== Testing Frontend on Port 80 ===" -ForegroundColor Cyan

# Test 1: Port availability
Write-Host "`n1. Testing port 80..." -ForegroundColor Yellow
`$portTest = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue
if (`$portTest.TcpTestSucceeded) {
    Write-Host "   Port 80: OK" -ForegroundColor Green
} else {
    Write-Host "   Port 80: NOT AVAILABLE" -ForegroundColor Red
    exit 1
}

# Test 2: Frontend response
Write-Host "`n2. Testing Frontend response..." -ForegroundColor Yellow
try {
    `$response = Invoke-WebRequest -Uri "http://localhost" -UseBasicParsing -TimeoutSec 10
    Write-Host "   Status Code: `$(`$response.StatusCode)" -ForegroundColor Green
    Write-Host "   Content Length: `$(`$response.Content.Length) bytes" -ForegroundColor Cyan
    
    if (`$response.Content -match "root" -or `$response.Content -match "html") {
        Write-Host "   Content: Valid HTML" -ForegroundColor Green
    } else {
        Write-Host "   Content: Unexpected" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   Error: `$(`$_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 3: Test with IP address
Write-Host "`n3. Testing with IP address..." -ForegroundColor Yellow
try {
    `$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { `$_.IPAddress -notlike "127.*" -and `$_.IPAddress -notlike "169.254.*" } | Select-Object -First 1).IPAddress
    `$response = Invoke-WebRequest -Uri "http://`$ip" -UseBasicParsing -TimeoutSec 10
    Write-Host "   IP Address: `$ip" -ForegroundColor Cyan
    Write-Host "   Status Code: `$(`$response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   Error: `$(`$_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Test API proxy (if Backend is running)
Write-Host "`n4. Testing API proxy..." -ForegroundColor Yellow
try {
    `$apiTest = Invoke-WebRequest -Uri "http://localhost/api/" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "   API Proxy: OK (Status: `$(`$apiTest.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "   API Proxy: Backend not running or proxy not working" -ForegroundColor Yellow
}

Write-Host "`n=== Tests Complete ===" -ForegroundColor Cyan
Write-Host "`nAccess URLs:" -ForegroundColor Yellow
Write-Host "   http://localhost" -ForegroundColor White
Write-Host "   http://191.101.113.163" -ForegroundColor White
Write-Host "   http://myaibaz.ir (via Cloudflare)" -ForegroundColor White
"@

Set-Content -Path "test_port80.ps1" -Value $testScript -Encoding UTF8
Write-Host "   Test script created: test_port80.ps1" -ForegroundColor Green

Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "   1. Run: .\start_frontend_port80.ps1" -ForegroundColor White
Write-Host "   2. In another terminal, run: .\test_port80.ps1" -ForegroundColor White



