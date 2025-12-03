# چک‌لیست امنیتی - Security Checklist

این چک‌لیست باید قبل از deploy به production بررسی شود.

## 🔴 مشکلات بحرانی (باید فوراً رفع شوند)

- [ ] **SECRET_KEY قوی تنظیم شده**
  - [ ] SECRET_KEY در .env تنظیم شده
  - [ ] SECRET_KEY پیش‌فرض استفاده نمی‌شود
  - [ ] SECRET_KEY حداقل 50 کاراکتر و تصادفی است

- [ ] **DEBUG غیرفعال**
  - [ ] DEBUG=False در .env
  - [ ] DEBUG در production فعال نیست
  - [ ] Error pages اطلاعات حساس نمایش نمی‌دهند

- [ ] **ALLOWED_HOSTS محدود شده**
  - [ ] فقط دامنه‌های مجاز در ALLOWED_HOSTS
  - [ ] استفاده از * حذف شده
  - [ ] IPهای عمومی محدود شده‌اند

- [ ] **CORS محدود شده**
  - [ ] CORS_ALLOW_ALL_ORIGINS=False
  - [ ] فقط origins مجاز در CORS_ALLOWED_ORIGINS
  - [ ] CORS برای production محدود شده

- [ ] **HTTPS فعال**
  - [ ] USE_HTTPS=True در .env
  - [ ] SSL certificate معتبر نصب شده
  - [ ] HTTP به HTTPS redirect می‌شود
  - [ ] HSTS فعال است

- [ ] **API Keys رمزنگاری شده**
  - [ ] API Keys در دیتابیس رمزنگاری شده‌اند
  - [ ] از django-cryptography استفاده می‌شود
  - [ ] کلیدهای رمزنگاری امن نگهداری می‌شوند

- [ ] **اعتبارسنجی فایل‌های آپلود**
  - [ ] نوع فایل بررسی می‌شود
  - [ ] اندازه فایل محدود شده
  - [ ] محتوای فایل (magic bytes) بررسی می‌شود
  - [ ] فایل‌های مخرب رد می‌شوند

- [ ] **لاگ‌های امن**
  - [ ] اطلاعات حساس در لاگ‌ها ثبت نمی‌شوند
  - [ ] OTP codes لاگ نمی‌شوند
  - [ ] API keys لاگ نمی‌شوند
  - [ ] Passwords لاگ نمی‌شوند

## 🟠 مشکلات با اولویت بالا

- [ ] **Rate Limiting مناسب**
  - [ ] Rate limiting برای همه endpoints حساس
  - [ ] استفاده از Redis برای rate limiting
  - [ ] محدودیت مناسب برای هر endpoint

- [ ] **اعتبارسنجی ورودی‌ها**
  - [ ] همه ورودی‌ها اعتبارسنجی می‌شوند
  - [ ] Sanitization انجام می‌شود
  - [ ] از Django validators استفاده می‌شود

- [ ] **Session Management امن**
  - [ ] SESSION_COOKIE_SECURE=True
  - [ ] SESSION_COOKIE_HTTPONLY=True
  - [ ] SESSION_COOKIE_SAMESITE='Lax'
  - [ ] SESSION_COOKIE_AGE مناسب تنظیم شده

- [ ] **Security Headers کامل**
  - [ ] X-Content-Type-Options: nosniff
  - [ ] X-Frame-Options: DENY
  - [ ] X-XSS-Protection: 1; mode=block
  - [ ] Strict-Transport-Security تنظیم شده
  - [ ] Content-Security-Policy تنظیم شده
  - [ ] Referrer-Policy تنظیم شده

- [ ] **Brute Force Protection**
  - [ ] Lockout بعد از تلاش‌های ناموفق
  - [ ] Rate limiting برای authentication
  - [ ] استفاده از django-axes یا مشابه

- [ ] **محدودیت دسترسی Admin**
  - [ ] IP whitelist برای admin
  - [ ] 2FA برای admin accounts
  - [ ] Logging دسترسی‌های admin

- [ ] **محدودیت حجم Request**
  - [ ] DATA_UPLOAD_MAX_MEMORY_SIZE تنظیم شده
  - [ ] FILE_UPLOAD_MAX_MEMORY_SIZE تنظیم شده
  - [ ] محافظت در برابر DoS

- [ ] **رمزنگاری داده‌های حساس**
  - [ ] شماره تلفن‌ها رمزنگاری شده
  - [ ] اطلاعات مالی رمزنگاری شده
  - [ ] اطلاعات شخصی رمزنگاری شده

- [ ] **Logging امنیتی**
  - [ ] Log کردن تلاش‌های ناموفق ورود
  - [ ] Log کردن تغییرات مهم
  - [ ] Centralized logging
  - [ ] Log retention policy

- [ ] **محدودیت دسترسی API**
  - [ ] همه endpoints حساس نیاز به authentication دارند
  - [ ] Permission classes مناسب استفاده شده
  - [ ] Custom permissions برای endpoints حساس

## 🟡 مشکلات با اولویت متوسط

- [ ] **Content Security Policy**
  - [ ] CSP فعال است
  - [ ] Policy مناسب تنظیم شده
  - [ ] Testing انجام شده

- [ ] **Subresource Integrity**
  - [ ] SRI برای منابع خارجی
  - [ ] بررسی integrity checksums

- [ ] **API Versioning**
  - [ ] Versioning پیاده‌سازی شده
  - [ ] Backward compatibility

- [ ] **Request ID Tracing**
  - [ ] Request ID برای همه requests
  - [ ] Correlation در logs

## 🟢 مشکلات با اولویت پایین

- [ ] **Documentation امنیتی**
  - [ ] Security policies مستند شده
  - [ ] Incident response plan
  - [ ] Backup و recovery plan

- [ ] **Security Testing**
  - [ ] Penetration testing انجام شده
  - [ ] Vulnerability scanning
  - [ ] Code review امنیتی

- [ ] **Monitoring**
  - [ ] Security monitoring فعال
  - [ ] Alerting برای anomalies
  - [ ] Dashboard برای security metrics

## 📋 بررسی‌های اضافی

- [ ] **Dependencies**
  - [ ] همه packages به‌روز هستند
  - [ ] Vulnerability scanning انجام شده
  - [ ] از safety check استفاده شده

- [ ] **Database**
  - [ ] Database credentials امن هستند
  - [ ] Connection encryption فعال است
  - [ ] Backup strategy وجود دارد

- [ ] **Backup**
  - [ ] Backup strategy تعریف شده
  - [ ] Backup testing انجام شده
  - [ ] Recovery plan وجود دارد

- [ ] **Incident Response**
  - [ ] Incident response plan وجود دارد
  - [ ] تیم response مشخص شده
  - [ ] Communication plan وجود دارد

## 🔧 ابزارهای پیشنهادی

- [ ] **django-security** نصب شده
- [ ] **django-axes** برای brute force protection
- [ ] **django-cryptography** برای رمزنگاری
- [ ] **django-ratelimit** برای rate limiting
- [ ] **django-otp** برای 2FA
- [ ] **safety** برای vulnerability scanning
- [ ] **bandit** برای static analysis

## 📝 مستندات

- [ ] Security policies مستند شده
- [ ] Incident response plan مستند شده
- [ ] Backup و recovery plan مستند شده
- [ ] Security audit report موجود است

---

**نکته:** این چک‌لیست باید قبل از هر deploy به production بررسی شود.

**تاریخ آخرین بررسی:** _______________

**بررسی کننده:** _______________

**وضعیت:** ☐ تایید شده | ☐ نیاز به بررسی بیشتر

