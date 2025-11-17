# Start application using Docker Compose
# This script starts all services using Docker Compose
# Usage: .\start_with_docker.ps1

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  راه‌اندازی با Docker Compose" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker
Write-Host "[1/5] بررسی Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "  ✓ $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Docker نصب نیست!" -ForegroundColor Red
    Write-Host "  لطفاً Docker Desktop را نصب کنید" -ForegroundColor Yellow
    exit 1
}

# Check Docker Compose
Write-Host ""
Write-Host "[2/5] بررسی Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker compose version
    Write-Host "  ✓ $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Docker Compose در دسترس نیست!" -ForegroundColor Red
    exit 1
}

# Check Docker context (Linux containers)
Write-Host ""
Write-Host "[3/5] بررسی نوع Container..." -ForegroundColor Yellow
$dockerInfo = docker info 2>&1 | Out-String
if ($dockerInfo -match "OSType:\s*(\w+)") {
    $osType = $matches[1]
    if ($osType -eq "windows") {
        Write-Host "  ✗ Docker در حالت Windows Container است!" -ForegroundColor Red
        Write-Host "  برای اجرای Redis و PostgreSQL باید به Linux Container تغییر دهید" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  لطفاً ابتدا اسکریپت زیر را اجرا کنید:" -ForegroundColor Cyan
        Write-Host "    .\setup_docker_linux.ps1" -ForegroundColor White
        Write-Host ""
        Write-Host "  یا از Docker Desktop:" -ForegroundColor Cyan
        Write-Host "    راست کلیک روی آیکون Docker -> Switch to Linux containers" -ForegroundColor White
        exit 1
    } else {
        Write-Host "  ✓ Docker در حالت Linux Container است" -ForegroundColor Green
    }
} else {
    Write-Host "  ⚠ نتوانست وضعیت Docker را تشخیص دهد" -ForegroundColor Yellow
}

# Check .env file
Write-Host ""
Write-Host "[4/5] بررسی فایل .env..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "  ✓ فایل .env یافت شد" -ForegroundColor Green
} else {
    Write-Host "  ⚠ فایل .env یافت نشد" -ForegroundColor Yellow
    if (Test-Path "env.example") {
        Write-Host "  در حال ایجاد از env.example..." -ForegroundColor Gray
        Copy-Item "env.example" ".env"
        Write-Host "  ✓ فایل .env ایجاد شد" -ForegroundColor Green
        Write-Host "  ⚠ لطفاً فایل .env را ویرایش کنید و تنظیمات را وارد کنید" -ForegroundColor Yellow
    } else {
        Write-Host "  ✗ فایل env.example هم یافت نشد!" -ForegroundColor Red
        exit 1
    }
}

# Start services
Write-Host ""
Write-Host "[5/5] راه‌اندازی سرویس‌ها..." -ForegroundColor Yellow
Write-Host ""

# Stop existing containers
Write-Host "  در حال توقف containerهای قبلی..." -ForegroundColor Gray
docker compose down 2>&1 | Out-Null

# Build and start
Write-Host "  در حال ساخت و راه‌اندازی..." -ForegroundColor Gray
docker compose up -d --build

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "  ✓ سرویس‌ها با موفقیت راه‌اندازی شدند!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host ""
    
    # Wait for services to start
    Write-Host "در حال انتظار برای راه‌اندازی کامل سرویس‌ها..." -ForegroundColor Cyan
    Start-Sleep -Seconds 10
    
    # Show status
    Write-Host ""
    Write-Host "وضعیت Containerها:" -ForegroundColor Yellow
    docker compose ps
    
    Write-Host ""
    Write-Host "📋 آدرس‌های دسترسی:" -ForegroundColor Yellow
    Write-Host "  Frontend:  http://localhost" -ForegroundColor White
    Write-Host "  Backend:   http://localhost:8000" -ForegroundColor White
    Write-Host "  Admin:     http://localhost:8000/admin/" -ForegroundColor White
    Write-Host ""
    Write-Host "🔧 دستورات مفید:" -ForegroundColor Cyan
    Write-Host "  مشاهده لاگ‌ها:     docker compose logs -f" -ForegroundColor White
    Write-Host "  توقف سرویس‌ها:     docker compose down" -ForegroundColor White
    Write-Host "  راه‌اندازی مجدد:   docker compose restart" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host "  ✗ خطا در راه‌اندازی سرویس‌ها!" -ForegroundColor Red
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "برای مشاهده خطاها:" -ForegroundColor Yellow
    Write-Host "  docker compose logs" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host ""

