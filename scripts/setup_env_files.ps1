# ============================================
# اسکریپت ایجاد فایل‌های Environment
# ============================================
# این اسکریپت فایل‌های .env.local و .env.production را از env.example ایجاد می‌کند

Write-Host "🔧 ایجاد فایل‌های Environment..." -ForegroundColor Cyan
Write-Host ""

# بررسی وجود env.example
if (-not (Test-Path "env.example")) {
    Write-Host "❌ فایل env.example یافت نشد!" -ForegroundColor Red
    exit 1
}

# ایجاد .env.local
if (Test-Path ".env.local") {
    $response = Read-Host "فایل .env.local از قبل وجود دارد. آیا می‌خواهید آن را بازنویسی کنید? (y/n)"
    if ($response -ne "y") {
        Write-Host "⏭ فایل .env.local بدون تغییر باقی ماند" -ForegroundColor Yellow
    } else {
        Copy-Item "env.example" ".env.local" -Force
        Write-Host "✅ فایل .env.local ایجاد شد" -ForegroundColor Green
        
        # تنظیمات پیش‌فرض برای لوکال
        $content = Get-Content ".env.local" -Raw
        $content = $content -replace "DEBUG=True", "DEBUG=True"
        $content = $content -replace "ENV=LOCAL", "ENV=LOCAL"
        $content = $content -replace "PUBLIC_IP=", "PUBLIC_IP="
        $content = $content -replace "FRONTEND_URL=http://localhost:3000", "FRONTEND_URL=http://localhost:3000"
        $content = $content -replace "BACKEND_URL=http://localhost:8000", "BACKEND_URL=http://localhost:8000"
        $content = $content -replace "ALLOWED_HOSTS=localhost,127.0.0.1,\*", "ALLOWED_HOSTS=localhost,127.0.0.1,*"
        Set-Content ".env.local" $content
    }
} else {
    Copy-Item "env.example" ".env.local" -Force
    Write-Host "✅ فایل .env.local ایجاد شد" -ForegroundColor Green
    
    # تنظیمات پیش‌فرض برای لوکال
    $content = Get-Content ".env.local" -Raw
    $content = $content -replace "DEBUG=True", "DEBUG=True"
    $content = $content -replace "ENV=LOCAL", "ENV=LOCAL"
    $content = $content -replace "PUBLIC_IP=", "PUBLIC_IP="
    $content = $content -replace "FRONTEND_URL=http://localhost:3000", "FRONTEND_URL=http://localhost:3000"
    $content = $content -replace "BACKEND_URL=http://localhost:8000", "BACKEND_URL=http://localhost:8000"
    $content = $content -replace "ALLOWED_HOSTS=localhost,127.0.0.1,\*", "ALLOWED_HOSTS=localhost,127.0.0.1,*"
    Set-Content ".env.local" $content
}

# ایجاد .env.production
if (Test-Path ".env.production") {
    $response = Read-Host "فایل .env.production از قبل وجود دارد. آیا می‌خواهید آن را بازنویسی کنید? (y/n)"
    if ($response -ne "y") {
        Write-Host "⏭ فایل .env.production بدون تغییر باقی ماند" -ForegroundColor Yellow
    } else {
        Copy-Item "env.example" ".env.production" -Force
        Write-Host "✅ فایل .env.production ایجاد شد" -ForegroundColor Green
        
        # تنظیمات پیش‌فرض برای Production
        $content = Get-Content ".env.production" -Raw
        $content = $content -replace "DEBUG=True", "DEBUG=False"
        $content = $content -replace "ENV=LOCAL", "ENV=PRODUCTION"
        $content = $content -replace "PUBLIC_IP=", "PUBLIC_IP=191.101.113.163"
        $content = $content -replace "FRONTEND_URL=http://localhost:3000", "FRONTEND_URL=http://191.101.113.163:3000"
        $content = $content -replace "BACKEND_URL=http://localhost:8000", "BACKEND_URL=http://191.101.113.163:8000"
        $content = $content -replace "ALLOWED_HOSTS=localhost,127.0.0.1,\*", "ALLOWED_HOSTS=191.101.113.163,localhost,127.0.0.1"
        Set-Content ".env.production" $content
        
        Write-Host ""
        Write-Host "⚠️  مهم: فایل .env.production را ویرایش کنید و:" -ForegroundColor Yellow
        Write-Host "   1. SECRET_KEY را به یک رشته تصادفی امن تغییر دهید" -ForegroundColor Yellow
        Write-Host "   2. تمام API keys را با مقادیر واقعی جایگزین کنید" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "   برای تولید SECRET_KEY:" -ForegroundColor Cyan
        Write-Host "   python -c `"import secrets; print(secrets.token_urlsafe(50))`"" -ForegroundColor Gray
    }
} else {
    Copy-Item "env.example" ".env.production" -Force
    Write-Host "✅ فایل .env.production ایجاد شد" -ForegroundColor Green
    
    # تنظیمات پیش‌فرض برای Production
    $content = Get-Content ".env.production" -Raw
    $content = $content -replace "DEBUG=True", "DEBUG=False"
    $content = $content -replace "ENV=LOCAL", "ENV=PRODUCTION"
    $content = $content -replace "PUBLIC_IP=", "PUBLIC_IP=191.101.113.163"
    $content = $content -replace "FRONTEND_URL=http://localhost:3000", "FRONTEND_URL=http://191.101.113.163:3000"
    $content = $content -replace "BACKEND_URL=http://localhost:8000", "BACKEND_URL=http://191.101.113.163:8000"
    $content = $content -replace "ALLOWED_HOSTS=localhost,127.0.0.1,\*", "ALLOWED_HOSTS=191.101.113.163,localhost,127.0.0.1"
    Set-Content ".env.production" $content
    
    Write-Host ""
    Write-Host "⚠️  مهم: فایل .env.production را ویرایش کنید و:" -ForegroundColor Yellow
    Write-Host "   1. SECRET_KEY را به یک رشته تصادفی امن تغییر دهید" -ForegroundColor Yellow
    Write-Host "   2. تمام API keys را با مقادیر واقعی جایگزین کنید" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   برای تولید SECRET_KEY:" -ForegroundColor Cyan
    Write-Host "   python -c `"import secrets; print(secrets.token_urlsafe(50))`"" -ForegroundColor Gray
}

Write-Host ""
Write-Host "✅ فایل‌های Environment ایجاد شدند!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 مراحل بعدی:" -ForegroundColor Cyan
Write-Host "   1. فایل .env.local را برای توسعه محلی ویرایش کنید" -ForegroundColor White
Write-Host "   2. فایل .env.production را برای VPS ویرایش کنید" -ForegroundColor White
Write-Host "   3. برای استفاده از .env.local: .\use_local.ps1" -ForegroundColor White
Write-Host "   4. برای استفاده از .env.production: .\use_production.ps1" -ForegroundColor White

