# Setup Public IP for Internet Access
# This script configures your application to be accessible from the internet
# Usage: .\setup_public_ip.ps1

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  تنظیم IP عمومی برای دسترسی از اینترنت" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
$envFile = ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "فایل .env یافت نشد. در حال ایجاد از env.example..." -ForegroundColor Yellow
    if (Test-Path "env.example") {
        Copy-Item "env.example" $envFile
        Write-Host "✓ فایل .env ایجاد شد" -ForegroundColor Green
    } else {
        Write-Host "✗ فایل env.example یافت نشد!" -ForegroundColor Red
        exit 1
    }
}

# Function to validate IP address
function Test-IPAddress {
    param([string]$IP)
    $IP -match '^(\d{1,3}\.){3}\d{1,3}$' -and ($IP -split '\.' | ForEach-Object { [int]$_ -ge 0 -and [int]$_ -le 255 }) -notcontains $false
}

# Try to detect public IP automatically
Write-Host "[1/4] تشخیص خودکار IP عمومی..." -ForegroundColor Yellow
$detectedPublicIP = $null
try {
    # Try multiple services to get public IP
    $services = @(
        "https://api.ipify.org",
        "https://icanhazip.com",
        "https://ifconfig.me/ip",
        "https://ipecho.net/plain"
    )
    
    foreach ($service in $services) {
        try {
            $response = Invoke-WebRequest -Uri $service -TimeoutSec 5 -UseBasicParsing
            $detectedPublicIP = $response.Content.Trim()
            if (Test-IPAddress $detectedPublicIP) {
                Write-Host "  ✓ IP عمومی تشخیص داده شد: $detectedPublicIP" -ForegroundColor Green
                break
            }
        } catch {
            continue
        }
    }
} catch {
    Write-Host "  ⚠ تشخیص خودکار IP ناموفق بود" -ForegroundColor Yellow
}

Write-Host ""

# Get public IP from user
Write-Host "[2/4] وارد کردن IP عمومی:" -ForegroundColor Yellow
if ($detectedPublicIP) {
    Write-Host "  IP تشخیص داده شده: $detectedPublicIP" -ForegroundColor Cyan
    $useDetected = Read-Host "  آیا از این IP استفاده کنید؟ (Y/n)"
    if ($useDetected -eq "" -or $useDetected -eq "Y" -or $useDetected -eq "y") {
        $publicIP = $detectedPublicIP
    } else {
        $publicIP = Read-Host "  لطفاً IP عمومی خود را وارد کنید (یا Enter برای خالی گذاشتن)"
    }
} else {
    Write-Host "  برای دسترسی از اینترنت، IP عمومی سرور خود را وارد کنید." -ForegroundColor Cyan
    Write-Host "  اگر فقط می‌خواهید از شبکه محلی دسترسی داشته باشید، Enter را بزنید." -ForegroundColor Gray
    $publicIP = Read-Host "  IP عمومی (یا Enter برای خالی گذاشتن)"
}

