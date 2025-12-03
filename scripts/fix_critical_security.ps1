# اسکریپت رفع مشکلات امنیتی بحرانی
# Critical Security Fixes Script

Write-Host "========================================" -ForegroundColor Red
Write-Host "رفع مشکلات امنیتی بحرانی" -ForegroundColor Red
Write-Host "Critical Security Fixes" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""

$projectRoot = $PSScriptRoot
if (-not $projectRoot) {
    $projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$settingsFile = Join-Path $projectRoot "backend\config\settings.py"
$envExampleFile = Join-Path $projectRoot "env.example"

# بررسی وجود فایل‌ها
if (-not (Test-Path $settingsFile)) {
    Write-Host "❌ فایل settings.py یافت نشد!" -ForegroundColor Red
    exit 1
}

Write-Host "🔍 بررسی فایل settings.py..." -ForegroundColor Yellow

# 1. بررسی SECRET_KEY
Write-Host "`n1. بررسی SECRET_KEY..." -ForegroundColor Cyan
$settingsContent = Get-Content $settingsFile -Raw

if ($settingsContent -match "SECRET_KEY = os\.environ\.get\('SECRET_KEY', 'django-insecure") {
    Write-Host "   ⚠️  SECRET_KEY پیش‌فرض استفاده می‌شود" -ForegroundColor Yellow
    Write-Host "   ✅ توصیه: SECRET_KEY قوی در .env تنظیم کنید" -ForegroundColor Green
} else {
    Write-Host "   ✅ SECRET_KEY بررسی می‌شود" -ForegroundColor Green
}

# 2. بررسی DEBUG
Write-Host "`n2. بررسی DEBUG..." -ForegroundColor Cyan
if ($settingsContent -match "DEBUG = os\.environ\.get\('DEBUG', 'True'\)") {
    Write-Host "   ⚠️  DEBUG به صورت پیش‌فرض True است" -ForegroundColor Yellow
    Write-Host "   ✅ توصیه: DEBUG=False در production تنظیم کنید" -ForegroundColor Green
} else {
    Write-Host "   ✅ DEBUG بررسی می‌شود" -ForegroundColor Green
}

# 3. بررسی ALLOWED_HOSTS
Write-Host "`n3. بررسی ALLOWED_HOSTS..." -ForegroundColor Cyan
if ($settingsContent -match "ALLOWED_HOSTS.*\*") {
    Write-Host "   ⚠️  ALLOWED_HOSTS شامل * است" -ForegroundColor Yellow
    Write-Host "   ✅ توصیه: فقط دامنه‌های مجاز را تنظیم کنید" -ForegroundColor Green
} else {
    Write-Host "   ✅ ALLOWED_HOSTS بررسی می‌شود" -ForegroundColor Green
}

# 4. بررسی CORS
Write-Host "`n4. بررسی CORS..." -ForegroundColor Cyan
if ($settingsContent -match "CORS_ALLOW_ALL_ORIGINS = True") {
    Write-Host "   ⚠️  CORS_ALLOW_ALL_ORIGINS فعال است" -ForegroundColor Yellow
    Write-Host "   ✅ توصیه: فقط origins مجاز را تنظیم کنید" -ForegroundColor Green
} else {
    Write-Host "   ✅ CORS بررسی می‌شود" -ForegroundColor Green
}

# 5. بررسی HTTPS
Write-Host "`n5. بررسی HTTPS..." -ForegroundColor Cyan
if ($settingsContent -match "USE_HTTPS = os\.environ\.get\('USE_HTTPS', 'False'\)") {
    Write-Host "   ⚠️  HTTPS به صورت پیش‌فرض غیرفعال است" -ForegroundColor Yellow
    Write-Host "   ✅ توصیه: USE_HTTPS=True در production تنظیم کنید" -ForegroundColor Green
} else {
    Write-Host "   ✅ HTTPS بررسی می‌شود" -ForegroundColor Green
}

# 6. بررسی .env
Write-Host "`n6. بررسی فایل .env..." -ForegroundColor Cyan
$envFile = Join-Path $projectRoot ".env"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    
    # بررسی SECRET_KEY
    if ($envContent -match "SECRET_KEY=your-secret-key-here") {
        Write-Host "   ⚠️  SECRET_KEY پیش‌فرض در .env است" -ForegroundColor Red
        Write-Host "   🔧 در حال تولید SECRET_KEY جدید..." -ForegroundColor Yellow
        
        # تولید SECRET_KEY جدید
        $newSecretKey = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 50 | ForEach-Object {[char]$_})
        $envContent = $envContent -replace "SECRET_KEY=.*", "SECRET_KEY=$newSecretKey"
        Set-Content -Path $envFile -Value $envContent -NoNewline
        Write-Host "   ✅ SECRET_KEY جدید تولید شد" -ForegroundColor Green
    }
    
    # بررسی DEBUG
    if ($envContent -match "DEBUG=True") {
        Write-Host "   ⚠️  DEBUG=True در .env است" -ForegroundColor Yellow
        Write-Host "   ✅ توصیه: DEBUG=False برای production" -ForegroundColor Green
    }
    
    # بررسی ALLOWED_HOSTS
    if ($envContent -match "ALLOWED_HOSTS=.*\*") {
        Write-Host "   ⚠️  ALLOWED_HOSTS شامل * است" -ForegroundColor Yellow
        Write-Host "   ✅ توصیه: فقط دامنه‌های مجاز را تنظیم کنید" -ForegroundColor Green
    }
} else {
    Write-Host "   ⚠️  فایل .env یافت نشد" -ForegroundColor Yellow
    Write-Host "   ✅ توصیه: فایل .env را از env.example ایجاد کنید" -ForegroundColor Green
}

# 7. بررسی dependencies برای vulnerabilities
Write-Host "`n7. بررسی وابستگی‌ها برای آسیب‌پذیری‌ها..." -ForegroundColor Cyan
$requirementsFile = Join-Path $projectRoot "backend\requirements.txt"
if (Test-Path $requirementsFile) {
    Write-Host "   ℹ️  برای بررسی کامل، از دستور زیر استفاده کنید:" -ForegroundColor Yellow
    Write-Host "   pip install safety && safety check -r requirements.txt" -ForegroundColor Cyan
} else {
    Write-Host "   ⚠️  فایل requirements.txt یافت نشد" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "✅ بررسی اولیه کامل شد" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "📋 اقدامات بعدی:" -ForegroundColor Cyan
Write-Host "1. فایل SECURITY_AUDIT_REPORT.md را مطالعه کنید" -ForegroundColor White
Write-Host "2. مشکلات بحرانی را فوراً رفع کنید" -ForegroundColor White
Write-Host "3. از ابزار safety برای بررسی dependencies استفاده کنید" -ForegroundColor White
Write-Host "4. HTTPS را در production فعال کنید" -ForegroundColor White
Write-Host "5. DEBUG را در production غیرفعال کنید" -ForegroundColor White
Write-Host ""

