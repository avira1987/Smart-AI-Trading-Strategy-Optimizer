# گزارش کارهای انجام شده برای رفع مشکل IIS و Cloudflare

## خلاصه مشکل
- خطای 503 Service Unavailable هنگام دسترسی به دامنه `myaibaz.ir` از طریق Cloudflare
- سایت با IP مستقیم (`http://191.101.113.163:3000`) کار می‌کند
- نیاز به تنظیم IIS به عنوان Reverse Proxy

## کارهای انجام شده

### 1. بررسی وضعیت اولیه ✅
- ✅ Application Pools: همه در حال اجرا
- ✅ Site "MyWebsite": در حال اجرا
- ✅ پورت 3000 (Frontend): در دسترس
- ✅ پورت 8000 (Backend): در دسترس
- ✅ مسیر فیزیکی Site: `C:\inetpub\wwwroot`

### 2. ساخت و تنظیم web.config ✅
فایل `web.config` در مسیر `C:\inetpub\wwwroot\web.config` ساخته شد با محتوای:
- Rule برای Backend API: `/api/*` → `http://127.0.0.1:8000/api/*`
- Rule برای Frontend: تمام درخواست‌های دیگر → `http://127.0.0.1:3000/*`
- Proxy enabled: `true`
- Reverse rewrite host headers: `true`

### 3. فعال‌سازی ماژول‌های IIS ✅
- ✅ URL Rewrite Module: نصب شده و فعال
- ✅ Application Request Routing (ARR): نصب شده و فعال
- ✅ Proxy در ARR: فعال شده

### 4. فعال‌سازی Server Variables ✅
Server Variables زیر برای URL Rewrite فعال شدند:
- `HTTP_X_FORWARDED_PROTO`
- `HTTP_X_FORWARDED_HOST`
- `HTTP_X_REAL_IP`

### 5. تنظیمات Application Pool ✅
- Application Pool: `DefaultAppPool`
- Identity: `ApplicationPoolIdentity`
- State: `Started`

### 6. تست‌های انجام شده
- ✅ تست مستقیم Frontend (`http://127.0.0.1:3000`): موفق (Status 200)
- ✅ تست مستقیم Backend (`http://127.0.0.1:8000/api/`): موفق (Status 200)
- ⚠️ تست از طریق IIS (`http://localhost`): خطای 503

## مشکل باقی‌مانده

### خطای 503 Service Unavailable
علت احتمالی:
1. Application Pool Identity ممکن است نتواند به `127.0.0.1` دسترسی پیدا کند
2. URL Rewrite rules ممکن است به درستی match نشوند
3. ممکن است نیاز به استفاده از IP address به جای `127.0.0.1` باشد

## راه‌حل‌های پیشنهادی

### راه‌حل 1: استفاده از IP Address به جای 127.0.0.1
در `web.config` به جای `127.0.0.1` از IP واقعی سرور استفاده کنید:
```xml
<action type="Rewrite" url="http://191.101.113.163:3000/{R:1}" />
<action type="Rewrite" url="http://191.101.113.163:8000/api/{R:1}" />
```

### راه‌حل 2: تغییر Application Pool Identity
Application Pool Identity را به یک User با دسترسی بیشتر تغییر دهید.

### راه‌حل 3: بررسی Logs
Event Viewer و IIS Logs را بررسی کنید برای جزئیات بیشتر خطا.

## فایل‌های ایجاد شده
1. `check_and_fix_iis.ps1` - اسکریپت اولیه بررسی
2. `fix_iis.ps1` - اسکریپت تنظیمات اصلی
3. `test_iis_final.ps1` - اسکریپت تست
4. `fix_503_error.ps1` - اسکریپت رفع خطای 503
5. `diagnose_503.ps1` - اسکریپت تشخیص مشکل
6. `C:\inetpub\wwwroot\web.config` - فایل کانفیگ IIS
7. `C:\inetpub\wwwroot\web.config.backup` - بکاپ فایل کانفیگ

## وضعیت فعلی
- ✅ تمام تنظیمات IIS انجام شده
- ✅ web.config ساخته و تنظیم شده
- ✅ Proxy و URL Rewrite فعال شده
- ⚠️ هنوز خطای 503 وجود دارد (نیاز به بررسی بیشتر)

## مراحل بعدی
1. بررسی Event Viewer برای خطاهای دقیق‌تر
2. تست استفاده از IP address به جای 127.0.0.1
3. بررسی IIS Logs در `C:\inetpub\logs\LogFiles`
4. در صورت نیاز، تغییر Application Pool Identity

