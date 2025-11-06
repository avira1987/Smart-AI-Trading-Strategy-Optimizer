# Stop Celery Processes
$ErrorActionPreference = "SilentlyContinue"

try {
    $processes = Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like "*celery*" }
    if ($processes) {
        $processes | ForEach-Object { 
            try {
                Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            } catch {
                # Process might already be stopped
            }
        }
        Start-Sleep -Seconds 2
        Write-Host "  ✓ Celery processes stopped" -ForegroundColor Green
    } else {
        Write-Host "  ℹ No Celery processes were running" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ℹ No Celery processes were running" -ForegroundColor Gray
}
