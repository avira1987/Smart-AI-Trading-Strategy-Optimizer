# Test SMS and Google OAuth on specific IP
# Usage: .\test_on_ip.ps1

$BACKEND_IP = "192.168.100.9"
$BACKEND_PORT = "8000"
$BACKEND_URL = "http://${BACKEND_IP}:${BACKEND_PORT}"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  تست Backend روی IP: $BACKEND_IP:$BACKEND_PORT" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Backend Status
Write-Host "[1/3] تست وضعیت Backend..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "${BACKEND_URL}/api/test/backend-status/" -Method GET -ContentType "application/json"
    Write-Host "  ✓ Backend در حال اجرا است" -ForegroundColor Green
    Write-Host "  Hostname: $($response.config.hostname)" -ForegroundColor Gray
    Write-Host "  Local IP: $($response.config.local_ip)" -ForegroundColor Gray
    Write-Host "  Network IPs: $($response.config.network_ips -join ', ')" -ForegroundColor Gray
    Write-Host "  Google Client ID: $($response.config.google_client_id_configured)" -ForegroundColor $(if ($response.config.google_client_id_configured) { "Green" } else { "Red" })
    Write-Host "  Kavenegar API Key: $($response.config.kavenegar_api_key_configured)" -ForegroundColor $(if ($response.config.kavenegar_api_key_configured) { "Green" } else { "Red" })
    Write-Host "  Kavenegar Sender: $($response.config.kavenegar_sender_configured)" -ForegroundColor $(if ($response.config.kavenegar_sender_configured) { "Green" } else { "Red" })
} catch {
    Write-Host "  ✗ Backend در دسترس نیست: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "لطفاً مطمئن شوید که Backend روی $BACKEND_IP:$BACKEND_PORT در حال اجرا است." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Test 2: Google OAuth Configuration
Write-Host "[2/3] تست تنظیمات Google OAuth..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "${BACKEND_URL}/api/test/google-oauth/" -Method GET -ContentType "application/json"
    Write-Host "  ✓ تست Google OAuth انجام شد" -ForegroundColor Green
    Write-Host "  Backend Client ID: $($response.config.backend_google_client_id)" -ForegroundColor Gray
    Write-Host "  Current Origin: $($response.config.current_origin)" -ForegroundColor Gray
    Write-Host "  Current Host: $($response.config.current_host)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  توصیه‌ها:" -ForegroundColor Cyan
    foreach ($rec in $response.recommendations) {
        Write-Host "    - $rec" -ForegroundColor White
    }
} catch {
    Write-Host "  ✗ خطا در تست Google OAuth: $_" -ForegroundColor Red
}

Write-Host ""

# Test 3: SMS Test
Write-Host "[3/3] تست ارسال SMS..." -ForegroundColor Yellow
Write-Host "  لطفاً شماره موبایل خود را وارد کنید (مثلاً 09123456789):" -ForegroundColor Cyan
$phoneNumber = Read-Host "  شماره موبایل"

if ($phoneNumber -match '^09\d{9}$') {
    try {
        $body = @{
            phone_number = $phoneNumber
        } | ConvertTo-Json
        
        Write-Host "  در حال ارسال SMS..." -ForegroundColor Gray
        $response = Invoke-RestMethod -Uri "${BACKEND_URL}/api/test/sms/" -Method POST -Body $body -ContentType "application/json"
        
        if ($response.success) {
            Write-Host "  ✓ SMS با موفقیت ارسال شد!" -ForegroundColor Green
            Write-Host "  کد تست: $($response.test_otp)" -ForegroundColor Cyan
            Write-Host "  پیام: $($response.message)" -ForegroundColor Gray
        } else {
            Write-Host "  ✗ خطا در ارسال SMS: $($response.message)" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ✗ خطا در ارسال SMS: $_" -ForegroundColor Red
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "  جزئیات: $responseBody" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  ✗ شماره موبایل نامعتبر است (باید به فرمت 09123456789 باشد)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  تست کامل شد!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 خلاصه:" -ForegroundColor Yellow
Write-Host "  Backend URL: $BACKEND_URL" -ForegroundColor White
Write-Host "  برای تست دستی:" -ForegroundColor Yellow
Write-Host "    - تست SMS: POST $BACKEND_URL/api/test/sms/ با body: {phone_number: '09123456789'}" -ForegroundColor Gray
Write-Host "    - تست Google OAuth: GET $BACKEND_URL/api/test/google-oauth/" -ForegroundColor Gray
Write-Host "    - وضعیت Backend: GET $BACKEND_URL/api/test/backend-status/" -ForegroundColor Gray
Write-Host ""

