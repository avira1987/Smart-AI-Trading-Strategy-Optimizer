# Final Test
Start-Sleep -Seconds 3
try {
    $response = Invoke-WebRequest -Uri "http://localhost" -UseBasicParsing -TimeoutSec 10
    Write-Host "SUCCESS - Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Content Length: $($response.Content.Length) bytes" -ForegroundColor Cyan
} catch {
    Write-Host "FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

