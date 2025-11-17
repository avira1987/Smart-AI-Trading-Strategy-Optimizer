# ============================================
# تنظیم Environment برای توسعه محلی
# ============================================
# این اسکریپت فایل .env.local را به .env کپی می‌کند

Write-Host "🔧 تنظیم Environment برای توسعه محلی..." -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path ".env.local")) {
    Write-Host "❌ فایل .env.local یافت نشد!" -ForegroundColor Red
    Write-Host ""
    Write-Host "لطفاً ابتدا فایل‌های Environment را ایجاد کنید:" -ForegroundColor Yellow
    Write-Host "  .\setup_env_files.ps1" -ForegroundColor White
    exit 1
}

Copy-Item .env.local .env -Force
Write-Host "✅ Environment برای لوکال تنظیم شد" -ForegroundColor Green
Write-Host ""
Write-Host "📝 تنظیمات:" -ForegroundColor Cyan
Write-Host "  - DEBUG=True" -ForegroundColor White
Write-Host "  - ENV=LOCAL" -ForegroundColor White
Write-Host "  - PUBLIC_IP= (خالی)" -ForegroundColor White
Write-Host "  - FRONTEND_URL=http://localhost:3000" -ForegroundColor White
Write-Host "  - BACKEND_URL=http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "حالا می‌توانید پروژه را راه‌اندازی کنید:" -ForegroundColor Cyan
Write-Host "  .\start_project.ps1" -ForegroundColor White
Write-Host ""

