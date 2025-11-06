# Start AI Forex Strategy Manager
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  AI Forex Strategy Manager" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# Check Redis connection
Write-Host "Checking Redis connection..." -ForegroundColor Cyan
$redisRunning = $false
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 6379)
    $tcpClient.Close()
    Write-Host "✓ Redis is running" -ForegroundColor Green
    $redisRunning = $true
} catch {
    Write-Host "⚠ Redis is NOT running on port 6379" -ForegroundColor Yellow
    Write-Host "  Attempting to start Redis with Docker..." -ForegroundColor Cyan
    
    # Check if Docker is available
    $dockerAvailable = $false
    try {
        $dockerVersion = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $dockerAvailable = $true
            Write-Host "  Docker is available: $dockerVersion" -ForegroundColor Green
        }
    } catch {
        Write-Host "  Docker is not available" -ForegroundColor Yellow
    }
    
    if ($dockerAvailable) {
        Write-Host "  Starting Redis container..." -ForegroundColor Cyan
        try {
            # Check if Redis container already exists
            $existingContainer = docker ps -a --filter "name=redis" --format "{{.Names}}" 2>&1
            if ($existingContainer -eq "redis") {
                Write-Host "  Redis container exists, starting it..." -ForegroundColor Cyan
                docker start redis 2>&1 | Out-Null
            } else {
                Write-Host "  Creating and starting Redis container..." -ForegroundColor Cyan
                docker run -d --name redis -p 6379:6379 redis:7-alpine 2>&1 | Out-Null
            }
            
            # Wait for Redis to start
            Start-Sleep -Seconds 3
            
            # Verify Redis is now running
            try {
                $tcpClient = New-Object System.Net.Sockets.TcpClient
                $tcpClient.Connect("localhost", 6379)
                $tcpClient.Close()
                Write-Host "✓ Redis started successfully!" -ForegroundColor Green
                $redisRunning = $true
            } catch {
                Write-Host "  ⚠ Redis container started but connection failed. Please check manually." -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  ❌ Failed to start Redis with Docker: $_" -ForegroundColor Red
            Write-Host "  Please start Redis manually:" -ForegroundColor Yellow
            Write-Host "    Option 1: docker run -d --name redis -p 6379:6379 redis:7-alpine" -ForegroundColor White
            Write-Host "    Option 2: Start Redis server directly if installed" -ForegroundColor White
        }
    } else {
        Write-Host "  Please start Redis manually:" -ForegroundColor Yellow
        Write-Host "    Option 1: Install and run: redis-server" -ForegroundColor White
        Write-Host "    Option 2: Use Docker: docker run -d --name redis -p 6379:6379 redis:7-alpine" -ForegroundColor White
        Write-Host "    Option 3: Download Redis for Windows from: https://github.com/microsoftarchive/redis/releases" -ForegroundColor White
    }
}
Write-Host ""

# If Redis is not running, stop execution
if (-not $redisRunning) {
    Write-Host ""
    Write-Host "❌ ERROR: Redis is required but not running!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start Redis before continuing:" -ForegroundColor Yellow
    Write-Host "  1. Start Docker Desktop (if using Docker)" -ForegroundColor White
    Write-Host "  2. Then run this script again, or manually start Redis:" -ForegroundColor White
    Write-Host "     docker run -d --name redis -p 6379:6379 redis:7-alpine" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Check if Node is running
$nodeProcess = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcess) {
    Write-Host "Stopping existing Node processes..." -ForegroundColor Yellow
    Stop-Process -Name "node" -Force
    Start-Sleep -Seconds 2
}

# Check and stop existing Celery processes (Worker and Beat)
Write-Host "Checking for existing Celery processes..." -ForegroundColor Cyan
$celeryProcesses = Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like "*celery*" }
if ($celeryProcesses) {
    Write-Host "Stopping existing Celery processes..." -ForegroundColor Yellow
    $celeryProcesses | ForEach-Object { 
        try {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        } catch {
            # Process might already be stopped
        }
    }
    Start-Sleep -Seconds 2
    Write-Host "✓ Celery processes stopped" -ForegroundColor Green
}

# Start Backend
Write-Host "Starting Backend (Django)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; python manage.py runserver"
Start-Sleep -Seconds 3

# Start Frontend
Write-Host "Starting Frontend (React)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"
Start-Sleep -Seconds 2

# Start Celery Worker
Write-Host "Starting Celery Worker..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; celery -A config worker --loglevel=info --pool=solo"
Start-Sleep -Seconds 2

# Start Celery Beat
Write-Host "Starting Celery Beat..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; celery -A config beat --loglevel=info"
Start-Sleep -Seconds 2

Write-Host "" 
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  All Services Started Successfully!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services running:" -ForegroundColor Yellow
Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  - Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  - Admin:    http://localhost:8000/admin/" -ForegroundColor White
Write-Host "  - Celery Worker: Running" -ForegroundColor White
Write-Host "  - Celery Beat: Running (Auto-trading every 5 minutes)" -ForegroundColor White
Write-Host ""
Write-Host "Login Info:" -ForegroundColor Cyan
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: admin" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT NOTES:" -ForegroundColor Yellow
Write-Host "  - Make sure Redis is running on port 6379" -ForegroundColor White
Write-Host "  - Make sure MT5 is open and AutoTrading is enabled" -ForegroundColor White
Write-Host "  - Auto-trading will run every 5 minutes automatically" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

