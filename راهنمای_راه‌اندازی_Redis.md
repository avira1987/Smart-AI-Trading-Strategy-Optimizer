# راهنمای راه‌اندازی Redis

## مشکل فعلی
Redis در حال اجرا نیست و Celery Worker و Beat نمی‌توانند به آن متصل شوند.

## راه‌حل‌ها

### راه حل 1: استفاده از Docker (پیشنهادی)

#### مرحله 1: Docker Desktop را راه‌اندازی کنید
- Docker Desktop را از Start Menu باز کنید
- صبر کنید تا Docker Desktop کامل راه‌اندازی شود

#### مرحله 2: Redis را راه‌اندازی کنید

**گزینه A: استفاده از اسکریپت**
```powershell
.\start_redis.ps1
```

**گزینه B: اجرای مستقیم**
```powershell
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

**گزینه C: استفاده از docker-compose**
```powershell
.\start_redis_compose.ps1
```

یا:
```powershell
docker-compose up -d redis
```

#### مرحله 3: بررسی کنید که Redis در حال اجرا است
```powershell
docker ps
```

باید container با نام `redis` را ببینید.

#### مرحله 4: اکنون اسکریپت اصلی را اجرا کنید
```powershell
.\start_project.ps1
```

---

### راه حل 2: نصب Redis برای Windows (بدون Docker)

اگر نمی‌خواهید از Docker استفاده کنید:

1. Redis for Windows را دانلود کنید:
   - از https://github.com/microsoftarchive/redis/releases
   - یا از https://github.com/tporadowski/redis/releases (نسخه جدیدتر)

2. Redis را نصب و اجرا کنید:
   ```powershell
   redis-server
   ```

---

### راه حل 3: استفاده از WSL2

اگر WSL2 نصب دارید:

```bash
# در WSL2 terminal
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

---

## بررسی وضعیت Redis

برای بررسی اینکه Redis در حال اجرا است:

```powershell
# PowerShell
Test-NetConnection -ComputerName localhost -Port 6379
```

یا:

```powershell
try { 
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 6379)
    $tcpClient.Close()
    Write-Host "✓ Redis is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Redis is NOT running" -ForegroundColor Red
}
```

---

## نکات مهم

1. **Redis باید قبل از اجرای Celery Worker و Beat راه‌اندازی شود**
2. **اگر از Docker استفاده می‌کنید، Docker Desktop باید همیشه در حال اجرا باشد**
3. **پورت 6379 نباید توسط برنامه دیگری استفاده شود**

---

## عیب‌یابی

### خطا: "Docker Desktop is not running"
- Docker Desktop را باز کنید و صبر کنید تا کامل راه‌اندازی شود

### خطا: "Port 6379 is already in use"
- بررسی کنید که Redis قبلاً راه‌اندازی نشده:
  ```powershell
  docker ps
  ```

### خطا: "Cannot connect to Redis"
- بررسی کنید که Redis container در حال اجرا است:
  ```powershell
  docker ps -a
  ```
- لاگ‌های Redis را بررسی کنید:
  ```powershell
  docker logs redis
  ```
