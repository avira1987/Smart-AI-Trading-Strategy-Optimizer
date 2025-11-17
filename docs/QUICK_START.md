# 🚀 راهنمای سریع راه‌اندازی

## ✅ کارهای انجام شده

1. ✅ فایل‌های `.env.local` و `.env.production` ایجاد شدند
2. ✅ فایل `.env` برای لوکال تنظیم شد
3. ✅ Git workflow تنظیم شد
4. ✅ Deploy script آماده است

## 📋 مراحل راه‌اندازی

### 1. بررسی Redis

```powershell
# بررسی Redis
Test-NetConnection -ComputerName localhost -Port 6379

# اگر Redis نصب نیست، یکی از این روش‌ها را استفاده کنید:
.\start_redis.ps1
# یا
.\start_redis_docker.ps1
```

### 2. راه‌اندازی پروژه

```powershell
# تنظیم Environment (اگر انجام نشده)
.\use_local.ps1

# راه‌اندازی پروژه
.\start_project.ps1
```

### 3. دسترسی به پروژه

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin

## 🔧 تنظیمات مهم

### فایل `.env.local` (برای لوکال):
- `DEBUG=True`
- `ENV=LOCAL`
- `PUBLIC_IP=` (خالی)
- `FRONTEND_URL=http://localhost:3000`
- `BACKEND_URL=http://localhost:8000`

### فایل `.env.production` (برای سرور):
- `DEBUG=False`
- `ENV=PRODUCTION`
- `PUBLIC_IP=191.101.113.163`
- `FRONTEND_URL=http://191.101.113.163:3000`
- `BACKEND_URL=http://191.101.113.163:8000`

## 🚀 Deploy به سرور

```powershell
# فقط یک دستور!
.\deploy.ps1
```

این اسکریپت:
1. تغییرات را commit می‌کند
2. به GitHub push می‌کند
3. روی VPS از GitHub pull می‌کند
4. وابستگی‌ها را نصب می‌کند
5. سرویس‌ها را راه‌اندازی می‌کند

## 📝 نکات مهم

- فایل `.env.production` را روی VPS ویرایش کنید و `SECRET_KEY` را تغییر دهید
- تمام API keys را در `.env.production` وارد کنید
- برای اولین بار روی VPS، باید Git را نصب کنید

## 🐛 مشکلات رایج

### Redis در حال اجرا نیست
```powershell
.\start_redis.ps1
```

### پورت 8000 یا 3000 اشغال است
```powershell
# پیدا کردن process
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess

# متوقف کردن
Stop-Process -Id <PID> -Force
```

### خطا در Build Frontend
```powershell
cd frontend
Remove-Item node_modules -Recurse -Force
npm install
npm run build
```

---

**✅ همه چیز آماده است! برای شروع، `.\start_project.ps1` را اجرا کنید.**

