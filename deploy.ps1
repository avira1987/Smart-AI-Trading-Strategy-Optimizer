# ============================================
# اسکریپت Deploy به VPS
# ============================================
# این اسکریپت پروژه را به سرور VPS شما deploy می‌کند
# استفاده: .\deploy.ps1

param(
    [switch]$SkipGit = $false,
    [switch]$SkipBuild = $false,
    [switch]$SkipRestart = $false
)

# تنظیمات VPS
$VPS_IP = "191.101.113.163"
$VPS_PORT = "7230"
$VPS_USER = "administrator"
$VPS_PASSWORD = "Li7n9NGhrEICYMO"
$VPS_PROJECT_PATH = "C:\SmartAITradingStrategyOptimizer"

# رنگ‌های کنسول
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success { Write-ColorOutput Green $args }
function Write-Error { Write-ColorOutput Red $args }
function Write-Info { Write-ColorOutput Cyan $args }
function Write-Warning { Write-ColorOutput Yellow $args }

# بررسی وجود Git و تنظیم متغیر useGit
$useGit = $false
if (-not $SkipGit) {
    Write-Info "بررسی وضعیت Git..."
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Error "Git نصب نشده است. لطفاً Git را نصب کنید."
        exit 1
    }

    # بررسی اینکه آیا در یک repository هستیم
    $gitStatus = git status 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Info "مخزن Git یافت نشد. در حال راه‌اندازی Git..."
        git init
        git branch -M main
        Write-Info "لطفاً remote repository را اضافه کنید:"
        Write-Info "git remote add origin https://github.com/avira1987/Smart-AI-Trading-Strategy-Optimizer.git"
        Write-Info "یا برای ادامه بدون Git از فلگ -SkipGit استفاده کنید."
        $continue = Read-Host "آیا می‌خواهید ادامه دهید؟ (y/n)"
        if ($continue -ne "y") {
            exit 0
        }
    } else {
        Write-Success "✓ Git repository یافت شد"
        
        # Commit تغییرات اگر وجود دارد
        $changes = git status --porcelain
        if ($changes) {
            Write-Info "تغییرات یافت شده. در حال commit..."
            git add .
            $commitMessage = Read-Host "پیام commit را وارد کنید (یا Enter برای استفاده از پیام پیش‌فرض)"
            if ([string]::IsNullOrWhiteSpace($commitMessage)) {
                $commitMessage = "Deploy: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
            }
            git commit -m $commitMessage
            Write-Success "✓ تغییرات commit شدند"
        }
        
        # بررسی remote و Push به GitHub
        $remoteUrl = git remote get-url origin 2>&1
        if ($LASTEXITCODE -eq 0 -and $remoteUrl -and -not $remoteUrl.ToString().Contains("error")) {
            $useGit = $true
            Write-Info "در حال Push به GitHub..."
            git push origin main
            if ($LASTEXITCODE -eq 0) {
                Write-Success "✓ تغییرات به GitHub push شدند"
            } else {
                Write-Warning "⚠️  Push به GitHub ناموفق بود (ادامه می‌دهیم...)"
            }
        } else {
            Write-Warning "⚠️  Git remote تنظیم نشده است - از روش ZIP استفاده می‌شود"
            Write-Info "💡 برای استفاده از Git، remote را تنظیم کنید:" -ForegroundColor Cyan
            Write-Info "   git remote add origin https://github.com/avira1987/Smart-AI-Trading-Strategy-Optimizer.git" -ForegroundColor Gray
        }
    }
}

# Build Frontend
if (-not $SkipBuild) {
    Write-Info "در حال Build کردن Frontend..."
    Push-Location frontend
    
    if (-not (Test-Path "node_modules")) {
        Write-Info "نصب وابستگی‌های Frontend..."
        npm install
    }
    
    # کپی فایل .env.production به .env
    if (Test-Path "..\.env.production") {
        Copy-Item "..\.env.production" "..\.env" -Force
        Write-Success "✓ فایل .env.production کپی شد"
    }
    
    Write-Info "در حال Build..."
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Error "خطا در Build Frontend"
        Pop-Location
        exit 1
    }
    Write-Success "✓ Frontend با موفقیت Build شد"
    Pop-Location
} else {
    Write-Warning "⏭ Build Frontend رد شد"
}

