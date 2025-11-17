# Start AI Forex Strategy Manager - Complete Setup
$Host.UI.RawUI.WindowTitle = "AI Forex Strategy Manager - Starting All Services"
$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  AI Forex Strategy Manager" -ForegroundColor Green
Write-Host "  راه‌اندازی خودکار تمام سرویس‌ها" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "در حال راه‌اندازی همه سرویس‌ها..." -ForegroundColor Cyan
Write-Host ""

# ==========================================
# Step 1: Check and Start Redis
# ==========================================
Write-Host "[1/5] بررسی و راه‌اندازی Redis..." -ForegroundColor Cyan
Write-Host ""

$redisRunning = $false
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 6379)
    $tcpClient.Close()
    Write-Host "  ✓ Redis در حال اجرا است" -ForegroundColor Green
    $redisRunning = $true
} catch {
    Write-Host "  ⚠ Redis در حال اجرا نیست. در حال راه‌اندازی..." -ForegroundColor Yellow
    
    # Check if Docker is available
    $dockerAvailable = $false
    try {
        $dockerVersion = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $dockerAvailable = $true
            Write-Host "    Docker در دسترس است: $dockerVersion" -ForegroundColor Gray
        }
    } catch {
        Write-Host "  ✗ Docker در دسترس نیست. لطفاً Docker Desktop را باز کنید." -ForegroundColor Red
        Write-Host ""
        Write-Host "Press any key to exit..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
    
    if ($dockerAvailable) {
        try {
            # Check if Redis container already exists
            $existingContainer = docker ps -a --filter "name=redis" --format "{{.Names}}" 2>&1
            if ($existingContainer -eq "redis") {
                Write-Host "    در حال راه‌اندازی container موجود..." -ForegroundColor Cyan
                docker start redis 2>&1 | Out-Null
            } else {
                Write-Host "    در حال ایجاد container جدید..." -ForegroundColor Cyan
                docker run -d --name redis -p 6379:6379 redis:7-alpine 2>&1 | Out-Null
            }
            
            # Wait for Redis to start
            Start-Sleep -Seconds 5
            
            # Verify Redis is now running
            try {
                $tcpClient = New-Object System.Net.Sockets.TcpClient
                $tcpClient.Connect("localhost", 6379)
                $tcpClient.Close()
                Write-Host "  ✓ Redis با موفقیت راه‌اندازی شد!" -ForegroundColor Green
                $redisRunning = $true
            } catch {
                Write-Host "  ✗ خطا در راه‌اندازی Redis. لطفاً دستی بررسی کنید." -ForegroundColor Red
                Write-Host "    دستور: docker logs redis" -ForegroundColor Yellow
                Write-Host ""
                Write-Host "Press any key to exit..." -ForegroundColor Gray
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                exit 1
            }
        } catch {
            Write-Host "  ✗ خطا در راه‌اندازی Redis: $_" -ForegroundColor Red
            Write-Host ""
            Write-Host "Press any key to exit..." -ForegroundColor Gray
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            exit 1
        }
    }
}

if (-not $redisRunning) {
    Write-Host ""
    Write-Host "✗ خطا: Redis راه‌اندازی نشد!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host ""
Start-Sleep -Seconds 2

# ==========================================
# Step 2: Stop existing processes
# ==========================================
Write-Host "[2/5] توقف پردازه‌های قبلی..." -ForegroundColor Cyan
Write-Host ""

# Stop Node processes
Write-Host "  در حال بررسی پردازه‌های Node..." -ForegroundColor Gray
$nodeProcess = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcess) {
    Write-Host "  ✓ پردازه‌های Node متوقف شدند" -ForegroundColor Green
    Stop-Process -Name "node" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
} else {
    Write-Host "  ℹ هیچ پردازه Node‌ای در حال اجرا نبود" -ForegroundColor Gray
}

# Stop Celery processes
Write-Host "  در حال بررسی پردازه‌های Celery..." -ForegroundColor Gray
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
    Start-Sleep -Seconds 2
} else {
    Write-Host "  ℹ هیچ پردازه Celery‌ای در حال اجرا نبود" -ForegroundColor Gray
}

Write-Host ""
Start-Sleep -Seconds 2

# ==========================================
# Step 3: Start Backend (Django)
# ==========================================
Write-Host "[3/5] راه‌اندازی Backend (Django)..." -ForegroundColor Cyan
Write-Host ""
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\..\backend'; Write-Host '=========================================' -ForegroundColor Green; Write-Host '  Backend Django Server' -ForegroundColor Green; Write-Host '  Port: 8000 (Accessible from local network)' -ForegroundColor Green; Write-Host '=========================================' -ForegroundColor Green; Write-Host ''; python manage.py runserver 0.0.0.0:8000"
Start-Sleep -Seconds 4
Write-Host "  ✓ Backend در حال راه‌اندازی..." -ForegroundColor Green
Write-Host ""

