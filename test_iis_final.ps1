# Final Test Script
Write-Host "=== Final IIS Test ===" -ForegroundColor Cyan

Import-Module WebAdministration -ErrorAction SilentlyContinue

# 1. Check Application Pool
Write-Host "`n1. Application Pool Status:" -ForegroundColor Yellow
$site = Get-Website -Name "MyWebsite"
if ($site) {
    $appPool = (Get-Item "IIS:\Sites\MyWebsite").applicationPool
    $poolState = (Get-WebAppPoolState -Name $appPool).Value
    Write-Host "   Pool: $appPool" -ForegroundColor Cyan
    Write-Host "   State: $poolState" -ForegroundColor $(if ($poolState -eq "Started") { "Green" } else { "Red" })
    
    if ($poolState -ne "Started") {
        Write-Host "   Starting pool..." -ForegroundColor Yellow
        Start-WebAppPool -Name $appPool
        Start-Sleep -Seconds 3
    }
}

# 2. Check Ports
Write-Host "`n2. Port Status:" -ForegroundColor Yellow
$port3000 = Test-NetConnection -ComputerName localhost -Port 3000 -WarningAction SilentlyContinue
$port8000 = Test-NetConnection -ComputerName localhost -Port 8000 -WarningAction SilentlyContinue

Write-Host "   Port 3000: " -NoNewline
if ($port3000.TcpTestSucceeded) {
    Write-Host "OK" -ForegroundColor Green
} else {
    Write-Host "FAILED" -ForegroundColor Red
}

Write-Host "   Port 8000: " -NoNewline
if ($port8000.TcpTestSucceeded) {
    Write-Host "OK" -ForegroundColor Green
} else {
    Write-Host "FAILED" -ForegroundColor Red
}

# 3. Test Direct Connections
Write-Host "`n3. Testing Direct Connections:" -ForegroundColor Yellow

Write-Host "   Testing http://127.0.0.1:3000 ..." -NoNewline
try {
    $frontend = Invoke-WebRequest -Uri "http://127.0.0.1:3000" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host " OK (Status: $($frontend.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host " FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "   Testing http://127.0.0.1:8000/api/ ..." -NoNewline
try {
    $backend = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host " OK (Status: $($backend.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host " FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. Test IIS Proxy
Write-Host "`n4. Testing IIS Proxy:" -ForegroundColor Yellow

Write-Host "   Testing http://localhost ..." -NoNewline
try {
    $iisTest = Invoke-WebRequest -Uri "http://localhost" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    Write-Host " OK (Status: $($iisTest.StatusCode))" -ForegroundColor Green
    Write-Host "   Content Length: $($iisTest.Content.Length) bytes" -ForegroundColor Cyan
} catch {
    Write-Host " FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Error Details: $($_.Exception.GetType().FullName)" -ForegroundColor Gray
}

# 5. Check web.config
Write-Host "`n5. web.config Status:" -ForegroundColor Yellow
$webConfigPath = "C:\inetpub\wwwroot\web.config"
if (Test-Path $webConfigPath) {
    Write-Host "   File exists: YES" -ForegroundColor Green
    $config = Get-Content $webConfigPath -Raw
    if ($config -match "127.0.0.1:3000" -and $config -match "127.0.0.1:8000") {
        Write-Host "   Configuration: CORRECT" -ForegroundColor Green
    } else {
        Write-Host "   Configuration: CHECK NEEDED" -ForegroundColor Yellow
    }
} else {
    Write-Host "   File exists: NO" -ForegroundColor Red
}

# 6. Check Proxy Setting
Write-Host "`n6. Proxy Setting:" -ForegroundColor Yellow
try {
    $proxyEnabled = (Get-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" -Filter "system.webServer/proxy" -Name "enabled").Value
    Write-Host "   Proxy Enabled: $proxyEnabled" -ForegroundColor $(if ($proxyEnabled) { "Green" } else { "Red" })
} catch {
    Write-Host "   Could not check proxy setting" -ForegroundColor Yellow
}

# Summary
Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "`nIf all tests passed, your site should be accessible at:" -ForegroundColor Yellow
Write-Host "   http://localhost" -ForegroundColor White
Write-Host "   http://191.101.113.163" -ForegroundColor White
Write-Host "   http://myaibaz.ir (via Cloudflare)" -ForegroundColor White

