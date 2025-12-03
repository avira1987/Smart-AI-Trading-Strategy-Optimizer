# اسکریپت تست نصب SSL و HTTPS
# این اسکریپت تمام مراحل نصب SSL را بررسی می‌کند

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  تست نصب SSL و HTTPS" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

$allTestsPassed = $true
$DOMAIN = "myaibaz.ir"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# ==========================================
# تست 1: بررسی وجود فایل‌های گواهینامه
# ==========================================
Write-Host "[1/8] بررسی فایل‌های گواهینامه SSL..." -ForegroundColor Cyan

$certPath = "C:\nginx-1.28.0\conf\ssl\myaibaz.ir.crt"
$keyPath = "C:\nginx-1.28.0\conf\ssl\myaibaz.ir.key"

if (Test-Path $certPath) {
    Write-Host "  ✓ Certificate پیدا شد: $certPath" -ForegroundColor Green
    
    # بررسی محتوای Certificate
    $certContent = Get-Content $certPath -Raw
    if ($certContent -match "BEGIN CERTIFICATE" -and $certContent -match "END CERTIFICATE") {
        Write-Host "  ✓ Certificate معتبر است" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Certificate معتبر نیست!" -ForegroundColor Red
        $allTestsPassed = $false
    }
} else {
    Write-Host "  ✗ Certificate پیدا نشد: $certPath" -ForegroundColor Red
    $allTestsPassed = $false
}

if (Test-Path $keyPath) {
    Write-Host "  ✓ Private Key پیدا شد: $keyPath" -ForegroundColor Green
    
    # بررسی محتوای Private Key
    $keyContent = Get-Content $keyPath -Raw
    if ($keyContent -match "BEGIN PRIVATE KEY" -and $keyContent -match "END PRIVATE KEY") {
        Write-Host "  ✓ Private Key معتبر است" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Private Key معتبر نیست!" -ForegroundColor Red
        $allTestsPassed = $false
    }
} else {
    Write-Host "  ✗ Private Key پیدا نشد: $keyPath" -ForegroundColor Red
    $allTestsPassed = $false
}

Write-Host ""

# ==========================================
# تست 2: بررسی فایل nginx_production.conf
# ==========================================
Write-Host "[2/8] بررسی فایل nginx_production.conf..." -ForegroundColor Cyan

