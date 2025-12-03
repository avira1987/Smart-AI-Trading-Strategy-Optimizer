# اسکریپت به‌روزرسانی خودکار مسیرهای SSL در nginx_production.conf
# این اسکریپت بعد از نصب SSL با certbot اجرا می‌شود

$ErrorActionPreference = "Continue"

$DOMAIN = "myaibaz.ir"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$nginxConfPath = Join-Path $scriptPath "nginx_production.conf"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  به‌روزرسانی مسیرهای SSL در Nginx" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# پیدا کردن مسیر گواهینامه‌ها
$possibleCertPaths = @(
    "C:\certbot\conf\live\$DOMAIN\fullchain.pem",
    "C:\ProgramData\certbot\live\$DOMAIN\fullchain.pem",
    "C:\letsencrypt\live\$DOMAIN\fullchain.pem",
    "/etc/letsencrypt/live/$DOMAIN/fullchain.pem"  # برای WSL
)

$certPath = $null
$keyPath = $null

foreach ($path in $possibleCertPaths) {
    if (Test-Path $path) {
        $certPath = $path
        $keyPath = $path -replace "fullchain.pem", "privkey.pem"
        break
    }
}

# اگر در WSL است، بررسی مسیرهای Linux
if (-not $certPath) {
    try {
        $wslCertPath = wsl bash -c "if [ -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem ]; then echo '/etc/letsencrypt/live/$DOMAIN/fullchain.pem'; fi" 2>&1
        if ($wslCertPath -and (Test-Path $wslCertPath)) {
            $certPath = $wslCertPath
            $keyPath = $certPath -replace "fullchain.pem", "privkey.pem"
        }
    } catch {
        # Ignore
    }
}

if (-not $certPath -or -not (Test-Path $certPath)) {
    Write-Host "❌ مسیر گواهینامه SSL پیدا نشد" -ForegroundColor Red
    Write-Host ""
    Write-Host "لطفاً مسیر گواهینامه را به صورت دستی وارد کنید:" -ForegroundColor Yellow
    $certPath = Read-Host "مسیر fullchain.pem (مثال: C:\certbot\conf\live\myaibaz.ir\fullchain.pem)"
    $keyPath = Read-Host "مسیر privkey.pem (مثال: C:\certbot\conf\live\myaibaz.ir\privkey.pem)"
    
    if (-not (Test-Path $certPath) -or -not (Test-Path $keyPath)) {
        Write-Host "❌ مسیرهای وارد شده معتبر نیستند" -ForegroundColor Red
        exit 1
    }
}

# تبدیل مسیر به فرمت Windows (اگر از WSL است)
if ($certPath -match "^/etc/letsencrypt") {
    # تبدیل مسیر Linux به Windows (برای WSL)
    $wslPath = $certPath
    $certPath = "C:\wsl$\Ubuntu\etc\letsencrypt\live\$DOMAIN\fullchain.pem"
    $keyPath = "C:\wsl$\Ubuntu\etc\letsencrypt\live\$DOMAIN\privkey.pem"
    
    # یا استفاده از مسیر نسبی در nginx که از WSL اجرا می‌شود
    Write-Host "⚠️  استفاده از مسیر WSL. لطفاً مطمئن شوید که Nginx از WSL اجرا می‌شود" -ForegroundColor Yellow
    $certPath = $wslPath
    $keyPath = $wslPath -replace "fullchain.pem", "privkey.pem"
}

# تبدیل backslash به forward slash برای nginx (در Windows)
$certPathNginx = $certPath -replace "\\", "/"
$keyPathNginx = $keyPath -replace "\\", "/"

Write-Host "✓ مسیر گواهینامه پیدا شد:" -ForegroundColor Green
Write-Host "   Certificate: $certPath" -ForegroundColor Gray
Write-Host "   Private Key: $keyPath" -ForegroundColor Gray
Write-Host ""

# خواندن فایل nginx_production.conf
if (-not (Test-Path $nginxConfPath)) {
    Write-Host "❌ فایل nginx_production.conf پیدا نشد: $nginxConfPath" -ForegroundColor Red
    exit 1
}

