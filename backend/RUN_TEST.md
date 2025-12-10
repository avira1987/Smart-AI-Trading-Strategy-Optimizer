# راهنمای تست GapGPT

برای تست و بررسی خطای GapGPT، یکی از روش‌های زیر را استفاده کنید:

## روش 1: استفاده از دستور مدیریتی Django

```bash
cd backend
python manage.py test_gapgpt_error
```

یا با کاربر خاص:

```bash
python manage.py test_gapgpt_error --user-id 1
```

## روش 2: استفاده از اسکریپت سریع

```bash
cd backend
python quick_test.py
```

سپس فایل `test_output.txt` را بررسی کنید.

## روش 3: استفاده از فایل batch (Windows)

```bash
cd backend
run_test.bat
```

## اطلاعاتی که تست نمایش می‌دهد:

1. ✅ وضعیت کلید API
2. 📥 Status Code از GapGPT API
3. 🔍 جزئیات خطا (اگر خطایی باشد)
4. ⚠️  تشخیص اینکه خطا مربوط به quota است یا نه

## بررسی لاگ‌ها

اگر هنوز مشکل دارید، لاگ‌های Django را بررسی کنید:

```bash
# در Windows
type logs\*.log

# یا در Linux/Mac
tail -f logs/*.log
```

لاگ‌ها شامل جزئیات کامل خطاهای 403 هستند.
