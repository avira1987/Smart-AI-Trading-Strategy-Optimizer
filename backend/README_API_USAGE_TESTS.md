# تست‌های سیستم ردیابی استفاده از API

## 📋 خلاصه

این فایل شامل تست‌های جامع برای سیستم ردیابی استفاده از API است که بررسی می‌کند:

1. ✅ لاگ‌گیری برای همه provider ها به درستی کار می‌کند
2. ✅ آمار بر اساس provider به درستی محاسبه می‌شود
3. ✅ فیلترها (تاریخ، provider، user) به درستی کار می‌کنند
4. ✅ محاسبه هزینه برای همه provider ها صحیح است
5. ✅ Endpoint های API به درستی کار می‌کنند

## 🧪 فایل‌های تست

### 1. `test_api_usage_tracking.py`
تست‌های جامع برای سیستم ردیابی استفاده از API:

```bash
cd backend
python test_api_usage_tracking.py
```

**تست‌های موجود:**
- `test_calculate_api_cost()` - تست محاسبه هزینه برای همه provider ها
- `test_log_api_usage_all_providers()` - تست لاگ‌گیری برای همه provider ها
- `test_get_api_usage_stats_all_providers()` - تست دریافت آمار
- `test_filter_by_date()` - تست فیلتر بر اساس تاریخ
- `test_filter_by_user()` - تست فیلتر بر اساس کاربر
- `test_provider_stats_structure()` - تست ساختار آمار provider ها
- `test_api_usage_stats_endpoint()` - تست endpoint آمار API

### 2. `test_api_usage_endpoints.py`
تست‌های endpoint های API با استفاده از Django Test Client:

```bash
cd backend
python test_api_usage_endpoints.py
```

**تست‌های موجود:**
- `test_admin_api_usage_stats_endpoint()` - تست endpoint ادمین
- `test_admin_api_usage_stats_with_provider_filter()` - تست فیلتر provider
- `test_admin_api_usage_stats_with_days_filter()` - تست فیلتر days
- `test_user_api_usage_stats_endpoint()` - تست endpoint کاربر
- `test_provider_stats_structure()` - تست ساختار آمار
- `test_all_providers_in_stats()` - تست حضور همه provider ها

## 🔍 بررسی مشکل: فقط MT5 در مانیتورینگ نمایش داده می‌شود

### مشکل گزارش شده
در قسمت مانیتورینگ، آمار بر اساس Provider فقط داده MetaTrader 5 به درستی نمایش داده می‌شود.

### بررسی انجام شده

#### ✅ تست‌ها نشان می‌دهند که:
1. **همه provider ها به درستی لاگ می‌شوند** - تست `test_log_api_usage_all_providers()` موفق است
2. **آمار همه provider ها محاسبه می‌شود** - تست `test_get_api_usage_stats_all_providers()` نشان می‌دهد که 11 provider در آمار موجود است
3. **فیلتر provider به درستی کار می‌کند** - تست `test_api_usage_stats_endpoint()` موفق است

#### 🔎 علل احتمالی مشکل:

1. **عدم وجود لاگ واقعی برای سایر provider ها:**
   - ممکن است در محیط production، فقط MT5 استفاده شده باشد
   - سایر provider ها ممکن است هنوز استفاده نشده باشند

2. **مشکل در Frontend:**
   - ممکن است frontend به درستی داده‌ها را نمایش ندهد
   - بررسی کنید که آیا `provider_stats` به درستی از response استخراج می‌شود

3. **مشکل در لاگ‌گیری واقعی:**
   - بررسی کنید که آیا سایر provider ها در کد واقعی لاگ می‌شوند
   - بررسی کنید که آیا `log_api_usage` در همه جاهای لازم فراخوانی می‌شود

### راه‌حل‌های پیشنهادی

#### 1. بررسی لاگ‌های واقعی در دیتابیس:
```python
from core.models import APIUsageLog
from django.db.models import Count

# بررسی تعداد لاگ‌ها برای هر provider
provider_counts = APIUsageLog.objects.values('provider').annotate(
    count=Count('id')
).order_by('-count')

for item in provider_counts:
    print(f"{item['provider']}: {item['count']} لاگ")
```

#### 2. بررسی endpoint مستقیماً:
```bash
# تست endpoint بدون فیلتر
curl http://localhost:8000/api/api-usage-stats/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# تست endpoint با فیلتر MT5
curl http://localhost:8000/api/api-usage-stats/?provider=mt5 \
  -H "Authorization: Bearer YOUR_TOKEN"

# تست endpoint با فیلتر twelvedata
curl http://localhost:8000/api/api-usage-stats/?provider=twelvedata \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 3. بررسی Frontend:
- بررسی کنید که آیا `stats.provider_stats` به درستی از response استخراج می‌شود
- بررسی کنید که آیا همه provider ها در `PROVIDER_NAMES` تعریف شده‌اند
- بررسی console برای خطاهای JavaScript

#### 4. بررسی لاگ‌گیری در کد:
بررسی کنید که آیا همه provider ها در کد واقعی لاگ می‌شوند:

```python
# بررسی لاگ‌گیری در data_providers.py
grep -r "log_api_usage" backend/api/

# بررسی لاگ‌گیری برای هر provider
grep -r "provider.*twelvedata" backend/
grep -r "provider.*alphavantage" backend/
```

## 📊 نتایج تست‌ها

### تست موفق:
```
✅ تست محاسبه هزینه موفق بود
✅ تست لاگ‌گیری برای همه Provider ها موفق بود (22 لاگ ایجاد شد)
✅ تست دریافت آمار موفق بود (11 provider در آمار)
✅ تست فیلتر تاریخ موفق بود
✅ تست فیلتر کاربر موفق بود
✅ ساختار آمار صحیح است
✅ تست endpoint موفق بود
```

### Provider های تست شده:
- twelvedata
- alphavantage
- oanda
- metalsapi
- financialmodelingprep
- nerkh
- gemini
- kavenegar
- mt5
- google_oauth
- zarinpal

## 🛠️ استفاده

### اجرای تست‌ها:
```bash
# تست کامل
cd backend
python test_api_usage_tracking.py

# تست endpoint ها
python test_api_usage_endpoints.py
```

### پاک کردن لاگ‌های تست:
```python
from core.models import APIUsageLog
APIUsageLog.objects.filter(metadata__test=True).delete()
```

## 📝 نکات مهم

1. **تست‌ها لاگ واقعی ایجاد می‌کنند** - برای پاک کردن از دستور بالا استفاده کنید
2. **برای تست endpoint ها نیاز به کاربر ادمین دارید** - تست‌ها به صورت خودکار کاربر ایجاد می‌کنند
3. **بررسی کنید که همه provider ها در کد واقعی لاگ می‌شوند** - ممکن است برخی provider ها در کد واقعی استفاده نشده باشند

## 🔧 رفع مشکل

اگر مشکل همچنان وجود دارد:

1. ✅ تست‌ها را اجرا کنید تا مطمئن شوید سیستم به درستی کار می‌کند
2. ✅ بررسی کنید که آیا لاگ‌های واقعی برای سایر provider ها وجود دارد
3. ✅ بررسی کنید که آیا frontend به درستی داده‌ها را نمایش می‌دهد
4. ✅ بررسی console مرورگر برای خطاهای JavaScript
5. ✅ بررسی network tab برای بررسی response API

