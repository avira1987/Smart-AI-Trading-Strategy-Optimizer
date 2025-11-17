# Start Redis using Docker CLI (Simple version)
# Usage: .\start_redis_simple.ps1

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  راه‌اندازی Redis با Docker" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker
Write-Host "[1/3] بررسی Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ $dockerVersion" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Docker در دسترس نیست!" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ✗ Docker نصب نیست!" -ForegroundColor Red
    exit 1
}

# Check Docker daemon
Write-Host ""
Write-Host "[2/3] بررسی Docker daemon..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info 2>&1 | Out-String
    if ($dockerInfo -match "error|cannot connect") {
        Write-Host "  ✗ Docker daemon در حال اجرا نیست!" -ForegroundColor Red
        Write-Host "  لطفاً Docker daemon را راه‌اندازی کنید" -ForegroundColor Yellow
        exit 1
    } else {
        Write-Host "  ✓ Docker daemon در حال اجرا است" -ForegroundColor Green
    }
} catch {
    Write-Host "  ✗ خطا در اتصال به Docker daemon!" -ForegroundColor Red
    exit 1
}

# Start Redis
Write-Host ""
Write-Host "[3/3] راه‌اندازی Redis..." -ForegroundColor Yellow

# Check if Redis container exists
$existingContainer = docker ps -a --filter "name=redis" --format "{{.Names}}" 2>&1

if ($existingContainer -match "redis") {
    Write-Host "  Container Redis موجود است" -ForegroundColor Gray
    
    # Check if running
    $runningContainer = docker ps --filter "name=redis" --format "{{.Names}}" 2>&1
    if ($runningContainer -match "redis") {
        Write-Host "  ✓ Redis در حال اجرا است" -ForegroundColor Green
    } else {
        Write-Host "  در حال راه‌اندازی container موجود..." -ForegroundColor Gray
        docker start redis 2>&1 | Out-Null
        Start-Sleep -Seconds 3
        Write-Host "  ✓ Redis راه‌اندازی شد" -ForegroundColor Green
    }
} else {
    Write-Host "  در حال ایجاد container جدید..." -ForegroundColor Gray
    docker run -d --name redis -p 6379:6379 redis:7-alpine 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Start-Sleep -Seconds 3
        Write-Host "  ✓ Container Redis ایجاد و راه‌اندازی شد" -ForegroundColor Green
    } else {
        Write-Host "  ✗ خطا در ایجاد container!" -ForegroundColor Red
        Write-Host "  ممکن است Docker در حالت Windows Container باشد" -ForegroundColor Yellow
        exit 1
    }
}

# Verify Redis is running
Write-Host ""
Write-Host "بررسی اتصال Redis..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 6379)
    $tcpClient.Close()
    Write-Host "  ✓ Redis روی پورت 6379 در دسترس است" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ Redis container راه‌اندازی شد اما اتصال برقرار نشد" -ForegroundColor Yellow
    Write-Host "  برای مشاهده لاگ‌ها: docker logs redis" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  ✓ Redis راه‌اندازی شد!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "دستورات مفید:" -ForegroundColor Cyan
Write-Host "  مشاهده لاگ‌ها:   docker logs redis" -ForegroundColor White
Write-Host "  توقف Redis:      docker stop redis" -ForegroundColor White
Write-Host "  راه‌اندازی مجدد: docker start redis" -ForegroundColor White
Write-Host "  حذف container:   docker rm -f redis" -ForegroundColor White
Write-Host ""

