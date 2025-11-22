# تشخیص منبع خطای Rate Limit

## خلاصه تغییرات

برای تشخیص دقیق منبع خطای Rate Limit، لاگ‌های تشخیصی دقیق‌تری اضافه شد.

### تغییرات انجام شده:

1. **در `backend/api/views.py`**:
   - لاگ‌های دقیق‌تری برای نمایش `status_code` واقعی از API اضافه شد
   - بررسی چند منبع برای تشخیص Rate Limit (API status code، result status code، پیام خطا، raw error)
   - نمایش منابع تشخیص Rate Limit در لاگ

2. **در `backend/ai_module/provider_manager.py`**:
   - لاگ‌های دقیق‌تری برای خطاهای 429 از API
   - لاگ‌های هشدار برای خطاهای غیر-429 برای تشخیص

3. **اسکریپت تست `backend/test_rate_limit_diagnostic.py`**:
   - اسکریپت تست برای بررسی منبع خطای Rate Limit
   - نمایش جزئیات کامل درخواست و پاسخ

## نحوه تشخیص منبع خطا:

### 1. اگر `status_code_from_api == 429`:
   - ✅ این یک خطای واقعی Rate Limit از OpenAI API است
   - ✅ راه‌حل: صبر کنید یا به حساب OpenAI خود برای افزایش محدودیت مراجعه کنید

### 2. اگر `status_code_from_api != 429` اما پیام خطا شامل "rate limit" است:
   - ⚠️ ممکن است از منطق برنامه باشد
   - ⚠️ بررسی لاگ‌ها برای تشخیص دقیق‌تر

### 3. بررسی لاگ‌ها:

لاگ‌های زیر برای تشخیص منبع خطا اضافه شد:

```
================================================================================
❌ AI Analysis Failed for Strategy {id}
Message: {message}
Status Code from API: {status_code_from_api}
Raw Error from API: {raw_error_from_api}
Provider Attempts: {provider_attempts}
Analysis Result Keys: {keys}
Status Code from result: {status_code}
================================================================================
```

و:

```
Rate Limit Detection for Strategy {id}:
is_rate_limit={bool}, sources={list}, api_status_code={code}, message='{msg}'
```

## نحوه استفاده:

### 1. اجرای تست تشخیص:
```bash
cd backend
python test_rate_limit_diagnostic.py
```

### 2. بررسی لاگ‌ها:
- بررسی لاگ‌های backend برای خطاهای Rate Limit
- جستجوی "RATE LIMIT (429) DETECTED FROM API" برای تشخیص خطاهای واقعی از API
- جستجوی "Rate Limit Detection" برای بررسی تشخیص Rate Limit

### 3. در صورت خطای Rate Limit:

#### اگر `status_code_from_api == 429`:
- این یک خطای واقعی از OpenAI API است
- OpenAI واقعاً محدودیت نرخ اعمال کرده است
- راه‌حل: صبر کنید یا به حساب OpenAI خود برای افزایش محدودیت مراجعه کنید

#### اگر `status_code_from_api != 429`:
- ممکن است از منطق برنامه باشد
- بررسی لاگ‌های دقیق‌تر برای تشخیص منبع
