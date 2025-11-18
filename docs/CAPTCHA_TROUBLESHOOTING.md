# راهنمای عیب‌یابی سوال امنیتی (CAPTCHA)

## مشکل: سوال امنیتی در صفحه لاگین نمایش داده نمی‌شود

### علت‌های احتمالی

#### 1. عدم پیکربندی Cache در Django

**مشکل:** Django نیاز به پیکربندی `CACHES` دارد تا CAPTCHA کار کند.

**راه‌حل:**
- بررسی کنید که در `backend/config/settings.py` تنظیمات `CACHES` وجود دارد:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'OPTIONS': {
            'MAX_ENTRIES': 10000
        }
    }
}
```

- برای production، بهتر است از Redis استفاده کنید:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}
```

**بررسی:**
```bash
cd backend
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value', 60)
>>> cache.get('test')  # باید 'value' برگرداند
```

---

#### 2. مشکل CORS

**مشکل:** اگر پروژه از GitHub clone شده و روی IP جدید اجرا می‌شود، ممکن است origin در `CORS_ALLOWED_ORIGINS` نباشد.

**راه‌حل:**

1. **در حالت DEBUG=True:**
   - CORS به صورت خودکار همه origins را می‌پذیرد

2. **در حالت DEBUG=False (Production):**
   - بررسی `backend/config/settings.py`:
   ```python
   CORS_ALLOWED_ORIGINS = [
       "http://localhost:3000",
       "http://127.0.0.1:3000",
       # اضافه کردن IP یا domain جدید
       "http://YOUR_IP:3000",
       "http://YOUR_DOMAIN:3000",
   ]
   ```
   
   - یا از environment variable استفاده کنید:
   ```bash
   # در .env یا environment variables
   CORS_ALLOWED_ORIGINS=http://YOUR_IP:3000,http://YOUR_DOMAIN:3000
   ```

**بررسی:**
- باز کردن Developer Tools (F12)
- تب Network
- درخواست به `/api/captcha/get/` را بررسی کنید
- اگر خطای CORS دیدید، origin را اضافه کنید

---

#### 3. مشکل در API URL Resolution

**مشکل:** Frontend نمی‌تواند به درستی URL بک‌اند را پیدا کند.

**راه‌حل:**

1. **بررسی environment variable:**
   ```bash
   # در frontend/.env
   VITE_BACKEND_URL=http://YOUR_IP:8000
   ```

2. **بررسی console مرورگر:**
   - خطاهای مربوط به fetch یا network را بررسی کنید

3. **تست مستقیم API:**
   ```bash
   curl -X POST http://YOUR_IP:8000/api/captcha/get/ \
     -H "Content-Type: application/json" \
     -d '{"action":"login"}'
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

#### 4. Backend در حال اجرا نیست

**بررسی:**
```bash
# بررسی که backend روی پورت 8000 در حال اجرا است
curl http://localhost:8000/api/

# یا
netstat -an | grep 8000  # Linux/Mac
netstat -an | findstr 8000  # Windows
```

**راه‌حل:**
```bash
cd backend
source venv/bin/activate  # Linux/Mac
# یا
.\venv\Scripts\Activate.ps1  # Windows

python manage.py runserver 0.0.0.0:8000
```

---

#### 5. خطای خاموش در Frontend

**مشکل:** خطا catch می‌شود اما به کاربر نمایش داده نمی‌شود.

**راه‌حل:**
- در `Login.tsx` باید مدیریت خطا بهبود یافته باشد
- خطا باید به صورت toast به کاربر نمایش داده شود
- تلاش مجدد خودکار باید انجام شود

**بررسی:**
- باز کردن Developer Tools (F12)
- تب Console
- خطاهای JavaScript را بررسی کنید

---

### چک‌لیست عیب‌یابی

- [ ] Backend در حال اجرا است؟
- [ ] Cache در Django پیکربندی شده است؟
- [ ] CORS به درستی تنظیم شده است؟
- [ ] API endpoint `/api/captcha/get/` پاسخ می‌دهد؟
- [ ] Console مرورگر خطایی نشان نمی‌دهد؟
- [ ] Network tab درخواست را نشان می‌دهد؟
- [ ] Environment variables به درستی تنظیم شده‌اند؟

---

### تست دستی

1. **باز کردن صفحه لاگین:**
   ```
   http://YOUR_IP:3000/login
   ```

2. **بررسی Console (F12):**
   - باید خطایی نباشد
   - باید درخواست به `/api/captcha/get/` موفق باشد

3. **بررسی Network Tab:**
   - درخواست POST به `/api/captcha/get/`
   - Status باید 200 باشد
   - Response باید شامل `challenge` باشد

4. **بررسی UI:**
   - باید سوال امنیتی (مثلاً "5 + 3 = ?") نمایش داده شود
   - دکمه refresh باید کار کند

---

### لاگ‌های مفید

**Backend:**
```bash
# لاگ‌های Django
tail -f backend/logs/api.log

# یا اگر از systemd استفاده می‌کنید:
sudo journalctl -u smart-trading-backend -f
```

**Frontend:**
- Developer Tools > Console
- Developer Tools > Network

---

### راه‌حل‌های سریع

#### اگر همه چیز درست است اما CAPTCHA نمایش داده نمی‌شود:

1. **پاک کردن cache مرورگر:**
   - Ctrl+Shift+Delete (Windows/Linux)
   - Cmd+Shift+Delete (Mac)

2. **Restart کردن Backend:**
   ```bash
   # Linux
   sudo systemctl restart smart-trading-backend
   
   # Windows
   # Restart service یا kill process و restart
   ```

3. **بررسی که cache directory وجود دارد:**
   ```bash
   ls -la backend/cache/  # Linux/Mac
   dir backend\cache\     # Windows
   ```

4. **تست مجدد API:**
   ```bash
   python manage.py shell
   >>> from django.core.cache import cache
   >>> cache.clear()  # پاک کردن cache
   ```

---

### تماس با پشتیبانی

اگر مشکل حل نشد، اطلاعات زیر را جمع‌آوری کنید:

1. لاگ‌های Backend
2. Screenshot از Console مرورگر
3. Screenshot از Network tab
4. نسخه Django و Python
5. سیستم عامل و نسخه
6. نحوه اجرای پروژه (Docker, systemd, manual, etc.)

---

**آخرین بروزرسانی:** 2024

