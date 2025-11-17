# Start Redis using Docker (Linux Container mode required)
# Usage: .\start_redis_docker.ps1

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  راه‌اندازی Redis با Docker" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker
try {
    $dockerVersion = docker --version
    Write-Host "Docker: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker نصب نیست!" -ForegroundColor Red
    exit 1
}

# Check if Docker daemon is running
$dockerInfo = docker info 2>&1 | Out-String
if ($dockerInfo -match "error|cannot connect") {
    Write-Host "⚠ Docker daemon در حال اجرا نیست!" -ForegroundColor Yellow
    Write-Host "لطفاً Docker daemon را راه‌اندازی کنید" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is in Linux mode (optional check)
if ($dockerInfo -match "OSType:\s*(\w+)") {
    $osType = $matches[1]
    if ($osType -eq "windows") {
        Write-Host "⚠ Docker در حالت Windows Container است!" -ForegroundColor Yellow
        Write-Host "برای اجرای Redis باید Docker در حالت Linux Container باشد" -ForegroundColor Yellow
        Write-Host "لطفاً Docker daemon را در حالت Linux Container راه‌اندازی کنید" -ForegroundColor Yellow
    } else {
        Write-Host "✓ Docker در حالت Linux Container است" -ForegroundColor Green
    }
}

# Check if Redis container exists
Write-Host "بررسی containerهای موجود..." -ForegroundColor Yellow
$existingContainer = docker ps -a --filter "name=redis" --format "{{.Names}}" 2>&1

if ($existingContainer -match "redis") {
    Write-Host "✓ Container Redis موجود است" -ForegroundColor Green
    
    # Check if running
    $runningContainer = docker ps --filter "name=redis" --format "{{.Names}}" 2>&1
    if ($runningContainer -match "redis") {
        Write-Host "✓ Redis در حال اجرا است" -ForegroundColor Green
    } else {
        Write-Host "در حال راه‌اندازی container موجود..." -ForegroundColor Yellow
        docker start redis
        Start-Sleep -Seconds 3
        Write-Host "✓ Redis راه‌اندازی شد" -ForegroundColor Green
    }
} else {
    Write-Host "در حال ایجاد container جدید..." -ForegroundColor Yellow
    docker run -d --name redis -p 6379:6379 redis:7-alpine
    Start-Sleep -Seconds 3
    Write-Host "✓ Container Redis ایجاد و راه‌اندازی شد" -ForegroundColor Green
}

# Verify Redis is running
Write-Host ""
Write-Host "بررسی اتصال Redis..." -ForegroundColor Yellow
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 6379)
    $tcpClient.Close()
    Write-Host "✓ Redis روی پورت 6379 در دسترس است" -ForegroundColor Green
} catch {
    Write-Host "✗ Redis در دسترس نیست!" -ForegroundColor Red
    Write-Host "برای مشاهده لاگ‌ها: docker logs redis" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  ✓ Redis با موفقیت راه‌اندازی شد!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "دستورات مفید:" -ForegroundColor Cyan
Write-Host "  مشاهده لاگ‌ها:   docker logs redis" -ForegroundColor White
Write-Host "  توقف Redis:      docker stop redis" -ForegroundColor White
Write-Host "  راه‌اندازی مجدد: docker start redis" -ForegroundColor White
Write-Host "  حذف container:   docker rm -f redis" -ForegroundColor White
Write-Host ""

