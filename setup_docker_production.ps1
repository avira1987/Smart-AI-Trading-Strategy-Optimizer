# ============================================
# راه‌اندازی Docker و Nginx برای Production
# دسترسی با IP بدون نیاز به پورت
# ============================================

Write-Host "=== راه‌اندازی Docker و Nginx برای Production ===" -ForegroundColor Cyan
Write-Host ""

# بررسی دسترسی Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️  این اسکریپت نیاز به دسترسی Administrator دارد!" -ForegroundColor Yellow
    Write-Host "لطفاً PowerShell را به عنوان Administrator اجرا کنید" -ForegroundColor Yellow
    exit 1
}

# 1. بررسی نصب Docker
Write-Host "1. بررسی نصب Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "   ✅ Docker نصب است: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Docker نصب نیست!" -ForegroundColor Red
    Write-Host "   لطفاً Docker Desktop را نصب کنید: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# بررسی Docker در حال اجرا
try {
    docker ps | Out-Null
    Write-Host "   ✅ Docker در حال اجرا است" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Docker در حال اجرا نیست!" -ForegroundColor Red
    Write-Host "   لطفاً Docker Desktop را راه‌اندازی کنید" -ForegroundColor Yellow
    exit 1
}

# 2. متوقف کردن IIS (اگر از پورت 80 استفاده می‌کند)
Write-Host "`n2. بررسی IIS..." -ForegroundColor Yellow
$iisRunning = Get-Service -Name W3SVC -ErrorAction SilentlyContinue
if ($iisRunning -and $iisRunning.Status -eq 'Running') {
    Write-Host "   ⚠️  IIS در حال اجرا است. متوقف کردن..." -ForegroundColor Yellow
    iisreset /stop
    Start-Sleep -Seconds 3
    Write-Host "   ✅ IIS متوقف شد" -ForegroundColor Green
} else {
    Write-Host "   ✅ IIS در حال اجرا نیست" -ForegroundColor Green
}

# 3. بررسی پورت 80
Write-Host "`n3. بررسی پورت 80..." -ForegroundColor Yellow
$port80 = Get-NetTCPConnection -LocalPort 80 -ErrorAction SilentlyContinue
if ($port80) {
    $pid = $port80.OwningProcess
    $procName = (Get-Process -Id $pid -ErrorAction SilentlyContinue).ProcessName
    Write-Host "   ⚠️  پورت 80 در حال استفاده است توسط: $procName (PID: $pid)" -ForegroundColor Yellow
    Write-Host "   لطفاً این process را متوقف کنید" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "   ✅ پورت 80 آزاد است" -ForegroundColor Green
}

# 4. دریافت IP آدرس سرور
Write-Host "`n4. دریافت IP آدرس سرور..." -ForegroundColor Yellow
$ipAddresses = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
    $_.IPAddress -notlike "127.*" -and 
    $_.IPAddress -notlike "169.254.*" -and
    $_.IPAddress -notlike "192.168.*" -and
    $_.IPAddress -notlike "10.*"
} | Select-Object -First 1

if ($ipAddresses) {
    $serverIP = $ipAddresses.IPAddress
    Write-Host "   ✅ IP آدرس سرور: $serverIP" -ForegroundColor Green
} else {
    # اگر IP عمومی پیدا نشد، از IP محلی استفاده کن
    $localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
        $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" 
    } | Select-Object -First 1).IPAddress
    $serverIP = $localIP
    Write-Host "   ⚠️  IP عمومی پیدا نشد. استفاده از IP محلی: $serverIP" -ForegroundColor Yellow
}

