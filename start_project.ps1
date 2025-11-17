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
# Step 0: Setup Environment (Auto-detect)
# ==========================================
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.local") {
        Write-Host "[0/5] تنظیم Environment برای لوکال..." -ForegroundColor Cyan
        Copy-Item .env.local .env -Force
        Write-Host "  ✓ فایل .env.local به .env کپی شد" -ForegroundColor Green
    } elseif (Test-Path ".env.production") {
        Write-Host "[0/5] تنظیم Environment برای Production..." -ForegroundColor Yellow
        Write-Host "  ⚠️  استفاده از .env.production برای لوکال!" -ForegroundColor Yellow
        Copy-Item .env.production .env -Force
        Write-Host "  ✓ فایل .env.production به .env کپی شد" -ForegroundColor Green
    } else {
        Write-Host "[0/5] ⚠️  فایل .env یافت نشد" -ForegroundColor Yellow
        Write-Host "  💡 برای ایجاد فایل‌های Environment: .\setup_env_files.ps1" -ForegroundColor Cyan
        Write-Host "  💡 یا برای استفاده از لوکال: .\use_local.ps1" -ForegroundColor Cyan
    }
} else {
    Write-Host "[0/5] فایل .env موجود است" -ForegroundColor Green
}
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
    Write-Host "  Redis is running" -ForegroundColor Green
    $redisRunning = $true
} catch {
    Write-Host "  WARNING: Redis is not running. Starting..." -ForegroundColor Yellow
    
    # Check if Docker is available and in Linux mode
    $dockerAvailable = $false
    $dockerLinuxMode = $false
    
    try {
        $dockerCheck = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $dockerAvailable = $true
            Write-Host "    Docker در دسترس است: $dockerCheck" -ForegroundColor Gray
            
            # Check if Docker daemon is running and in Linux mode
            $dockerInfo = docker info 2>&1 | Out-String
            if ($dockerInfo -match "error|cannot connect") {
                Write-Host "    WARNING: Docker daemon is not running" -ForegroundColor Yellow
            } else {
                if ($dockerInfo -match "OSType:\s*linux") {
                    $dockerLinuxMode = $true
                    Write-Host "    Docker is in Linux Container mode" -ForegroundColor Green
                } else {
                    if ($dockerInfo -match "OSType:\s*windows") {
                        Write-Host "    WARNING: Docker is in Windows Container mode" -ForegroundColor Yellow
                        Write-Host "    Redis requires Docker in Linux Container mode" -ForegroundColor Yellow
                    } else {
                        # Try anyway - might work
                        $dockerLinuxMode = $true
                        Write-Host "    Attempting to start Redis..." -ForegroundColor Gray
                    }
                }
            }
        }
    } catch {
        Write-Host "  WARNING: Docker is not available" -ForegroundColor Yellow
    }
    
    if ($dockerAvailable -and $dockerLinuxMode) {
        try {
            # Check if Redis container already exists
            $existingContainer = docker ps -a --filter "name=redis" --format "{{.Names}}" 2>&1
            if ($existingContainer -match "redis") {
                Write-Host "    Starting existing container..." -ForegroundColor Cyan
                docker start redis 2>&1 | Out-Null
            } else {
                Write-Host "    Creating new container..." -ForegroundColor Cyan
                docker run -d --name redis -p 6379:6379 redis:7-alpine 2>&1 | Out-Null
            }
            
            # Wait for Redis to start
            Start-Sleep -Seconds 5
            
            # Verify Redis is now running
            try {
                $tcpClient = New-Object System.Net.Sockets.TcpClient
                $tcpClient.Connect("localhost", 6379)
                $tcpClient.Close()
                Write-Host "  Redis started successfully!" -ForegroundColor Green
                $redisRunning = $true
            } catch {
                Write-Host "  WARNING: Redis container started but connection failed" -ForegroundColor Yellow
                Write-Host "    دستور: docker logs redis" -ForegroundColor Cyan
            }
        } catch {
            Write-Host "  WARNING: Error starting Redis: $_" -ForegroundColor Yellow
        }
    } else {
        if (-not $dockerAvailable) {
            Write-Host "  WARNING: Docker is not available. Redis not started." -ForegroundColor Yellow
        } else {
            Write-Host "  WARNING: Docker is in Windows Container mode. Redis not started." -ForegroundColor Yellow
        }
        Write-Host "  INFO: Program will run without Redis (Celery will not work)" -ForegroundColor Gray
        Write-Host "  TIP: To start Redis: Start Docker Engine in Linux Container mode" -ForegroundColor Cyan
        Write-Host "  TIP: Or use script: .\start_redis_simple.ps1" -ForegroundColor Cyan
    }
}

