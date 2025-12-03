# Smart AI Trading Strategy Optimizer - Start Script
# This script starts all services for internet access
# Only Nginx is accessible from the internet (port 80)
# Backend runs only on localhost (127.0.0.1:8000)
# Frontend is served through Nginx

$ErrorActionPreference = "Continue"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Smart AI Trading Strategy Optimizer" -ForegroundColor Green
Write-Host "  Starting for Internet Access" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# ==========================================
# Step 1: Stop IIS
# ==========================================
Write-Host "[1/9] Stopping IIS..." -ForegroundColor Cyan
try {
    $iisService = Get-Service -Name W3SVC -ErrorAction SilentlyContinue
    if ($iisService -and $iisService.Status -eq 'Running') {
        iisreset /stop 2>&1 | Out-Null
        Start-Sleep -Seconds 3
        Write-Host "  ✓ IIS stopped" -ForegroundColor Green
    } else {
        Write-Host "  ✓ IIS is not running" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠ Error checking IIS: $_" -ForegroundColor Yellow
}

Write-Host ""

# ==========================================
# Step 2: Stop existing processes
# ==========================================
Write-Host "[2/9] Stopping previous services..." -ForegroundColor Cyan

# Stop Node processes (Frontend)
$nodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcesses) {
    Write-Host "  Stopping Node processes..." -ForegroundColor Gray
    $nodeProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "  ✓ Node processes stopped" -ForegroundColor Green
} else {
    Write-Host "  ✓ No Node processes were running" -ForegroundColor Green
}

# Stop Django processes (Backend)
$djangoProcesses = Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like "*manage.py*runserver*" }
if ($djangoProcesses) {
    Write-Host "  Stopping Django processes..." -ForegroundColor Gray
    $djangoProcesses | ForEach-Object { 
        try {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        } catch {}
    }
    Start-Sleep -Seconds 2
    Write-Host "  ✓ Django processes stopped" -ForegroundColor Green
} else {
    Write-Host "  ✓ No Django processes were running" -ForegroundColor Green
}

# Stop Celery processes
$celeryProcesses = Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like "*celery*" }
if ($celeryProcesses) {
    Write-Host "  Stopping Celery processes..." -ForegroundColor Gray
    $celeryProcesses | ForEach-Object { 
        try {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        } catch {}
    }
    Start-Sleep -Seconds 2
    Write-Host "  ✓ Celery processes stopped" -ForegroundColor Green
} else {
    Write-Host "  ✓ No Celery processes were running" -ForegroundColor Green
}

# Stop Nginx processes
$nginxProcesses = Get-Process -Name "nginx" -ErrorAction SilentlyContinue
if ($nginxProcesses) {
    Write-Host "  Stopping Nginx processes..." -ForegroundColor Gray
    $nginxProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "  ✓ Nginx processes stopped" -ForegroundColor Green
} else {
    Write-Host "  ✓ No Nginx processes were running" -ForegroundColor Green
}

Write-Host ""

# ==========================================
# Step 3: Check port 80
# ==========================================
Write-Host "[3/9] Checking port 80..." -ForegroundColor Cyan
$port80Check = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue
if ($port80Check.TcpTestSucceeded) {
    Write-Host "  ⚠ Port 80 is in use!" -ForegroundColor Yellow
    Write-Host "  Attempting to free it..." -ForegroundColor Yellow
    # Try to stop IIS again
    iisreset /stop 2>&1 | Out-Null
    Start-Sleep -Seconds 3
    $port80Check2 = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue
    if ($port80Check2.TcpTestSucceeded) {
        Write-Host "  ✗ Port 80 is still in use. Please check manually" -ForegroundColor Red
        Write-Host "  Command: netstat -ano | findstr :80" -ForegroundColor Yellow
        exit 1
    } else {
        Write-Host "  ✓ Port 80 is now free" -ForegroundColor Green
    }
} else {
    Write-Host "  ✓ Port 80 is free" -ForegroundColor Green
}

Write-Host ""

# ==========================================
# Step 4: Check and Start Redis
# ==========================================
Write-Host "[4/9] Checking and starting Redis..." -ForegroundColor Cyan
$redisRunning = $false

