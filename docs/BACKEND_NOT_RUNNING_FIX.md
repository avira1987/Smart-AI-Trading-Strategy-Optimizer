# راهنمای حل مشکل: Backend در حال اجرا نیست

## مشکل
خطای `ECONNREFUSED ::1:8000` یا `Failed to get CAPTCHA` در صفحه لاگین

## علت
Backend Django در حال اجرا نیست یا روی پورت 8000 در دسترس نیست.

---

## راه‌حل سریع

### روش 1: استفاده از فایل آماده (توصیه می‌شود)

**Windows:**
```powershell
# در root پروژه
.\start.ps1
```

یا:
```cmd
START_HERE.bat
```

### روش 2: اجرای دستی

#### مرحله 1: اجرای Backend

**ترمینال 1 - Backend:**
```powershell
cd backend
python manage.py runserver 0.0.0.0:8000
```

یا اگر از virtual environment استفاده می‌کنید:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py runserver 0.0.0.0:8000
```

**باید این پیام را ببینید:**
```
Starting development server at http://0.0.0.0:8000/
Quit the server with CTRL-BREAK.
```

#### مرحله 2: اجرای Frontend (در ترمینال جداگانه)

**ترمینال 2 - Frontend:**
```powershell
cd frontend
npm run dev
```

---

## بررسی

### 1. بررسی که Backend در حال اجرا است

**در مرورگر:**
```
http://localhost:8000/api/
```

باید پاسخ JSON ببینید.

**یا با curl:**
```powershell
curl http://localhost:8000/api/
```

### 2. بررسی پورت 8000

**Windows PowerShell:**
```powershell
netstat -an | findstr :8000
```

باید چیزی شبیه این ببینید:
```
TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING
```

### 3. تست API CAPTCHA

```powershell
curl -X POST http://localhost:8000/api/captcha/get/ `
  -H "Content-Type: application/json" `
  -d '{\"action\":\"login\"}'
```

باید پاسخ زیر را ببینید:
```json
{
  "success": true,
  "token": "...",
  "challenge": "5 + 3",
  "type": "math"
}
```

---

## مشکلات رایج

### مشکل 1: پورت 8000 اشغال است

**راه‌حل:**
```powershell
# پیدا کردن process که از پورت 8000 استفاده می‌کند
netstat -ano | findstr :8000

# متوقف کردن process (PID را از خروجی بالا بگیرید)
taskkill /PID <PID> /F
```

### مشکل 2: Python پیدا نمی‌شود

**راه‌حل:**
```powershell
# بررسی نصب Python
python --version

# اگر نصب نیست، از python.org دانلود کنید
```

### مشکل 3: Virtual Environment فعال نیست

**راه‌حل:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py runserver 0.0.0.0:8000
```

### مشکل 4: Dependencies نصب نشده

**راه‌حل:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### مشکل 5: Database migrations انجام نشده

**راه‌حل:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py migrate
```

---

## چک‌لیست

قبل از اجرای Frontend، مطمئن شوید:

- [ ] Backend در حال اجرا است
- [ ] Backend روی پورت 8000 پاسخ می‌دهد
- [ ] API endpoint `/api/captcha/get/` کار می‌کند
- [ ] Virtual environment فعال است (اگر استفاده می‌کنید)
- [ ] Dependencies نصب شده‌اند
- [ ] Migrations انجام شده‌اند

---

## دستورات سریع

### متوقف کردن همه سرویس‌ها

**Windows:**
```powershell
# متوقف کردن Python
taskkill /F /IM python.exe

# متوقف کردن Node
taskkill /F /IM node.exe
```

### راه‌اندازی مجدد

```powershell
# 1. متوقف کردن همه
taskkill /F /IM python.exe /IM node.exe

# 2. راه‌اندازی مجدد
.\start.ps1
```

---

## لاگ‌ها

### Backend Logs
اگر Backend در حال اجرا است اما خطا می‌دهد، لاگ‌ها را بررسی کنید:

```powershell
# در ترمینال Backend
# خطاها به صورت مستقیم نمایش داده می‌شوند
```

### Frontend Logs
در ترمینال Frontend، خطاهای proxy را بررسی کنید.

---

## تماس با پشتیبانی

اگر مشکل حل نشد:

1. Screenshot از ترمینال Backend
2. Screenshot از ترمینال Frontend
3. خروجی `python --version`
4. خروجی `netstat -an | findstr :8000`

---

**آخرین بروزرسانی:** 2024