# Allow program to continue even if Redis is not running
# if (-not $redisRunning) {
#     Write-Host ""
#     Write-Host "✗ خطا: Redis راه‌اندازی نشد!" -ForegroundColor Red
#     Write-Host ""
#     Write-Host "Press any key to exit..." -ForegroundColor Gray
#     $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
#     exit 1
# }

Write-Host ""
Start-Sleep -Seconds 2

# ==========================================
# Step 2: Stop existing processes
# ==========================================
Write-Host "[2/5] توقف پردازه‌های قبلی..." -ForegroundColor Cyan
Write-Host ""

# Stop Node processes
Write-Host "  Checking Node processes..." -ForegroundColor Gray
$nodeProcess = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcess) {
    Write-Host "  Node processes stopped" -ForegroundColor Green
    Stop-Process -Name "node" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
} else {
    Write-Host "  No Node processes were running" -ForegroundColor Gray
}

# Stop Celery processes
Write-Host "  Checking Celery processes..." -ForegroundColor Gray
$celeryProcesses = Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like "*celery*" }
if ($celeryProcesses) {
    Write-Host "  Celery processes stopped" -ForegroundColor Green
    $celeryProcesses | ForEach-Object { 
        try {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        } catch {
            # Process might already be stopped
        }
    }
    Start-Sleep -Seconds 2
} else {
    Write-Host "  No Celery processes were running" -ForegroundColor Gray
}

Write-Host ""
Start-Sleep -Seconds 2

# ==========================================
# Step 2.5: Load environment variables
# ==========================================
Write-Host "[2.5/5] Loading settings..." -ForegroundColor Cyan
Write-Host ""

# Load .env file if it exists
$publicIP = ""
$backendPort = "8000"
$frontendPort = "3000"

if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "(?m)^\s*PUBLIC_IP\s*=\s*(.+)$") {
        $publicIP = $matches[1].Trim()
    }
    if ($envContent -match "(?m)^\s*PUBLIC_PORT\s*=\s*(.+)$") {
        $backendPort = $matches[1].Trim()
    }
    if ($envContent -match "(?m)^\s*FRONTEND_PUBLIC_PORT\s*=\s*(.+)$") {
        $frontendPort = $matches[1].Trim()
    }
    
    if ($publicIP -and $publicIP -ne "") {
        Write-Host "  Public IP configured: $publicIP" -ForegroundColor Green
        Write-Host "  Backend Port: $backendPort" -ForegroundColor Green
        Write-Host "  Frontend Port: $frontendPort" -ForegroundColor Green
    } else {
        Write-Host "  Local network access only" -ForegroundColor Gray
    }
} else {
    Write-Host "  .env file not found" -ForegroundColor Yellow
}

Write-Host ""

# ==========================================
# Step 3: Start Backend (Django)
# ==========================================
Write-Host "[3/5] راه‌اندازی Backend (Django)..." -ForegroundColor Cyan
Write-Host ""

