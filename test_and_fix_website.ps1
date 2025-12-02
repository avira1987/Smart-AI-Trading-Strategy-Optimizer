# Test and Fix Website
Write-Host "=== Testing Website Access ===" -ForegroundColor Cyan

# Test 1: IP Address
Write-Host "`n1. Testing with IP address (http://191.101.113.163)..." -ForegroundColor Yellow
try {
    $ipResponse = Invoke-WebRequest -Uri "http://191.101.113.163" -UseBasicParsing -TimeoutSec 10
    Write-Host "   SUCCESS - Status: $($ipResponse.StatusCode)" -ForegroundColor Green
    Write-Host "   Content Length: $($ipResponse.Content.Length) bytes" -ForegroundColor Cyan
} catch {
    Write-Host "   FAILED - $($_.Exception.Message)" -ForegroundColor Red
    $ipFailed = $true
}

# Test 2: Domain
Write-Host "`n2. Testing with domain (http://myaibaz.ir)..." -ForegroundColor Yellow
try {
    $domainResponse = Invoke-WebRequest -Uri "http://myaibaz.ir" -UseBasicParsing -TimeoutSec 10
    Write-Host "   SUCCESS - Status: $($domainResponse.StatusCode)" -ForegroundColor Green
    Write-Host "   Content Length: $($domainResponse.Content.Length) bytes" -ForegroundColor Cyan
} catch {
    Write-Host "   FAILED - $($_.Exception.Message)" -ForegroundColor Red
    $domainFailed = $true
}

# Check IIS Status
Write-Host "`n3. Checking IIS Status..." -ForegroundColor Yellow
Import-Module WebAdministration -ErrorAction SilentlyContinue

$iisState = (Get-Service -Name W3SVC -ErrorAction SilentlyContinue).Status
Write-Host "   IIS Service: $iisState" -ForegroundColor $(if ($iisState -eq "Running") { "Green" } else { "Red" })

# Check Sites
$sites = Get-Website
Write-Host "   Sites:" -ForegroundColor Cyan
foreach ($site in $sites) {
    $siteState = (Get-WebsiteState -Name $site.Name).Value
    Write-Host "     $($site.Name): $siteState" -ForegroundColor $(if ($siteState -eq "Started") { "Green" } else { "Yellow" })
    
    $bindings = Get-WebBinding -Name $site.Name
    foreach ($binding in $bindings) {
        Write-Host "       $($binding.Protocol) - $($binding.BindingInformation)" -ForegroundColor Gray
    }
}

# Check Port 80
Write-Host "`n4. Checking Port 80..." -ForegroundColor Yellow
$port80 = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue
if ($port80.TcpTestSucceeded) {
    Write-Host "   Port 80: IN USE" -ForegroundColor Green
    $process = Get-NetTCPConnection -LocalPort 80 -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($process) {
        $pid = $process.OwningProcess
        $procName = (Get-Process -Id $pid -ErrorAction SilentlyContinue).ProcessName
        Write-Host "   Process: $procName (PID: $pid)" -ForegroundColor Cyan
    }
} else {
    Write-Host "   Port 80: NOT IN USE" -ForegroundColor Red
}

# Check Frontend and Backend
Write-Host "`n5. Checking Frontend and Backend..." -ForegroundColor Yellow
$port3000 = Test-NetConnection -ComputerName localhost -Port 3000 -WarningAction SilentlyContinue
$port8000 = Test-NetConnection -ComputerName localhost -Port 8000 -WarningAction SilentlyContinue

Write-Host "   Port 3000 (Frontend): " -NoNewline
if ($port3000.TcpTestSucceeded) {
    Write-Host "RUNNING" -ForegroundColor Green
} else {
    Write-Host "NOT RUNNING" -ForegroundColor Red
}

Write-Host "   Port 8000 (Backend): " -NoNewline
if ($port8000.TcpTestSucceeded) {
    Write-Host "RUNNING" -ForegroundColor Green
} else {
    Write-Host "NOT RUNNING" -ForegroundColor Red
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan



