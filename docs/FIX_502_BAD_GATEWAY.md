# رفع خطای 502 Bad Gateway

## مشکل
خطای "خطای سرور: 502" در صفحه لاگین نمایش داده می‌شود.

## علت
خطای 502 Bad Gateway یعنی Nginx نمی‌تواند به Backend Django متصل شود. این معمولاً به این دلایل است:

1. **Backend در حال اجرا نیست** (شایع‌ترین علت)
2. Backend روی پورت 8000 در دسترس نیست
3. مشکل در proxy_pass configuration در Nginx

## راه‌حل

### 1. بررسی وضعیت Backend

```powershell
# بررسی پورت 8000
Get-NetTCPConnection -LocalPort 8000

# یا
netstat -ano | findstr :8000
```

**اگر پورت 8000 بسته است**: Backend در حال اجرا نیست.

### 2. اجرای Backend

```powershell
# روش 1: استفاده از start.ps1 (توصیه می‌شود)
.\start.ps1

# روش 2: اجرای دستی
cd backend
python manage.py runserver 0.0.0.0:8000
```

### 3. بررسی اتصال

```powershell
# تست مستقیم Backend
$body = @{action='login'} | ConvertTo-Json
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/captcha/get/" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

**باید Status 200 دریافت کنید.**

### 4. بررسی Nginx Proxy

```powershell
# تست از طریق Nginx
$body = @{action='login'} | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost/api/captcha/get/" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

**باید Status 200 دریافت کنید (نه 502).**

## مراحل عیب‌یابی

1. ✅ **Backend را اجرا کنید**
2. ✅ **بررسی کنید که پورت 8000 باز است**
3. ✅ **تست کنید که Backend پاسخ می‌دهد**
4. ✅ **تست کنید که Nginx proxy کار می‌کند**
5. ✅ **Reload Nginx**: `C:\nginx-1.28.0\nginx.exe -s reload`

## نکات مهم

- **همیشه Backend را قبل از Nginx اجرا کنید**
- **مطمئن شوید که Backend روی `0.0.0.0:8000` یا `127.0.0.1:8000` اجرا می‌شود**
- **پورت 8000 باید در دسترس باشد**

