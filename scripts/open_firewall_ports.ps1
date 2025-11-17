# Open Firewall Ports for Internet Access
# This script opens the required ports in Windows Firewall
# Usage: .\open_firewall_ports.ps1

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  باز کردن پورت‌های فایروال Windows" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️  این اسکریپت نیاز به دسترسی Administrator دارد!" -ForegroundColor Yellow
    Write-Host "   لطفاً PowerShell را به عنوان Administrator اجرا کنید." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   راست کلیک روی PowerShell -> Run as Administrator" -ForegroundColor Gray
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Load port configuration from .env file
$backendPort = "8000"
$frontendPort = "3000"

if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "(?m)^\s*PUBLIC_PORT\s*=\s*(.+)$") {
        $backendPort = $matches[1].Trim()
    }
    if ($envContent -match "(?m)^\s*FRONTEND_PUBLIC_PORT\s*=\s*(.+)$") {
        $frontendPort = $matches[1].Trim()
    }
}

Write-Host "در حال باز کردن پورت‌های زیر در فایروال:" -ForegroundColor Yellow
Write-Host "  Backend Port:  $backendPort" -ForegroundColor White
Write-Host "  Frontend Port: $frontendPort" -ForegroundColor White
Write-Host ""

# Function to add firewall rule
function Add-FirewallRule {
    param(
        [string]$Name,
        [int]$Port,
        [string]$Direction = "Inbound"
    )
    
    # Check if rule already exists
    $existingRule = Get-NetFirewallRule -DisplayName $Name -ErrorAction SilentlyContinue
    if ($existingRule) {
        Write-Host "  ℹ Rule '$Name' already exists. Skipping..." -ForegroundColor Gray
        return $true
    }
    
    try {
        # Create firewall rule
        New-NetFirewallRule -DisplayName $Name `
            -Direction $Direction `
            -LocalPort $Port `
            -Protocol TCP `
            -Action Allow `
            -Profile Any | Out-Null
        
        Write-Host "  ✓ Rule '$Name' created successfully" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "  ✗ Failed to create rule '$Name': $_" -ForegroundColor Red
        return $false
    }
}

# Add firewall rules
Write-Host "[1/2] ایجاد قوانین فایروال برای Backend..." -ForegroundColor Cyan
$backendSuccess = Add-FirewallRule -Name "Backend Port $backendPort" -Port $backendPort

Write-Host ""
Write-Host "[2/2] ایجاد قوانین فایروال برای Frontend..." -ForegroundColor Cyan
$frontendSuccess = Add-FirewallRule -Name "Frontend Port $frontendPort" -Port $frontendPort

Write-Host ""

if ($backendSuccess -and $frontendSuccess) {
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "  ✓ پورت‌ها با موفقیت باز شدند!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 خلاصه:" -ForegroundColor Yellow
    Write-Host "  ✓ Backend Port $backendPort: باز" -ForegroundColor Green
    Write-Host "  ✓ Frontend Port $frontendPort: باز" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  نکات مهم:" -ForegroundColor Yellow
    Write-Host "  - اگر از روتر استفاده می‌کنید، باید Port Forwarding را نیز تنظیم کنید" -ForegroundColor Gray
    Write-Host "  - برای امنیت بیشتر، می‌توانید فقط IP‌های خاصی را مجاز کنید" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host "  ✗ خطا در باز کردن پورت‌ها!" -ForegroundColor Red
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "لطفاً به صورت دستی پورت‌ها را باز کنید:" -ForegroundColor Yellow
    Write-Host "  netsh advfirewall firewall add rule name='Backend Port $backendPort' dir=in action=allow protocol=TCP localport=$backendPort" -ForegroundColor White
    Write-Host "  netsh advfirewall firewall add rule name='Frontend Port $frontendPort' dir=in action=allow protocol=TCP localport=$frontendPort" -ForegroundColor White
    Write-Host ""
}

Write-Host "Press Enter to exit..."
Read-Host