try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 6379)
    $tcpClient.Close()
    Write-Host "  ✓ Redis is running" -ForegroundColor Green
    $redisRunning = $true
} catch {
    Write-Host "  ⚠ Redis is not running. Starting..." -ForegroundColor Yellow
    
    # Check Docker
    $dockerAvailable = $false
    try {
        $dockerCheck = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $dockerAvailable = $true
        }
    } catch {
        Write-Host "  ✗ Docker is not available" -ForegroundColor Red
    }
    
    if ($dockerAvailable) {
        try {
            $existingContainer = docker ps -a --filter "name=redis" --format "{{.Names}}" 2>&1
            if ($existingContainer -eq "redis") {
                Write-Host "    Starting existing container..." -ForegroundColor Gray
                docker start redis 2>&1 | Out-Null
            } else {
                Write-Host "    Creating new container..." -ForegroundColor Gray
                docker run -d --name redis -p 6379:6379 redis:7-alpine 2>&1 | Out-Null
            }
            
            Start-Sleep -Seconds 3
            
            try {
                $tcpClient2 = New-Object System.Net.Sockets.TcpClient
                $tcpClient2.Connect("localhost", 6379)
                $tcpClient2.Close()
                Write-Host "  ✓ Redis started successfully!" -ForegroundColor Green
                $redisRunning = $true
            } catch {
                Write-Host "  ✗ Error starting Redis" -ForegroundColor Red
            }
        } catch {
            Write-Host "  ✗ Error starting Redis: $_" -ForegroundColor Red
        }
    }
}

if (-not $redisRunning) {
    Write-Host ""
    Write-Host "  ⚠ Warning: Redis is not running!" -ForegroundColor Yellow
    Write-Host "  Some features may not work" -ForegroundColor Yellow
    Write-Host "  To start Redis: docker start redis" -ForegroundColor Cyan
}

Write-Host ""

# ==========================================
# Step 5: Run Database Migrations
# ==========================================
Write-Host "[5/9] Running Database Migrations..." -ForegroundColor Cyan
$backendPath = Join-Path $scriptPath "backend"

# Check for Python virtual environment
$venvPython = Join-Path $backendPath "venv\Scripts\python.exe"
$rootVenvPython = Join-Path $scriptPath "venv\Scripts\python.exe"

$pythonExe = "python"
if (Test-Path $venvPython) {
    $pythonExe = $venvPython
} elseif (Test-Path $rootVenvPython) {
    $pythonExe = $rootVenvPython
}

Set-Location $backendPath
Write-Host "  Running migrations..." -ForegroundColor Gray
& $pythonExe manage.py migrate 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Migrations completed successfully" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Migration completed with warnings" -ForegroundColor Yellow
}

Set-Location $scriptPath
Write-Host ""

# ==========================================
# Step 6: Start Backend (Django) on localhost:8000
# ==========================================
Write-Host "[6/9] Starting Backend (Django) on localhost:8000..." -ForegroundColor Cyan
$backendPath = Join-Path $scriptPath "backend"

# Determine Python executable to use (same as migrations)
$venvPython = Join-Path $backendPath "venv\Scripts\python.exe"
$rootVenvPython = Join-Path $scriptPath "venv\Scripts\python.exe"

$pythonExeForBackend = "python"
if (Test-Path $venvPython) {
    $pythonExeForBackend = $venvPython
    Write-Host "  Using Python from backend\venv" -ForegroundColor Gray
} elseif (Test-Path $rootVenvPython) {
    $pythonExeForBackend = $rootVenvPython
    Write-Host "  Using Python from root\venv" -ForegroundColor Gray
} else {
    Write-Host "  Using system Python" -ForegroundColor Gray
}

# Set PUBLIC_IP for backend configuration
$publicIP = "191.101.113.163"  # Your known IP

