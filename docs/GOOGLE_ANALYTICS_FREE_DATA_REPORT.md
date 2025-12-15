# 📊 گزارش داده‌های رایگان Google Analytics API

## ✅ خلاصه

Google Analytics Data API به صورت **کاملاً رایگان** است و محدودیت‌های زیر را دارد:
- **10 میلیون درخواست در ماه** (بیش از کافی برای اکثر پروژه‌ها)
- **10 درخواست در ثانیه** (Rate Limit)
- **داده‌های تاریخی تا 14 ماه گذشته**

---

## 📋 داده‌های قابل دسترس (رایگان)

### 1️⃣ Metric های پایه (Basic Metrics)

این Metric ها بدون هیچ تنظیمات اضافی در دسترس هستند:

| Metric | نام فارسی | توضیحات |
|--------|-----------|---------|
| `activeUsers` | کاربران فعال | تعداد کاربرانی که در بازه زمانی مشخص فعال بودند |
| `newUsers` | کاربران جدید | تعداد کاربرانی که برای اولین بار بازدید کردند |
| `totalUsers` | کل کاربران | تعداد کل کاربران منحصر به فرد |
| `sessions` | جلسات | تعداد جلسات کاربران |
| `screenPageViews` | بازدید صفحات | تعداد بازدید صفحات |
| `pageViews` | بازدید صفحات | (مشابه screenPageViews) |
| `averageSessionDuration` | میانگین مدت جلسه | به ثانیه |
| `bounceRate` | نرخ پرش | درصد کاربرانی که فقط یک صفحه را دیدند |
| `engagementRate` | نرخ تعامل | درصد جلسات تعاملی |
| `engagedSessions` | جلسات تعاملی | تعداد جلساتی که تعامل داشتند |
| `eventCount` | تعداد رویدادها | تعداد کل رویدادها |
| `conversions` | تبدیل‌ها | تعداد تبدیل‌ها (نیاز به تنظیم) |
| `totalRevenue` | کل درآمد | درآمد کل (نیاز به تنظیم) |
| `purchaseRevenue` | درآمد خرید | درآمد از خریدها (نیاز به تنظیم) |
| `transactions` | تراکنش‌ها | تعداد تراکنش‌ها (نیاز به تنظیم) |
| `itemsPurchased` | آیتم‌های خریداری شده | تعداد آیتم‌های خریداری شده |

### 2️⃣ Dimension های قابل دسترس

#### 📅 Dimension های زمانی:
- `date` - تاریخ (YYYYMMDD)
- `year` - سال
- `month` - ماه
- `week` - هفته
- `day` - روز
- `hour` - ساعت
- `minute` - دقیقه

#### 🌍 Dimension های جغرافیایی:
- `country` - کشور
- `region` - منطقه/استان
- `city` - شهر
- `continent` - قاره
- `subContinent` - زیرقاره
- `metro` - منطقه مترو

#### 📱 Dimension های دستگاه:
- `deviceCategory` - نوع دستگاه (desktop, mobile, tablet)
- `mobileDeviceInfo` - اطلاعات موبایل
- `mobileDeviceBranding` - برند موبایل
- `mobileDeviceModel` - مدل موبایل
- `operatingSystem` - سیستم عامل
- `operatingSystemVersion` - نسخه سیستم عامل
- `browser` - مرورگر
- `browserVersion` - نسخه مرورگر
- `screenResolution` - رزولوشن صفحه
- `language` - زبان

#### 📄 Dimension های صفحات:
- `pagePath` - مسیر صفحه (مثل `/dashboard`)
- `pageTitle` - عنوان صفحه
- `pageLocation` - آدرس کامل صفحه
- `hostName` - نام هاست

#### 🔗 Dimension های ترافیک:
- `source` - منبع (مثل google, direct)
- `medium` - رسانه (مثل organic, cpc)
- `campaign` - کمپین
- `sessionSource` - منبع جلسه
- `sessionMedium` - رسانه جلسه
- `sessionCampaign` - کمپین جلسه
- `sessionDefaultChannelGroup` - گروه کانال پیش‌فرض

#### 👤 Dimension های کاربر:
- `userAgeBracket` - گروه سنی
- `userGender` - جنسیت
- `newVsReturning` - کاربر جدید/بازگشتی
- `sessionId` - شناسه جلسه
- `clientId` - شناسه کلاینت
- `userId` - شناسه کاربر (نیاز به تنظیم)

---

## 🎯 داده‌های مفید برای بخش ادمین

### ✅ داده‌هایی که می‌توانید استفاده کنید:

#### 1. آمار کلی بازدیدها:
```python
# دریافت آمار 7 روز گذشته
metrics = ["activeUsers", "newUsers", "sessions", "screenPageViews"]
dimensions = ["date"]
```

