# اسکریپت به‌روزرسانی مبلغ هدیه ثبت‌نام
# این اسکریپت مقدار registration_bonus را در SystemSettings به 39000 تومان به‌روزرسانی می‌کند

param(
    [float]$Amount = 39000.0
)

$ErrorActionPreference = "Stop"

# تابع‌های کمکی برای نمایش پیام‌ها
function Write-Info {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

# پیدا کردن مسیر پروژه
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendPath = Join-Path $ProjectRoot "backend"

if (-not (Test-Path $BackendPath)) {
    Write-Error "❌ پوشه backend یافت نشد: $BackendPath"
    exit 1
}

Write-Info "📁 مسیر پروژه: $ProjectRoot"
Write-Info "📁 مسیر backend: $BackendPath"

# بررسی وجود manage.py
$ManagePy = Join-Path $BackendPath "manage.py"
if (-not (Test-Path $ManagePy)) {
    Write-Error "❌ فایل manage.py یافت نشد: $ManagePy"
    exit 1
}

# تغییر به مسیر backend
Push-Location $BackendPath

try {
    Write-Info "🔄 در حال به‌روزرسانی مبلغ هدیه ثبت‌نام به $Amount تومان..."
    Write-Info ""
    
    # اجرای دستور Django
    python manage.py update_registration_bonus --amount $Amount
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success ""
        Write-Success "✅ مبلغ هدیه ثبت‌نام با موفقیت به‌روزرسانی شد!"
        Write-Info ""
        Write-Info "💡 از این پس، کاربران جدیدی که ثبت‌نام می‌کنند، $Amount تومان هدیه دریافت خواهند کرد."
    } else {
        Write-Error ""
        Write-Error "❌ خطا در به‌روزرسانی مبلغ هدیه ثبت‌نام"
        exit 1
    }
} catch {
    Write-Error ""
    Write-Error "❌ خطا در اجرای دستور: $_"
    exit 1
} finally {
    Pop-Location
}

Write-Info ""
Write-Success "✨ عملیات با موفقیت انجام شد!"

