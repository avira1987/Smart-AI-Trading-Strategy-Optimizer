# 🔧 راهنمای تنظیم Google Analytics Data API

## 📋 مراحل تنظیم

### مرحله 1: ایجاد Service Account در Google Cloud Console

1. به [Google Cloud Console](https://console.cloud.google.com/) بروید
2. پروژه خود را انتخاب کنید (یا یک پروژه جدید ایجاد کنید)
3. به **IAM & Admin > Service Accounts** بروید
4. روی **Create Service Account** کلیک کنید
5. نام Service Account را وارد کنید (مثلاً: `analytics-reader`)
6. روی **Create and Continue** کلیک کنید
7. در بخش **Grant this service account access to project**:
   - Role را **Viewer** انتخاب کنید (یا **BigQuery Data Viewer** اگر از BigQuery استفاده می‌کنید)
8. روی **Continue** و سپس **Done** کلیک کنید

### مرحله 2: فعال کردن Google Analytics Data API

1. در Google Cloud Console، به **APIs & Services > Library** بروید
2. در جستجو، **Google Analytics Data API** را تایپ کنید
3. روی **Google Analytics Data API** کلیک کنید
4. روی **Enable** کلیک کنید

### مرحله 3: دانلود JSON Key File

1. به **IAM & Admin > Service Accounts** بروید
2. روی Service Account ایجاد شده کلیک کنید
3. به تب **Keys** بروید
4. روی **Add Key > Create new key** کلیک کنید
5. نوع **JSON** را انتخاب کنید
6. روی **Create** کلیک کنید
7. فایل JSON دانلود می‌شود - آن را در جای امنی نگه دارید

### مرحله 4: تنظیم دسترسی در Google Analytics

1. به [Google Analytics](https://analytics.google.com/) بروید
2. به **Admin** (چرخ دنده) بروید
3. در ستون **Property**، روی **Property Access Management** کلیک کنید
4. روی **+** کلیک کنید
5. ایمیل Service Account را وارد کنید (از فایل JSON: `client_email`)
6. دسترسی را **Viewer** انتخاب کنید
7. روی **Add** کلیک کنید

### مرحله 5: پیدا کردن Property ID

1. در Google Analytics، به **Admin** بروید
2. در ستون **Property**، روی **Property Settings** کلیک کنید
3. **Property ID** را کپی کنید (یک عدد مثل `123456789`)

### مرحله 6: تنظیم متغیرهای محیطی

#### در فایل `.env`:
```bash
# Google Analytics API
GOOGLE_ANALYTICS_SERVICE_ACCOUNT_FILE=C:\path\to\service-account-key.json
GOOGLE_ANALYTICS_PROPERTY_ID=123456789
```

#### یا در PowerShell:
```powershell
$env:GOOGLE_ANALYTICS_SERVICE_ACCOUNT_FILE="C:\path\to\service-account-key.json"
$env:GOOGLE_ANALYTICS_PROPERTY_ID="123456789"
```

### مرحله 7: تست اتصال

```bash
python scripts/test_google_analytics_free_data.py
```

---

## ✅ بررسی تنظیمات

### چک‌لیست:

- [ ] Service Account در Google Cloud Console ایجاد شد
- [ ] Google Analytics Data API فعال شد
- [ ] JSON Key File دانلود شد
- [ ] Service Account به Google Analytics Property دسترسی دارد
- [ ] Property ID پیدا شد
- [ ] متغیرهای محیطی تنظیم شدند
- [ ] تست اتصال موفق بود

---

## 🔒 نکات امنیتی

1. **هرگز فایل JSON Key را در Git commit نکنید**
2. فایل را در `.gitignore` اضافه کنید:
   ```
   *.json
   service-account-key.json
   ```
3. در production، از Environment Variables استفاده کنید
4. دسترسی Service Account را فقط **Viewer** بگذارید (نه Editor یا Admin)

---

## 🐛 رفع مشکلات

### خطا: PERMISSION_DENIED
- **علت**: Service Account به Property دسترسی ندارد
- **راه حل**: مراحل 4 را دوباره انجام دهید

### خطا: NOT_FOUND
- **علت**: Property ID اشتباه است
- **راه حل**: Property ID را دوباره بررسی کنید

### خطا: UNAUTHENTICATED
- **علت**: فایل JSON معتبر نیست
- **راه حل**: فایل JSON را دوباره دانلود کنید

### خطا: API not enabled
- **علت**: Google Analytics Data API فعال نشده
- **راه حل**: مراحل 2 را انجام دهید

---

## 📞 پشتیبانی

اگر مشکلی داشتید:
1. لاگ‌های خطا را بررسی کنید
2. مستندات رسمی Google را مطالعه کنید
3. از اسکریپت تست استفاده کنید