#### 2. صفحات پربازدید:
```python
# 10 صفحه پربازدید
metrics = ["screenPageViews", "activeUsers"]
dimensions = ["pagePath", "pageTitle"]
order_by = "screenPageViews" (descending)
limit = 10
```

#### 3. کاربران بر اساس کشور:
```python
metrics = ["activeUsers"]
dimensions = ["country"]
order_by = "activeUsers" (descending)
```

#### 4. نوع دستگاه:
```python
metrics = ["activeUsers", "sessions"]
dimensions = ["deviceCategory"]
```

#### 5. منابع ترافیک:
```python
metrics = ["sessions", "activeUsers"]
dimensions = ["sessionSource", "sessionMedium", "sessionDefaultChannelGroup"]
```

#### 6. سری زمانی (نمودار):
```python
# آمار روزانه برای نمودار
metrics = ["activeUsers", "sessions", "screenPageViews"]
dimensions = ["date"]
order_by = "date" (ascending)
```

#### 7. کاربران جدید vs بازگشتی:
```python
metrics = ["activeUsers", "sessions"]
dimensions = ["newVsReturning"]
```

#### 8. مدت زمان حضور:
```python
# میانگین مدت جلسه
metrics = ["averageSessionDuration", "sessions"]
dimensions = ["date"]
```

---

## ⚠️ محدودیت‌ها و نکات مهم

### ❌ داده‌هایی که **نیاز به تنظیمات خاص** دارند:

1. **userId** - برای ردیابی کاربران خاص:
   - باید در frontend با `gtag('config', 'GA_MEASUREMENT_ID', {user_id: 'USER_ID'})` تنظیم شود
   - فقط برای کاربران لاگین شده کار می‌کند

2. **Conversions & Revenue** - برای ردیابی تبدیل‌ها:
   - نیاز به تنظیم Goals در Google Analytics
   - نیاز به ارسال رویدادهای ecommerce

3. **Custom Events** - برای رویدادهای سفارشی:
   - باید در frontend با `gtag('event', 'event_name', {...})` ارسال شوند

### ✅ داده‌هایی که **بدون تنظیمات** در دسترس هستند:

- ✅ آمار کلی بازدیدها
- ✅ صفحات پربازدید
- ✅ اطلاعات جغرافیایی
- ✅ اطلاعات دستگاه
- ✅ منابع ترافیک
- ✅ سری زمانی
- ✅ مدت زمان حضور (میانگین)
- ✅ کاربران جدید vs بازگشتی

---

## 💡 توصیه برای پیاده‌سازی

### روش ترکیبی (پیشنهادی):

#### 1. Google Analytics API برای:
- ✅ آمار کلی بازدیدها (همه کاربران)
- ✅ صفحات پربازدید
- ✅ اطلاعات جغرافیایی
- ✅ منابع ترافیک
- ✅ نمودارهای سری زمانی

#### 2. Database Internal برای:
- ✅ ردیابی دقیق کاربران لاگین شده
- ✅ زمان ورود/خروج دقیق
- ✅ مسیرهای ناوبری کاربران خاص
- ✅ مدت زمان حضور دقیق در هر صفحه

---

## 📊 مثال داده‌های قابل دریافت

### مثال 1: آمار 7 روز گذشته
```json
{
  "date": "2024-01-15",
  "activeUsers": 1250,
  "newUsers": 320,
  "sessions": 1850,
  "screenPageViews": 5420,
  "averageSessionDuration": 245.5
}
```

### مثال 2: صفحات پربازدید
```json
[
  {
    "pagePath": "/dashboard",
    "pageTitle": "Dashboard",
    "screenPageViews": 1250,
    "activeUsers": 850
  },
  {
    "pagePath": "/login",
    "pageTitle": "Login",
    "screenPageViews": 980,
    "activeUsers": 980
  }
]
```

### مثال 3: کاربران بر اساس کشور
```json
[
  {"country": "Iran", "activeUsers": 850},
  {"country": "United States", "activeUsers": 120},
  {"country": "Germany", "activeUsers": 45}
]
```

### مثال 4: نوع دستگاه
```json
[
  {"deviceCategory": "desktop", "activeUsers": 650, "sessions": 920},
  {"deviceCategory": "mobile", "activeUsers": 480, "sessions": 720},
  {"deviceCategory": "tablet", "activeUsers": 120, "sessions": 210}
]
```

---

## 🚀 مراحل بعدی

1. ✅ کتابخانه‌ها نصب شدند
2. ⏳ تنظیم Service Account در Google Cloud Console
3. ⏳ تنظیم Property ID
4. ⏳ اجرای تست کامل
5. ⏳ پیاده‌سازی API endpoint در backend
6. ⏳ ایجاد صفحه Analytics در بخش ادمین

---

## 📚 منابع

- [Google Analytics Data API Documentation](https://developers.google.com/analytics/devguides/reporting/data/v1)
- [Available Dimensions](https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema#dimensions)
- [Available Metrics](https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema#metrics)

