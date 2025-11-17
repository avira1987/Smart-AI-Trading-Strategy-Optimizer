# راهنمای اجرای برنامه بدون Docker

این راهنما برای اجرای برنامه در محیط محلی (بدون Docker) نوشته شده است.

## پیش‌نیازها

- Python 3.11+ (نصب شده ✓)
- Node.js 18+ (نصب شده ✓)
- Redis (اختیاری - برای Celery)

## مراحل نصب و اجرا

### 1. راه‌اندازی Backend

```bash
# فعال‌سازی محیط مجازی
.\venv\Scripts\Activate.ps1

# نصب وابستگی‌ها (انجام شده)
pip install Django==5.0.2 djangorestframework==3.14.0 django-cors-headers==4.3.1 requests pandas numpy

# ساخت migration های اولیه
python backend/manage.py makemigrations

# اجرای migration ها
python backend/manage.py migrate

# ایجاد superuser (اختیاری)
python backend/manage.py createsuperuser

# راه‌اندازی سرور Django
python backend/manage.py runserver
```

Backend در آدرس `http://localhost:8000` در دسترس خواهد بود.

### 2. راه‌اندازی Frontend

در یک ترمینال جدید:

```bash
# رفتن به دایرکتوری frontend
cd frontend

# نصب وابستگی‌ها (در صورت نیاز)
npm install --legacy-peer-deps

# یا با yarn:
yarn install

# راه‌اندازی سرور توسعه
npm run dev
```

Frontend در آدرس `http://localhost:3000` در دسترس خواهد بود.

## نحوه استفاده

1. باز کردن مرورگر و رفتن به `http://localhost:3000`
2. در بخش Dashboard، API keys خود را اضافه کنید
3. یک strategy upload کنید
4. روی "Run Backtest" کلیک کنید

## مشکلات احتمالی و راه حل

### مشکل نصب npm packages
اگر npm install کار نمی‌کند:

```bash
# پاک کردن cache
npm cache clean --force

# یا نصب مجدد با yarn
yarn install
```

### مشکل Celery (Redis)
Celery اختیاری است. برنامه بدون Celery هم کار می‌کند، اما tasks به صورت همزمان اجرا می‌شوند.

### مشکل CORS
اگر frontend نمی‌تواند به backend وصل شود، در `backend/config/settings.py` این خط را اضافه کنید:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

## API Endpoints

پس از راه‌اندازی backend، این API ها در دسترس هستند:

- `GET /api/apis/` - لیست API configurations
- `POST /api/apis/` - اضافه کردن API configuration
- `GET /api/strategies/` - لیست strategies
- `POST /api/strategies/` - آپلود strategy
- `GET /api/jobs/` - لیست jobs
- `POST /api/jobs/` - ایجاد job جدید
- `GET /api/results/` - نتایج backtest

## دسترسی به Admin Panel

برای دسترسی به admin panel:

```
URL: http://localhost:8000/admin/
Username: admin
Password: (ساخته شده با createsuperuser)
```

## ساخت اولیه کاربر admin

```bash
python backend/manage.py createsuperuser
# سپس username, email, password را وارد کنید
```

## ساختار فایل‌ها

```
project/
├── backend/
│   ├── config/       # تنظیمات Django
│   ├── core/         # Models
│   ├── api/          # API views و serializers
│   ├── ai_module/    # AI parsers
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── pages/    # صفحات React
│   │   └── api/      # API client
│   └── package.json
└── venv/             # محیط مجازی Python
```

## نکات مهم

1. **بدون Docker**: برنامه بدون Docker کامل کار می‌کند اما Celery و Redis در دسترس نخواهند بود.
2. **SQLite**: در محیط محلی از SQLite استفاده می‌شود (فایل `db.sqlite3`).
3. **Hot Reload**: برای frontend، Vite به صورت خودکار صفحه را رفرش می‌کند.
4. **پورت‌ها**:
   - Backend: 8000
   - Frontend: 3000

## خاتمه اجرا

برای متوقف کردن سرورها:

- Backend: `Ctrl+C` در ترمینال Django
- Frontend: `Ctrl+C` در ترمینال npm

## تست برنامه

بعد از راه‌اندازی، این URLs را تست کنید:

- Dashboard: http://localhost:3000
- API List: http://localhost:8000/api/apis/
- Admin Panel: http://localhost:8000/admin/

