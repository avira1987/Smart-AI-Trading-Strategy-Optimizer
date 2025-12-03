# رفع مشکل عدم نمایش CAPTCHA در دسترسی از اینترنت

## مشکل

در زمان دسترسی به وب‌سایت از طریق اینترنت (با IP)، کد CAPTCHA محاسباتی به کاربر نمایش داده نمی‌شد، اما با دسترسی از localhost کد به درستی نمایش داده می‌شد.

## علت مشکل

مشکل اصلی به دلیل **تنظیمات CORS** در backend بود. در حالت production، لیست `CORS_ALLOWED_ORIGINS` فقط شامل localhost و 127.0.0.1 بود و IP های شبکه محلی (مثل 192.168.x.x) را شامل نمی‌شد. بنابراین وقتی کاربر از IP اینترنت دسترسی داشت، درخواست CAPTCHA به دلیل خطای CORS رد می‌شد.

### تفاوت بین localhost و اینترنت:

- **localhost**: Origin = `http://localhost` → در لیست CORS_ALLOWED_ORIGINS بود ✅
- **اینترنت (IP)**: Origin = `http://192.168.1.100` → در لیست CORS_ALLOWED_ORIGINS نبود ❌

## راه‌حل‌های اعمال شده

### 1. بهبود تنظیمات CORS در Backend

در فایل `backend/config/settings.py`:

- افزودن تابع `get_local_network_cors_origins()` که به صورت خودکار IP های شبکه محلی را تشخیص می‌دهد
- این تابع IP های شبکه محلی (192.168.x.x, 10.x.x.x, 172.x.x.x) را با پورت‌های رایج (80, 3000, 8000) به `CORS_ALLOWED_ORIGINS` اضافه می‌کند
- پشتیبانی از Windows و Linux/Mac برای تشخیص IP

```python
def get_local_network_cors_origins():
    """Get local network IP addresses for CORS_ALLOWED_ORIGINS"""
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost",
        "http://127.0.0.1",
    ]
    # ... تشخیص خودکار IP های شبکه محلی
    return origins
```

### 2. بهبود تنظیمات Nginx

در فایل `nginx_production.conf`:

- افزودن CORS headers به location `/api/`
- پشتیبانی از preflight OPTIONS requests
- تنظیم headers مناسب برای CORS

```nginx
location /api/ {
    # ... سایر تنظیمات
    
    # CORS headers
    add_header 'Access-Control-Allow-Origin' $http_origin always;
    add_header 'Access-Control-Allow-Credentials' 'true' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, PATCH, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization, X-CSRFToken, X-Requested-With' always;
    
    # Handle preflight requests
    if ($request_method = 'OPTIONS') {
        return 204;
    }
}
```

### 3. بهبود Error Handling در Frontend

در فایل `frontend/src/utils/selfCaptcha.ts`:

- افزودن لاگ‌های دقیق‌تر برای debugging
- نمایش اطلاعات origin و hostname در console
- پیام‌های خطای واضح‌تر برای CORS errors

### 4. افزودن تست تشخیصی

ایجاد فایل `frontend/src/__tests__/CaptchaInternetAccess.test.tsx` برای:
- تست تفاوت بین localhost و اینترنت
- تست سناریوهای مختلف خطا (CORS, timeout, network)
- تست پیکربندی CORS

## نحوه تست

### 1. تست در localhost

```bash
# باز کردن مرورگر
http://localhost/login

# بررسی Console (F12)
# باید CAPTCHA نمایش داده شود
```

### 2. تست از اینترنت

```bash
# باز کردن مرورگر با IP واقعی
http://192.168.1.100/login  # جایگزین با IP واقعی

# بررسی Console (F12)
# باید CAPTCHA نمایش داده شود (بعد از اعمال تغییرات)
```

### 3. بررسی لاگ‌های Backend

```bash
# بررسی لاگ Django
# باید پیام زیر را ببینید:
# "CORS_ALLOWED_ORIGINS configured with X origins"
```

### 4. تست با curl

```bash
# تست از localhost
curl -X POST http://localhost/api/captcha/get/ \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost" \
  -d '{"action": "login"}' \
  -v

# تست از IP اینترنت
curl -X POST http://192.168.1.100/api/captcha/get/ \
  -H "Content-Type: application/json" \
  -H "Origin: http://192.168.1.100" \
  -d '{"action": "login"}' \
  -v
```

## تنظیمات اضافی (اختیاری)

اگر IP شما به صورت خودکار تشخیص داده نشد، می‌توانید به صورت دستی اضافه کنید:

### روش 1: استفاده از متغیر محیطی

```bash
# در فایل .env یا environment variables
CORS_ALLOWED_ORIGINS=http://192.168.1.100,http://192.168.1.100:80
```

### روش 2: ویرایش مستقیم settings.py

در بخش production، به صورت دستی IP را اضافه کنید:

```python
CORS_ALLOWED_ORIGINS = get_local_network_cors_origins()
CORS_ALLOWED_ORIGINS.append("http://192.168.1.100")
CORS_ALLOWED_ORIGINS.append("http://192.168.1.100:80")
```

## بررسی مشکل

اگر بعد از اعمال تغییرات هنوز مشکل دارید:

1. **بررسی Console مرورگر (F12)**: خطاهای CORS را بررسی کنید
2. **بررسی Network Tab**: درخواست `/api/captcha/get/` را بررسی کنید
3. **بررسی لاگ Django**: خطاهای backend را بررسی کنید
4. **بررسی تنظیمات Nginx**: مطمئن شوید nginx restart شده است
5. **بررسی CORS_ALLOWED_ORIGINS**: در لاگ Django باید IP شما در لیست باشد

## فایل‌های تغییر یافته

1. `backend/config/settings.py` - بهبود تنظیمات CORS
2. `nginx_production.conf` - افزودن CORS headers
3. `frontend/src/utils/selfCaptcha.ts` - بهبود error handling
4. `frontend/src/__tests__/CaptchaInternetAccess.test.tsx` - تست تشخیصی (جدید)

## نتیجه

بعد از اعمال این تغییرات، CAPTCHA باید هم در localhost و هم در دسترسی از اینترنت به درستی نمایش داده شود. مشکل اصلی به دلیل عدم وجود IP های شبکه محلی در `CORS_ALLOWED_ORIGINS` بود که اکنون به صورت خودکار تشخیص داده می‌شوند.