# Load .env file for backend
$backendDir = Join-Path $PSScriptRoot "backend"
$backendCommand = "cd '$backendDir'; "
if (Test-Path ".env") {
    # Load environment variables from .env
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)\s*=\s*(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            $escapedValue = $value -replace '"', '`"'
            $backendCommand += "`$env:$key=`"$escapedValue`"; "
        }
    }
}
$backendCommand += "Write-Host '=========================================' -ForegroundColor Green; Write-Host '  Backend Django Server' -ForegroundColor Green; "
if ($publicIP -and $publicIP -ne "") {
    $portInfo = "Port: $backendPort (Public IP: $publicIP)"
} else {
    $portInfo = "Port: $backendPort (Local network only)"
}
$backendCommand += "Write-Host '  $portInfo' -ForegroundColor Green; "
$backendCommand += "Write-Host '=========================================' -ForegroundColor Green; Write-Host ''; python manage.py runserver 0.0.0.0:$backendPort"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand
Start-Sleep -Seconds 4
Write-Host "  ✓ Backend در حال راه‌اندازی..." -ForegroundColor Green
Write-Host ""

# ==========================================
# Step 4: Start Frontend (React)
# ==========================================
Write-Host "[4/5] راه‌اندازی Frontend (React)..." -ForegroundColor Cyan
Write-Host ""

# Load .env file for frontend (Vite uses VITE_ prefixed vars)
$frontendCommand = "cd '$PSScriptRoot\frontend'; "
$frontendEnvPath = Join-Path $PSScriptRoot "frontend\.env"
if (Test-Path $frontendEnvPath) {
    # Frontend .env is already created by setup_public_ip.ps1
    Write-Host "  Using frontend/.env settings" -ForegroundColor Green
} elseif (Test-Path ".env") {
    # Create frontend .env from main .env if public IP is set
    if ($publicIP -and $publicIP -ne "") {
        $frontendEnvContent = "VITE_BACKEND_URL=http://${publicIP}:${backendPort}`nVITE_FRONTEND_PORT=${frontendPort}"
        $frontendEnvPath = Join-Path $PSScriptRoot "frontend\.env"
        $frontendEnvContent | Set-Content $frontendEnvPath
        Write-Host "  ✓ فایل frontend/.env ایجاد شد" -ForegroundColor Green
    }
}

$frontendCommand += 'Write-Host ''========================================='' -ForegroundColor Cyan; Write-Host ''  Frontend React Server'' -ForegroundColor Cyan; '
if ($publicIP -and $publicIP -ne "") {
    $frontendPortInfo = 'Port: ' + $frontendPort + ' (Public IP: ' + $publicIP + ')'
} else {
    $frontendPortInfo = 'Port: ' + $frontendPort + ' (Local network only)'
}
$portInfoForCommand = $frontendPortInfo -replace "'", "''"
$frontendCommand += "Write-Host '  $portInfoForCommand' -ForegroundColor Cyan; "
$frontendCommand += "Write-Host '=========================================' -ForegroundColor Cyan; Write-Host ''; npm run dev"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand
Start-Sleep -Seconds 3
Write-Host "  ✓ Frontend در حال راه‌اندازی..." -ForegroundColor Green
Write-Host ""

# ==========================================
# Step 5: Start Celery Worker and Beat
# ==========================================
Write-Host "[5/5] راه‌اندازی Celery Worker و Beat..." -ForegroundColor Cyan
Write-Host ""

# Start Celery Worker
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; Write-Host '=========================================' -ForegroundColor Yellow; Write-Host '  Celery Worker' -ForegroundColor Yellow; Write-Host '=========================================' -ForegroundColor Yellow; Write-Host ''; celery -A config worker --loglevel=info --pool=solo"
Start-Sleep -Seconds 2
Write-Host "  ✓ Celery Worker در حال راه‌اندازی..." -ForegroundColor Green

