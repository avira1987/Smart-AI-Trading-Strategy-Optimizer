# راهنمای تنظیم reCAPTCHA v3 برای محافظت از بات‌ها

این راهنما نحوه تنظیم reCAPTCHA v3 را برای محافظت از وب‌سایت در برابر بات‌ها و حملات خودکار توضیح می‌دهد.

## ویژگی‌های پیاده‌سازی شده

✅ **reCAPTCHA v3** - محافظت نامرئی و سبک  
✅ **Rate Limiting** - محدودیت تعداد درخواست‌ها  
✅ **Bot Detection** - تشخیص و مسدودسازی بات‌ها  
✅ **Security Headers** - هدرهای امنیتی  
✅ **محافظت از Endpoint های حساس**:
   - ورود با شماره موبایل (Send OTP)
   - تایید کد OTP
   - ورود با Google OAuth
   - دریافت قیمت طلا
   - معاملات دمو

## مراحل تنظیم

### 1. دریافت کلیدهای reCAPTCHA

1. به [Google reCAPTCHA Admin Console](https://www.google.com/recaptcha/admin/create) بروید
2. یک سایت جدید ایجاد کنید:
   - **Label**: نام سایت شما (مثلاً: AI Trading Strategy Optimizer)
   - **reCAPTCHA type**: **reCAPTCHA v3** را انتخاب کنید
   - **Domains**: دامنه‌های خود را اضافه کنید:
     - `localhost` (برای توسعه)
     - `127.0.0.1` (برای توسعه)
     - دامنه تولیدی شما (مثلاً: `yourdomain.com`)
3. پس از ایجاد، دو کلید دریافت می‌کنید:
   - **Site Key** (کلید عمومی - برای Frontend)
   - **Secret Key** (کلید خصوصی - برای Backend)

### 2. تنظیم Backend

#### روش 1: استفاده از Environment Variables

فایل `.env` را ویرایش کنید:

```env
# reCAPTCHA v3
RECAPTCHA_SITE_KEY=your-site-key-here
RECAPTCHA_SECRET_KEY=your-secret-key-here
```

#### روش 2: استفاده از Admin Panel

1. به Admin Panel بروید (`/admin/`)
2. به بخش **API Configurations** بروید
3. یک Configuration جدید ایجاد کنید:
   - **Provider**: `reCAPTCHA v3 (Site Key & Secret Key)` را انتخاب کنید
   - **API Key**: کلید Secret Key را وارد کنید
   - **Is Active**: تیک بزنید
4. برای Site Key، یک Configuration دیگر ایجاد کنید (یا از Environment Variable استفاده کنید)

### 3. تنظیم Frontend

فایل `.env` یا `.env.local` در پوشه `frontend/` را ویرایش کنید:

```env
VITE_RECAPTCHA_SITE_KEY=your-site-key-here
```

یا در `vite.config.ts`:

```typescript
define: {
  'import.meta.env.VITE_RECAPTCHA_SITE_KEY': JSON.stringify(process.env.VITE_RECAPTCHA_SITE_KEY || '')
}
```

### 4. راه‌اندازی مجدد

پس از تنظیم کلیدها:

```bash
# Backend
cd backend
python manage.py runserver

# Frontend
cd frontend
npm run dev
```

## نحوه کار

### reCAPTCHA v3

- **نامرئی**: کاربر هیچ چک‌باکسی نمی‌بیند
- **Score-based**: Google یک امتیاز از 0.0 (بات) تا 1.0 (انسان) می‌دهد
- **Action-based**: هر عملیات (login, send_otp, etc.) یک action جداگانه دارد

### Rate Limiting

محدودیت‌های پیش‌فرض:
- **Send OTP**: 5 درخواست در 5 دقیقه
- **Verify OTP**: 10 درخواست در 1 دقیقه
- **Google OAuth**: 5 درخواست در 1 دقیقه
- **Gold Price**: 30 درخواست در 1 دقیقه
- **Demo Trades**: 20 درخواست در 1 دقیقه

در صورت تجاوز از حد، IP برای 5 دقیقه مسدود می‌شود.

### Bot Detection

- تشخیص User Agent های مشکوک (bot, crawler, scraper, etc.)
- مسدودسازی درخواست‌های بدون User Agent
- افزودن Security Headers به پاسخ‌ها

## تست

### تست در Development

در حالت Development، اگر reCAPTCHA تنظیم نشده باشد:
- Backend درخواست‌ها را می‌پذیرد (fail open)
- Frontend بدون خطا کار می‌کند

### تست در Production

1. کلیدهای reCAPTCHA را تنظیم کنید
2. یک درخواست ارسال کنید
3. در Console Backend، لاگ‌های reCAPTCHA را بررسی کنید:
   ```
   reCAPTCHA verified: score=0.9, action=send_otp
   ```

## تنظیمات پیشرفته

### تغییر Threshold Score

در `backend/api/auth_views.py`:

```python
# برای Send OTP (حساس‌تر)
if not is_human(recaptcha_result['score'], threshold=0.5):

# برای Verify OTP (کمتر حساس)
if not is_human(recaptcha_result['score'], threshold=0.4):
```

### تغییر Rate Limits

در `backend/api/rate_limiter.py`:

```python
RATE_LIMITS = {
    '/api/auth/send-otp/': (5, 300),  # (max_requests, window_seconds)
    # ...
}
```

### غیرفعال کردن reCAPTCHA (Development)

اگر می‌خواهید در Development reCAPTCHA را غیرفعال کنید:

1. کلیدها را تنظیم نکنید
2. یا در `backend/api/recaptcha.py`، threshold را کاهش دهید

## عیب‌یابی

### خطا: "reCAPTCHA token missing"

- مطمئن شوید Site Key در Frontend تنظیم شده است
- Console Browser را بررسی کنید برای خطاهای JavaScript
- مطمئن شوید reCAPTCHA script بارگذاری شده است

### خطا: "reCAPTCHA verification failed"

- Secret Key را بررسی کنید
- Domain را در Google reCAPTCHA Console بررسی کنید
- IP شما ممکن است در لیست سیاه باشد

### Score همیشه پایین است

- ممکن است از VPN یا Proxy استفاده می‌کنید
- سعی کنید از IP واقعی خود استفاده کنید
- Threshold را موقتاً کاهش دهید

## امنیت

⚠️ **مهم**: 
- Secret Key را **هرگز** در Frontend قرار ندهید
- Secret Key را در Git commit نکنید
- از Environment Variables یا Admin Panel استفاده کنید
- در Production، HTTPS را فعال کنید

## منابع

- [Google reCAPTCHA Documentation](https://developers.google.com/recaptcha/docs/v3)
- [reCAPTCHA Admin Console](https://www.google.com/recaptcha/admin)