$nginxContent = Get-Content $nginxConfPath -Raw

# فعال کردن بخش HTTPS (uncomment)
$nginxContent = $nginxContent -replace "# HTTPS server - برای فعال‌سازی، این بخش را uncomment کنید و مسیر گواهینامه‌ها را تنظیم کنید", "HTTPS server - فعال شده با certbot"
$nginxContent = $nginxContent -replace "# server \{", "server {"
$nginxContent = $nginxContent -replace "#     listen 443 ssl;", "    listen 443 ssl;"
$nginxContent = $nginxContent -replace "#     http2 on;", "    http2 on;"
$nginxContent = $nginxContent -replace "#     server_name myaibaz.ir www.myaibaz.ir;", "    server_name myaibaz.ir www.myaibaz.ir;"

# به‌روزرسانی مسیرهای SSL
$nginxContent = $nginxContent -replace "#     # SSL certificate paths - مسیر گواهینامه‌های SSL خود را تنظیم کنید", "    # SSL certificate paths - تنظیم شده با certbot"
$nginxContent = $nginxContent -replace "#     # ssl_certificate C:/certbot/conf/live/myaibaz.ir/fullchain.pem;", "    ssl_certificate $certPathNginx;"
$nginxContent = $nginxContent -replace "#     # ssl_certificate_key C:/certbot/conf/live/myaibaz.ir/privkey.pem;", "    ssl_certificate_key $keyPathNginx;"

# Uncomment سایر خطوط SSL
$nginxContent = $nginxContent -replace "#     # SSL configuration for security", "    # SSL configuration for security"
$nginxContent = $nginxContent -replace "#     ssl_protocols TLSv1.2 TLSv1.3;", "    ssl_protocols TLSv1.2 TLSv1.3;"
$nginxContent = $nginxContent -replace "#     ssl_ciphers HIGH:!aNULL:!MD5;", "    ssl_ciphers HIGH:!aNULL:!MD5;"
$nginxContent = $nginxContent -replace "#     ssl_prefer_server_ciphers on;", "    ssl_prefer_server_ciphers on;"
$nginxContent = $nginxContent -replace "#     ssl_session_cache shared:SSL:10m;", "    ssl_session_cache shared:SSL:10m;"
$nginxContent = $nginxContent -replace "#     ssl_session_timeout 10m;", "    ssl_session_timeout 10m;"

# Uncomment سایر بخش‌ها
$nginxContent = $nginxContent -replace "#     # افزایش buffer size", "    # افزایش buffer size"
$nginxContent = $nginxContent -replace "#     client_max_body_size 100M;", "    client_max_body_size 100M;"
$nginxContent = $nginxContent -replace "#     # Security headers", "    # Security headers"
$nginxContent = $nginxContent -replace "#     add_header X-Frame-Options", "    add_header X-Frame-Options"
$nginxContent = $nginxContent -replace "#     add_header X-Content-Type-Options", "    add_header X-Content-Type-Options"
$nginxContent = $nginxContent -replace "#     add_header X-XSS-Protection", "    add_header X-XSS-Protection"
$nginxContent = $nginxContent -replace "#     add_header Referrer-Policy", "    add_header Referrer-Policy"
$nginxContent = $nginxContent -replace "#     add_header Strict-Transport-Security", "    add_header Strict-Transport-Security"

# Uncomment location blocks
$nginxContent = $nginxContent -replace "#     # Robots.txt", "    # Robots.txt"
$nginxContent = $nginxContent -replace "#     location = /robots.txt \{", "    location = /robots.txt {"
$nginxContent = $nginxContent -replace "#         root html;", "        root html;"
$nginxContent = $nginxContent -replace "#         try_files", "        try_files"
$nginxContent = $nginxContent -replace "#         access_log", "        access_log"
$nginxContent = $nginxContent -replace "#         log_not_found", "        log_not_found"
$nginxContent = $nginxContent -replace "#         expires", "        expires"
$nginxContent = $nginxContent -replace "#         add_header Cache-Control", "        add_header Cache-Control"
$nginxContent = $nginxContent -replace "#     \}", "    }"

