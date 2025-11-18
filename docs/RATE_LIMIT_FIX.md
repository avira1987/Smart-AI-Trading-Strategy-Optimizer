# راهنمای حل مشکل Rate Limiting و CAPTCHA Time Validation

## مشکلات حل شده

### 1. مشکل: "درخواست شما خیلی سریع ارسال شد"
**علت:** CAPTCHA time validation خیلی سخت‌گیرانه بود (2 ثانیه)

**راه‌حل:**
- کاهش `CAPTCHA_MIN_TIME` از 2 ثانیه به 0.5 ثانیه
- اجازه دادن به درخواست‌هایی که `page_load_time` ندارند (اولین بار باز کردن صفحه)
- بهبود پیام خطا

### 2. مشکل: "Too many requests. Please try again in X seconds"
**علت:** Rate limiting برای localhost هم اعمال می‌شد

**راه‌حل:**
- غیرفعال کردن rate limiting برای localhost/127.0.0.1 در DEBUG mode
- این باعث می‌شود در development مشکلی نداشته باشید

---

## تغییرات انجام شده

### 1. `backend/api/self_captcha.py`
- `CAPTCHA_MIN_TIME` از 2 به 0.5 ثانیه کاهش یافت
- اجازه دادن به درخواست‌هایی که `page_load_time` ندارند
- بهبود منطق validation

### 2. `backend/api/rate_limiter.py`
- اضافه شدن exception برای localhost در DEBUG mode
- اضافه شدن تابع `clear_rate_limit_for_ip()` برای testing

---

## نحوه استفاده

### پاک کردن Rate Limit برای IP خاص

اگر IP شما block شده است:

```python
# در Django shell
python manage.py shell

>>> from api.rate_limiter import clear_rate_limit_for_ip
>>> clear_rate_limit_for_ip('127.0.0.1')
>>> clear_rate_limit_for_ip('YOUR_IP')
```

### پاک کردن همه Rate Limits

```python
# در Django shell
python manage.py shell

>>> from api.rate_limiter import rate_limiter
>>> rate_limiter.blocked_ips.clear()
>>> rate_limiter.requests.clear()
```

---

## تنظیمات

### CAPTCHA Time Validation

در `backend/api/self_captcha.py`:

```python
CAPTCHA_MIN_TIME = 0.5  # حداقل 0.5 ثانیه (قبلاً 2 ثانیه)
CAPTCHA_MAX_TIME = 600  # حداکثر 10 دقیقه
```

### Rate Limiting

در `backend/api/rate_limiter.py`:

```python
RATE_LIMITS = {
    '/api/auth/send-otp/': (5, 300),  # 5 درخواست در 5 دقیقه
    '/api/auth/verify-otp/': (10, 60),  # 10 درخواست در 1 دقیقه
    # ...
}
```

**نکته:** در DEBUG mode، localhost از rate limiting معاف است.

---

## تست

### تست CAPTCHA

1. باز کردن صفحه لاگین
2. وارد کردن شماره موبایل
3. حل کردن سوال امنیتی
4. ارسال فرم

**انتظار:** باید بدون خطا کار کند.

### تست Rate Limiting

1. در DEBUG mode، localhost نباید rate limit شود
2. در production، rate limiting باید کار کند

---

## عیب‌یابی

### اگر هنوز "Too many requests" می‌بینید:

1. **بررسی DEBUG mode:**
   ```python
   # در settings.py
   DEBUG = True  # باید True باشد برای localhost exception
   ```

2. **پاک کردن Rate Limit:**
   ```python
   python manage.py shell
   >>> from api.rate_limiter import rate_limiter
   >>> rate_limiter.blocked_ips.clear()
   >>> rate_limiter.requests.clear()
   ```

3. **Restart Backend:**
   ```bash
   # متوقف کردن
   Ctrl+C
   
   # راه‌اندازی مجدد
   python manage.py runserver
   ```

### اگر هنوز "خیلی سریع ارسال شد" می‌بینید:

1. **بررسی page_load_time:**
   - در Console مرورگر (F12) بررسی کنید
   - باید بعد از لود شدن صفحه، چند ثانیه صبر کنید

2. **Refresh صفحه:**
   - صفحه را refresh کنید
   - دوباره تلاش کنید

---

## نکات مهم

1. **در Development:**
   - Rate limiting برای localhost غیرفعال است
   - CAPTCHA time validation نرم‌تر است

2. **در Production:**
   - Rate limiting فعال است
   - CAPTCHA time validation کار می‌کند

3. **برای Testing:**
   - می‌توانید rate limit را پاک کنید
   - یا از IP دیگری استفاده کنید

---

**آخرین بروزرسانی:** 2024

