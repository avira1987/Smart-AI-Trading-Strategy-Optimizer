# Smart AI Trading Strategy Optimizer - Auto Deployment Script (PowerShell)
# این اسکریپت پروژه را از GitHub دریافت کرده و راه‌اندازی می‌کند

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Smart AI Trading Strategy Optimizer" -ForegroundColor Green
Write-Host "  Auto Deployment Script" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Configuration
$REPO_URL = "https://github.com/avira1987/Smart-AI-Trading-Strategy-Optimizer.git"
$BRANCH = "main"
$PROJECT_DIR = "SmartAITradingStrategyOptimizer"

# Step 1: Clone or Pull
Write-Host "[1/9] Cloning/Pulling project from GitHub..." -ForegroundColor Yellow
if (Test-Path $PROJECT_DIR) {
    Write-Host "  Project directory exists. Pulling latest changes..." -ForegroundColor Gray
    Set-Location $PROJECT_DIR
    git pull origin $BRANCH
    Set-Location ..
} else {
    Write-Host "  Cloning project..." -ForegroundColor Gray
    git clone -b $BRANCH $REPO_URL $PROJECT_DIR
}
Write-Host "  ✓ Project updated" -ForegroundColor Green
Write-Host ""

# Step 2: Check dependencies
Write-Host "[2/9] Checking dependencies..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python is not installed" -ForegroundColor Red
    exit 1
}

# Check pip
try {
    $pipVersion = pip --version 2>&1
    Write-Host "  ✓ pip is available" -ForegroundColor Green
} catch {
    Write-Host "  ✗ pip is not installed" -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  ✓ Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Node.js is not installed" -ForegroundColor Red
    exit 1
}

# Check npm
try {
    $npmVersion = npm --version 2>&1
    Write-Host "  ✓ npm: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ npm is not installed" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 3: Setup Backend
Write-Host "[3/9] Setting up Backend..." -ForegroundColor Yellow
Set-Location "$PROJECT_DIR\backend"

# Create virtual environment if not exists
if (-not (Test-Path "venv")) {
    Write-Host "  Creating virtual environment..." -ForegroundColor Gray
    python -m venv venv
}

# Activate virtual environment
Write-Host "  Activating virtual environment..." -ForegroundColor Gray
& ".\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "  Installing Python dependencies..." -ForegroundColor Gray
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host "  ✓ Backend dependencies installed" -ForegroundColor Green
Write-Host ""

# Step 4: Setup Environment Variables
Write-Host "[4/9] Setting up Environment Variables..." -ForegroundColor Yellow
Set-Location ..

if (-not (Test-Path ".env")) {
    if (Test-Path "env.example") {
        Write-Host "  Creating .env from env.example..." -ForegroundColor Gray
        Copy-Item env.example .env
        
        # Generate SECRET_KEY
        $secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 50 | ForEach-Object {[char]$_})
        $secretKey = "django-insecure-$secretKey"
        
        # Update .env file
        (Get-Content .env) -replace 'SECRET_KEY=.*', "SECRET_KEY=$secretKey" | Set-Content .env
        (Get-Content .env) -replace 'DEBUG=.*', "DEBUG=False" | Set-Content .env
        (Get-Content .env) -replace 'ENV=.*', "ENV=PRODUCTION" | Set-Content .env
        
        Write-Host "  ✓ .env file created" -ForegroundColor Green
        Write-Host "  ⚠ Please edit .env file and add your API keys" -ForegroundColor Yellow
    } else {
        Write-Host "  ✗ env.example not found" -ForegroundColor Red
    }
} else {
    Write-Host "  .env file already exists" -ForegroundColor Gray
}

Write-Host ""

# Step 5: Run Migrations
Write-Host "[5/9] Running Database Migrations..." -ForegroundColor Yellow
Set-Location backend
& ".\venv\Scripts\Activate.ps1"
python manage.py migrate
Write-Host "  ✓ Migrations completed" -ForegroundColor Green
Write-Host ""