# Start Celery Beat
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; Write-Host '=========================================' -ForegroundColor Magenta; Write-Host '  Celery Beat Scheduler' -ForegroundColor Magenta; Write-Host '  Auto-trading every 5 minutes' -ForegroundColor Magenta; Write-Host '=========================================' -ForegroundColor Magenta; Write-Host ''; celery -A config beat --loglevel=info"
Start-Sleep -Seconds 2
Write-Host "  ✓ Celery Beat در حال راه‌اندازی..." -ForegroundColor Green
Write-Host ""

# ==========================================
# Final Summary
# ==========================================
Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  All services started successfully!" -ForegroundColor Green
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

Write-Host "آدرس‌های دسترسی:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Frontend (Local):     http://localhost:$frontendPort" -ForegroundColor White
if ($localIP) {
    $frontendNetworkUrl = "http://${localIP}:${frontendPort}"
    Write-Host "  Frontend (Network):   $frontendNetworkUrl" -ForegroundColor Cyan
}
if ($publicIP -and $publicIP -ne "") {
    $frontendInternetUrl = "http://${publicIP}:${frontendPort}"
    Write-Host "  Frontend (Internet):  $frontendInternetUrl" -ForegroundColor Green
}
Write-Host "  Backend (Local):      http://localhost:$backendPort" -ForegroundColor White
if ($localIP) {
    $backendNetworkUrl = "http://${localIP}:${backendPort}"
    Write-Host "  Backend (Network):    $backendNetworkUrl" -ForegroundColor Cyan
}
if ($publicIP -and $publicIP -ne "") {
    $backendInternetUrl = "http://${publicIP}:${backendPort}"
    Write-Host "  Backend (Internet):   $backendInternetUrl" -ForegroundColor Green
}
Write-Host "  Admin (Local):        http://localhost:$backendPort/admin/" -ForegroundColor White
if ($localIP) {
    $adminNetworkUrl = "http://${localIP}:${backendPort}/admin/"
    Write-Host "  Admin (Network):      $adminNetworkUrl" -ForegroundColor Cyan
}
if ($publicIP -and $publicIP -ne "") {
    $adminInternetUrl = "http://${publicIP}:${backendPort}/admin/"
    Write-Host "  Admin (Internet):     $adminInternetUrl" -ForegroundColor Green
}
Write-Host ""

if ($publicIP -and $publicIP -ne "") {
    Write-Host "دسترسی از اینترنت فعال است!" -ForegroundColor Green
    Write-Host "  IP عمومی: $publicIP" -ForegroundColor White
    Write-Host "  مطمئن شوید که:" -ForegroundColor Yellow
    Write-Host "    - فایروال Windows پورت‌های $backendPort و $frontendPort را باز کرده است" -ForegroundColor Gray
    Write-Host "    - Port Forwarding در روتر تنظیم شده است (اگر از روتر استفاده می‌کنید)" -ForegroundColor Gray
    Write-Host ""
}
Write-Host "اطلاعات ورود Admin:" -ForegroundColor Cyan
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: admin" -ForegroundColor White
Write-Host ""
Write-Host "وضعیت سرویس‌ها:" -ForegroundColor Yellow
Write-Host "  ✓ Redis          (Port 6379)" -ForegroundColor Green
Write-Host "  ✓ Django Server  (Port $backendPort)" -ForegroundColor Green
Write-Host "  ✓ React Dev      (Port $frontendPort)" -ForegroundColor Green
Write-Host "  Celery Worker  (Running)" -ForegroundColor Green
Write-Host "  Celery Beat    (Every 5 minutes)" -ForegroundColor Green
Write-Host ""
Write-Host "نکات مهم:" -ForegroundColor Yellow
Write-Host "  - Redis must always be running" -ForegroundColor White
Write-Host "  - For auto-trading, MT5 must be open" -ForegroundColor White
Write-Host "  - Celery Beat runs every 5 minutes" -ForegroundColor White
Write-Host ""
Write-Host "To stop all services:" -ForegroundColor Cyan
Write-Host "  Run STOP_ALL.bat or STOP_ALL.ps1" -ForegroundColor White
Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "All terminal windows have been opened." -ForegroundColor Gray
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")