# Uncomment sitemap
$nginxContent = $nginxContent -replace "#     location = /sitemap.xml \{", "    location = /sitemap.xml {"
$nginxContent = $nginxContent -replace "#         add_header Content-Type", "        add_header Content-Type"

# Uncomment Frontend
$nginxContent = $nginxContent -replace "#     # Frontend - React App", "    # Frontend - React App"
$nginxContent = $nginxContent -replace "#     location / \{", "    location / {"
$nginxContent = $nginxContent -replace "#         root html;", "        root html;"
$nginxContent = $nginxContent -replace "#         index index.html;", "        index index.html;"
$nginxContent = $nginxContent -replace "#         try_files", "        try_files"
$nginxContent = $nginxContent -replace "#         add_header Cache-Control", "        add_header Cache-Control"
$nginxContent = $nginxContent -replace "#         add_header X-Robots-Tag", "        add_header X-Robots-Tag"

# Uncomment Backend API
$nginxContent = $nginxContent -replace "#     # Backend API proxy", "    # Backend API proxy"
$nginxContent = $nginxContent -replace "#     location /api/ \{", "    location /api/ {"
$nginxContent = $nginxContent -replace "#         proxy_pass", "        proxy_pass"
$nginxContent = $nginxContent -replace "#         proxy_set_header Host", "        proxy_set_header Host"
$nginxContent = $nginxContent -replace "#         proxy_set_header X-Real-IP", "        proxy_set_header X-Real-IP"
$nginxContent = $nginxContent -replace "#         proxy_set_header X-Forwarded-For", "        proxy_set_header X-Forwarded-For"
$nginxContent = $nginxContent -replace "#         proxy_set_header X-Forwarded-Proto https;", "        proxy_set_header X-Forwarded-Proto https;"
$nginxContent = $nginxContent -replace "#         proxy_set_header X-Forwarded-Host", "        proxy_set_header X-Forwarded-Host"
$nginxContent = $nginxContent -replace "#         proxy_next_upstream", "        proxy_next_upstream"
$nginxContent = $nginxContent -replace "#         add_header 'Access-Control-Allow-Origin'", "        add_header 'Access-Control-Allow-Origin'"
$nginxContent = $nginxContent -replace "#         if \(\$request_method = 'OPTIONS'\) \{", "        if (`$request_method = 'OPTIONS') {"
$nginxContent = $nginxContent -replace "#             add_header 'Access-Control-Allow-Origin'", "            add_header 'Access-Control-Allow-Origin'"
$nginxContent = $nginxContent -replace "#             add_header 'Access-Control-Allow-Credentials'", "            add_header 'Access-Control-Allow-Credentials'"
$nginxContent = $nginxContent -replace "#             add_header 'Access-Control-Allow-Methods'", "            add_header 'Access-Control-Allow-Methods'"
$nginxContent = $nginxContent -replace "#             add_header 'Access-Control-Allow-Headers'", "            add_header 'Access-Control-Allow-Headers'"
$nginxContent = $nginxContent -replace "#             add_header 'Access-Control-Max-Age'", "            add_header 'Access-Control-Max-Age'"
$nginxContent = $nginxContent -replace "#             add_header 'Content-Type'", "            add_header 'Content-Type'"
$nginxContent = $nginxContent -replace "#             add_header 'Content-Length'", "            add_header 'Content-Length'"
$nginxContent = $nginxContent -replace "#             return 204;", "            return 204;"
$nginxContent = $nginxContent -replace "#         \}", "        }"
$nginxContent = $nginxContent -replace "#         proxy_connect_timeout", "        proxy_connect_timeout"
$nginxContent = $nginxContent -replace "#         proxy_send_timeout", "        proxy_send_timeout"
$nginxContent = $nginxContent -replace "#         proxy_read_timeout", "        proxy_read_timeout"
$nginxContent = $nginxContent -replace "#         proxy_buffering", "        proxy_buffering"
$nginxContent = $nginxContent -replace "#         proxy_request_buffering", "        proxy_request_buffering"
$nginxContent = $nginxContent -replace "#         add_header X-Robots-Tag", "        add_header X-Robots-Tag"
$nginxContent = $nginxContent -replace "#         proxy_intercept_errors", "        proxy_intercept_errors"
$nginxContent = $nginxContent -replace "#         access_log", "        access_log"
$nginxContent = $nginxContent -replace "#         error_log", "        error_log"

