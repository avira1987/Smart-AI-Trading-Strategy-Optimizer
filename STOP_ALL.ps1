# Stop AI Forex Strategy Manager - All Services
$Host.UI.RawUI.WindowTitle = "AI Forex Strategy Manager - Stopping All Services"
$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Red
Write-Host "  AI Forex Strategy Manager" -ForegroundColor Red
Write-Host "  توقف تمام سرویس‌ها" -ForegroundColor Red
Write-Host "=========================================" -ForegroundColor Red
Write-Host ""
Write-Host "در حال توقف همه سرویس‌ها..." -ForegroundColor Yellow
Write-Host ""

# Stop Node processes
Write-Host "[1/4] توقف پردازه‌های Node..." -ForegroundColor Cyan
$nodeProcess = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcess) {
    Write-Host "  ✓ پردازه‌های Node متوقف شدند" -ForegroundColor Green
    Stop-Process -Name "node" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
} else {
    Write-Host "  ℹ هیچ پردازه Node‌ای در حال اجرا نبود" -ForegroundColor Gray
}
Write-Host ""

# Stop Python/Django processes
Write-Host "[2/4] توقف پردازه‌های Python (Django)..." -ForegroundColor Cyan
$pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    Write-Host "  ✓ پردازه‌های Python متوقف شدند" -ForegroundColor Green
    Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
} else {
    Write-Host "  ℹ هیچ پردازه Python‌ای در حال اجرا نبود" -ForegroundColor Gray
}
Write-Host ""

# Stop Celery processes
Write-Host "[3/4] توقف پردازه‌های Celery..." -ForegroundColor Cyan
$celeryProcesses = Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like "*celery*" }
if ($celeryProcesses) {
    Write-Host "  ✓ پردازه‌های Celery متوقف شدند" -ForegroundColor Green
    $celeryProcesses | ForEach-Object { 
        try {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        } catch {
            # Process might already be stopped
        }
    }
    Start-Sleep -Seconds 1
} else {
    Write-Host "  ℹ هیچ پردازه Celery‌ای در حال اجرا نبود" -ForegroundColor Gray
}
Write-Host ""

# Optional: Stop Redis (commented out by default)
Write-Host "[4/4] بررسی Redis..." -ForegroundColor Cyan
Write-Host "  ℹ Redis همچنان در حال اجرا است" -ForegroundColor Yellow
Write-Host "  برای توقف Redis: docker stop redis" -ForegroundColor Gray
Write-Host ""

Write-Host "=========================================" -ForegroundColor Green
Write-Host "  ✓ تمام سرویس‌ها متوقف شدند!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "توجه: Redis همچنان در حال اجرا است." -ForegroundColor Yellow
Write-Host "برای توقف Redis: docker stop redis" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