# Step 6: Collect Static Files
Write-Host "[6/9] Collecting Static Files..." -ForegroundColor Yellow
python manage.py collectstatic --noinput
Write-Host "  ✓ Static files collected" -ForegroundColor Green
Write-Host ""

# Step 7: Setup Frontend
Write-Host "[7/9] Setting up Frontend..." -ForegroundColor Yellow
Set-Location ..\frontend

# Install dependencies
Write-Host "  Installing Node.js dependencies..." -ForegroundColor Gray
npm install

# Build frontend
Write-Host "  Building frontend..." -ForegroundColor Gray
npm run build

Write-Host "  ✓ Frontend built" -ForegroundColor Green
Write-Host ""

# Step 8: Check Redis
Write-Host "[8/9] Checking Redis..." -ForegroundColor Yellow
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 6379)
    $tcpClient.Close()
    Write-Host "  ✓ Redis is running" -ForegroundColor Green
} catch {
    # Check Docker
    try {
        $dockerVersion = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $existingContainer = docker ps -a --filter "name=redis" --format "{{.Names}}" 2>&1
            if ($existingContainer -eq "redis") {
                Write-Host "  Starting Redis container..." -ForegroundColor Gray
                docker start redis 2>&1 | Out-Null
                Start-Sleep -Seconds 3
                Write-Host "  ✓ Redis container started" -ForegroundColor Green
            } else {
                Write-Host "  Creating Redis container..." -ForegroundColor Gray
                docker run -d --name redis -p 6379:6379 redis:7-alpine 2>&1 | Out-Null
                Start-Sleep -Seconds 3
                Write-Host "  ✓ Redis container created and started" -ForegroundColor Green
            }
        }
    } catch {
        Write-Host "  ⚠ Redis is not available. Please install Redis or Docker" -ForegroundColor Yellow
    }
}

Write-Host ""

# Step 9: Final Summary
Write-Host "[9/9] Deployment Summary..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ Deployment Completed Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Get local IP
$localIP = ""
try {
    $localIP = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*","Wi-Fi*" | Where-Object { $_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" -or $_.IPAddress -like "172.16.*" } | Select-Object -First 1).IPAddress
    if (-not $localIP) {
        $localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } | Select-Object -First 1).IPAddress
    }
} catch {
    $localIP = "YOUR_SERVER_IP"
}

Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Edit .env file and add your API keys:"
Write-Host "   notepad $PROJECT_DIR\.env"
Write-Host ""
Write-Host "2. Create superuser (optional):"
Write-Host "   cd $PROJECT_DIR\backend"
Write-Host "   .\venv\Scripts\Activate.ps1"
Write-Host "   python manage.py createsuperuser"
Write-Host ""
Write-Host "3. Start services:"
Write-Host ""
Write-Host "   Backend (PowerShell 1):"
Write-Host "   cd $PROJECT_DIR\backend"
Write-Host "   .\venv\Scripts\Activate.ps1"
Write-Host "   gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2"
Write-Host ""
Write-Host "   Frontend (PowerShell 2):"
Write-Host "   cd $PROJECT_DIR\frontend"
Write-Host "   npx serve -s dist -l 3000"
Write-Host ""
Write-Host "   Celery Worker (PowerShell 3):"
Write-Host "   cd $PROJECT_DIR\backend"
Write-Host "   .\venv\Scripts\Activate.ps1"
Write-Host "   celery -A config worker --loglevel=info --pool=solo"
Write-Host ""
Write-Host "   Celery Beat (PowerShell 4):"
Write-Host "   cd $PROJECT_DIR\backend"
Write-Host "   .\venv\Scripts\Activate.ps1"
Write-Host "   celery -A config beat --loglevel=info"
Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Yellow
Write-Host "  - Backend API: http://$localIP:8000" -ForegroundColor White
Write-Host "  - Frontend: http://$localIP:3000" -ForegroundColor White
Write-Host "  - Admin Panel: http://$localIP:8000/admin" -ForegroundColor White
Write-Host ""

