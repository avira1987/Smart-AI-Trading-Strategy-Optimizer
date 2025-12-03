# راهنمای عیب‌یابی مشکل Proxy در Nginx

## مشکل: "درخواست به سرور ارسال شد اما پاسخی دریافت نشد"

### علت مشکل

وقتی از IP اینترنت دسترسی دارید، درخواست به nginx می‌رسد اما nginx نمی‌تواند به backend Django (پورت 8000) متصل شود.

### مراحل عیب‌یابی

#### 1. بررسی اینکه Backend در حال اجرا است

```powershell
# بررسی پورت 8000
netstat -ano | findstr :8000

# یا
Get-NetTCPConnection -LocalPort 8000
```

اگر پورت 8000 باز نیست، backend در حال اجرا نیست.

**راه حل**: Backend را اجرا کنید:
```powershell
cd backend
python manage.py runserver 0.0.0.0:8000
```

#### 2. تست مستقیم Backend

```powershell
# تست از localhost
curl http://127.0.0.1:8000/api/captcha/get/ -X POST -H "Content-Type: application/json" -d "{\"action\":\"login\"}"

# یا با PowerShell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/captcha/get/" -Method POST -ContentType "application/json" -Body '{"action":"login"}'
```

اگر این کار نمی‌کند، مشکل از backend است.

#### 3. بررسی Nginx

```powershell
# بررسی اینکه nginx در حال اجرا است
Get-Process nginx -ErrorAction SilentlyContinue

# بررسی لاگ‌های nginx
# در Windows: C:\nginx-1.28.0\logs\
```

**بررسی لاگ‌های خطا**:
```
C:\nginx-1.28.0\logs\error.log
C:\nginx-1.28.0\logs\api_error.log
```

#### 4. تست Nginx Proxy

```powershell
# تست از طریق nginx
Invoke-WebRequest -Uri "http://localhost/api/captcha/get/" -Method POST -ContentType "application/json" -Body '{"action":"login"}'
```

اگر این کار نمی‌کند، مشکل از nginx proxy است.

### راه‌حل‌های احتمالی

#### راه‌حل 1: اطمینان از اجرای Backend

```powershell
# در PowerShell
cd backend
python manage.py runserver 0.0.0.0:8000
```

یا اگر از start.ps1 استفاده می‌کنید:
```powershell
.\start.ps1
```

#### راه‌حل 2: بررسی تنظیمات Nginx

مطمئن شوید که `nginx_production.conf` به درستی کپی شده است:

```powershell
# کپی فایل به محل nginx
Copy-Item nginx_production.conf C:\nginx-1.28.0\conf\nginx.conf -Force

# تست تنظیمات
C:\nginx-1.28.0\nginx.exe -t

# Reload nginx
C:\nginx-1.28.0\nginx.exe -s reload
```

#### راه‌حل 3: بررسی Firewall

ممکن است firewall مانع اتصال شود:

```powershell
# بررسی firewall rules
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*8000*"}

# اگر نیاز است، rule اضافه کنید
New-NetFirewallRule -DisplayName "Django Backend" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

#### راه‌حل 4: بررسی Proxy Pass

در `nginx_production.conf`، مطمئن شوید که:

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000/api/;
    # ...
}
```

**نکته مهم**: trailing slash (`/`) در انتهای `proxy_pass` مهم است!

### بررسی لاگ‌ها

#### لاگ Nginx

```powershell
# مشاهده لاگ‌های خطا
Get-Content C:\nginx-1.28.0\logs\error.log -Tail 50

# مشاهده لاگ‌های API
Get-Content C:\nginx-1.28.0\logs\api_error.log -Tail 50
```

#### لاگ Django

```powershell
# اگر backend با runserver اجرا می‌شود، لاگ‌ها در console نمایش داده می‌شوند
# یا بررسی فایل لاگ Django (اگر تنظیم شده باشد)
```

### تست نهایی

بعد از اعمال تغییرات:

1. **Restart Backend**:
   ```powershell
   # Stop
   .\stop.ps1
   
   # Start
   .\start.ps1
   ```

2. **Reload Nginx**:
   ```powershell
   C:\nginx-1.28.0\nginx.exe -s reload
   ```

3. **تست از IP اینترنت**:
   - باز کردن `http://<IP>/login`
   - بررسی Console (F12)
   - بررسی Network tab

### پیام‌های خطای رایج

#### "Connection refused"
- Backend در حال اجرا نیست
- پورت 8000 بسته است

#### "Timeout"
- Backend خیلی کند پاسخ می‌دهد
- مشکل شبکه
- Timeout settings در nginx کم است

#### "502 Bad Gateway"
- Nginx نمی‌تواند به backend متصل شود
- Backend crash کرده است

#### "504 Gateway Timeout"
- Backend خیلی کند پاسخ می‌دهد
- Timeout در nginx

### نکات مهم

1. **همیشه backend را قبل از nginx اجرا کنید**
2. **مطمئن شوید که پورت 8000 در دسترس است**
3. **لاگ‌های nginx را بررسی کنید**
4. **از `127.0.0.1` به جای `localhost` در proxy_pass استفاده کنید** (در Windows بهتر کار می‌کند)

