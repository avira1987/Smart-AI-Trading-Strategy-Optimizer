# ============================================
# تست دسترسی به وب‌سایت Production
# ============================================

Write-Host "=== تست دسترسی به وب‌سایت ===" -ForegroundColor Cyan
Write-Host ""

# دریافت IP آدرس
$ipAddresses = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
    $_.IPAddress -notlike "127.*" -and 
    $_.IPAddress -notlike "169.254.*"
} | Select-Object -First 1
$serverIP = $ipAddresses.IPAddress

# تست 1: پورت 80
Write-Host "1. تست پورت 80..." -ForegroundColor Yellow
$port80 = Get-NetTCPConnection -LocalPort 80 -ErrorAction SilentlyContinue
if ($port80) {
    Write-Host "   ✅ پورت 80 در حال استفاده است" -ForegroundColor Green
} else {
    Write-Host "   ❌ پورت 80 آزاد است (وب‌سایت در حال اجرا نیست)" -ForegroundColor Red
}

# تست 2: Health check
Write-Host "`n2. تست Health Check..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "   ✅ Health Check: OK (Status: $($response.StatusCode))" -ForegroundColor Green
    Write-Host "   Response: $($response.Content)" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Health Check: FAILED" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# تست 3: Frontend
Write-Host "`n3. تست Frontend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost" -UseBasicParsing -TimeoutSec 10
    if ($response.Content -match "root" -or $response.Content -match "html") {
        Write-Host "   ✅ Frontend: OK (Status: $($response.StatusCode))" -ForegroundColor Green
        Write-Host "   Content Length: $($response.Content.Length) bytes" -ForegroundColor Gray
    } else {
        Write-Host "   ⚠️  Frontend: پاسخ غیرمنتظره" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Frontend: FAILED" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# تست 4: Backend API
Write-Host "`n4. تست Backend API..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost/api/" -UseBasicParsing -TimeoutSec 10
    Write-Host "   ✅ Backend API: OK (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 404 -or $statusCode -eq 403) {
        Write-Host "   ⚠️  Backend API: ممکن است نیاز به احراز هویت داشته باشد (Status: $statusCode)" -ForegroundColor Yellow
    } else {
        Write-Host "   ❌ Backend API: FAILED (Status: $statusCode)" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# تست 5: دسترسی با IP
Write-Host "`n5. تست دسترسی با IP ($serverIP)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://$serverIP" -UseBasicParsing -TimeoutSec 10
    Write-Host "   ✅ دسترسی با IP: OK (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  دسترسی با IP: ممکن است از خارج سرور قابل دسترسی نباشد" -ForegroundColor Yellow
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# تست 6: Docker Containers
Write-Host "`n6. بررسی Docker Containers..." -ForegroundColor Yellow
try {
    $containersOutput = docker-compose ps --format json 2>&1
    if ($LASTEXITCODE -eq 0 -and $containersOutput) {
        $containers = $containersOutput | ConvertFrom-Json
        $running = $containers | Where-Object { $_.State -eq "running" }
        $total = $containers.Count

        Write-Host "   Containers در حال اجرا: $($running.Count)/$total" -ForegroundColor Cyan
        foreach ($container in $containers) {
            $status = if ($container.State -eq "running") { "✅" } else { "❌" }
            Write-Host "   $status $($container.Service): $($container.State)" -ForegroundColor $(if ($container.State -eq "running") { "Green" } else { "Red" })
        }
    } else {
        Write-Host "   ⚠️  نتوانست وضعیت containers را بررسی کند" -ForegroundColor Yellow
        Write-Host "   خروجی: $containersOutput" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ⚠️  خطا در بررسی containers: $_" -ForegroundColor Yellow
}

# تست 7: بررسی فایروال
Write-Host "`n7. بررسی فایروال..." -ForegroundColor Yellow
$firewallRule = Get-NetFirewallRule -DisplayName "Allow HTTP Port 80" -ErrorAction SilentlyContinue
if ($firewallRule) {
    Write-Host "   ✅ قانون فایروال برای پورت 80 موجود است" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  قانون فایروال برای پورت 80 پیدا نشد" -ForegroundColor Yellow
    Write-Host "   ممکن است نیاز به ایجاد قانون فایروال داشته باشید" -ForegroundColor Gray
}

Write-Host "`n=== تست کامل شد ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 آدرس‌های دسترسی:" -ForegroundColor Yellow
Write-Host "   http://localhost" -ForegroundColor White
Write-Host "   http://$serverIP" -ForegroundColor White
Write-Host ""
Write-Host "📋 در صورت بروز مشکل:" -ForegroundColor Cyan
Write-Host "   - لاگ‌ها: docker-compose logs -f" -ForegroundColor White
Write-Host "   - وضعیت: docker-compose ps" -ForegroundColor White
Write-Host "   - راه‌اندازی مجدد: docker-compose restart" -ForegroundColor White
Write-Host ""

