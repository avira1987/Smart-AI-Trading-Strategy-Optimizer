# راهنمای استفاده از Docker

این پروژه برای استفاده از Docker 24.0.5 به‌روزرسانی شده است.

## پیش‌نیازها

1. **Docker Desktop** نصب شده باشد
2. Docker در حالت **Linux Containers** باشد (نه Windows Containers)

## تنظیم اولیه

### 1. تغییر Docker به Linux Containers

دو روش برای تغییر Docker به Linux Containers:

#### روش 1: از Docker Desktop (پیشنهادی)
1. Docker Desktop را باز کنید
2. روی آیکون Docker در System Tray (کنار ساعت) راست کلیک کنید
3. "Switch to Linux containers..." را انتخاب کنید
4. منتظر بمانید تا Docker restart شود

#### روش 2: از Command Line
```powershell
# استفاده از context desktop-linux (اگر Docker Desktop نصب است)
docker context use desktop-linux

# یا استفاده از context پیش‌فرض
docker context use default
```

#### روش 3: استفاده از اسکریپت
```powershell
.\setup_docker_linux.ps1
```

### 2. بررسی وضعیت Docker

```powershell
docker info | Select-String "OSType"
```

باید `OSType: linux` نمایش داده شود.

## راه‌اندازی سرویس‌ها

### روش 1: راه‌اندازی فقط Redis

```powershell
.\start_redis_docker.ps1
```

این اسکریپت:
- بررسی می‌کند که Docker در حالت Linux Container است
- Container Redis را ایجاد یا راه‌اندازی می‌کند
- اتصال Redis را بررسی می‌کند

### روش 2: راه‌اندازی کامل با Docker Compose

```powershell
.\start_with_docker.ps1
```

این اسکریپت:
- تمام سرویس‌ها را با Docker Compose راه‌اندازی می‌کند
- Backend, Frontend, Redis, PostgreSQL را راه‌اندازی می‌کند

### روش 3: راه‌اندازی دستی

```powershell
# راه‌اندازی Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# یا با docker-compose
docker compose up -d redis

# راه‌اندازی همه سرویس‌ها
docker compose up -d
```

## دستورات مفید Docker

### مشاهده Containerها
```powershell
docker ps                    # Containerهای در حال اجرا
docker ps -a                 # همه Containerها
docker compose ps            # Containerهای docker-compose
```

### مشاهده لاگ‌ها
```powershell
docker logs redis            # لاگ Redis
docker logs -f redis         # لاگ زنده Redis
docker compose logs          # لاگ همه سرویس‌ها
docker compose logs -f       # لاگ زنده همه سرویس‌ها
```

### مدیریت Containerها
```powershell
docker start redis           # راه‌اندازی Redis
docker stop redis            # توقف Redis
docker restart redis         # راه‌اندازی مجدد Redis
docker rm -f redis           # حذف Redis
```

### مدیریت Docker Compose
```powershell
docker compose up -d         # راه‌اندازی در background
docker compose down          # توقف و حذف
docker compose restart       # راه‌اندازی مجدد
docker compose build         # ساخت مجدد images
```

## عیب‌یابی

### مشکل: "OSType: windows" نمایش داده می‌شود

**راه‌حل:**
1. Docker Desktop را باز کنید
2. راست کلیک روی آیکون Docker -> Switch to Linux containers
3. یا از اسکریپت: `.\setup_docker_linux.ps1`

### مشکل: "The system cannot find the file specified"

**راه‌حل:**
- Docker Desktop را باز کنید
- مطمئن شوید که Docker Desktop در حال اجرا است

### مشکل: "no matching manifest for windows/amd64"

**راه‌حل:**
- Docker در حالت Windows Container است
- باید به Linux Container تغییر دهید

### مشکل: Redis راه‌اندازی نمی‌شود

**بررسی‌ها:**
```powershell
# بررسی وضعیت Docker
docker info | Select-String "OSType"

# بررسی Container Redis
docker ps -a | findstr redis

# مشاهده لاگ‌ها
docker logs redis

# تست اتصال
Test-NetConnection -ComputerName localhost -Port 6379
```

## ساختار Docker Compose

پروژه شامل سرویس‌های زیر است:

- **redis**: Redis برای Celery
- **db**: PostgreSQL برای دیتابیس
- **backend**: Django Backend
- **frontend**: React Frontend (با Nginx)

## فایل‌های Docker

- `docker-compose.yml`: تنظیمات Docker Compose
- `Dockerfile.backend`: Image برای Backend
- `Dockerfile.frontend`: Image برای Frontend
- `nginx.conf`: تنظیمات Nginx

## نکات مهم

1. **Docker Desktop باید باز باشد** برای استفاده از Docker
2. **Linux Containers** برای Redis و PostgreSQL ضروری است
3. **پورت‌ها**: مطمئن شوید که پورت‌های 6379, 8000, 3000, 5432 باز هستند
4. **Volumeها**: داده‌های دیتابیس و Redis در Volumeهای Docker ذخیره می‌شوند

## پشتیبانی

برای مشکلات بیشتر:
- بررسی لاگ‌ها: `docker compose logs`
- بررسی وضعیت: `docker compose ps`
- مستندات Docker: https://docs.docker.com/

