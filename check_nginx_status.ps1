# Quick Nginx Status Check Script
$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Nginx Status Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Nginx is installed
Write-Host "[1] Checking Nginx Installation..." -ForegroundColor Yellow
$nginxPaths = @(
    "C:\nginx\nginx.exe",
    "C:\nginx-1.28.0\nginx.exe",
    "C:\nginx-1.27.0\nginx.exe",
    "C:\nginx-1.26.0\nginx.exe",
    "C:\nginx-1.25.0\nginx.exe",
    "C:\nginx-1.24.0\nginx.exe"
)

$nginxFound = $false
$nginxPath = $null

foreach ($path in $nginxPaths) {
    if (Test-Path $path) {
        $nginxPath = $path
        $nginxFound = $true
        Write-Host "  ✓ Nginx found at: $path" -ForegroundColor Green
        break
    }
}

if (-not $nginxFound) {
    Write-Host "  ✗ Nginx is not installed" -ForegroundColor Red
    Write-Host "  → Run: .\install_nginx.ps1" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

Write-Host ""

# Check if Nginx is running
Write-Host "[2] Checking Nginx Process..." -ForegroundColor Yellow
$nginxProcesses = Get-Process -Name "nginx" -ErrorAction SilentlyContinue
if ($nginxProcesses) {
    Write-Host "  ✓ Nginx is running ($($nginxProcesses.Count) process(es))" -ForegroundColor Green
    $nginxProcesses | ForEach-Object {
        Write-Host "    - PID: $($_.Id), Started: $($_.StartTime)" -ForegroundColor Gray
    }
} else {
    Write-Host "  ✗ Nginx is not running" -ForegroundColor Red
    Write-Host "  → Run: .\start.ps1" -ForegroundColor Cyan
}

Write-Host ""

# Check port 80
Write-Host "[3] Checking Port 80..." -ForegroundColor Yellow
try {
    $port80Check = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($port80Check) {
        Write-Host "  ✓ Port 80 is open" -ForegroundColor Green
        
        # Try to access site
        try {
            $response = Invoke-WebRequest -Uri "http://localhost" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
            Write-Host "  ✓ Site is accessible (Status: $($response.StatusCode))" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠ Port 80 is open but site may not be responding: $_" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ✗ Port 80 is not open" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Error checking port 80: $_" -ForegroundColor Red
}

Write-Host ""

# Check Nginx configuration
Write-Host "[4] Checking Nginx Configuration..." -ForegroundColor Yellow
$nginxDir = Split-Path $nginxPath -Parent
$nginxConfPath = Join-Path $nginxDir "conf\nginx.conf"

if (Test-Path $nginxConfPath) {
    Write-Host "  ✓ Configuration file exists: $nginxConfPath" -ForegroundColor Green
    
    # Test configuration
    Set-Location $nginxDir
    $configTest = & $nginxPath -t 2>&1
    Set-Location $PSScriptRoot
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Configuration is valid" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Configuration has errors:" -ForegroundColor Red
        $configTest | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    }
} else {
    Write-Host "  ✗ Configuration file not found: $nginxConfPath" -ForegroundColor Red
    Write-Host "  -> Copy nginx_production.conf to $nginxConfPath" -ForegroundColor Cyan
}

Write-Host ""

# Check Nginx logs
Write-Host "[5] Checking Nginx Logs..." -ForegroundColor Yellow
$nginxLogsDir = Join-Path $nginxDir "logs"
if (Test-Path $nginxLogsDir) {
    Write-Host "  ✓ Logs directory exists: $nginxLogsDir" -ForegroundColor Green
    
    $errorLog = Join-Path $nginxLogsDir "error.log"
    $accessLog = Join-Path $nginxLogsDir "access.log"
    
    if (Test-Path $errorLog) {
        $errorLogSize = (Get-Item $errorLog).Length
        Write-Host "  ✓ Error log exists ($errorLogSize bytes)" -ForegroundColor Green
        
        # Show last 5 error lines if any
        $lastErrors = Get-Content $errorLog -Tail 5 -ErrorAction SilentlyContinue
        if ($lastErrors) {
            Write-Host "  Last errors:" -ForegroundColor Yellow
            $lastErrors | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        }
    } else {
        Write-Host "  ⚠ Error log not found" -ForegroundColor Yellow
    }
    
    if (Test-Path $accessLog) {
        $accessLogSize = (Get-Item $accessLog).Length
        Write-Host "  ✓ Access log exists ($accessLogSize bytes)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Access log not found" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✗ Logs directory not found: $nginxLogsDir" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

