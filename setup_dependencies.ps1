# Script برای نصب و راه‌اندازی تمام وابستگی‌های پروژه
# این اسکریپت باید با دسترسی Administrator اجرا شود

# رنگ‌ها برای خروجی
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

# بررسی دسترسی Administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# بررسی نصب Python
function Test-PythonInstalled {
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 11)) {
                return $true, $pythonVersion
            }
        }
        return $false, $null
    } catch {
        try {
            $pythonVersion = py --version 2>&1
            if ($pythonVersion -match "Python (\d+)\.(\d+)") {
                $major = [int]$matches[1]
                $minor = [int]$matches[2]
                if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 11)) {
                    return $true, $pythonVersion
                }
            }
        } catch {
            return $false, $null
        }
    }
    return $false, $null
}

# نصب Python
function Install-Python {
    Write-Info "در حال نصب Python 3.11..."
    
    # تلاش با winget (اگر موجود باشد)
    try {
        $wingetAvailable = Get-Command winget -ErrorAction SilentlyContinue
        if ($wingetAvailable) {
            Write-Info "استفاده از winget برای نصب Python..."
            winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
            Start-Sleep -Seconds 5
            
            # به‌روزرسانی PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            
            # بررسی مجدد
            Start-Sleep -Seconds 3
            $isInstalled, $version = Test-PythonInstalled
            if ($isInstalled) {
                Write-Success "Python $version نصب و آماده است!"
                return $true
            }
        }
    } catch {
        Write-Warning "winget در دسترس نیست یا خطا داد. استفاده از روش مستقیم..."
    }
    
    # روش مستقیم: دانلود و نصب
    Write-Info "دانلود Python 3.11 از python.org..."
    $pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    $pythonInstaller = "$env:TEMP\python-3.11.9-amd64.exe"
    
    try {
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller -UseBasicParsing -TimeoutSec 300
        Write-Info "در حال نصب Python (این ممکن است چند دقیقه طول بکشد)..."
        
        $process = Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0", "Include_launcher=1" -Wait -PassThru -NoNewWindow
        
        if ($process.ExitCode -eq 0 -or $process.ExitCode -eq $null) {
            Remove-Item $pythonInstaller -Force -ErrorAction SilentlyContinue
            Write-Success "Python نصب شد!"
            
            # به‌روزرسانی PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            
            # بررسی مجدد
            Start-Sleep -Seconds 5
            $isInstalled, $version = Test-PythonInstalled
            if ($isInstalled) {
                Write-Success "Python $version نصب و آماده است!"
                return $true
            } else {
                # بررسی مسیرهای متداول Python
                $pythonPaths = @(
                    "C:\Python311\python.exe",
                    "C:\Program Files\Python311\python.exe",
                    "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\python.exe"
                )
                
                foreach ($path in $pythonPaths) {
                    if (Test-Path $path) {
                        $env:Path = "$($path | Split-Path -Parent);$env:Path"
                        $isInstalled, $version = Test-PythonInstalled
                        if ($isInstalled) {
                            Write-Success "Python $version نصب و آماده است!"
                            return $true
                        }
                    }
                }
                
                Write-Warning "Python نصب شد اما نیاز به restart terminal است."
                Write-Info "لطفا terminal را ببندید و دوباره باز کنید، سپس اسکریپت را دوباره اجرا کنید."
                return $false
            }
        } else {
            Write-Error "خطا در نصب Python. Exit Code: $($process.ExitCode)"
            return $false
        }
    } catch {
        Write-Error "خطا در نصب Python: $_"
        Write-Warning "لطفا Python 3.11+ را به صورت دستی از https://www.python.org/downloads/ نصب کنید."
        Write-Warning "در هنگام نصب، گزینه 'Add Python to PATH' را فعال کنید."
        return $false
    }
}