# اگر Git remote تنظیم نشده، از ZIP استفاده می‌کنیم
if (-not $useGit) {
    # ایجاد فایل ZIP برای انتقال
    Write-Info "در حال ایجاد فایل ZIP..."
    $zipFile = "deploy-$(Get-Date -Format 'yyyyMMdd-HHmmss').zip"
    $excludePatterns = @(
        "node_modules",
        "venv",
        ".git",
        "__pycache__",
        "*.pyc",
        ".env.local",
        "db.sqlite3",
        "*.log",
        "dist",
        "build",
        "staticfiles",
        "media",
        "cache"
    )

    # استفاده از Compress-Archive (نیاز به PowerShell 5.0+)
    $tempDir = New-TemporaryFile | ForEach-Object { Remove-Item $_; New-Item -ItemType Directory -Path $_ }
    Write-Info "کپی فایل‌ها به پوشه موقت..."

    Get-ChildItem -Path . -Recurse | Where-Object {
        $relativePath = $_.FullName.Substring($PWD.Path.Length + 1)
        $shouldExclude = $false
        foreach ($pattern in $excludePatterns) {
            if ($relativePath -like "*\$pattern\*" -or $relativePath -like "$pattern\*") {
                $shouldExclude = $true
                break
            }
        }
        -not $shouldExclude
    } | Copy-Item -Destination {
        $destPath = Join-Path $tempDir $_.FullName.Substring($PWD.Path.Length + 1)
        $destDir = Split-Path $destPath -Parent
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        $destPath
    } -Recurse -Force

    # کپی فایل .env.production به .env در ZIP
    if (Test-Path ".env.production") {
        Copy-Item ".env.production" (Join-Path $tempDir ".env") -Force
    }

    Compress-Archive -Path "$tempDir\*" -DestinationPath $zipFile -Force
    Remove-Item $tempDir -Recurse -Force
    Write-Success "✓ فایل ZIP ایجاد شد: $zipFile"
}

# اتصال به VPS و انتقال فایل
Write-Info "در حال اتصال به VPS..."
$securePassword = ConvertTo-SecureString $VPS_PASSWORD -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential($VPS_USER, $securePassword)

# ایجاد session
$session = New-PSSession -ComputerName $VPS_IP -Port $VPS_PORT -Credential $credential -ErrorAction Stop
Write-Success "✓ اتصال به VPS برقرار شد"

