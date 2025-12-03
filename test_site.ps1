# Smart AI Trading Strategy Optimizer - Site Test Script
# This script tests if all services are running correctly

$ErrorActionPreference = "Continue"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Smart AI Trading Strategy Optimizer" -ForegroundColor Cyan
Write-Host "  Site Health Check & Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allTestsPassed = $true

# ==========================================
# Test 1: Check Port 80
# ==========================================
Write-Host "[Test 1/8] Checking Port 80..." -ForegroundColor Yellow
try {
    $port80Check = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($port80Check) {
        Write-Host "  ✓ Port 80 is open" -ForegroundColor Green
        
        # Try to access the site
        try {
            $response = Invoke-WebRequest -Uri "http://localhost" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host "  ✓ Site is accessible on http://localhost" -ForegroundColor Green
            } else {
                Write-Host "  ⚠ Site returned status code: $($response.StatusCode)" -ForegroundColor Yellow
                $allTestsPassed = $false
            }
        } catch {
            Write-Host "  ✗ Cannot access site: $_" -ForegroundColor Red
            $allTestsPassed = $false
        }
    } else {
        Write-Host "  ✗ Port 80 is not open" -ForegroundColor Red
        Write-Host "  → Run start.ps1 to start services" -ForegroundColor Yellow
        $allTestsPassed = $false
    }
} catch {
    Write-Host "  ✗ Error checking port 80: $_" -ForegroundColor Red
    $allTestsPassed = $false
}

Write-Host ""

# ==========================================
# Test 2: Check Backend (Port 8000)
# ==========================================
Write-Host "[Test 2/8] Checking Backend (Port 8000)..." -ForegroundColor Yellow
try {
    $port8000Check = Test-NetConnection -ComputerName localhost -Port 8000 -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($port8000Check) {
        Write-Host "  ✓ Backend port 8000 is open" -ForegroundColor Green
        
        # Try to access backend API
        try {
            $apiResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/auth/check/" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            if ($apiResponse.StatusCode -eq 200) {
                Write-Host "  ✓ Backend API is responding" -ForegroundColor Green
            } else {
                Write-Host "  ⚠ Backend returned status code: $($apiResponse.StatusCode)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  ⚠ Backend API check failed: $_" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ✗ Backend port 8000 is not open" -ForegroundColor Red
        Write-Host "  → Backend may not be running" -ForegroundColor Yellow
        $allTestsPassed = $false
    }
} catch {
    Write-Host "  ✗ Error checking backend: $_" -ForegroundColor Red
    $allTestsPassed = $false
}

Write-Host ""

# ==========================================
# Test 3: Check Backend via Nginx Proxy
# ==========================================
Write-Host "[Test 3/8] Checking Backend via Nginx Proxy (/api)..." -ForegroundColor Yellow
try {
    $proxyResponse = Invoke-WebRequest -Uri "http://localhost/api/auth/check/" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    if ($proxyResponse.StatusCode -eq 200) {
        Write-Host "  ✓ Backend is accessible via Nginx proxy" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Proxy returned status code: $($proxyResponse.StatusCode)" -ForegroundColor Yellow
        $allTestsPassed = $false
    }
} catch {
    Write-Host "  ✗ Backend not accessible via proxy: $_" -ForegroundColor Red
    Write-Host "  → Check Nginx configuration" -ForegroundColor Yellow
    $allTestsPassed = $false
}

Write-Host ""

# ==========================================
# Test 4: Check Redis
# ==========================================
Write-Host "[Test 4/8] Checking Redis (Port 6379)..." -ForegroundColor Yellow
try {
    $redisCheck = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($redisCheck) {
        Write-Host "  ✓ Redis is running on port 6379" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Redis is not running" -ForegroundColor Yellow
        Write-Host "  → Some features may not work" -ForegroundColor Yellow
        Write-Host "  → Start Redis: docker start redis" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  ⚠ Error checking Redis: $_" -ForegroundColor Yellow
}

Write-Host ""

# ==========================================
# Test 5: Check Frontend Build
# ==========================================
Write-Host "[Test 5/8] Checking Frontend Build..." -ForegroundColor Yellow
$distPath = Join-Path $scriptPath "frontend\dist"
if (Test-Path $distPath) {
    $distFiles = Get-ChildItem $distPath -File -ErrorAction SilentlyContinue
    if ($distFiles.Count -gt 0) {
        Write-Host "  ✓ Frontend build exists ($($distFiles.Count) files)" -ForegroundColor Green
        
        # Check for index.html
        $indexPath = Join-Path $distPath "index.html"
        if (Test-Path $indexPath) {
            Write-Host "  ✓ index.html found" -ForegroundColor Green
        } else {
            Write-Host "  ✗ index.html not found" -ForegroundColor Red
            $allTestsPassed = $false
        }
    } else {
        Write-Host "  ✗ Frontend dist folder is empty" -ForegroundColor Red
        Write-Host "  → Run: cd frontend && npm run build" -ForegroundColor Yellow
        $allTestsPassed = $false
    }
} else {
    Write-Host "  ✗ Frontend dist folder not found" -ForegroundColor Red
    Write-Host "  → Run: cd frontend && npm run build" -ForegroundColor Yellow
    $allTestsPassed = $false
}

Write-Host ""

# ==========================================
# Test 6: Check Nginx Process
# ==========================================
Write-Host "[Test 6/8] Checking Nginx Process..." -ForegroundColor Yellow
$nginxProcesses = Get-Process -Name "nginx" -ErrorAction SilentlyContinue
if ($nginxProcesses) {
    Write-Host "  ✓ Nginx is running ($($nginxProcesses.Count) process(es))" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Nginx process not found" -ForegroundColor Yellow
    Write-Host "  → Frontend may be running directly (less secure)" -ForegroundColor Yellow
}

Write-Host ""

# ==========================================
# Test 7: Check Django Process
# ==========================================
Write-Host "[Test 7/8] Checking Django Process..." -ForegroundColor Yellow
$djangoProcesses = Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like "*manage.py*runserver*" }
if ($djangoProcesses) {
    Write-Host "  ✓ Django is running ($($djangoProcesses.Count) process(es))" -ForegroundColor Green
} else {
    Write-Host "  ✗ Django process not found" -ForegroundColor Red
    Write-Host "  → Backend may not be running" -ForegroundColor Yellow
    $allTestsPassed = $false
}

Write-Host ""

# ==========================================
# Test 8: Check Celery Processes
# ==========================================
Write-Host "[Test 8/8] Checking Celery Processes..." -ForegroundColor Yellow
$celeryProcesses = Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like "*celery*" }
if ($celeryProcesses) {
    $workerCount = ($celeryProcesses | Where-Object { $_.CommandLine -like "*worker*" }).Count
    $beatCount = ($celeryProcesses | Where-Object { $_.CommandLine -like "*beat*" }).Count
    Write-Host "  ✓ Celery is running" -ForegroundColor Green
    Write-Host "    - Workers: $workerCount" -ForegroundColor Gray
    Write-Host "    - Beat: $beatCount" -ForegroundColor Gray
} else {
    Write-Host "  ⚠ Celery processes not found" -ForegroundColor Yellow
    Write-Host "  → Background tasks may not work" -ForegroundColor Yellow
}