# Validate IP if provided
if ($publicIP -and $publicIP -ne "") {
    if (-not (Test-IPAddress $publicIP)) {
        Write-Host "  ✗ IP وارد شده معتبر نیست!" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Get ports
$defaultBackendPort = "8000"
$defaultFrontendPort = if ($publicIP -and $publicIP -ne "") { "80" } else { "3000" }

Write-Host "[3/4] تنظیم پورت‌ها:" -ForegroundColor Yellow
if ($publicIP -and $publicIP -ne "") {
    Write-Host "  توصیه می‌شود برای دسترسی اینترنتی Frontend روی پورت 80 باشد." -ForegroundColor Gray
}

$backendPortInput = Read-Host "  پورت Backend (پیش‌فرض: $defaultBackendPort)"
if ([string]::IsNullOrWhiteSpace($backendPortInput)) {
    $backendPort = $defaultBackendPort
} else {
    $backendPort = $backendPortInput
}

$frontendPortInput = Read-Host "  پورت Frontend (پیش‌فرض: $defaultFrontendPort)"
if ([string]::IsNullOrWhiteSpace($frontendPortInput)) {
    $frontendPort = $defaultFrontendPort
} else {
    $frontendPort = $frontendPortInput
}

Write-Host ""

# Update .env file
Write-Host "[4/4] به‌روزرسانی فایل .env..." -ForegroundColor Yellow

# Read existing .env file
$envContent = Get-Content $envFile -Raw

# Function to update or add environment variable
function Update-EnvVariable {
    param([string]$Name, [string]$Value)
    
    $pattern = "(?m)^\s*${Name}\s*=(.*)$"
    if ($envContent -match $pattern) {
        # Replace existing value
        $envContent = $envContent -replace $pattern, "${Name}=${Value}"
    } else {
        # Add new variable
        if (-not $envContent.EndsWith("`n") -and -not $envContent.EndsWith("`r`n")) {
            $envContent += "`n"
        }
        $envContent += "${Name}=${Value}`n"
    }
}

# Update PUBLIC_IP
if ($publicIP -and $publicIP -ne "") {
    Update-EnvVariable "PUBLIC_IP" $publicIP
    Update-EnvVariable "PUBLIC_PORT" $backendPort
    Update-EnvVariable "FRONTEND_PUBLIC_PORT" $frontendPort
    Update-EnvVariable "FRONTEND_URL" "http://${publicIP}:${frontendPort}"
    Update-EnvVariable "BACKEND_URL" "http://${publicIP}:${backendPort}"
    
    # Also update ALLOWED_HOSTS to include public IP
    $allowedHostsPattern = "(?m)^\s*ALLOWED_HOSTS\s*=(.*)$"
    if ($envContent -match $allowedHostsPattern) {
        $currentHosts = $matches[1].Trim()
        if ($currentHosts -notmatch $publicIP) {
            $newHosts = if ($currentHosts -eq "*") { "localhost,127.0.0.1,${publicIP}" } else { "${currentHosts},${publicIP}" }
            $envContent = $envContent -replace $allowedHostsPattern, "ALLOWED_HOSTS=${newHosts}"
        }
    }
    
    Write-Host "  ✓ IP عمومی تنظیم شد: $publicIP" -ForegroundColor Green
    Write-Host "  ✓ پورت Backend: $backendPort" -ForegroundColor Green
    Write-Host "  ✓ پورت Frontend: $frontendPort" -ForegroundColor Green
} else {
    Update-EnvVariable "PUBLIC_IP" ""
    Write-Host "  ✓ IP عمومی پاک شد (فقط دسترسی محلی)" -ForegroundColor Green
}

# Write updated content back to .env file
$envContent | Set-Content $envFile -NoNewline

Write-Host ""

# Create/update frontend .env file
Write-Host "[5/5] تنظیم Frontend..." -ForegroundColor Yellow
$frontendEnvFile = "frontend\.env"
$frontendEnvContent = ""

if ($publicIP -and $publicIP -ne "") {
    $frontendEnvContent = @"
# Backend URL for frontend
VITE_BACKEND_URL=http://${publicIP}:${backendPort}
VITE_FRONTEND_PORT=${frontendPort}
"@
} else {
    $frontendEnvContent = @"
# Backend URL for frontend
VITE_BACKEND_URL=http://localhost:${backendPort}
VITE_FRONTEND_PORT=${frontendPort}
"@
}

# Create frontend directory if it doesn't exist
if (-not (Test-Path "frontend")) {
    New-Item -ItemType Directory -Path "frontend" | Out-Null
}

$frontendEnvContent | Set-Content $frontendEnvFile
Write-Host "  ✓ فایل frontend\.env به‌روزرسانی شد" -ForegroundColor Green

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  تنظیمات کامل شد!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

if ($publicIP -and $publicIP -ne "") {
    Write-Host "📋 خلاصه تنظیمات:" -ForegroundColor Yellow
    Write-Host "  IP عمومی: $publicIP" -ForegroundColor White
    Write-Host "  Backend URL: http://${publicIP}:${backendPort}" -ForegroundColor White
    Write-Host "  Frontend URL: http://${publicIP}:${frontendPort}" -ForegroundColor White
    Write-Host ""
    Write-Host "⚠️  نکات مهم:" -ForegroundColor Yellow
    Write-Host "  1. مطمئن شوید که فایروال Windows پورت‌های $backendPort و $frontendPort را باز کرده است" -ForegroundColor Gray
    Write-Host "  2. اگر از روتر استفاده می‌کنید، Port Forwarding را برای پورت‌های $backendPort و $frontendPort تنظیم کنید" -ForegroundColor Gray
    Write-Host "  3. اگر IP عمومی شما تغییر می‌کند (Dynamic IP)، باید بعد از هر تغییر این اسکریپت را دوباره اجرا کنید" -ForegroundColor Gray
    Write-Host "  4. برای امنیت بیشتر، استفاده از HTTPS و فایروال را در نظر بگیرید" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🔧 برای باز کردن پورت‌ها در فایروال Windows:" -ForegroundColor Cyan
    Write-Host "  netsh advfirewall firewall add rule name='Backend Port $backendPort' dir=in action=allow protocol=TCP localport=$backendPort" -ForegroundColor White
    Write-Host "  netsh advfirewall firewall add rule name='Frontend Port $frontendPort' dir=in action=allow protocol=TCP localport=$frontendPort" -ForegroundColor White
} else {
    Write-Host "ℹ️  برنامه فقط از شبکه محلی قابل دسترسی است" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "برای راه‌اندازی برنامه:" -ForegroundColor Yellow
Write-Host "  .\START_ALL.ps1" -ForegroundColor White
Write-Host ""