# ==========================================
# Step 4: Start Frontend (React)
# ==========================================
Write-Host "[4/5] راه‌اندازی Frontend (React)..." -ForegroundColor Cyan
Write-Host ""
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\..\frontend'; Write-Host '=========================================' -ForegroundColor Cyan; Write-Host '  Frontend React Server' -ForegroundColor Cyan; Write-Host '  Port: 3000' -ForegroundColor Cyan; Write-Host '=========================================' -ForegroundColor Cyan; Write-Host ''; npm run dev"
Start-Sleep -Seconds 3
Write-Host "  ✓ Frontend در حال راه‌اندازی..." -ForegroundColor Green
Write-Host ""

# ==========================================
# Step 5: Start Celery Worker and Beat
# ==========================================
Write-Host "[5/5] راه‌اندازی Celery Worker و Beat..." -ForegroundColor Cyan
Write-Host ""

# Start Celery Worker
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\..\backend'; Write-Host '=========================================' -ForegroundColor Yellow; Write-Host '  Celery Worker' -ForegroundColor Yellow; Write-Host '=========================================' -ForegroundColor Yellow; Write-Host ''; celery -A config worker --loglevel=info --pool=solo"
Start-Sleep -Seconds 2
Write-Host "  ✓ Celery Worker در حال راه‌اندازی..." -ForegroundColor Green

# Start Celery Beat
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\..\backend'; Write-Host '=========================================' -ForegroundColor Magenta; Write-Host '  Celery Beat Scheduler' -ForegroundColor Magenta; Write-Host '  Auto-trading every 5 minutes' -ForegroundColor Magenta; Write-Host '=========================================' -ForegroundColor Magenta; Write-Host ''; celery -A config beat --loglevel=info"
Start-Sleep -Seconds 2
Write-Host "  ✓ Celery Beat در حال راه‌اندازی..." -ForegroundColor Green
Write-Host ""

# ==========================================
# Final Summary
# ==========================================
Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  ✓ همه سرویس‌ها با موفقیت راه‌اندازی شدند!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
# Get local IP address for network access
$localIP = ""
try {
    $localIP = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*","Wi-Fi*" | Where-Object { $_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" -or $_.IPAddress -like "172.16.*" } | Select-Object -First 1).IPAddress
    if (-not $localIP) {
        $localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } | Select-Object -First 1).IPAddress
    }
} catch {
    $localIP = ""
}

Write-Host "📋 آدرس‌های دسترسی:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  🌐 Frontend (Local):     http://localhost:3000" -ForegroundColor White
if ($localIP) {
    Write-Host "  🌐 Frontend (Network):   http://$localIP:3000" -ForegroundColor Cyan
}
Write-Host "  🔧 Backend (Local):      http://localhost:8000" -ForegroundColor White
if ($localIP) {
    Write-Host "  🔧 Backend (Network):    http://$localIP:8000" -ForegroundColor Cyan
}
Write-Host "  ⚙️  Admin (Local):        http://localhost:8000/admin/" -ForegroundColor White
if ($localIP) {
    Write-Host "  ⚙️  Admin (Network):      http://$localIP:8000/admin/" -ForegroundColor Cyan
}
Write-Host ""
Write-Host "🔑 اطلاعات ورود Admin:" -ForegroundColor Cyan
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: admin" -ForegroundColor White
Write-Host ""
Write-Host "📊 وضعیت سرویس‌ها:" -ForegroundColor Yellow
Write-Host "  ✓ Redis          (Port 6379)" -ForegroundColor Green
Write-Host "  ✓ Django Server  (Port 8000)" -ForegroundColor Green
Write-Host "  ✓ React Dev      (Port 3000)" -ForegroundColor Green
Write-Host "  ✓ Celery Worker  (در حال اجرا)" -ForegroundColor Green
Write-Host "  ✓ Celery Beat    (هر 5 دقیقه)" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  نکات مهم:" -ForegroundColor Yellow
Write-Host "  - Redis باید همیشه در حال اجرا باشد" -ForegroundColor White
Write-Host "  - برای معاملات خودکار، MT5 باید باز باشد" -ForegroundColor White
Write-Host "  - Celery Beat هر 5 دقیقه یکبار کار می‌کند" -ForegroundColor White
Write-Host ""
Write-Host "💡 برای متوقف کردن همه سرویس‌ها:" -ForegroundColor Cyan
Write-Host "  STOP_ALL.bat یا STOP_ALL.ps1 را اجرا کنید" -ForegroundColor White
Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "تمام پنجره‌های ترمینال باز شده‌اند." -ForegroundColor Gray
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
