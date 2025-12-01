# راهنمای راه‌اندازی Production با Docker و Nginx

این راهنما برای راه‌اندازی وب‌سایت با Docker و Nginx برای دسترسی با IP بدون نیاز به پورت است.

## پیش‌نیازها

1. Docker Desktop نصب و در حال اجرا باشد
2. دسترسی Administrator در Windows
3. پورت 80 آزاد باشد (IIS متوقف باشد)

## مراحل راه‌اندازی

### 1. تنظیم فایل `.env`

فایل `.env` را ویرایش کنید و این تنظیمات را اضافه/تغییر دهید:

```bash
# Django Settings
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ENV=PRODUCTION

# Database
DB_NAME=forex_db
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_HOST=db
DB_PORT=5432

# Redis (برای Docker)
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0

# Allowed Hosts - IP آدرس سرور خود را اینجا قرار دهید
ALLOWED_HOSTS=YOUR_IP_ADDRESS,localhost,127.0.0.1

# Public IP Configuration
PUBLIC_IP=YOUR_IP_ADDRESS
PUBLIC_PORT=80
FRONTEND_PUBLIC_PORT=80
FRONTEND_URL=http://YOUR_IP_ADDRESS
BACKEND_URL=http://YOUR_IP_ADDRESS

# سایر API Keys...
```

**مهم:** `YOUR_IP_ADDRESS` را با IP آدرس واقعی سرور خود جایگزین کنید.

### 2. اجرای اسکریپت راه‌اندازی

PowerShell را به عنوان Administrator اجرا کنید و این دستور را اجرا کنید:

```powershell
.\setup_docker_production.ps1
```

این اسکریپت:
- Docker را بررسی می‌کند
- IIS را متوقف می‌کند (اگر در حال اجرا باشد)
- پورت 80 را بررسی می‌کند
- IP آدرس سرور را تشخیص می‌دهد
- فایروال را تنظیم می‌کند
- Docker containers را build و راه‌اندازی می‌کند

### 3. تست دسترسی

بعد از راه‌اندازی، دستور زیر را اجرا کنید:

```powershell
.\test_production.ps1
```

این اسکریپت تمام بخش‌های سیستم را تست می‌کند.

## دسترسی به وب‌سایت

بعد از راه‌اندازی موفق، وب‌سایت در آدرس‌های زیر در دسترس است:

- **محلی:** `http://localhost`
- **با IP:** `http://YOUR_IP_ADDRESS`

**نکته:** نیازی به اضافه کردن پورت نیست. Nginx روی پورت 80 (پورت پیش‌فرض HTTP) اجرا می‌شود.

## معماری سیستم

```
Internet
   ↓
[Port 80] → Nginx (Frontend Container)
   ↓
   ├─→ Frontend Files (React Build)
   └─→ /api/* → Backend Container (Port 8000)
                ├─→ Django + Gunicorn
                ├─→ PostgreSQL (Port 5432 - فقط localhost)
                └─→ Redis (Port 6379 - فقط localhost)
```

## دستورات مفید

### مشاهده لاگ‌ها
```powershell
# همه لاگ‌ها
docker-compose logs -f

# فقط Backend
docker-compose logs -f backend

# فقط Frontend
docker-compose logs -f frontend
```

### متوقف کردن
```powershell
docker-compose down
```

### راه‌اندازی مجدد
```powershell
docker-compose restart
```

### مشاهده وضعیت
```powershell
docker-compose ps
```

### Rebuild بعد از تغییرات
```powershell
docker-compose up -d --build
```

## عیب‌یابی

### مشکل: پورت 80 در حال استفاده است

**راه حل:**
1. IIS را متوقف کنید: `iisreset /stop`
2. یا process دیگری که از پورت 80 استفاده می‌کند را پیدا و متوقف کنید:
   ```powershell
   Get-NetTCPConnection -LocalPort 80 | Select-Object OwningProcess
   ```

### مشکل: Frontend کار می‌کند اما Backend پاسخ نمی‌دهد

**بررسی:**
1. وضعیت containers: `docker-compose ps`
2. لاگ Backend: `docker-compose logs backend`
3. بررسی `.env` که `ALLOWED_HOSTS` شامل IP سرور باشد
4. بررسی که Backend container در حال اجرا است

### مشکل: از خارج سرور دسترسی ندارید

**بررسی:**
1. فایروال Windows: قانون برای پورت 80 باید فعال باشد
2. فایروال سرور/راه‌انداز: پورت 80 باید باز باشد
3. IP آدرس: مطمئن شوید IP آدرس درست است

### مشکل: خطای CORS یا 403

**راه حل:**
1. بررسی `ALLOWED_HOSTS` در `.env`
2. بررسی `DEBUG=False` در production
3. بررسی `ENV=PRODUCTION` در `.env`

## نکات امنیتی

1. **Database و Redis:** فقط از localhost قابل دسترسی هستند (امنیت بیشتر)
2. **Backend:** فقط از طریق Nginx قابل دسترسی است (مستقیم از خارج در دسترس نیست)
3. **DEBUG:** همیشه `False` در production
4. **SECRET_KEY:** باید یک رشته تصادفی قوی باشد

## به‌روزرسانی

برای به‌روزرسانی بعد از تغییرات در کد:

```powershell
# متوقف کردن
docker-compose down

# Build مجدد و راه‌اندازی
docker-compose up -d --build
```

## پشتیبان‌گیری

### Database
```powershell
docker-compose exec db pg_dump -U postgres forex_db > backup.sql
```

### Restore Database
```powershell
docker-compose exec -T db psql -U postgres forex_db < backup.sql
```

## پشتیبانی

در صورت بروز مشکل:
1. لاگ‌ها را بررسی کنید: `docker-compose logs -f`
2. وضعیت containers را بررسی کنید: `docker-compose ps`
3. تست دسترسی را اجرا کنید: `.\test_production.ps1`

