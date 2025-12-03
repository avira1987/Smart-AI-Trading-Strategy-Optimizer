# Script to install and configure Nginx for Smart AI Trading Strategy Optimizer

$ErrorActionPreference = "Continue"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Nginx Installation Script" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if Nginx is already installed
$nginxPath = "C:\nginx\nginx.exe"
if (Test-Path $nginxPath) {
    Write-Host "✓ Nginx is already installed at: $nginxPath" -ForegroundColor Green
    Write-Host ""
    exit 0
}

Write-Host "[1/4] Checking for Nginx download..." -ForegroundColor Cyan

# Nginx download URL (Windows version)
$nginxUrl = "http://nginx.org/download/nginx-1.24.0.zip"
$downloadPath = Join-Path $env:TEMP "nginx.zip"
$extractPath = "C:\nginx"

Write-Host "  Download URL: $nginxUrl" -ForegroundColor Gray
Write-Host "  Download path: $downloadPath" -ForegroundColor Gray
Write-Host "  Extract path: $extractPath" -ForegroundColor Gray
Write-Host ""

# Check if C:\nginx already exists
if (Test-Path $extractPath) {
    Write-Host "  ⚠ C:\nginx already exists" -ForegroundColor Yellow
    $response = Read-Host "  Do you want to remove it and reinstall? (y/n)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Remove-Item -Path $extractPath -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ Removed existing directory" -ForegroundColor Green
    } else {
        Write-Host "  Installation cancelled" -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "[2/4] Downloading Nginx..." -ForegroundColor Cyan
try {
    Write-Host "  Please wait, downloading Nginx..." -ForegroundColor Gray
    Invoke-WebRequest -Uri $nginxUrl -OutFile $downloadPath -UseBasicParsing
    Write-Host "  ✓ Download completed" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Download failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Please download Nginx manually:" -ForegroundColor Yellow
    Write-Host "  1. Go to: http://nginx.org/en/download.html" -ForegroundColor Gray
    Write-Host "  2. Download nginx/Windows version" -ForegroundColor Gray
    Write-Host "  3. Extract to C:\nginx" -ForegroundColor Gray
    Write-Host "  4. Run this script again" -ForegroundColor Gray
    exit 1
}

Write-Host ""
Write-Host "[3/4] Extracting Nginx..." -ForegroundColor Cyan
try {
    # Create extract directory
    New-Item -ItemType Directory -Path $extractPath -Force | Out-Null
    
    # Extract zip file
    Expand-Archive -Path $downloadPath -DestinationPath $extractPath -Force
    Write-Host "  ✓ Extraction completed" -ForegroundColor Green
    
    # Move files from nginx-1.24.0 to nginx root if needed
    $versionedPath = Join-Path $extractPath "nginx-1.24.0"
    if (Test-Path $versionedPath) {
        Write-Host "  Moving files to root..." -ForegroundColor Gray
        Get-ChildItem -Path $versionedPath | Move-Item -Destination $extractPath -Force
        Remove-Item -Path $versionedPath -Force -ErrorAction SilentlyContinue
    }
} catch {
    Write-Host "  ✗ Extraction failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[4/4] Configuring Nginx..." -ForegroundColor Cyan

# Create conf directory if it doesn't exist
$confDir = Join-Path $extractPath "conf"
if (-not (Test-Path $confDir)) {
    New-Item -ItemType Directory -Path $confDir -Force | Out-Null
    Write-Host "  ✓ Created conf directory" -ForegroundColor Green
}

# Create html directory if it doesn't exist
$htmlDir = Join-Path $extractPath "html"
if (-not (Test-Path $htmlDir)) {
    New-Item -ItemType Directory -Path $htmlDir -Force | Out-Null
    Write-Host "  ✓ Created html directory" -ForegroundColor Green
}

# Copy nginx configuration
$nginxConfPath = Join-Path $scriptPath "nginx_production.conf"
$targetConfPath = Join-Path $confDir "nginx.conf"

if (Test-Path $nginxConfPath) {
    Copy-Item -Path $nginxConfPath -Destination $targetConfPath -Force
    Write-Host "  ✓ Configuration file copied" -ForegroundColor Green
} else {
    Write-Host "  ⚠ nginx_production.conf not found, using default" -ForegroundColor Yellow
}

# Clean up download file
Remove-Item -Path $downloadPath -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ Nginx installation completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Nginx is installed at: $extractPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run .\start.ps1 to start all services" -ForegroundColor Gray
Write-Host "  2. Nginx will be used as reverse proxy" -ForegroundColor Gray
Write-Host ""

