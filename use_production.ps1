# ============================================
# تنظیم Environment برای Production
# ============================================
# این اسکریپت فایل .env.production را به .env کپی می‌کند
# ⚠️ توجه: این فقط برای تست محلی است

Write-Host "🔧 تنظیم Environment برای Production..." -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path ".env.production")) {
    Write-Host "❌ فایل .env.production یافت نشد!" -ForegroundColor Red
    Write-Host ""
    Write-Host "لطفاً ابتدا فایل‌های Environment را ایجاد کنید:" -ForegroundColor Yellow
    Write-Host "  .\setup_env_files.ps1" -ForegroundColor White
    exit 1
}

Copy-Item .env.production .env -Force
Write-Host "✅ Environment برای Production تنظیم شد" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  توجه: این فقط برای تست محلی است" -ForegroundColor Yellow
Write-Host "برای Deploy به سرور از .\deploy.ps1 استفاده کنید" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 تنظیمات:" -ForegroundColor Cyan
Write-Host "  - DEBUG=False" -ForegroundColor White
Write-Host "  - ENV=PRODUCTION" -ForegroundColor White
Write-Host "  - PUBLIC_IP=191.101.113.163" -ForegroundColor White
Write-Host "  - FRONTEND_URL=http://191.101.113.163:3000" -ForegroundColor White
Write-Host "  - BACKEND_URL=http://191.101.113.163:8000" -ForegroundColor White
Write-Host ""

