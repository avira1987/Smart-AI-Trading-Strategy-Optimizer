# راهنمای تنظیم DDNS (Dynamic DNS)

## 🎯 هدف
استفاده از DDNS برای دسترسی به سرور از طریق یک دامنه عمومی (مثلاً `mydomain.duckdns.org`) به جای IP که ممکن است تغییر کند.

---

## 📋 سرویس‌های رایگان DDNS

### 1. DuckDNS (پیشنهاد می‌شود)
- ✅ کاملاً رایگان
- ✅ بدون نیاز به تایید
- ✅ ساده‌ترین تنظیمات

### 2. No-IP
- ✅ رایگان
- ⚠️ نیاز به تایید ماهانه

### 3. Dynu
- ✅ رایگان
- ⚠️ نیاز به تایید

### 4. FreeDNS
- ✅ رایگان
- ⚠️ نیاز به ثبت‌نام

---

## 🔧 راهنمای تنظیم DuckDNS (پیشنهاد می‌شود)

### مرحله 1: ثبت‌نام در DuckDNS

1. به [duckdns.org](https://www.duckdns.org/) بروید
2. روی **"Sign In with Google"** یا **"Sign In with GitHub"** کلیک کنید
3. با حساب Google/GitHub خود وارد شوید

### مرحله 2: ایجاد دامنه

1. بعد از ورود، یک دامنه انتخاب کنید (مثلاً `myforex`)
2. دامنه شما خواهد بود: `myforex.duckdns.org`
3. روی **"Add domain"** کلیک کنید

### مرحله 3: دریافت Token

1. در صفحه اصلی، **Token** خود را کپی کنید
2. این Token را در تنظیمات DDNS در پنل ادمین وارد کنید

### مرحله 4: تنظیم در پنل ادمین

1. به پنل ادمین بروید: `http://YOUR_IP:8000/admin/`
2. وارد شوید (admin/admin)
3. به بخش **"DDNS Configurations"** بروید
4. روی **"Add DDNS Configuration"** کلیک کنید
5. این اطلاعات را وارد کنید:
   - **Provider**: DuckDNS (رایگان)
   - **Domain**: `myforex` (بدون `.duckdns.org`)
   - **Token**: Token که از DuckDNS کپی کردید
   - **Is Enabled**: ✅ تیک بزنید
   - **Update Interval Minutes**: `5` (هر 5 دقیقه)
6. **Save** کنید

### مرحله 5: تست

1. در صفحه DDNS Configuration، روی تنظیمات کلیک کنید
2. دکمه **"Test"** را بزنید (یا از API استفاده کنید)
3. باید پیام موفقیت ببینید

---

## 🔧 راهنمای تنظیم No-IP

### مرحله 1: ثبت‌نام

1. به [noip.com](https://www.noip.com/) بروید
2. ثبت‌نام کنید (رایگان)
3. یک دامنه انتخاب کنید (مثلاً `myforex.ddns.net`)

### مرحله 2: تنظیم در پنل ادمین

1. **Provider**: No-IP (رایگان)
2. **Domain**: دامنه کامل (مثلاً `myforex.ddns.net`)
3. **Username**: نام کاربری No-IP
4. **Password**: رمز عبور No-IP
5. **Is Enabled**: ✅ تیک بزنید

---

## 🔧 راهنمای تنظیم Dynu

### مرحله 1: ثبت‌نام

1. به [dynu.com](https://www.dynu.com/) بروید
2. ثبت‌نام کنید
3. یک دامنه ایجاد کنید

### مرحله 2: تنظیم در پنل ادمین

1. **Provider**: Dynu (رایگان)
2. **Domain**: دامنه کامل
3. **Username**: نام کاربری Dynu
4. **Password**: رمز عبور Dynu
5. **Is Enabled**: ✅ تیک بزنید

---

## 🔧 راهنمای تنظیم سرویس سفارشی

اگر از سرویس DDNS دیگری استفاده می‌کنید:

1. **Provider**: سرویس سفارشی
2. **Update URL**: URL به‌روزرسانی سرویس شما
   - مثال: `https://example.com/update?domain=DOMAIN&token=TOKEN&ip=IP`
   - `IP` به صورت خودکار جایگزین می‌شود

---

## 📊 به‌روزرسانی خودکار

سیستم به‌صورت خودکار:
- هر 5 دقیقه IP عمومی را بررسی می‌کند
- اگر IP تغییر کند، DDNS را به‌روزرسانی می‌کند
- اگر IP تغییر نکرده باشد، به‌روزرسانی نمی‌کند (صرفه‌جویی در API calls)

---

## 🔍 API Endpoints

### دریافت لیست تنظیمات DDNS (فقط ادمین):
```
GET /api/ddns-configurations/
```

### ایجاد تنظیمات جدید:
```
POST /api/ddns-configurations/
Body: {
  "provider": "duckdns",
  "domain": "myforex",
  "token": "YOUR_TOKEN",
  "is_enabled": true,
  "update_interval_minutes": 5
}
```

### تست تنظیمات:
```
POST /api/ddns-configurations/{id}/test/
```

### به‌روزرسانی دستی:
```
POST /api/ddns-configurations/update_now/
```

### دریافت IP عمومی:
```
GET /api/ddns-configurations/get_public_ip/
```

---

## ⚠️ نکات مهم

1. **فقط یک تنظیمات فعال**: فقط یک DDNS configuration می‌تواند فعال باشد

2. **Port Forwarding**: برای دسترسی از اینترنت:
   - پورت 8000 (Backend) را در Router باز کنید
   - پورت 3000 (Frontend) را در Router باز کنید
   - یا از Reverse Proxy استفاده کنید (nginx)

3. **امنیت**: 
   - در production از HTTPS استفاده کنید
   - فایروال را تنظیم کنید
   - فقط IPهای معتبر را allow کنید

4. **Celery Beat**: برای به‌روزرسانی خودکار، Celery Beat باید در حال اجرا باشد

---

## 🆘 عیب‌یابی

### مشکل: DDNS به‌روزرسانی نمی‌شود
1. لاگ‌های Backend را بررسی کنید: `backend/logs/api.log`
2. Token/Username/Password را بررسی کنید
3. Celery Beat را بررسی کنید (باید در حال اجرا باشد)

### مشکل: IP عمومی دریافت نمی‌شود
1. اتصال اینترنت را بررسی کنید
2. فایروال را بررسی کنید
3. سرویس‌های IP detection را بررسی کنید

### مشکل: دامنه کار نمی‌کند
1. چند دقیقه صبر کنید (DNS propagation)
2. با `ping mydomain.duckdns.org` تست کنید
3. مطمئن شوید که DDNS به‌روزرسانی شده است

---

## ✅ چک‌لیست

- [ ] در DuckDNS/No-IP/Dynu ثبت‌نام کرده‌ام
- [ ] دامنه ایجاد کرده‌ام
- [ ] Token/Username/Password را دریافت کرده‌ام
- [ ] تنظیمات را در پنل ادمین وارد کرده‌ام
- [ ] Is Enabled را فعال کرده‌ام
- [ ] تست انجام داده‌ام و موفق بوده
- [ ] Celery Beat در حال اجرا است
- [ ] Port Forwarding انجام داده‌ام (برای دسترسی از اینترنت)

---

## 📞 دسترسی به سرور

بعد از تنظیم DDNS، می‌توانید از این آدرس‌ها استفاده کنید:

- **Frontend**: `http://mydomain.duckdns.org:3000`
- **Backend**: `http://mydomain.duckdns.org:8000`
- **Admin**: `http://mydomain.duckdns.org:8000/admin/`

**نکته**: برای استفاده از HTTPS، باید یک Reverse Proxy (nginx) تنظیم کنید و SSL certificate نصب کنید.