# Escape the Python path for use in PowerShell command
$pythonExeEscaped = $pythonExeForBackend -replace "'", "''"
$backendCommand = @"
cd '$backendPath'
`$env:PUBLIC_IP='$publicIP'
`$env:ALLOWED_HOSTS='localhost,127.0.0.1,$publicIP'
Write-Host '========================================' -ForegroundColor Green
Write-Host '  Backend Django Server' -ForegroundColor Green
Write-Host '  Port: 8000' -ForegroundColor Green
Write-Host '  Accessible from: 127.0.0.1:8000 (localhost only)' -ForegroundColor Green
Write-Host '  Public IP: $publicIP' -ForegroundColor Green
Write-Host '  Security: Only accessible from localhost' -ForegroundColor Yellow
Write-Host '========================================' -ForegroundColor Green
Write-Host ''
& '$pythonExeEscaped' manage.py runserver 127.0.0.1:8000
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand
Start-Sleep -Seconds 5
Write-Host "  ✓ Backend is starting..." -ForegroundColor Green

# Wait a bit more and verify backend is running
Start-Sleep -Seconds 3
try {
    $backendCheck = Test-NetConnection -ComputerName localhost -Port 8000 -WarningAction SilentlyContinue
    if ($backendCheck.TcpTestSucceeded) {
        Write-Host "  ✓ Backend is running on port 8000" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Backend is not ready yet, please wait a few seconds" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠ Could not check Backend status" -ForegroundColor Yellow
}

Write-Host ""

# ==========================================
# Step 7: Build Frontend
# ==========================================
Write-Host "[7/9] Building Frontend..." -ForegroundColor Cyan

# Check if npm is available
$npmAvailable = $false
try {
    $npmVersion = npm --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $npmAvailable = $true
        Write-Host "  ✓ npm is available (v$npmVersion)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ⚠ npm not found" -ForegroundColor Yellow
}

if (-not $npmAvailable) {
    Write-Host "  ✗ npm is not available. Please install Node.js" -ForegroundColor Red
    exit 1
}

# Check if Frontend is built
$distPath = Join-Path $scriptPath "frontend\dist"
if (-not (Test-Path $distPath) -or (Get-ChildItem $distPath -File -ErrorAction SilentlyContinue).Count -eq 0) {
    Write-Host "  Building Frontend..." -ForegroundColor Yellow
    $frontendDir = Join-Path $scriptPath "frontend"
    if (-not (Test-Path $frontendDir)) {
        Write-Host "  ✗ Frontend folder not found!" -ForegroundColor Red
        exit 1
    }
    Set-Location $frontendDir
    # Don't set VITE_BACKEND_URL for production build
    # In production, we use relative URL '/api' which goes through Nginx proxy
    # VITE_BACKEND_URL is only for development mode
    if ($env:VITE_BACKEND_URL) {
        Remove-Item Env:\VITE_BACKEND_URL
    }
    $buildOutput = npm run build 2>&1
    $buildSuccess = $LASTEXITCODE -eq 0
    Set-Location $scriptPath
    if ($buildSuccess -and (Test-Path $distPath)) {
        Write-Host "  ✓ Frontend built successfully" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Error building Frontend" -ForegroundColor Red
        Write-Host "  Build output:" -ForegroundColor Yellow
        $buildOutput | Select-Object -Last 10 | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        exit 1
    }
} else {
    Write-Host "  ✓ Frontend build exists" -ForegroundColor Green
}

Write-Host ""

# ==========================================
# Step 8: Setup and Start Nginx
# ==========================================
Write-Host "[8/9] Starting Nginx as Reverse Proxy..." -ForegroundColor Cyan

# Check if Nginx is installed
$nginxPath = "C:\nginx\nginx.exe"
$nginxInstalled = $false

# Check common Nginx installation paths
$possiblePaths = @(
    "C:\nginx\nginx.exe",
    "C:\nginx-1.28.0\nginx.exe",
    "C:\nginx-1.27.0\nginx.exe",
    "C:\nginx-1.26.0\nginx.exe",
    "C:\nginx-1.25.0\nginx.exe",
    "C:\nginx-1.24.0\nginx.exe",
    "C:\Program Files\nginx\nginx.exe",
    "C:\Program Files (x86)\nginx\nginx.exe",
    "$env:ProgramFiles\nginx\nginx.exe",
    "$env:ProgramFiles(x86)\nginx\nginx.exe"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $nginxPath = $path
        $nginxInstalled = $true
        Write-Host "  ✓ Nginx found: $path" -ForegroundColor Green
        break
    }
}

