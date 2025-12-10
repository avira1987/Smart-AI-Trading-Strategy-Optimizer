# اسکریپت به‌روزرسانی فرانت‌اند
# این اسکریپت فرانت‌اند را build می‌کند، فایل‌ها را به nginx کپی می‌کند و nginx را reload می‌کند

param(
    [switch]$SkipBuild = $false,
    [switch]$SkipReload = $false
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

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  به‌روزرسانی فرانت‌اند" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# پیدا کردن مسیر پروژه
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectPath = Split-Path -Parent $scriptPath
$frontendDir = Join-Path $projectPath "frontend"
$distPath = Join-Path $frontendDir "dist"

# بررسی وجود پوشه frontend
if (-not (Test-Path $frontendDir)) {
    Write-Error "✗ پوشه frontend پیدا نشد: $frontendDir"
    exit 1
}

# ==========================================
# Step 1: Build کردن فرانت‌اند
# ==========================================
if (-not $SkipBuild) {
    Write-Info "[1/3] در حال Build کردن فرانت‌اند..."
    
    # بررسی وجود npm
    $npmAvailable = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npmAvailable) {
        Write-Error "✗ npm پیدا نشد. لطفاً Node.js را نصب کنید."
        exit 1
    }
    
    # بررسی وجود node_modules
    $nodeModulesPath = Join-Path $frontendDir "node_modules"
    if (-not (Test-Path $nodeModulesPath)) {
        Write-Warning "⚠️  node_modules پیدا نشد. در حال نصب وابستگی‌ها..."
        Set-Location $frontendDir
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Error "✗ خطا در نصب وابستگی‌ها"
            exit 1
        }
        Write-Success "✓ وابستگی‌ها نصب شدند"
    }
    
    # Build کردن
    Set-Location $frontendDir
    
    # حذف متغیر محیطی VITE_BACKEND_URL برای production build
    if ($env:VITE_BACKEND_URL) {
        Remove-Item Env:\VITE_BACKEND_URL
    }
    
    Write-Info "  در حال اجرای npm run build..."
    $buildOutput = npm run build 2>&1
    $buildSuccess = $LASTEXITCODE -eq 0
    
    Set-Location $projectPath
    
    if (-not $buildSuccess) {
        Write-Error "✗ خطا در Build فرانت‌اند"
        Write-Host "  Build output:" -ForegroundColor Yellow
        $buildOutput | Select-Object -Last 20 | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        exit 1
    }
    
    if (-not (Test-Path $distPath) -or (Get-ChildItem $distPath -File -ErrorAction SilentlyContinue).Count -eq 0) {
        Write-Error "✗ پوشه dist خالی است یا وجود ندارد"
        exit 1
    }
    
    Write-Success "✓ فرانت‌اند با موفقیت Build شد"
} else {
    Write-Warning "⏭ Build رد شد (SkipBuild فعال است)"
    
    # بررسی وجود dist
    if (-not (Test-Path $distPath) -or (Get-ChildItem $distPath -File -ErrorAction SilentlyContinue).Count -eq 0) {
        Write-Error "✗ پوشه dist وجود ندارد یا خالی است. لطفاً ابتدا build کنید."
        exit 1
    }
}

Write-Host ""

# ==========================================
# Step 2: پیدا کردن Nginx و کپی فایل‌ها
# ==========================================
Write-Info "[2/3] پیدا کردن Nginx و کپی فایل‌ها..."

# پیدا کردن مسیر nginx
$nginxPath = $null
$possibleNginxPaths = @(
    "C:\nginx-1.28.0\nginx.exe",
    "C:\nginx-1.27.0\nginx.exe",
    "C:\nginx-1.26.0\nginx.exe",
    "C:\nginx-1.25.0\nginx.exe",
    "C:\nginx\nginx.exe",
    "C:\Program Files\nginx\nginx.exe",
    "C:\Program Files (x86)\nginx\nginx.exe"
)

foreach ($path in $possibleNginxPaths) {
    if (Test-Path $path) {
        $nginxPath = $path
        Write-Success "✓ Nginx پیدا شد: $path"
        break
    }
}

