# دستورات بروزرسانی پروژه در VPS

## 🚀 بروزرسانی سریع (یک خط)

```bash
cd /path/to/SmartAITradingStrategyOptimizer && git pull origin main && cd frontend && npm run build && cd ../backend && source venv/bin/activate && python manage.py collectstatic --noinput && systemctl restart smart-trading-backend
```

---

## 📋 بروزرسانی کامل (مرحله به مرحله)

### 1. Pull آخرین تغییرات از GitHub

```bash
cd /path/to/SmartAITradingStrategyOptimizer
git pull origin main
```

**یا اگر اولین بار است:**
```bash
cd /path/to
git clone https://github.com/avira1987/Smart-AI-Trading-Strategy-Optimizer.git SmartAITradingStrategyOptimizer
cd SmartAITradingStrategyOptimizer
```

### 2. بروزرسانی وابستگی‌های Backend (اگر requirements.txt تغییر کرده)

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### 3. اجرای Migrations جدید (اگر وجود دارد)

```bash
cd backend
source venv/bin/activate
python manage.py migrate
```

### 4. Collect Static Files

```bash
cd backend
source venv/bin/activate
python manage.py collectstatic --noinput
```

### 5. Build Frontend

```bash
cd frontend
npm install  # اگر package.json تغییر کرده
npm run build
```

### 6. Restart سرویس‌ها

#### اگر از Systemd استفاده می‌کنید:

```bash
# Restart Backend
sudo systemctl restart smart-trading-backend

# Restart Celery Worker (اگر سرویس جداگانه دارید)
sudo systemctl restart smart-trading-celery-worker
sudo systemctl restart smart-trading-celery-beat

# Restart Frontend (اگر سرویس جداگانه دارید)
sudo systemctl restart smart-trading-frontend
```

#### اگر از Docker Compose استفاده می‌کنید:

```bash
cd /path/to/SmartAITradingStrategyOptimizer
docker-compose down
docker-compose up -d --build
```

#### اگر به صورت دستی اجرا می‌کنید:

```bash
# توقف پردازه‌های قبلی
pkill -f "gunicorn"
pkill -f "celery"
pkill -f "node.*serve"

# راه‌اندازی مجدد (در ترمینال‌های جداگانه)
cd backend
source venv/bin/activate
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2

# Frontend
cd frontend
npx serve -s dist -l 3000

# Celery Worker
cd backend
source venv/bin/activate
celery -A config worker --loglevel=info

# Celery Beat
cd backend
source venv/bin/activate
celery -A config beat --loglevel=info
```

---

## 🔧 برای Windows VPS (PowerShell)

### 1. Pull تغییرات

```powershell
cd C:\SmartAITradingStrategyOptimizer
git pull origin main
```

### 2. بروزرسانی وابستگی‌ها

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Migrations

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py collectstatic --noinput
```

### 4. Build Frontend

```powershell
cd frontend
npm install
npm run build
```

### 5. Restart سرویس‌ها

اگر از NSSM استفاده می‌کنید:
```powershell
# Restart Backend Service
nssm restart SmartAITradingBackend

# Restart Frontend Service (اگر دارید)
nssm restart SmartAITradingFrontend
```

یا به صورت دستی:
```powershell
# توقف پردازه‌های قبلی
Get-Process | Where-Object { $_.ProcessName -like "*python*" -or $_.ProcessName -like "*node*" } | Stop-Process -Force

# راه‌اندازی مجدد با start.ps1
.\start.ps1
```

---

## ✅ بررسی بعد از بروزرسانی

### 1. بررسی وضعیت سرویس‌ها

```bash
# Linux
sudo systemctl status smart-trading-backend
sudo systemctl status smart-trading-celery-worker

# Windows
Get-Service | Where-Object { $_.Name -like "*SmartAI*" }
```

### 2. بررسی لاگ‌ها

```bash
# Linux
sudo journalctl -u smart-trading-backend -f
tail -f /var/log/smart-trading/backend.log

# Windows
Get-Content C:\SmartAITradingStrategyOptimizer\backend\logs\*.log -Tail 50 -Wait
```

### 3. تست API

```bash
# تست Backend
curl http://YOUR_SERVER_IP:8000/api/

# تست CAPTCHA endpoint
curl -X POST http://YOUR_SERVER_IP:8000/api/captcha/get/ \
  -H "Content-Type: application/json" \
  -d '{"action":"login"}'
```

### 4. تست Frontend

باز کردن مرورگر و بررسی:
- http://YOUR_SERVER_IP:3000
- بررسی Console مرورگر برای خطاها
- تست صفحه لاگین و بررسی لود شدن سوال امنیتی

---

## 🐛 Troubleshooting

### مشکل: "git pull" خطا می‌دهد

```bash
# بررسی وضعیت Git
git status

# اگر فایل‌های local تغییر کرده:
git stash
git pull origin main
git stash pop

# یا اگر می‌خواهید تغییرات local را نادیده بگیرید:
git reset --hard origin/main
```

### مشکل: Frontend build خطا می‌دهد

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### مشکل: Backend خطا می‌دهد

```bash
cd backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python manage.py check
```

### مشکل: سوال امنیتی لود نمی‌شود

**راهنمای کامل عیب‌یابی:** برای جزئیات بیشتر به فایل `docs/CAPTCHA_TROUBLESHOOTING.md` مراجعه کنید.

**راه‌حل‌های سریع:**

1. **بررسی Cache Configuration:**
   - مطمئن شوید که در `backend/config/settings.py` تنظیمات `CACHES` وجود دارد
   - برای production، Redis توصیه می‌شود

2. **بررسی CORS در `backend/config/settings.py`:**
```python
CORS_ALLOWED_ORIGINS = [
    "http://YOUR_SERVER_IP:3000",
    "https://YOUR_DOMAIN.com",
]
```

3. **بررسی لاگ‌های Backend:**
```bash
tail -f backend/logs/api.log
```

4. **بررسی Console مرورگر برای خطاهای JavaScript**

5. **تست API endpoint:**
```bash
curl -X POST http://YOUR_IP:8000/api/captcha/get/ \
  -H "Content-Type: application/json" \
  -d '{"action":"login"}'
```

---

## 📝 خلاصه دستورات (کپی-پیست)

### Linux/Mac:
```bash
cd /path/to/SmartAITradingStrategyOptimizer
git pull origin main
cd backend && source venv/bin/activate && pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput && cd ..
cd frontend && npm install && npm run build && cd ..
sudo systemctl restart smart-trading-backend
```

### Windows (PowerShell):
```powershell
cd C:\SmartAITradingStrategyOptimizer
git pull origin main
cd backend; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt; python manage.py migrate; python manage.py collectstatic --noinput; cd ..
cd frontend; npm install; npm run build; cd ..
.\start.ps1
```

---

**نکته:** بعد از هر بروزرسانی، حتماً صفحه لاگین را تست کنید تا مطمئن شوید سوال امنیتی به درستی لود می‌شود.