Write-Host ""

# ==========================================
# Final Summary
# ==========================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($allTestsPassed) {
    Write-Host "  ✓ All Critical Tests Passed!" -ForegroundColor Green
    Write-Host "  Site should be accessible at:" -ForegroundColor White
    Write-Host "    http://localhost" -ForegroundColor Cyan
    Write-Host "    http://191.101.113.163" -ForegroundColor Cyan
} else {
    Write-Host "  ✗ Some Tests Failed!" -ForegroundColor Red
    Write-Host "  Please check the errors above" -ForegroundColor Yellow
    Write-Host "  Try running: .\start.ps1" -ForegroundColor Cyan
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ==========================================
# Quick Fix Suggestions
# ==========================================
if (-not $allTestsPassed) {
    Write-Host "🔧 Quick Fix Suggestions:" -ForegroundColor Yellow
    Write-Host ""
    
    if (-not (Test-Path $distPath)) {
        Write-Host "  1. Build Frontend:" -ForegroundColor Cyan
        Write-Host "     cd frontend" -ForegroundColor Gray
        Write-Host "     npm run build" -ForegroundColor Gray
        Write-Host ""
    }
    
    if (-not $port8000Check) {
        Write-Host "  2. Start Backend:" -ForegroundColor Cyan
        Write-Host "     cd backend" -ForegroundColor Gray
        Write-Host "     python manage.py runserver 127.0.0.1:8000" -ForegroundColor Gray
        Write-Host ""
    }
    
    if (-not $port80Check) {
        Write-Host "  3. Check Port 80:" -ForegroundColor Cyan
        Write-Host "     netstat -ano | findstr :80" -ForegroundColor Gray
        Write-Host "     Stop any service using port 80" -ForegroundColor Gray
        Write-Host ""
    }
    
    Write-Host "  4. Or run the full start script:" -ForegroundColor Cyan
    Write-Host "     .\start.ps1" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "Press Enter to exit..."
Read-Host