# Uncomment Admin panel
$nginxContent = $nginxContent -replace "#     # Admin panel", "    # Admin panel"
$nginxContent = $nginxContent -replace "#     location /admin/ \{", "    location /admin/ {"

# Uncomment Static files
$nginxContent = $nginxContent -replace "#     # Static files", "    # Static files"
$nginxContent = $nginxContent -replace "#     location /static/ \{", "    location /static/ {"

# Uncomment Media files
$nginxContent = $nginxContent -replace "#     # Media files", "    # Media files"
$nginxContent = $nginxContent -replace "#     location /media/ \{", "    location /media/ {"

# Uncomment Health check
$nginxContent = $nginxContent -replace "#     # Health check endpoint", "    # Health check endpoint"
$nginxContent = $nginxContent -replace "#     location /health \{", "    location /health {"
$nginxContent = $nginxContent -replace "#         access_log off;", "        access_log off;"
$nginxContent = $nginxContent -replace "#         return 200", "        return 200"
$nginxContent = $nginxContent -replace "#         add_header Content-Type", "        add_header Content-Type"
$nginxContent = $nginxContent -replace "#     \}", "    }"

# بستن server block
$nginxContent = $nginxContent -replace "# \}", "}"

# فعال کردن redirect HTTP به HTTPS در بخش HTTP
$nginxContent = $nginxContent -replace "# اگر HTTPS فعال باشد، این خط را uncomment کنید:", "# Redirect HTTP to HTTPS"
$nginxContent = $nginxContent -replace "# return 301 https://\$server_name\$request_uri;", "    return 301 https://`$server_name`$request_uri;"

# ذخیره فایل
Write-Host "💾 در حال ذخیره فایل nginx_production.conf..." -ForegroundColor Cyan
$nginxContent | Set-Content $nginxConfPath -Encoding UTF8

Write-Host "✓ فایل nginx_production.conf به‌روزرسانی شد" -ForegroundColor Green
Write-Host ""

# کپی فایل به مسیر nginx
Write-Host "📋 در حال کپی فایل به مسیر Nginx..." -ForegroundColor Cyan

$possibleNginxPaths = @(
    "C:\nginx\nginx.exe",
    "C:\nginx-1.28.0\nginx.exe",
    "C:\nginx-1.27.0\nginx.exe"
)

$nginxPath = $null
foreach ($path in $possibleNginxPaths) {
    if (Test-Path $path) {
        $nginxPath = $path
        break
    }
}

if ($nginxPath) {
    $nginxDir = Split-Path $nginxPath -Parent
    $nginxConfDir = Join-Path $nginxDir "conf"
    $targetConfPath = Join-Path $nginxConfDir "nginx.conf"
    
    if (Test-Path $nginxConfDir) {
        Copy-Item -Path $nginxConfPath -Destination $targetConfPath -Force
        Write-Host "✓ فایل به $targetConfPath کپی شد" -ForegroundColor Green
        Write-Host ""
        
        # تست پیکربندی
        Write-Host "🔍 تست پیکربندی Nginx..." -ForegroundColor Cyan
        Set-Location $nginxDir
        $configTest = & $nginxPath -t 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ پیکربندی Nginx معتبر است" -ForegroundColor Green
            Write-Host ""
            Write-Host "✅ همه چیز آماده است!" -ForegroundColor Green
            Write-Host "   برای اعمال تغییرات، Nginx را راه‌اندازی مجدد کنید" -ForegroundColor Yellow
        } else {
            Write-Host "❌ خطا در پیکربندی Nginx:" -ForegroundColor Red
            $configTest | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
        }
    } else {
        Write-Host "⚠️  پوشه conf در Nginx پیدا نشد" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Nginx پیدا نشد. لطفاً به صورت دستی فایل را کپی کنید" -ForegroundColor Yellow
}

Write-Host ""

