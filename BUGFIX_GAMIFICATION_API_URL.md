# رفع مشکل URL دوگانه در API گیمیفیکیشن

## 📋 خلاصه مشکل

در زمان اجرای بک‌تست، خطای زیر در لاگ‌های بک‌اند مشاهده می‌شد:

```
Not Found: /api/api/gamification/scores/me/
2025-12-05 22:49:38 [WARNING] django.request: Not Found: /api/api/gamification/scores/me/
```

همچنین بک‌تست به کندی اجرا می‌شد و در نهایت خروجی بک‌تست 0 بود و هیچ اطلاعاتی ثبت نمی‌شد.

## 🔍 علت مشکل

مشکل در فایل `frontend/src/components/GamificationScore.tsx` بود. این کامپوننت برای دریافت امتیاز کاربر از API استفاده می‌کند، اما URL به اشتباه با پیشوند `/api/` فراخوانی می‌شد:

```typescript
const response = await get('/api/gamification/scores/me/')
```

در حالی که در فایل `frontend/src/api/client.ts`، `baseURL` قبلاً به `/api` تنظیم شده است:

```typescript
const client = axios.create({
  baseURL: API_BASE_URL, // که برابر با '/api' است
  ...
})
```

بنابراین وقتی کامپوننت `/api/gamification/scores/me/` را فراخوانی می‌کرد، axios آن را به `baseURL + url` تبدیل می‌کرد که نتیجه آن `/api/api/gamification/scores/me/` می‌شد.

## ✅ راه حل

URL در `GamificationScore.tsx` از `/api/gamification/scores/me/` به `/gamification/scores/me/` تغییر یافت تا با `baseURL` ترکیب شود و URL صحیح `/api/gamification/scores/me/` تولید شود.

### تغییرات انجام شده:

**فایل:** `frontend/src/components/GamificationScore.tsx`

```diff
- const response = await get('/api/gamification/scores/me/')
+ const response = await get('/gamification/scores/me/')
```

## 🧪 تست‌های نوشته شده

فایل تست `backend/tests/test_gamification_endpoint.py` ایجاد شد که شامل تست‌های زیر است:

1. **test_gamification_scores_me_endpoint_exists**: بررسی وجود endpoint
2. **test_gamification_scores_me_returns_user_score**: بررسی بازگشت داده‌های صحیح
3. **test_gamification_scores_me_creates_score_if_not_exists**: بررسی ایجاد خودکار امتیاز
4. **test_gamification_scores_me_requires_authentication**: بررسی نیاز به احراز هویت
5. **test_gamification_scores_me_url_not_doubled**: بررسی عدم وجود `/api/api` در URL

### اجرای تست‌ها:

```bash
cd backend
python manage.py test tests.test_gamification_endpoint
```

## 🔗 ارتباط با مشکل بک‌تست

کامپوننت `GamificationScore` در صفحه `Results` استفاده می‌شود و در زمان نمایش نتایج بک‌تست، این کامپوننت برای نمایش امتیاز کاربر تلاش می‌کند API را فراخوانی کند. اگرچه این فراخوانی مستقیماً بر اجرای بک‌تست تأثیر نمی‌گذارد، اما:

1. خطای 404 در لاگ‌ها ثبت می‌شد
2. درخواست‌های ناموفق ممکن است باعث تأخیر در UI شوند
3. کامپوننت به درستی کار نمی‌کرد و امتیاز کاربر نمایش داده نمی‌شد

**نکته:** مشکل خروجی صفر بک‌تست احتمالاً مشکل جداگانه‌ای است و باید به صورت مستقل بررسی شود. این رفع مشکل فقط مشکل URL گیمیفیکیشن را حل می‌کند.

## 📝 بررسی سایر موارد مشابه

با استفاده از `grep` بررسی شد که آیا موارد مشابه دیگری وجود دارد یا خیر. نتیجه بررسی نشان داد که فقط `GamificationScore.tsx` این مشکل را داشت و سایر فایل‌ها از توابع API client به درستی استفاده می‌کنند.

## ✅ نتیجه

- ✅ مشکل URL دوگانه `/api/api` برطرف شد
- ✅ کامپوننت `GamificationScore` اکنون به درستی کار می‌کند
- ✅ تست‌های جامع برای endpoint نوشته شد
- ✅ هیچ بخش دیگری از سیستم آسیب ندید

## 🚀 مراحل بعدی (پیشنهادی)

برای بررسی مشکل خروجی صفر بک‌تست، موارد زیر پیشنهاد می‌شود:

1. بررسی لاگ‌های بک‌تست برای خطاهای احتمالی
2. بررسی اینکه آیا داده‌های بازار به درستی دریافت می‌شوند
3. بررسی اینکه آیا استراتژی به درستی پارس می‌شود
4. بررسی اینکه آیا شرایط ورود/خروج به درستی ارزیابی می‌شوند
5. بررسی لاگ‌های `BacktestEngine` برای جزئیات بیشتر

