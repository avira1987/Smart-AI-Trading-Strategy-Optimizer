# اسکریپت نصب SSL با Certbot برای Nginx در Windows
# این اسکریپت برای Windows طراحی شده است

$ErrorActionPreference = "Continue"

$DOMAIN = "myaibaz.ir"
$WWW_DOMAIN = "www.myaibaz.ir"
$EMAIL = ""  # ایمیل خود را اینجا وارد کنید (اختیاری اما توصیه می‌شود)

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  نصب SSL با Let's Encrypt Certbot" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# بررسی اینکه آیا در WSL هستیم
$isWSL = $false
if (Test-Path "/proc/version") {
    $procVersion = Get-Content "/proc/version" -ErrorAction SilentlyContinue
    if ($procVersion -match "Microsoft|WSL") {
        $isWSL = $true
        Write-Host "✓ WSL شناسایی شد" -ForegroundColor Green
        Write-Host ""
        Write-Host "⚠️  برای نصب SSL در WSL، لطفاً از اسکریپت setup_ssl.sh استفاده کنید:" -ForegroundColor Yellow
        Write-Host "   wsl bash setup_ssl.sh" -ForegroundColor Cyan
        Write-Host ""
        exit 0
    }
}

# بررسی اینکه آیا certbot در Windows نصب است
$certbotInstalled = $false
try {
    $certbotVersion = certbot --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $certbotInstalled = $true
        Write-Host "✓ Certbot نصب است: $certbotVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Certbot در Windows نصب نیست" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📋 گزینه‌های نصب SSL در Windows:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1️⃣  استفاده از WSL (توصیه می‌شود):" -ForegroundColor Yellow
    Write-Host "   - WSL را نصب کنید" -ForegroundColor Gray
    Write-Host "   - در WSL: sudo apt-get install certbot python3-certbot-nginx" -ForegroundColor Gray
    Write-Host "   - سپس: wsl bash setup_ssl.sh" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2️⃣  استفاده از Docker:" -ForegroundColor Yellow
    Write-Host "   - docker run -it --rm -v C:/certbot/conf:/etc/letsencrypt -v C:/certbot/www:/var/www/certbot certbot/certbot certonly --webroot -w /var/www/certbot -d $DOMAIN -d $WWW_DOMAIN" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3️⃣  استفاده از سرور Linux:" -ForegroundColor Yellow
    Write-Host "   - گواهینامه را روی سرور Linux نصب کنید" -ForegroundColor Gray
    Write-Host "   - فایل‌های گواهینامه را به Windows کپی کنید" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4️⃣  استفاده از Cloudflare (اگر از Cloudflare استفاده می‌کنید):" -ForegroundColor Yellow
    Write-Host "   - SSL را در پنل Cloudflare فعال کنید" -ForegroundColor Gray
    Write-Host "   - از گواهینامه Origin Certificate استفاده کنید" -ForegroundColor Gray
    Write-Host ""
    
    $choice = Read-Host "آیا می‌خواهید از WSL استفاده کنید؟ (y/n)"
    if ($choice -eq "y" -or $choice -eq "Y") {
        Write-Host ""
        Write-Host "در حال اجرای اسکریپت در WSL..." -ForegroundColor Cyan
        wsl bash setup_ssl.sh
        exit $LASTEXITCODE
    } else {
        Write-Host ""
        Write-Host "❌ لطفاً یکی از روش‌های بالا را انتخاب کنید" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# بررسی اینکه آیا Nginx در حال اجرا است
$nginxRunning = $false
$nginxProcesses = Get-Process -Name "nginx" -ErrorAction SilentlyContinue
if ($nginxProcesses) {
    $nginxRunning = $true
    Write-Host "✓ Nginx در حال اجرا است" -ForegroundColor Green
} else {
    Write-Host "⚠️  Nginx در حال اجرا نیست" -ForegroundColor Yellow
    Write-Host "   لطفاً ابتدا Nginx را راه‌اندازی کنید: .\start.ps1" -ForegroundColor Cyan
    exit 1
}

Write-Host ""

# بررسی اینکه پورت 80 باز است
try {
    $port80Check = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue
    if ($port80Check.TcpTestSucceeded) {
        Write-Host "✓ پورت 80 باز است" -ForegroundColor Green
    } else {
        Write-Host "❌ پورت 80 باز نیست" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ خطا در بررسی پورت 80" -ForegroundColor Red
    exit 1
}

Write-Host ""

# درخواست گواهینامه SSL
Write-Host "📋 در حال درخواست گواهینامه SSL برای $DOMAIN و $WWW_DOMAIN..." -ForegroundColor Cyan
Write-Host ""

if ([string]::IsNullOrEmpty($EMAIL)) {
    Write-Host "⚠️  ایمیل تنظیم نشده است. استفاده از حالت بدون ایمیل..." -ForegroundColor Yellow
    certbot --nginx -d $DOMAIN -d $WWW_DOMAIN --non-interactive --agree-tos --register-unsafely-without-email
} else {
    Write-Host "📧 استفاده از ایمیل: $EMAIL" -ForegroundColor Cyan
    certbot --nginx -d $DOMAIN -d $WWW_DOMAIN --non-interactive --agree-tos --email $EMAIL
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ گواهینامه SSL با موفقیت نصب شد!" -ForegroundColor Green
    Write-Host ""
    
    # بررسی مسیر گواهینامه‌ها (معمولاً در Windows متفاوت است)
    $possibleCertPaths = @(
        "C:\certbot\conf\live\$DOMAIN\fullchain.pem",
        "C:\ProgramData\certbot\live\$DOMAIN\fullchain.pem",
        "C:\letsencrypt\live\$DOMAIN\fullchain.pem"
    )
    
    $certPath = $null
    $keyPath = $null
    
    foreach ($path in $possibleCertPaths) {
        if (Test-Path $path) {
            $certPath = $path
            $keyPath = $path -replace "fullchain.pem", "privkey.pem"
            break
        }
    }
    
    if ($certPath -and (Test-Path $certPath) -and (Test-Path $keyPath)) {
        Write-Host "📁 مسیر گواهینامه‌ها:" -ForegroundColor Cyan
        Write-Host "   Certificate: $certPath" -ForegroundColor Gray
        Write-Host "   Private Key: $keyPath" -ForegroundColor Gray
        Write-Host ""
        
        # به‌روزرسانی فایل nginx_production.conf
        Write-Host "🔄 به‌روزرسانی فایل nginx_production.conf..." -ForegroundColor Cyan
        # این کار باید به صورت دستی انجام شود یا با اسکریپت جداگانه
        Write-Host "   ⚠️  لطفاً فایل nginx_production.conf را به صورت دستی به‌روزرسانی کنید" -ForegroundColor Yellow
        Write-Host "   مسیرهای گواهینامه را تنظیم کنید:" -ForegroundColor Yellow
        Write-Host "   ssl_certificate $certPath;" -ForegroundColor Gray
        Write-Host "   ssl_certificate_key $keyPath;" -ForegroundColor Gray
        Write-Host ""
    }
    
    # تست پیکربندی Nginx
    Write-Host "🔍 تست پیکربندی Nginx..." -ForegroundColor Cyan
    
    # پیدا کردن مسیر nginx
    $nginxPath = $null
    $possibleNginxPaths = @(
        "C:\nginx\nginx.exe",
        "C:\nginx-1.28.0\nginx.exe",
        "C:\nginx-1.27.0\nginx.exe"
    )
    
    foreach ($path in $possibleNginxPaths) {
        if (Test-Path $path) {
            $nginxPath = $path
            break
        }
    }
    
    if ($nginxPath) {
        $nginxDir = Split-Path $nginxPath -Parent
        Set-Location $nginxDir
        $configTest = & $nginxPath -t 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ پیکربندی Nginx معتبر است" -ForegroundColor Green
            Write-Host ""
            
            # راه‌اندازی مجدد Nginx
            Write-Host "🔄 راه‌اندازی مجدد Nginx..." -ForegroundColor Cyan
            $nginxProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
            Start-Process $nginxPath
            Start-Sleep -Seconds 3
            Write-Host "✓ Nginx با موفقیت راه‌اندازی مجدد شد" -ForegroundColor Green
            Write-Host ""
        } else {
            Write-Host "❌ خطا در پیکربندی Nginx:" -ForegroundColor Red
            $configTest | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
            Write-Host ""
            Write-Host "⚠️  لطفاً به صورت دستی بررسی کنید" -ForegroundColor Yellow
        }
    }
    
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  ✅ SSL با موفقیت نصب شد!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 آدرس‌های سایت:" -ForegroundColor Cyan
    Write-Host "   https://$DOMAIN" -ForegroundColor White
    Write-Host "   https://$WWW_DOMAIN" -ForegroundColor White
    Write-Host ""
    Write-Host "📝 نکات مهم:" -ForegroundColor Yellow
    Write-Host "   - گواهینامه به صورت خودکار هر 90 روز تمدید می‌شود" -ForegroundColor Gray
    Write-Host "   - برای تمدید دستی: certbot renew" -ForegroundColor Gray
    Write-Host "   - برای تست تمدید: certbot renew --dry-run" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ خطا در نصب گواهینامه SSL" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔍 بررسی‌های لازم:" -ForegroundColor Yellow
    Write-Host "   1. دامنه باید به IP سرور شما اشاره کند" -ForegroundColor Gray
    Write-Host "   2. پورت 80 باید از اینترنت قابل دسترسی باشد" -ForegroundColor Gray
    Write-Host "   3. فایروال باید پورت 80 را باز کند" -ForegroundColor Gray
    Write-Host "   4. Nginx باید در حال اجرا باشد" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

