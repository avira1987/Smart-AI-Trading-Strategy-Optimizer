# راهنمای تنظیم Docker Engine برای Linux Containers

برای اجرای Redis و PostgreSQL با Docker version 24.0.5، Docker Engine باید در حالت **Linux Containers** باشد.

## مشکل فعلی

Docker در حال حاضر در حالت **Windows Containers** است که نمی‌تواند Linux images (مثل Redis و PostgreSQL) را اجرا کند.

## راه‌حل‌ها

### روش 1: استفاده از WSL 2 (پیشنهادی برای Windows)

اگر WSL 2 نصب دارید:

```powershell
# نصب WSL 2 (اگر نصب نیست)
wsl --install

# راه‌اندازی Docker در WSL 2
# Docker باید در WSL 2 نصب شود
```

### روش 2: استفاده از Docker Engine مستقیم

اگر Docker Engine به صورت مستقل نصب است:

1. **بررسی سرویس Docker:**
   ```powershell
   Get-Service | Where-Object {$_.Name -like "*docker*"}
   ```

2. **راه‌اندازی Docker daemon در حالت Linux:**
   - Docker daemon باید با پارامتر `--exec-opt native.cgroupdriver=systemd` یا مشابه راه‌اندازی شود
   - معمولاً در فایل تنظیمات Docker (مثلاً `C:\ProgramData\docker\config\daemon.json`)

3. **Restart Docker service:**
   ```powershell
   Restart-Service docker
   ```

### روش 3: استفاده از Docker Desktop (اگر نصب است)

اگر Docker Desktop نصب است:
1. Docker Desktop را باز کنید
2. راست کلیک روی آیکون -> Switch to Linux containers

## بررسی وضعیت

```powershell
# بررسی نوع Container
docker info | Select-String "OSType"

# باید نمایش دهد: OSType: linux
```

## راه‌اندازی Redis

پس از تغییر به Linux Containers:

```powershell
# راه‌اندازی Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# یا استفاده از اسکریپت
.\start_redis_simple.ps1
```

## اگر نمی‌توانید به Linux Containers تغییر دهید

اگر نمی‌توانید Docker را به Linux Containers تغییر دهید، می‌توانید:

1. **از Redis Windows استفاده کنید:**
   - نصب Redis برای Windows
   - یا استفاده از Redis در WSL 2

2. **برنامه را بدون Redis اجرا کنید:**
   - برنامه بدون Redis هم کار می‌کند
   - فقط Celery (برای background tasks) کار نمی‌کند

## دستورات مفید

```powershell
# بررسی وضعیت Docker
docker version
docker info

# مشاهده Containerها
docker ps
docker ps -a

# راه‌اندازی Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# مشاهده لاگ Redis
docker logs redis

# توقف Redis
docker stop redis

# راه‌اندازی مجدد Redis
docker start redis
```

## نکات مهم

- Docker version 24.0.5 نصب است ✓
- Docker در حالت Windows Container است ✗
- برای اجرای Redis باید به Linux Container تغییر دهید
- اگر نمی‌توانید تغییر دهید، برنامه بدون Redis هم کار می‌کند

