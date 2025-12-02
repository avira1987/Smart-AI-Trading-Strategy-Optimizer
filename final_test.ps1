# Final Test
Import-Module WebAdministration -ErrorAction SilentlyContinue

$pool = (Get-Item "IIS:\Sites\MyWebsite").applicationPool
Restart-WebAppPool -Name $pool
Start-Sleep -Seconds 5

Write-Host "Testing http://localhost..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost" -UseBasicParsing -TimeoutSec 10
    Write-Host "SUCCESS! Status Code: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Content Length: $($response.Content.Length) bytes" -ForegroundColor Cyan
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

