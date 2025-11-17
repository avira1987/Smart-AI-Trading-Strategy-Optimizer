# ✅ پروژه در حال اجرا است!

## 📍 دسترسی به برنامه

- **Frontend (React)**: http://localhost:3000
- **Backend (Django API)**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/
  - Username: `admin`
  - Password: `admin`

## 🚀 نحوه استفاده

### 1. باز کردن Frontend
مرورگر را باز کنید و به آدرس زیر بروید:
```
http://localhost:3000
```

### 2. دسترسی به Admin Panel
برای مدیریت کامل پروژه:
```
http://localhost:8000/admin/
```

### 3. تست API
برای تست API endpoints:
```
http://localhost:8000/api/
```

## 🔧 مدیریت سرورها

### متوقف کردن سرورها
در ترمینال PowerShell:
```powershell
# متوقف کردن همه
Stop-Process -Name "python" -ErrorAction SilentlyContinue
Stop-Process -Name "node" -ErrorAction SilentlyContinue
```

### یا از طریق Task Manager
- Ctrl + Shift + Esc
- Process tab
- پیدا کردن python.exe و node.exe
- End Task

## 📝 API Endpoints

### API Configurations
- GET http://localhost:8000/api/apis/ - لیست همه API ها
- POST http://localhost:8000/api/apis/ - اضافه کردن API جدید

### Strategies
- GET http://localhost:8000/api/strategies/ - لیست strategies
- POST http://localhost:8000/api/strategies/ - آپلود strategy جدید

### Jobs
- GET http://localhost:8000/api/jobs/ - لیست jobs
- POST http://localhost:8000/api/jobs/ - ایجاد job جدید

### Results
- GET http://localhost:8000/api/results/ - نتایج

## 🎯 اقدامات بعدی

1. ✅ پروژه نصب و راه‌اندازی شد
2. ⏭️ اضافه کردن Celery + Redis (برای async tasks)
3. ⏭️ تکمیل Frontend UI
4. ⏭️ اتصال به API های واقعی (TwelveData, MetalsAPI)
5. ⏭️ پیاده‌سازی AI parser

## 📞 پشتیبانی

اگر مشکلی بود:
- Backend logs: ترمینالی که `python manage.py runserver` اجرا کردید
- Frontend logs: ترمینالی که `npm run dev` اجرا کردید