# 5. بررسی فایل .env
Write-Host "`n5. بررسی فایل .env..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "   ⚠️  فایل .env پیدا نشد. ایجاد از env.example..." -ForegroundColor Yellow
    if (Test-Path "env.example") {
        Copy-Item "env.example" ".env"
        Write-Host "   ✅ فایل .env ایجاد شد" -ForegroundColor Green
        Write-Host "   ⚠️  لطفاً فایل .env را ویرایش کنید و:" -ForegroundColor Yellow
        Write-Host "      - SECRET_KEY را تغییر دهید" -ForegroundColor White
        Write-Host "      - ALLOWED_HOSTS را تنظیم کنید: ALLOWED_HOSTS=$serverIP,localhost,127.0.0.1" -ForegroundColor White
        Write-Host "      - PUBLIC_IP را تنظیم کنید: PUBLIC_IP=$serverIP" -ForegroundColor White
        Write-Host "      - DEBUG=False را تنظیم کنید" -ForegroundColor White
        Write-Host "      - ENV=PRODUCTION را تنظیم کنید" -ForegroundColor White
        Write-Host ""
        $continue = Read-Host "آیا می‌خواهید ادامه دهید؟ (y/n)"
        if ($continue -ne "y") {
            exit 0
        }
    } else {
        Write-Host "   ❌ فایل env.example پیدا نشد!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ✅ فایل .env موجود است" -ForegroundColor Green
    
    # بررسی تنظیمات مهم
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "DEBUG=True") {
        Write-Host "   ⚠️  DEBUG=True است! برای Production باید DEBUG=False باشد" -ForegroundColor Yellow
    }
    if ($envContent -notmatch "ALLOWED_HOSTS.*$serverIP") {
        Write-Host "   ⚠️  IP آدرس $serverIP در ALLOWED_HOSTS نیست!" -ForegroundColor Yellow
    }
}

# 6. تنظیم فایروال
Write-Host "`n6. تنظیم فایروال Windows..." -ForegroundColor Yellow
$firewallRule = Get-NetFirewallRule -DisplayName "Allow HTTP Port 80" -ErrorAction SilentlyContinue
if (-not $firewallRule) {
    try {
        New-NetFirewallRule -DisplayName "Allow HTTP Port 80" `
            -Direction Inbound `
            -LocalPort 80 `
            -Protocol TCP `
            -Action Allow `
            -Description "Allow HTTP traffic on port 80 for web server" | Out-Null
        Write-Host "   ✅ قانون فایروال برای پورت 80 ایجاد شد" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  خطا در ایجاد قانون فایروال: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ✅ قانون فایروال برای پورت 80 موجود است" -ForegroundColor Green
}

# 7. Build و راه‌اندازی Docker
Write-Host "`n7. Build و راه‌اندازی Docker containers..." -ForegroundColor Yellow
Write-Host "   این مرحله ممکن است چند دقیقه طول بکشد..." -ForegroundColor Cyan

# متوقف کردن containers قبلی
Write-Host "   متوقف کردن containers قبلی..." -ForegroundColor Gray
docker-compose down 2>&1 | Out-Null

# Build و راه‌اندازی
Write-Host "   در حال build و راه‌اندازی..." -ForegroundColor Gray
docker-compose up -d --build

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Docker containers راه‌اندازی شدند" -ForegroundColor Green
} else {
    Write-Host "   ❌ خطا در راه‌اندازی Docker containers!" -ForegroundColor Red
    Write-Host "   لطفاً لاگ‌ها را بررسی کنید: docker-compose logs" -ForegroundColor Yellow
    exit 1
}

# 8. بررسی وضعیت containers
Write-Host "`n8. بررسی وضعیت containers..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
docker-compose ps

# 9. بررسی دسترسی
Write-Host "`n9. بررسی دسترسی به وب‌سایت..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

try {
    $response = Invoke-WebRequest -Uri "http://localhost/health" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    Write-Host "   ✅ وب‌سایت در حال اجرا است (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  وب‌سایت هنوز آماده نیست. لطفاً چند ثانیه صبر کنید و دوباره تست کنید" -ForegroundColor Yellow
}

# 10. نمایش اطلاعات نهایی
Write-Host "`n=== راه‌اندازی کامل شد! ===" -ForegroundColor Green
Write-Host ""
Write-Host "📝 اطلاعات دسترسی:" -ForegroundColor Cyan
Write-Host "   محلی: http://localhost" -ForegroundColor White
Write-Host "   با IP: http://$serverIP" -ForegroundColor White
Write-Host ""
Write-Host "📋 دستورات مفید:" -ForegroundColor Cyan
Write-Host "   مشاهده لاگ‌ها: docker-compose logs -f" -ForegroundColor White
Write-Host "   متوقف کردن: docker-compose down" -ForegroundColor White
Write-Host "   راه‌اندازی مجدد: docker-compose restart" -ForegroundColor White
Write-Host "   مشاهده وضعیت: docker-compose ps" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  نکات مهم:" -ForegroundColor Yellow
Write-Host "   1. مطمئن شوید فایل .env به درستی تنظیم شده است" -ForegroundColor White
Write-Host "   2. IP آدرس $serverIP باید در ALLOWED_HOSTS باشد" -ForegroundColor White
Write-Host "   3. اگر از خارج از سرور دسترسی ندارید، فایروال سرور را بررسی کنید" -ForegroundColor White
Write-Host ""