# بررسی نصب Node.js
function Test-NodeInstalled {
    try {
        $nodeVersion = node --version 2>&1
        if ($nodeVersion -match "v(\d+)\.(\d+)") {
            $major = [int]$matches[1]
            if ($major -ge 18) {
                return $true, $nodeVersion
            }
        }
        return $false, $null
    } catch {
        return $false, $null
    }
}

# نصب Node.js
function Install-Node {
    Write-Info "در حال نصب Node.js 18 LTS..."
    
    # تلاش با winget (اگر موجود باشد)
    try {
        $wingetAvailable = Get-Command winget -ErrorAction SilentlyContinue
        if ($wingetAvailable) {
            Write-Info "استفاده از winget برای نصب Node.js..."
            winget install OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements
            Start-Sleep -Seconds 5
            
            # به‌روزرسانی PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            
            # بررسی مجدد
            Start-Sleep -Seconds 3
            $isInstalled, $version = Test-NodeInstalled
            if ($isInstalled) {
                Write-Success "Node.js $version نصب و آماده است!"
                return $true
            }
        }
    } catch {
        Write-Warning "winget در دسترس نیست یا خطا داد. استفاده از روش مستقیم..."
    }
    
    # روش مستقیم: دانلود و نصب
    Write-Info "دانلود Node.js 18 LTS از nodejs.org..."
    $nodeUrl = "https://nodejs.org/dist/v18.20.4/node-v18.20.4-x64.msi"
    $nodeInstaller = "$env:TEMP\node-v18.20.4-x64.msi"
    
    try {
        Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeInstaller -UseBasicParsing -TimeoutSec 300
        Write-Info "در حال نصب Node.js (این ممکن است چند دقیقه طول بکشد)..."
        
        $process = Start-Process -FilePath "msiexec.exe" -ArgumentList "/i", "`"$nodeInstaller`"", "/quiet", "/norestart" -Wait -PassThru -NoNewWindow
        
        if ($process.ExitCode -eq 0 -or $process.ExitCode -eq $null) {
            Remove-Item $nodeInstaller -Force -ErrorAction SilentlyContinue
            Write-Success "Node.js نصب شد!"
            
            # به‌روزرسانی PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            
            # بررسی مجدد
            Start-Sleep -Seconds 5
            $isInstalled, $version = Test-NodeInstalled
            if ($isInstalled) {
                Write-Success "Node.js $version نصب و آماده است!"
                return $true
            } else {
                # بررسی مسیرهای متداول Node.js
                $nodePaths = @(
                    "C:\Program Files\nodejs\node.exe",
                    "C:\Program Files (x86)\nodejs\node.exe"
                )
                
                foreach ($path in $nodePaths) {
                    if (Test-Path $path) {
                        $env:Path = "$($path | Split-Path -Parent);$env:Path"
                        $isInstalled, $version = Test-NodeInstalled
                        if ($isInstalled) {
                            Write-Success "Node.js $version نصب و آماده است!"
                            return $true
                        }
                    }
                }
                
                Write-Warning "Node.js نصب شد اما نیاز به restart terminal است."
                Write-Info "لطفا terminal را ببندید و دوباره باز کنید، سپس اسکریپت را دوباره اجرا کنید."
                return $false
            }
        } else {
            Write-Error "خطا در نصب Node.js. Exit Code: $($process.ExitCode)"
            return $false
        }
    } catch {
        Write-Error "خطا در نصب Node.js: $_"
        Write-Warning "لطفا Node.js 18+ را به صورت دستی از https://nodejs.org/ نصب کنید."
        return $false
    }
}

# بررسی Docker
function Test-DockerInstalled {
    try {
        $dockerVersion = docker --version 2>&1
        return $true, $dockerVersion
    } catch {
        return $false, $null
    }
}

# بررسی Redis (Docker یا Windows)
function Test-RedisRunning {
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.Connect("localhost", 6379)
        $tcpClient.Close()
        return $true
    } catch {
        return $false
    }
}

# راه‌اندازی Redis با Docker
function Start-RedisDocker {
    $isDockerInstalled, $dockerVersion = Test-DockerInstalled
    if (-not $isDockerInstalled) {
        Write-Warning "Docker نصب نیست. Redis را نمی‌توان راه‌اندازی کرد."
        Write-Info "گزینه‌ها:"
        Write-Info "1. Docker Desktop را از https://www.docker.com/products/docker-desktop نصب کنید"
        Write-Info "2. یا Redis را به صورت دستی نصب کنید (اختیاری - برای Celery)"
        return $false
    }
    
    Write-Info "بررسی Redis container..."
    try {
        $redisContainer = docker ps -a --filter "name=redis" --format "{{.Names}}"
        if ($redisContainer -eq "redis") {
            $redisRunning = docker ps --filter "name=redis" --format "{{.Names}}"
            if ($redisRunning -eq "redis") {
                Write-Success "Redis در حال اجرا است!"
                return $true
            } else {
                Write-Info "در حال راه‌اندازی Redis container..."
                docker start redis 2>&1 | Out-Null
                Start-Sleep -Seconds 2
                if (Test-RedisRunning) {
                    Write-Success "Redis راه‌اندازی شد!"
                    return $true
                }
            }
        } else {
            Write-Info "در حال ایجاد Redis container..."
            docker run -d --name redis -p 6379:6379 redis:7-alpine 2>&1 | Out-Null
            Start-Sleep -Seconds 3
            if (Test-RedisRunning) {
                Write-Success "Redis راه‌اندازی شد!"
                return $true
            }
        }
    } catch {
        Write-Warning "خطا در راه‌اندازی Redis: $_"
        Write-Warning "Redis اختیاری است. برنامه بدون Redis هم کار می‌کند (اما Celery کار نمی‌کند)."
        return $false
    }
    
    return $false
}

# نصب وابستگی‌های Python
function Install-PythonDependencies {
    $projectRoot = $PSScriptRoot
    $backendPath = Join-Path $projectRoot "backend"
    $venvPath = Join-Path $projectRoot "venv"
    $requirementsPath = Join-Path $backendPath "requirements.txt"
    
    # پیدا کردن Python
    $pythonExe = $null
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python") {
            $pythonExe = "python"
        }
    } catch {
        try {
            $pythonVersion = py --version 2>&1
            if ($pythonVersion -match "Python") {
                $pythonExe = "py"
            }
        } catch {
            # بررسی مسیرهای متداول
            $pythonPaths = @(
                "C:\Python311\python.exe",
                "C:\Program Files\Python311\python.exe",
                "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\python.exe"
            )
            
            foreach ($path in $pythonPaths) {
                if (Test-Path $path) {
                    $pythonExe = $path
                    break
                }
            }
        }
    }
    
    if (-not $pythonExe) {
        Write-Error "Python یافت نشد! لطفا Python را نصب کنید."
        return $false
    }
    
    Write-Info "بررسی virtual environment..."
    
    # بررسی وجود venv
    if (-not (Test-Path $venvPath)) {
        Write-Info "در حال ایجاد virtual environment..."
        & $pythonExe -m venv $venvPath
        if (-not (Test-Path $venvPath)) {
            Write-Error "خطا در ایجاد virtual environment!"
            return $false
        }
        Write-Success "Virtual environment ایجاد شد!"
    } else {
        Write-Success "Virtual environment از قبل وجود دارد!"
    }
    
    # استفاده از Python از venv
    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    if (Test-Path $venvPython) {
        $pythonExe = $venvPython
    } else {
        Write-Warning "Python در venv یافت نشد. استفاده از Python سیستم..."
    }
    
    # به‌روزرسانی pip
    Write-Info "در حال به‌روزرسانی pip..."
    & $pythonExe -m pip install --upgrade pip --quiet
    
    # نصب وابستگی‌ها
    Write-Info "در حال نصب وابستگی‌های Python (این ممکن است چند دقیقه طول بکشد)..."
    if (Test-Path $requirementsPath) {
        & $pythonExe -m pip install -r $requirementsPath
        if ($LASTEXITCODE -eq 0) {
            Write-Success "وابستگی‌های Python نصب شدند!"
            return $true
        } else {
            Write-Error "خطا در نصب وابستگی‌های Python!"
            Write-Info "تلاش مجدد با pip upgrade..."
            & $pythonExe -m pip install --upgrade pip setuptools wheel
            & $pythonExe -m pip install -r $requirementsPath
            if ($LASTEXITCODE -eq 0) {
                Write-Success "وابستگی‌های Python نصب شدند!"
                return $true
            } else {
                return $false
            }
        }
    } else {
        Write-Error "فایل requirements.txt یافت نشد!"
        return $false
    }
}

# نصب وابستگی‌های Node.js
function Install-NodeDependencies {
    $projectRoot = $PSScriptRoot
    $frontendPath = Join-Path $projectRoot "frontend"
    $packageJsonPath = Join-Path $frontendPath "package.json"
    
    Write-Info "بررسی وابستگی‌های Node.js..."
    
    if (-not (Test-Path $packageJsonPath)) {
        Write-Error "فایل package.json یافت نشد!"
        return $false
    }
    
    Set-Location $frontendPath
    
    # بررسی node_modules
    $nodeModulesPath = Join-Path $frontendPath "node_modules"
    if (-not (Test-Path $nodeModulesPath)) {
        Write-Info "در حال نصب وابستگی‌های Node.js (این ممکن است چند دقیقه طول بکشد)..."
        npm install
        if ($LASTEXITCODE -eq 0) {
            Write-Success "وابستگی‌های Node.js نصب شدند!"
            Set-Location $projectRoot
            return $true
        } else {
            Write-Warning "خطا در نصب وابستگی‌های Node.js. در حال تلاش با --legacy-peer-deps..."
            npm install --legacy-peer-deps
            if ($LASTEXITCODE -eq 0) {
                Write-Success "وابستگی‌های Node.js نصب شدند!"
                Set-Location $projectRoot
                return $true
            } else {
                Write-Error "خطا در نصب وابستگی‌های Node.js!"
                Set-Location $projectRoot
                return $false
            }
        }
    } else {
        Write-Success "وابستگی‌های Node.js از قبل نصب شده‌اند!"
        Set-Location $projectRoot
        return $true
    }
}

# بررسی و ایجاد .env
function Setup-EnvironmentFile {
    $projectRoot = $PSScriptRoot
    $envPath = Join-Path $projectRoot ".env"
    $envExamplePath = Join-Path $projectRoot "env.example"
    
    if (-not (Test-Path $envPath)) {
        Write-Info "در حال ایجاد فایل .env..."
        if (Test-Path $envExamplePath) {
            Copy-Item $envExamplePath $envPath
            Write-Success "فایل .env ایجاد شد! لطفا آن را ویرایش کرده و API keys خود را اضافه کنید."
        } else {
            Write-Warning "فایل env.example یافت نشد. فایل .env به صورت دستی ایجاد می‌شود..."
            # ایجاد فایل .env پایه
            @"
# Django Settings
SECRET_KEY=your-secret-key-here-change-in-production-$(Get-Random -Minimum 1000 -Maximum 9999)
DEBUG=True
ENV=LOCAL

# Database (SQLite for local development)
# DB_NAME=forex_db
# DB_USER=postgres
# DB_PASSWORD=postgres
# DB_HOST=localhost
# DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# API Keys (Add your own)
TWELVEDATA_API_KEY=your-twelvedata-api-key
FINANCIALMODELINGPREP_API_KEY=your_financial_modeling_prep_api_key_here
METALSAPI_API_KEY=your-metalsapi-api-key
OANDA_API_KEY=your-oanda-api-key

# AI Providers
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-flash

# Allowed Hosts
ALLOWED_HOSTS=localhost,127.0.0.1,*

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id-here

# Kavenegar SMS
KAVENEGAR_API_KEY=your-kavenegar-api-key-here
KAVENEGAR_SENDER=your-sender-number-here
"@ | Out-File -FilePath $envPath -Encoding UTF8
            Write-Success "فایل .env ایجاد شد!"
        }
    } else {
        Write-Success "فایل .env از قبل وجود دارد!"
    }
}

# اجرای migrations
function Run-Migrations {
    $projectRoot = $PSScriptRoot
    $backendPath = Join-Path $projectRoot "backend"
    $venvPath = Join-Path $projectRoot "venv"
    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    
    Write-Info "اجرای migrations..."
    
    # استفاده از Python از venv
    $pythonExe = "python"
    if (Test-Path $venvPython) {
        $pythonExe = $venvPython
    }
    
    Set-Location $backendPath
    
    & $pythonExe manage.py makemigrations
    & $pythonExe manage.py migrate
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Migrations با موفقیت اجرا شد!"
        Set-Location $projectRoot
        return $true
    } else {
        Write-Warning "خطا در اجرای migrations!"
        Set-Location $projectRoot
        return $false
    }
}

# ایجاد superuser
function Create-Superuser {
    $projectRoot = $PSScriptRoot
    $backendPath = Join-Path $projectRoot "backend"
    $venvPath = Join-Path $projectRoot "venv"
    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    
    Write-Info "بررسی وجود superuser..."
    
    # استفاده از Python از venv
    $pythonExe = "python"
    if (Test-Path $venvPython) {
        $pythonExe = $venvPython
    }
    
    Set-Location $backendPath
    
    # بررسی وجود کاربر admin
    $adminExists = & $pythonExe manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('EXISTS' if User.objects.filter(username='admin').exists() else 'NOT_EXISTS')" 2>&1
    
    if ($adminExists -match "EXISTS") {
        Write-Success "کاربر admin از قبل وجود دارد!"
        Set-Location $projectRoot
        return $true
    } else {
        Write-Info "در حال ایجاد کاربر admin (username: admin, password: admin)..."
        $createUserScript = @"
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('SUPERUSER_CREATED')
else:
    print('SUPERUSER_EXISTS')
"@
        $createUserScript | & $pythonExe manage.py shell
        Write-Success "کاربر admin ایجاد شد! (username: admin, password: admin)"
        Set-Location $projectRoot
        return $true
    }
}

# ============================================
# شروع اصلی
# ============================================

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  نصب و راه‌اندازی وابستگی‌های پروژه" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# بررسی دسترسی Administrator
if (-not (Test-Administrator)) {
    Write-Warning "این اسکریپت نیاز به دسترسی Administrator دارد!"
    Write-Info "لطفا PowerShell را به عنوان Administrator باز کنید و دوباره اجرا کنید."
    Write-Info "راه‌اندازی: کلیک راست روی PowerShell > Run as Administrator"
    pause
    exit 1
}

Write-Success "✓ دسترسی Administrator تایید شد!"
Write-Host ""

# 1. بررسی و نصب Python
Write-Info "=== بررسی Python ==="
$isPythonInstalled, $pythonVersion = Test-PythonInstalled
if ($isPythonInstalled) {
    Write-Success "✓ Python $pythonVersion نصب است!"
} else {
    Write-Warning "Python 3.11+ یافت نشد!"
    $installPython = Read-Host "آیا می‌خواهید Python را نصب کنید? (Y/N)"
    if ($installPython -eq "Y" -or $installPython -eq "y") {
        $pythonInstalled = Install-Python
        if (-not $pythonInstalled) {
            Write-Error "نصب Python ناموفق بود. لطفا به صورت دستی نصب کنید."
            pause
            exit 1
        }
    } else {
        Write-Error "نصب Python ضروری است!"
        pause
        exit 1
    }
}
Write-Host ""

# 2. بررسی و نصب Node.js
Write-Info "=== بررسی Node.js ==="
$isNodeInstalled, $nodeVersion = Test-NodeInstalled
if ($isNodeInstalled) {
    Write-Success "✓ Node.js $nodeVersion نصب است!"
} else {
    Write-Warning "Node.js 18+ یافت نشد!"
    $installNode = Read-Host "آیا می‌خواهید Node.js را نصب کنید? (Y/N)"
    if ($installNode -eq "Y" -or $installNode -eq "y") {
        $nodeInstalled = Install-Node
        if (-not $nodeInstalled) {
            Write-Error "نصب Node.js ناموفق بود. لطفا به صورت دستی نصب کنید."
            pause
            exit 1
        }
    } else {
        Write-Error "نصب Node.js ضروری است!"
        pause
        exit 1
    }
}
Write-Host ""

# 3. بررسی و راه‌اندازی Redis
Write-Info "=== بررسی Redis ==="
if (Test-RedisRunning) {
    Write-Success "✓ Redis در حال اجرا است!"
} else {
    Write-Warning "Redis در حال اجرا نیست!"
    $setupRedis = Read-Host "آیا می‌خواهید Redis را راه‌اندازی کنید? (Y/N)"
    if ($setupRedis -eq "Y" -or $setupRedis -eq "y") {
        Start-RedisDocker | Out-Null
        if (-not (Test-RedisRunning)) {
            Write-Warning "Redis راه‌اندازی نشد. این اختیاری است و برنامه بدون Redis هم کار می‌کند."
        }
    } else {
        Write-Warning "Redis راه‌اندازی نشد. این اختیاری است و برنامه بدون Redis هم کار می‌کند."
    }
}
Write-Host ""

# 4. نصب وابستگی‌های Python
Write-Info "=== نصب وابستگی‌های Python ==="
Install-PythonDependencies
Write-Host ""

# 5. نصب وابستگی‌های Node.js
Write-Info "=== نصب وابستگی‌های Node.js ==="
Install-NodeDependencies
Write-Host ""

# 6. تنظیم فایل .env
Write-Info "=== تنظیم فایل .env ==="
Setup-EnvironmentFile
Write-Host ""

# 7. اجرای migrations
Write-Info "=== اجرای Migrations ==="
Run-Migrations
Write-Host ""

# 8. ایجاد superuser
Write-Info "=== ایجاد Superuser ==="
Create-Superuser
Write-Host ""

# خلاصه
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  نصب و راه‌اندازی کامل شد!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Info "خلاصه:"
Write-Success "✓ Python نصب و آماده است"
Write-Success "✓ Node.js نصب و آماده است"
Write-Success "✓ وابستگی‌های Python نصب شدند"
Write-Success "✓ وابستگی‌های Node.js نصب شدند"
Write-Success "✓ فایل .env ایجاد شد"
Write-Success "✓ Migrations اجرا شد"
Write-Success "✓ Superuser ایجاد شد"
Write-Host ""
Write-Info "برای راه‌اندازی پروژه:"
Write-Info "1. Backend: cd backend && python manage.py runserver"
Write-Info "2. Frontend: cd frontend && npm run dev"
Write-Info "3. یا از فایل START_HERE.bat استفاده کنید"
Write-Host ""
Write-Info "اطلاعات ورود Admin Panel:"
Write-Info "  URL: http://localhost:8000/admin/"
Write-Info "  Username: admin"
Write-Info "  Password: admin"
Write-Host ""
Write-Warning "نکته مهم:"
Write-Warning "  - فایل .env را ویرایش کرده و API keys خود را اضافه کنید"
Write-Warning "  - اگر Redis نصب نیست، Celery کار نمی‌کند اما برنامه اصلی کار می‌کند"
Write-Host ""
pause