if (-not $nginxPath) {
    Write-Warning "⚠️  Nginx پیدا نشد!"
    Write-Warning "  فایل‌های build شده در: $distPath"
    Write-Warning "  لطفاً به صورت دستی فایل‌ها را به پوشه html nginx کپی کنید."
    exit 1
}

# پیدا کردن پوشه html nginx
$nginxDir = Split-Path $nginxPath -Parent
$nginxHtmlDir = Join-Path $nginxDir "html"

# ایجاد پوشه html اگر وجود ندارد
if (-not (Test-Path $nginxHtmlDir)) {
    Write-Info "  ایجاد پوشه html nginx..."
    New-Item -ItemType Directory -Path $nginxHtmlDir -Force | Out-Null
    Write-Success "✓ پوشه html ایجاد شد: $nginxHtmlDir"
}

# کپی فایل‌ها
Write-Info "  در حال کپی فایل‌ها از $distPath به $nginxHtmlDir ..."
try {
    # حذف محتوای قبلی (اختیاری - برای اطمینان از پاک بودن)
    # Get-ChildItem $nginxHtmlDir -Exclude "*.bak" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    
    # کپی فایل‌های جدید
    Copy-Item -Path "$distPath\*" -Destination $nginxHtmlDir -Recurse -Force -ErrorAction Stop
    
    # کپی صفحات خطای سفارشی (403.html و 404.html)
    $publicDir = Join-Path $frontendDir "public"
    $errorPages = @("403.html", "404.html")
    foreach ($errorPage in $errorPages) {
        $sourcePage = Join-Path $publicDir $errorPage
        if (Test-Path $sourcePage) {
            Copy-Item -Path $sourcePage -Destination $nginxHtmlDir -Force -ErrorAction SilentlyContinue
            Write-Success "  ✓ صفحه خطای $errorPage کپی شد"
        }
    }
    
    # بررسی تعداد فایل‌های کپی شده
    $copiedFiles = (Get-ChildItem $nginxHtmlDir -Recurse -File).Count
    Write-Success "✓ فایل‌ها با موفقیت کپی شدند ($copiedFiles فایل)"
    Write-Success "  مسیر: $nginxHtmlDir"
} catch {
    Write-Error "✗ خطا در کپی فایل‌ها: $_"
    exit 1
}

Write-Host ""

# ==========================================
# Step 3: Reload کردن Nginx
# ==========================================
if (-not $SkipReload) {
    Write-Info "[3/3] در حال Reload کردن Nginx..."
    
    try {
        # تست تنظیمات nginx
        $nginxDir = Split-Path $nginxPath -Parent
        Set-Location $nginxDir
        $configTest = & $nginxPath -t 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ تنظیمات Nginx معتبر است"
        } else {
            Write-Warning "⚠️  هشدار در تنظیمات Nginx:"
            $configTest | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        }
        
        # Reload nginx
        $reloadOutput = & $nginxPath -s reload 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ Nginx با موفقیت Reload شد"
        } else {
            Write-Warning "⚠️  خطا در Reload Nginx (ممکن است nginx در حال اجرا نباشد)"
            Write-Host "  خروجی: $reloadOutput" -ForegroundColor Gray
            Write-Info "  می‌توانید به صورت دستی nginx را reload کنید:"
            Write-Host "    $nginxPath -s reload" -ForegroundColor Gray
        }
    } catch {
        Write-Warning "⚠️  خطا در Reload Nginx: $_"
        Write-Info "  می‌توانید به صورت دستی nginx را reload کنید:"
        Write-Host "    $nginxPath -s reload" -ForegroundColor Gray
    }
    
    Set-Location $projectPath
} else {
    Write-Warning "⏭ Reload رد شد (SkipReload فعال است)"
    Write-Info "  لطفاً به صورت دستی nginx را reload کنید:"
    Write-Host "    $nginxPath -s reload" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ به‌روزرسانی با موفقیت انجام شد!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "نکته: برای مشاهده تغییرات در مرورگر:" -ForegroundColor Yellow
Write-Host "  - Ctrl+Shift+R (Hard Refresh)" -ForegroundColor Gray
Write-Host "  - یا Ctrl+F5" -ForegroundColor Gray
Write-Host ""