try {
    # اجرای دستورات روی VPS
    Write-Info "در حال Deploy روی VPS..."
    
    if ($useGit) {
        # استفاده از Git Pull
        $deployScript = @"
# بررسی وجود Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git روی VPS نصب نشده است!" -ForegroundColor Red
    Write-Host "لطفاً Git را نصب کنید: winget install Git.Git" -ForegroundColor Yellow
    exit 1
}

# ایجاد پوشه پروژه اگر وجود ندارد
if (-not (Test-Path "$VPS_PROJECT_PATH")) {
    New-Item -ItemType Directory -Path "$VPS_PROJECT_PATH" -Force | Out-Null
    Write-Host "✓ پوشه پروژه ایجاد شد" -ForegroundColor Green
    
    # Clone از GitHub
    Write-Host "در حال Clone از GitHub..." -ForegroundColor Cyan
    git clone https://github.com/avira1987/Smart-AI-Trading-Strategy-Optimizer.git "$VPS_PROJECT_PATH"
    if (`$LASTEXITCODE -ne 0) {
        Write-Host "❌ خطا در Clone از GitHub" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ پروژه از GitHub clone شد" -ForegroundColor Green
} else {
    # Pull از GitHub
    Write-Host "در حال Pull از GitHub..." -ForegroundColor Cyan
    Set-Location "$VPS_PROJECT_PATH"
    
    # بررسی remote
    `$remoteUrl = git remote get-url origin 2>&1
    if (`$LASTEXITCODE -ne 0 -or `$remoteUrl.ToString().Contains("error")) {
        Write-Host "⚠️  Git remote تنظیم نشده است. در حال تنظیم..." -ForegroundColor Yellow
        git remote add origin https://github.com/avira1987/Smart-AI-Trading-Strategy-Optimizer.git
    }
    
    git pull origin main
    if (`$LASTEXITCODE -ne 0) {
        Write-Host "⚠️  خطا در Pull (ادامه می‌دهیم...)" -ForegroundColor Yellow
    } else {
        Write-Host "✓ تغییرات از GitHub pull شدند" -ForegroundColor Green
    }
}

# کپی .env.production به .env
if (Test-Path "$VPS_PROJECT_PATH\.env.production") {
    Copy-Item "$VPS_PROJECT_PATH\.env.production" "$VPS_PROJECT_PATH\.env" -Force
    Write-Host "✓ فایل .env.production به .env کپی شد" -ForegroundColor Green
} else {
    Write-Host "⚠️  فایل .env.production یافت نشد" -ForegroundColor Yellow
    Write-Host "💡 لطفاً فایل .env.production را روی VPS ایجاد کنید" -ForegroundColor Cyan
}

# نصب وابستگی‌های Python
Write-Host "در حال نصب وابستگی‌های Python..." -ForegroundColor Cyan
Set-Location "$VPS_PROJECT_PATH\backend"
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "✓ Virtual environment ایجاد شد" -ForegroundColor Green
}
& ".\venv\Scripts\Activate.ps1"
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
Write-Host "✓ وابستگی‌های Python نصب شدند" -ForegroundColor Green

# اجرای Migrations
Write-Host "در حال اجرای Migrations..." -ForegroundColor Cyan
python manage.py migrate --noinput
Write-Host "✓ Migrations اجرا شدند" -ForegroundColor Green

# جمع‌آوری Static Files
Write-Host "در حال جمع‌آوری Static Files..." -ForegroundColor Cyan
python manage.py collectstatic --noinput
Write-Host "✓ Static Files جمع‌آوری شدند" -ForegroundColor Green

# نصب وابستگی‌های Frontend (اگر نیاز باشد)
Write-Host "بررسی Frontend..." -ForegroundColor Cyan
Set-Location "$VPS_PROJECT_PATH\frontend"
if (-not (Test-Path "node_modules")) {
    npm install --production --silent
    Write-Host "✓ وابستگی‌های Frontend نصب شدند" -ForegroundColor Green
}

# Build Frontend (اگر dist وجود ندارد)
if (-not (Test-Path "dist")) {
    Write-Host "در حال Build Frontend..." -ForegroundColor Cyan
    npm run build
    if (`$LASTEXITCODE -eq 0) {
        Write-Host "✓ Frontend build شد" -ForegroundColor Green
    } else {
        Write-Host "⚠️  خطا در Build Frontend" -ForegroundColor Yellow
    }
}

Write-Host "✓ Deploy با موفقیت انجام شد!" -ForegroundColor Green
"@
    } else {
        # استفاده از ZIP (fallback)
        Write-Info "در حال انتقال فایل ZIP به VPS..."
        Copy-Item -Path $zipFile -Destination "C:\$zipFile" -ToSession $session -Force
        Write-Success "✓ فایل ZIP انتقال یافت"

        $deployScript = @"
# ایجاد پوشه پروژه اگر وجود ندارد
if (-not (Test-Path "$VPS_PROJECT_PATH")) {
    New-Item -ItemType Directory -Path "$VPS_PROJECT_PATH" -Force | Out-Null
}

# پشتیبان‌گیری از نسخه قبلی
`$backupPath = "$VPS_PROJECT_PATH-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
if (Test-Path "$VPS_PROJECT_PATH") {
    Copy-Item "$VPS_PROJECT_PATH" `$backupPath -Recurse -Force
    Write-Host "✓ پشتیبان‌گیری انجام شد: `$backupPath"
}

# استخراج فایل ZIP
Write-Host "در حال استخراج فایل ZIP..." -ForegroundColor Cyan
Expand-Archive -Path "C:\$zipFile" -DestinationPath "$VPS_PROJECT_PATH" -Force
Remove-Item "C:\$zipFile" -Force
Write-Host "✓ فایل ZIP استخراج شد" -ForegroundColor Green

# کپی .env.production به .env
if (Test-Path "$VPS_PROJECT_PATH\.env.production") {
    Copy-Item "$VPS_PROJECT_PATH\.env.production" "$VPS_PROJECT_PATH\.env" -Force
    Write-Host "✓ فایل .env.production به .env کپی شد" -ForegroundColor Green
}

# نصب وابستگی‌های Python
Write-Host "در حال نصب وابستگی‌های Python..." -ForegroundColor Cyan
Set-Location "$VPS_PROJECT_PATH\backend"
if (-not (Test-Path "venv")) {
    python -m venv venv
}
& ".\venv\Scripts\Activate.ps1"
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
Write-Host "✓ وابستگی‌های Python نصب شدند" -ForegroundColor Green

# اجرای Migrations
Write-Host "در حال اجرای Migrations..." -ForegroundColor Cyan
python manage.py migrate --noinput
Write-Host "✓ Migrations اجرا شدند" -ForegroundColor Green

# جمع‌آوری Static Files
Write-Host "در حال جمع‌آوری Static Files..." -ForegroundColor Cyan
python manage.py collectstatic --noinput
Write-Host "✓ Static Files جمع‌آوری شدند" -ForegroundColor Green

# نصب وابستگی‌های Frontend (اگر نیاز باشد)
Write-Host "بررسی Frontend..." -ForegroundColor Cyan
Set-Location "$VPS_PROJECT_PATH\frontend"
if (-not (Test-Path "node_modules")) {
    npm install --production --silent
    Write-Host "✓ وابستگی‌های Frontend نصب شدند" -ForegroundColor Green
}

Write-Host "✓ Deploy با موفقیت انجام شد!" -ForegroundColor Green
"@
    }

    Invoke-Command -Session $session -ScriptBlock ([scriptblock]::Create($deployScript))
    
    # Restart سرویس‌ها
    if (-not $SkipRestart) {
        Write-Info "در حال راه‌اندازی مجدد سرویس‌ها..."
        
        $restartScript = @"
# توقف سرویس‌های قبلی (اگر در حال اجرا هستند)
Get-Process | Where-Object { `$_.ProcessName -like "*python*" -or `$_.ProcessName -like "*node*" } | Where-Object { `$_.Path -like "*$VPS_PROJECT_PATH*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# راه‌اندازی Backend
Write-Host "راه‌اندازی Backend..."
Set-Location "$VPS_PROJECT_PATH\backend"
& ".\venv\Scripts\Activate.ps1"
Start-Process python -ArgumentList "manage.py", "runserver", "0.0.0.0:8000" -WindowStyle Hidden

# راه‌اندازی Celery Worker
Write-Host "راه‌اندازی Celery Worker..."
Start-Process celery -ArgumentList "-A", "config", "worker", "--loglevel=info" -WindowStyle Hidden

# راه‌اندازی Frontend
Write-Host "راه‌اندازی Frontend..."
Set-Location "$VPS_PROJECT_PATH\frontend"
Start-Process npm -ArgumentList "run", "preview", "--", "--port", "3000", "--host", "0.0.0.0" -WindowStyle Hidden

Write-Host "✓ سرویس‌ها راه‌اندازی شدند"
Write-Host "Backend: http://$VPS_IP:8000"
Write-Host "Frontend: http://$VPS_IP:3000"
"@

        Invoke-Command -Session $session -ScriptBlock ([scriptblock]::Create($restartScript))
        Write-Success "✓ سرویس‌ها راه‌اندازی شدند"
    } else {
        Write-Warning "⏭ راه‌اندازی مجدد سرویس‌ها رد شد"
    }

    Write-Success "`n✓✓✓ Deploy با موفقیت انجام شد! ✓✓✓"
    Write-Info "Backend: http://$VPS_IP:8000"
    Write-Info "Frontend: http://$VPS_IP:3000"

} catch {
    Write-Error "خطا در Deploy: $_"
    exit 1
} finally {
    # بستن session
    Remove-PSSession $session
    # حذف فایل ZIP محلی (اگر وجود دارد)
    if ($useGit -eq $false -and (Test-Path $zipFile)) {
        Remove-Item $zipFile -Force
    }
}

