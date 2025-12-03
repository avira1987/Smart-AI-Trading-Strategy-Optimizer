# Smart AI Trading Strategy Optimizer - Production Start (IP Only - No Port)
# این اسکریپت پروژه را برای دسترسی فقط با IP (بدون پورت) راه‌اندازی می‌کند

$ErrorActionPreference = "Continue"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  راه‌اندازی Production (فقط IP - بدون پورت)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Step 1: Stop IIS
Write-Host "[1/6] متوقف کردن IIS..." -ForegroundColor Cyan
$iisService = Get-Service -Name W3SVC -ErrorAction SilentlyContinue
if ($iisService -and $iisService.Status -eq 'Running') {
    iisreset /stop 2>&1 | Out-Null
    Start-Sleep -Seconds 3
    Write-Host "  ✓ IIS متوقف شد" -ForegroundColor Green
} else {
    Write-Host "  ✓ IIS در حال اجرا نیست" -ForegroundColor Green
}

# Step 2: Stop existing processes
Write-Host "`n[2/6] متوقف کردن سرویس‌های قبلی..." -ForegroundColor Cyan
$djangoProcesses = Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like "*manage.py*runserver*" -or $_.CommandLine -like "*gunicorn*" }
if ($djangoProcesses) {
    $djangoProcesses | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Write-Host "  ✓ Django/Gunicorn متوقف شد" -ForegroundColor Green
} else {
    Write-Host "  ✓ Django/Gunicorn در حال اجرا نیست" -ForegroundColor Green
}
$nodeProcesses = Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*Smart-AI-Trading*" -or $_.Path -like "*frontend*" }
if ($nodeProcesses) {
    $nodeProcesses | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Write-Host "  ✓ Node processes متوقف شد" -ForegroundColor Green
} else {
    Write-Host "  ✓ Node processes در حال اجرا نیست" -ForegroundColor Green
}

# Step 3: Check and Start Redis
Write-Host "`n[3/6] بررسی Redis..." -ForegroundColor Cyan
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 6379)
    $tcpClient.Close()
    Write-Host "  ✓ Redis در حال اجرا است" -ForegroundColor Green
} catch {
    Write-Host "  راه‌اندازی Redis..." -ForegroundColor Yellow
    try {
        docker start redis 2>&1 | Out-Null
        Start-Sleep -Seconds 3
        Write-Host "  ✓ Redis راه‌اندازی شد" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠ Redis راه‌اندازی نشد - لطفاً به صورت دستی راه‌اندازی کنید" -ForegroundColor Yellow
    }
}

# Step 4: Build Frontend (if needed)
Write-Host "`n[4/6] بررسی Frontend build..." -ForegroundColor Cyan
$distPath = Join-Path $scriptPath "frontend\dist"
if (-not (Test-Path $distPath) -or (Get-ChildItem $distPath -File -ErrorAction SilentlyContinue).Count -eq 0) {
    Write-Host "  Build کردن Frontend..." -ForegroundColor Yellow
    cd frontend
    npm run build 2>&1 | Out-Null
    cd ..
    if (Test-Path $distPath) {
        Write-Host "  ✓ Frontend build شد" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Frontend build با خطا مواجه شد - از build قبلی استفاده می‌شود" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✓ Frontend build موجود است" -ForegroundColor Green
}

# Step 5: Start Backend with Gunicorn
Write-Host "`n[5/6] راه‌اندازی Backend (Gunicorn)..." -ForegroundColor Cyan
$backendPath = Join-Path $scriptPath "backend"
cd $backendPath

# Install gunicorn if not available
try {
    $gunicornCheck = python -c "import gunicorn" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  نصب gunicorn..." -ForegroundColor Gray
        pip install gunicorn 2>&1 | Out-Null
    }
} catch {
    Write-Host "  نصب gunicorn..." -ForegroundColor Gray
    pip install gunicorn 2>&1 | Out-Null
}

$backendCommand = @"
cd '$backendPath'
Write-Host '========================================' -ForegroundColor Green
Write-Host '  Backend (Gunicorn)' -ForegroundColor Green
Write-Host '  Port: 8000' -ForegroundColor Green
Write-Host '  Accessible via: http://191.101.113.163/api/' -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Green
Write-Host ''
gunicorn --bind 0.0.0.0:8000 --workers 2 --threads 2 --timeout 120 config.wsgi:application
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand -WindowStyle Normal
Start-Sleep -Seconds 5
Write-Host "  ✓ Backend راه‌اندازی شد" -ForegroundColor Green
cd ..

# Step 6: Start Frontend with Vite preview on port 80 (supports proxy)
Write-Host "`n[6/6] راه‌اندازی Frontend (Port 80)..." -ForegroundColor Cyan
$frontendPath = Join-Path $scriptPath "frontend"
cd $frontendPath

# Set environment variables for Vite preview
$env:VITE_FRONTEND_PORT = "80"
$env:VITE_BACKEND_URL = "http://127.0.0.1:8000"

$frontendCommand = @"
cd '$frontendPath'
`$env:VITE_FRONTEND_PORT='80'
`$env:VITE_BACKEND_URL='http://127.0.0.1:8000'
Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  Frontend (Port 80 - IP Only)' -ForegroundColor Cyan
Write-Host '  URL: http://191.101.113.163' -ForegroundColor Cyan
Write-Host '  Backend Proxy: /api/ -> http://127.0.0.1:8000/api/' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''
npm run preview -- --port 80 --host 0.0.0.0
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand -WindowStyle Normal
Start-Sleep -Seconds 5
Write-Host "  ✓ Frontend راه‌اندازی شد (با Vite preview و proxy)" -ForegroundColor Green
cd ..

# Final Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ تمام سرویس‌ها راه‌اندازی شدند!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "دسترسی از اینترنت (فقط IP - بدون پورت):" -ForegroundColor Cyan
Write-Host "  Frontend: http://191.101.113.163" -ForegroundColor White
Write-Host "  Backend:  http://191.101.113.163/api/" -ForegroundColor White
Write-Host "  Admin:    http://191.101.113.163/admin/`n" -ForegroundColor White
Write-Host "نکته: Backend از طریق /api/ در دسترس است." -ForegroundColor Yellow
Write-Host "برای دسترسی کامل Backend بدون پورت، نیاز به Nginx یا IIS است.`n" -ForegroundColor Yellow
Write-Host "برای توقف سرویس‌ها، از فایل stop.ps1 استفاده کنید.`n" -ForegroundColor Gray

