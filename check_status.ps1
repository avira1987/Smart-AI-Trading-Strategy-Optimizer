# Check Current Status
Write-Host "=== Current Status ===" -ForegroundColor Cyan

# Check Ports
Write-Host "`nPort Status:" -ForegroundColor Yellow
$p80 = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue
$p3000 = Test-NetConnection -ComputerName localhost -Port 3000 -WarningAction SilentlyContinue
$p8000 = Test-NetConnection -ComputerName localhost -Port 8000 -WarningAction SilentlyContinue

Write-Host "  Port 80 (IIS): " -NoNewline
Write-Host $(if ($p80.TcpTestSucceeded) { "IN USE" } else { "FREE" }) -ForegroundColor $(if ($p80.TcpTestSucceeded) { "Green" } else { "Gray" })

Write-Host "  Port 3000 (Frontend): " -NoNewline
Write-Host $(if ($p3000.TcpTestSucceeded) { "RUNNING" } else { "NOT RUNNING" }) -ForegroundColor $(if ($p3000.TcpTestSucceeded) { "Green" } else { "Red" })

Write-Host "  Port 8000 (Backend): " -NoNewline
Write-Host $(if ($p8000.TcpTestSucceeded) { "RUNNING" } else { "NOT RUNNING" }) -ForegroundColor $(if ($p8000.TcpTestSucceeded) { "Green" } else { "Red" })

# Check IIS
Write-Host "`nIIS Status:" -ForegroundColor Yellow
Import-Module WebAdministration -ErrorAction SilentlyContinue
$iisService = Get-Service -Name W3SVC -ErrorAction SilentlyContinue
Write-Host "  Service: $($iisService.Status)" -ForegroundColor $(if ($iisService.Status -eq "Running") { "Green" } else { "Red" })

$site = Get-Website -Name "MyWebsite" -ErrorAction SilentlyContinue
if ($site) {
    $siteState = (Get-WebsiteState -Name "MyWebsite").Value
    Write-Host "  Site 'MyWebsite': $siteState" -ForegroundColor $(if ($siteState -eq "Started") { "Green" } else { "Yellow" })
    
    $bindings = Get-WebBinding -Name "MyWebsite"
    Write-Host "  Bindings:" -ForegroundColor Cyan
    foreach ($b in $bindings) {
        Write-Host "    $($b.Protocol) - $($b.BindingInformation)" -ForegroundColor Gray
    }
}

# Test Access
Write-Host "`nAccess Tests:" -ForegroundColor Yellow
Start-Sleep -Seconds 2

try {
    $ipTest = Invoke-WebRequest -Uri "http://191.101.113.163" -UseBasicParsing -TimeoutSec 10
    Write-Host "  IP (191.101.113.163): SUCCESS - Status $($ipTest.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "  IP (191.101.113.163): FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

try {
    $domainTest = Invoke-WebRequest -Uri "http://myaibaz.ir" -UseBasicParsing -TimeoutSec 10
    Write-Host "  Domain (myaibaz.ir): SUCCESS - Status $($domainTest.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "  Domain (myaibaz.ir): FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Status Check Complete ===" -ForegroundColor Cyan