$nginxConfPath = Join-Path $scriptPath "nginx_production.conf"
if (Test-Path $nginxConfPath) {
    Write-Host "  ✓ فایل nginx_production.conf پیدا شد" -ForegroundColor Green
    
    $nginxContent = Get-Content $nginxConfPath -Raw
    
    # بررسی فعال بودن HTTPS
    if ($nginxContent -match "listen 443 ssl;" -and $nginxContent -notmatch "#\s*listen 443 ssl;") {
        Write-Host "  ✓ بخش HTTPS فعال است" -ForegroundColor Green
    } else {
        Write-Host "  ✗ بخش HTTPS فعال نیست!" -ForegroundColor Red
        $allTestsPassed = $false
    }
    
    # بررسی مسیرهای SSL
    if ($nginxContent -match "ssl_certificate C:/nginx-1.28.0/conf/ssl/myaibaz.ir.crt" -and 
        $nginxContent -notmatch "#\s*ssl_certificate") {
        Write-Host "  ✓ مسیر Certificate تنظیم شده است" -ForegroundColor Green
    } else {
        Write-Host "  ✗ مسیر Certificate تنظیم نشده است!" -ForegroundColor Red
        $allTestsPassed = $false
    }
    
    if ($nginxContent -match "ssl_certificate_key C:/nginx-1.28.0/conf/ssl/myaibaz.ir.key" -and 
        $nginxContent -notmatch "#\s*ssl_certificate_key") {
        Write-Host "  ✓ مسیر Private Key تنظیم شده است" -ForegroundColor Green
    } else {
        Write-Host "  ✗ مسیر Private Key تنظیم نشده است!" -ForegroundColor Red
        $allTestsPassed = $false
    }
    
    # بررسی redirect HTTP به HTTPS
    if ($nginxContent -match "return 301 https://" -and $nginxContent -notmatch "#\s*return 301 https://") {
        Write-Host "  ✓ Redirect HTTP به HTTPS فعال است" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Redirect HTTP به HTTPS فعال نیست" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✗ فایل nginx_production.conf پیدا نشد!" -ForegroundColor Red
    $allTestsPassed = $false
}

Write-Host ""

# ==========================================
# تست 3: بررسی فایل nginx.conf در مسیر نصب
# ==========================================
Write-Host "[3/8] بررسی فایل nginx.conf در مسیر نصب..." -ForegroundColor Cyan

$nginxInstallPath = "C:\nginx-1.28.0\conf\nginx.conf"
if (Test-Path $nginxInstallPath) {
    Write-Host "  ✓ فایل nginx.conf در مسیر نصب پیدا شد" -ForegroundColor Green
    
    # بررسی اینکه آیا فایل به‌روزرسانی شده است
    $installedContent = Get-Content $nginxInstallPath -Raw
    if ($installedContent -match "ssl_certificate") {
        Write-Host "  ✓ فایل nginx.conf شامل تنظیمات SSL است" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ فایل nginx.conf شامل تنظیمات SSL نیست" -ForegroundColor Yellow
        Write-Host "     باید فایل nginx_production.conf را کپی کنید" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠ فایل nginx.conf در مسیر نصب پیدا نشد" -ForegroundColor Yellow
}

Write-Host ""

# ==========================================
# تست 4: بررسی Nginx در حال اجرا
# ==========================================
Write-Host "[4/8] بررسی Nginx..." -ForegroundColor Cyan

$nginxProcesses = Get-Process -Name "nginx" -ErrorAction SilentlyContinue
if ($nginxProcesses) {
    Write-Host "  ✓ Nginx در حال اجرا است ($($nginxProcesses.Count) process(es))" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Nginx در حال اجرا نیست" -ForegroundColor Yellow
}

Write-Host ""

# ==========================================
# تست 5: بررسی پورت 80
# ==========================================
Write-Host "[5/8] بررسی پورت 80 (HTTP)..." -ForegroundColor Cyan

$port80Check = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue -InformationLevel Quiet
if ($port80Check) {
    Write-Host "  ✓ پورت 80 باز است" -ForegroundColor Green
} else {
    Write-Host "  ⚠ پورت 80 باز نیست" -ForegroundColor Yellow
}

Write-Host ""

# ==========================================
# تست 6: بررسی پورت 443
# ==========================================
Write-Host "[6/8] بررسی پورت 443 (HTTPS)..." -ForegroundColor Cyan

$port443Check = Test-NetConnection -ComputerName localhost -Port 443 -WarningAction SilentlyContinue -InformationLevel Quiet
if ($port443Check) {
    Write-Host "  ✓ پورت 443 باز است" -ForegroundColor Green
} else {
    Write-Host "  ⚠ پورت 443 باز نیست (ممکن است Nginx نیاز به راه‌اندازی مجدد داشته باشد)" -ForegroundColor Yellow
}

Write-Host ""

# ==========================================
# تست 7: تست پیکربندی Nginx
# ==========================================
Write-Host "[7/8] تست پیکربندی Nginx..." -ForegroundColor Cyan

$nginxExe = "C:\nginx-1.28.0\nginx.exe"
if (Test-Path $nginxExe) {
    $originalLocation = Get-Location
    Set-Location "C:\nginx-1.28.0"
    $configTest = & $nginxExe -t 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ پیکربندی Nginx معتبر است" -ForegroundColor Green
    } else {
        Write-Host "  ✗ خطا در پیکربندی Nginx:" -ForegroundColor Red
        $configTest | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        $allTestsPassed = $false
    }
    Set-Location $originalLocation
} else {
    Write-Host "  ⚠ Nginx.exe پیدا نشد: $nginxExe" -ForegroundColor Yellow
}

Write-Host ""

# ==========================================
# تست 8: تست دسترسی HTTP و HTTPS
# ==========================================
Write-Host "[8/8] تست دسترسی HTTP و HTTPS..." -ForegroundColor Cyan

# تست HTTP (باید redirect شود)
try {
    $httpResponse = Invoke-WebRequest -Uri "http://localhost" -MaximumRedirection 0 -ErrorAction Stop -TimeoutSec 5 -UseBasicParsing
    Write-Host "  ⚠ HTTP redirect نشد" -ForegroundColor Yellow
} catch {
    $statusCode = $null
    try {
        $statusCode = $_.Exception.Response.StatusCode.value__
    } catch {
        # Ignore
    }
    
    if ($statusCode -eq 301 -or $statusCode -eq 302) {
        Write-Host "  ✓ HTTP به HTTPS redirect می‌شود (Status: $statusCode)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ خطا در تست HTTP" -ForegroundColor Yellow
    }
}

# تست HTTPS (اگر پورت 443 باز است)
if ($port443Check) {
    try {
        $httpsResponse = Invoke-WebRequest -Uri "https://localhost" -SkipCertificateCheck -ErrorAction Stop -TimeoutSec 5 -UseBasicParsing
        if ($httpsResponse.StatusCode -eq 200) {
            Write-Host "  ✓ HTTPS در دسترس است (Status: 200)" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ HTTPS پاسخ داد اما Status: $($httpsResponse.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ⚠ خطا در تست HTTPS" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠ پورت 443 باز نیست - نمی‌توان HTTPS را تست کرد" -ForegroundColor Yellow
}

Write-Host ""

# ==========================================
# خلاصه نتایج
# ==========================================
Write-Host "========================================" -ForegroundColor Green
if ($allTestsPassed) {
    Write-Host "  ✅ همه تست‌های اصلی موفق بودند!" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  برخی تست‌ها ناموفق بودند" -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# ==========================================
# دستورالعمل‌های بعدی
# ==========================================
Write-Host "📋 دستورالعمل‌های بعدی:" -ForegroundColor Cyan
Write-Host ""

if (-not $allTestsPassed) {
    Write-Host "1. کپی فایل nginx_production.conf به مسیر نصب:" -ForegroundColor Yellow
    Write-Host "   Copy-Item nginx_production.conf C:\nginx-1.28.0\conf\nginx.conf -Force" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "2. راه‌اندازی مجدد Nginx:" -ForegroundColor Yellow
Write-Host "   # متوقف کردن Nginx" -ForegroundColor Gray
Write-Host "   Get-Process -Name nginx | Stop-Process -Force" -ForegroundColor Gray
Write-Host "   # راه‌اندازی مجدد" -ForegroundColor Gray
Write-Host "   Start-Process C:\nginx-1.28.0\nginx.exe" -ForegroundColor Gray
Write-Host ""

Write-Host "3. تست دسترسی:" -ForegroundColor Yellow
Write-Host "   - HTTP: http://localhost (باید به HTTPS redirect شود)" -ForegroundColor Gray
Write-Host "   - HTTPS: https://localhost" -ForegroundColor Gray
Write-Host "   - Domain: https://myaibaz.ir" -ForegroundColor Gray
Write-Host ""

Write-Host "4. بررسی لاگ‌های Nginx:" -ForegroundColor Yellow
$logCommand = "Get-Content C:\nginx-1.28.0\logs\error.log -Tail 20"
Write-Host "   $logCommand" -ForegroundColor Gray
Write-Host ""