if (-not $nginxInstalled) {
    Write-Host "  ⚠ Nginx is not installed!" -ForegroundColor Yellow
    Write-Host "  For full security, Nginx should be installed" -ForegroundColor Yellow
    Write-Host "  Installation guide:" -ForegroundColor Cyan
    Write-Host "    1. Download from: http://nginx.org/en/download.html" -ForegroundColor Gray
    Write-Host "    2. Extract to C:\nginx" -ForegroundColor Gray
    Write-Host "    3. Copy nginx_production.conf to C:\nginx\conf\nginx.conf" -ForegroundColor Gray
    Write-Host "    4. Copy frontend\dist contents to C:\nginx\html" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Using alternative method (Direct Frontend)..." -ForegroundColor Yellow
    
    # Fallback: Start frontend directly (less secure but works)
    Write-Host "  Using direct Frontend server (Nginx not installed)" -ForegroundColor Yellow
    
    # Ensure frontend is built
    $distPath = Join-Path $scriptPath "frontend\dist"
    if (-not (Test-Path $distPath) -or (Get-ChildItem $distPath -File -ErrorAction SilentlyContinue).Count -eq 0) {
        Write-Host "  Frontend not built, building now..." -ForegroundColor Yellow
        $frontendDir = Join-Path $scriptPath "frontend"
        Set-Location $frontendDir
        $buildOutput = npm run build 2>&1
        $buildSuccess = $LASTEXITCODE -eq 0
        Set-Location $scriptPath
        if (-not $buildSuccess) {
            Write-Host "  ✗ Failed to build Frontend" -ForegroundColor Red
            Write-Host "  Build output:" -ForegroundColor Yellow
            $buildOutput | Select-Object -Last 10 | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
            exit 1
        }
        Write-Host "  ✓ Frontend built successfully" -ForegroundColor Green
    }
    
    # Check if port 80 is available
    $port80Check = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($port80Check) {
        Write-Host "  ⚠ Port 80 is already in use!" -ForegroundColor Yellow
        Write-Host "  Trying to stop conflicting services..." -ForegroundColor Yellow
        iisreset /stop 2>&1 | Out-Null
        Start-Sleep -Seconds 3
        
        # Check again
        $port80Check2 = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue -InformationLevel Quiet
        if ($port80Check2) {
            Write-Host "  ✗ Port 80 is still in use. Please free it manually" -ForegroundColor Red
            Write-Host "  Command: netstat -ano | findstr :80" -ForegroundColor Yellow
            exit 1
        }
    }
    
    $frontendPath = Join-Path $scriptPath "frontend"
    $frontendCommand = @"
cd '$frontendPath'
`$env:VITE_FRONTEND_PORT='80'
`$env:VITE_BACKEND_URL='http://127.0.0.1:8000'
Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  Frontend React Server (Direct)' -ForegroundColor Cyan
Write-Host '  Port: 80' -ForegroundColor Cyan
Write-Host '  Backend URL: http://127.0.0.1:8000' -ForegroundColor Cyan
Write-Host '  ⚠ Note: Nginx recommended for production' -ForegroundColor Yellow
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''
npm run preview -- --port 80 --host 0.0.0.0
"@
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand
    Start-Sleep -Seconds 8
    
    # Verify frontend is running
    try {
        $frontendCheck = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue -InformationLevel Quiet
        if ($frontendCheck) {
            Write-Host "  ✓ Frontend is running on port 80" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ Frontend may not have started yet, please wait a few seconds" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ⚠ Could not verify Frontend status" -ForegroundColor Yellow
    }
} else {
    # Nginx is installed, use it
    $nginxConfPath = Join-Path $scriptPath "nginx_production.conf"
    $nginxConfDir = Split-Path $nginxPath -Parent
    $nginxConfSubDir = Join-Path $nginxConfDir "conf"
    $targetConfPath = Join-Path $nginxConfSubDir "nginx.conf"
    
    # Create conf directory if it doesn't exist
    if (-not (Test-Path $nginxConfSubDir)) {
        Write-Host "  Creating Nginx conf directory..." -ForegroundColor Gray
        New-Item -ItemType Directory -Path $nginxConfSubDir -Force | Out-Null
        Write-Host "  ✓ Conf directory created: $nginxConfSubDir" -ForegroundColor Green
    }
    
    # Copy frontend dist to nginx html directory
    $nginxHtmlDir = Join-Path $nginxConfDir "html"
    if (-not (Test-Path $nginxHtmlDir)) {
        Write-Host "  Creating Nginx html directory..." -ForegroundColor Gray
        New-Item -ItemType Directory -Path $nginxHtmlDir -Force | Out-Null
        Write-Host "  ✓ Html directory created: $nginxHtmlDir" -ForegroundColor Green
    }
    
    Write-Host "  Copying Frontend files to Nginx..." -ForegroundColor Gray
    $distPath = Join-Path $scriptPath "frontend\dist"
    if (Test-Path $distPath) {
        Copy-Item -Path "$distPath\*" -Destination $nginxHtmlDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ Frontend files copied to: $nginxHtmlDir" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Frontend dist folder not found: $distPath" -ForegroundColor Yellow
    }
    
    # Copy nginx config
    Write-Host "  Copying Nginx configuration..." -ForegroundColor Gray
    Write-Host "    Source: $nginxConfPath" -ForegroundColor Gray
    Write-Host "    Destination: $targetConfPath" -ForegroundColor Gray
    if (Test-Path $nginxConfPath) {
        Copy-Item -Path $nginxConfPath -Destination $targetConfPath -Force -ErrorAction SilentlyContinue
        if (Test-Path $targetConfPath) {
            Write-Host "  ✓ Nginx configuration copied successfully" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Failed to copy Nginx configuration" -ForegroundColor Red
        }
    } else {
        Write-Host "  ⚠ nginx_production.conf file not found at: $nginxConfPath" -ForegroundColor Yellow
    }
    
    # Stop any existing Nginx processes first
    Write-Host "  Stopping any existing Nginx processes..." -ForegroundColor Gray
    $existingNginx = Get-Process -Name "nginx" -ErrorAction SilentlyContinue
    if ($existingNginx) {
        $existingNginx | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Write-Host "  ✓ Stopped existing Nginx processes" -ForegroundColor Green
    }
    
    # Test Nginx configuration before starting
    Write-Host "  Testing Nginx configuration..." -ForegroundColor Gray
    $nginxDir = Split-Path $nginxPath -Parent
    Set-Location $nginxDir
    $configTest = & $nginxPath -t 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Nginx configuration is valid" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Nginx configuration test failed:" -ForegroundColor Yellow
        $configTest | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        Write-Host "  → Continuing anyway, but Nginx may not start correctly" -ForegroundColor Yellow
    }
    
    # Start Nginx in a separate window to show logs
    Write-Host "  Starting Nginx..." -ForegroundColor Gray
    $nginxCommand = @"
cd '$nginxDir'
Write-Host '========================================' -ForegroundColor Green
Write-Host '  Nginx Reverse Proxy Server' -ForegroundColor Green
Write-Host '  Port: 80' -ForegroundColor Green
Write-Host '  Config: $targetConfPath' -ForegroundColor Green
Write-Host '  Logs: $nginxDir\logs\' -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Green
Write-Host ''
Write-Host 'Nginx is running. Logs will appear below:' -ForegroundColor Cyan
Write-Host 'Press Ctrl+C to stop Nginx' -ForegroundColor Yellow
Write-Host ''
& '$nginxPath'
"@
    
    # Start Nginx in a visible window for logs
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $nginxCommand
    Start-Sleep -Seconds 5
    
    # Verify Nginx is running
    try {
        $nginxCheck = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue -InformationLevel Quiet
        if ($nginxCheck) {
            Write-Host "  ✓ Nginx started successfully on port 80" -ForegroundColor Green
            
            # Check Nginx processes
            $nginxProcesses = Get-Process -Name "nginx" -ErrorAction SilentlyContinue
            if ($nginxProcesses) {
                Write-Host "  ✓ Nginx processes running ($($nginxProcesses.Count) process(es))" -ForegroundColor Green
            }
            
            # Try to access Nginx
            try {
                $nginxResponse = Invoke-WebRequest -Uri "http://localhost/health" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
                if ($nginxResponse.StatusCode -eq 200) {
                    Write-Host "  ✓ Nginx is responding to requests" -ForegroundColor Green
                }
            } catch {
                Write-Host "  ⚠ Nginx may not be fully ready yet" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  ⚠ Nginx may not have started - port 80 is not open" -ForegroundColor Yellow
            Write-Host "  → Check Nginx window for error messages" -ForegroundColor Cyan
            Write-Host "  → Check logs at: $nginxDir\logs\error.log" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "  ⚠ Could not verify Nginx status: $_" -ForegroundColor Yellow
    }
    
    Set-Location $scriptPath
}

Write-Host ""

# ==========================================
# Step 9: Start Celery Worker and Beat
# ==========================================
Write-Host "[9/9] Starting Celery Worker and Beat..." -ForegroundColor Cyan
$backendPath = Join-Path $scriptPath "backend"

# Determine Python executable to use (same as backend)
$venvPython = Join-Path $backendPath "venv\Scripts\python.exe"
$rootVenvPython = Join-Path $scriptPath "venv\Scripts\python.exe"

$pythonExeForCelery = "python"
if (Test-Path $venvPython) {
    $pythonExeForCelery = $venvPython
    Write-Host "  Using Python from backend\venv" -ForegroundColor Gray
} elseif (Test-Path $rootVenvPython) {
    $pythonExeForCelery = $rootVenvPython
    Write-Host "  Using Python from root\venv" -ForegroundColor Gray
} else {
    Write-Host "  Using system Python" -ForegroundColor Gray
}

# Set Redis URLs for Celery
$redisUrl = "redis://localhost:6379/0"

# Escape the Python path for use in PowerShell command
$pythonExeEscaped = $pythonExeForCelery -replace "'", "''"

# Start Celery Worker
Write-Host "  Starting Celery Worker..." -ForegroundColor Gray
$celeryWorkerCommand = @"
cd '$backendPath'
`$env:CELERY_BROKER_URL='$redisUrl'
`$env:REDIS_URL='$redisUrl'
Write-Host '========================================' -ForegroundColor Yellow
Write-Host '  Celery Worker' -ForegroundColor Yellow
Write-Host '  Redis: localhost:6379' -ForegroundColor Yellow
Write-Host '========================================' -ForegroundColor Yellow
Write-Host ''
& '$pythonExeEscaped' -m celery -A config worker --loglevel=info --pool=solo
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $celeryWorkerCommand
Start-Sleep -Seconds 2
Write-Host "  ✓ Celery Worker is starting..." -ForegroundColor Green

# Start Celery Beat
Write-Host "  Starting Celery Beat..." -ForegroundColor Gray
$celeryBeatCommand = @"
cd '$backendPath'
`$env:CELERY_BROKER_URL='$redisUrl'
`$env:REDIS_URL='$redisUrl'
Write-Host '========================================' -ForegroundColor Magenta
Write-Host '  Celery Beat Scheduler' -ForegroundColor Magenta
Write-Host '  Redis: localhost:6379' -ForegroundColor Magenta
Write-Host '  Auto-trading every 5 minutes' -ForegroundColor Magenta
Write-Host '========================================' -ForegroundColor Magenta
Write-Host ''
& '$pythonExeEscaped' -m celery -A config beat --loglevel=info
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $celeryBeatCommand
Start-Sleep -Seconds 2
Write-Host "  ✓ Celery Beat is starting..." -ForegroundColor Green

# Wait a bit and verify Celery processes
Start-Sleep -Seconds 3
try {
    $celeryProcesses = Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like "*celery*" }
    if ($celeryProcesses) {
        Write-Host "  ✓ Celery processes are running ($($celeryProcesses.Count) processes)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Celery processes may not have started yet" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠ Could not check Celery status" -ForegroundColor Yellow
}

Write-Host ""

# ==========================================
# Final Summary
# ==========================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ All services started successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# ==========================================
# Final Verification
# ==========================================
Write-Host "🔍 Verifying services..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

$verificationPassed = $true

# Check port 80
try {
    $port80Final = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($port80Final) {
        Write-Host "  ✓ Port 80 is accessible" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Port 80 is not accessible" -ForegroundColor Red
        $verificationPassed = $false
    }
} catch {
    Write-Host "  ⚠ Could not verify port 80" -ForegroundColor Yellow
}

# Check backend
try {
    $backendFinal = Test-NetConnection -ComputerName localhost -Port 8000 -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($backendFinal) {
        Write-Host "  ✓ Backend is accessible" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Backend may not be ready yet" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠ Could not verify backend" -ForegroundColor Yellow
}

# Try to access site
try {
    $siteResponse = Invoke-WebRequest -Uri "http://localhost" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    if ($siteResponse.StatusCode -eq 200) {
        Write-Host "  ✓ Site is accessible at http://localhost" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Site returned status: $($siteResponse.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠ Could not access site: $_" -ForegroundColor Yellow
    Write-Host "  → Please wait a few more seconds and try again" -ForegroundColor Cyan
}

Write-Host ""

if (-not $verificationPassed) {
    Write-Host "⚠️  Some services may not be ready yet" -ForegroundColor Yellow
    Write-Host "   Run .\test_site.ps1 to check status" -ForegroundColor Cyan
    Write-Host ""
}

# Get public IP (already set above)
# $publicIP is already defined in Step 6

Write-Host "📋 Access URLs:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  🌐 Frontend (Local):     http://localhost" -ForegroundColor White
Write-Host "  🌐 Frontend (Internet):  http://$publicIP" -ForegroundColor Cyan
Write-Host "  🌐 Frontend (Domain):    http://myaibaz.ir (via Cloudflare)" -ForegroundColor Cyan
Write-Host ""
Write-Host "  🔧 Backend API:         http://localhost/api/ (via Nginx)" -ForegroundColor White
Write-Host "  ⚙️  Admin Panel:         http://localhost/admin/ (via Nginx)" -ForegroundColor White
Write-Host ""
Write-Host "  🔒 Backend (Direct):    http://127.0.0.1:8000 (localhost only - secure)" -ForegroundColor Gray
Write-Host ""
Write-Host "📊 Service Status:" -ForegroundColor Yellow
Write-Host "  ✓ Redis          (Port 6379 - localhost only)" -ForegroundColor Green
Write-Host "  ✓ Django Server  (Port 8000 - 127.0.0.1:8000 - localhost only)" -ForegroundColor Green
Write-Host "  ✓ Celery Worker  (Background tasks)" -ForegroundColor Green
Write-Host "  ✓ Celery Beat    (Scheduled tasks)" -ForegroundColor Green
if ($nginxInstalled) {
    Write-Host "  ✓ Nginx          (Port 80 - 0.0.0.0:80 - accessible from internet)" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Frontend      (Port 80 - 0.0.0.0:80 - direct, Nginx recommended)" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "🔒 Security:" -ForegroundColor Yellow
Write-Host "  ✓ Backend runs only on localhost (127.0.0.1:8000)" -ForegroundColor Green
Write-Host "  ✓ Backend is not accessible from the internet" -ForegroundColor Green
if ($nginxInstalled) {
    Write-Host "  ✓ Nginx manages requests as Reverse Proxy" -ForegroundColor Green
} else {
    Write-Host "  ⚠ For full security, install Nginx" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "⚠️  Important Notes:" -ForegroundColor Yellow
Write-Host "  - Backend is only accessible from localhost (secure)" -ForegroundColor White
Write-Host "  - Frontend connects to Backend via /api" -ForegroundColor White
if ($nginxInstalled) {
    Write-Host "  - All API requests are proxied through Nginx" -ForegroundColor White
} else {
    Write-Host "  - Frontend connects directly to Backend (Nginx recommended)" -ForegroundColor White
}
Write-Host "  - To stop services: .\stop.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "All terminal windows have been opened." -ForegroundColor Gray
Write-Host "This console will remain open. Press Ctrl+C to exit." -ForegroundColor Yellow
Write-Host ""

# Keep console open indefinitely
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} catch {
    # User pressed Ctrl+C
    Write-Host ""
    Write-Host "Exiting... Services will continue running in background windows." -ForegroundColor Yellow
}
