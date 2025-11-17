# راهنمای بازیابی و تنظیم مجدد API Key کاوهنگار

اگر API key کاوهنگار حذف شده و نمی‌توانید وارد سیستم شوید، از یکی از روش‌های زیر استفاده کنید:

## روش 1: استفاده از Management Command (توصیه می‌شود)

این روش امن‌ترین راه است و از طریق terminal انجام می‌شود.

### مراحل:

1. **Terminal/PowerShell را باز کنید** و به پوشه backend بروید:

```powershell
cd "C:\Users\393\Desktop\Smart AI Trading Strategy Optimizer\backend"
```

2. **API key را تنظیم کنید**:

```powershell
python manage.py set_kavenegar_api_key --api-key YOUR_API_KEY_HERE
```

**مثال:**
```powershell
python manage.py set_kavenegar_api_key --api-key 1234567890ABCDEF1234567890ABCDEF
```

3. **اگر شماره فرستنده دارید** (اختیاری):

```powershell
python manage.py set_kavenegar_api_key --api-key YOUR_API_KEY --sender 10008663
```

4. **بررسی کنید که API key تنظیم شده است**:

```powershell
python manage.py shell
```

سپس در shell:
```python
from core.models import APIConfiguration
config = APIConfiguration.objects.filter(provider='kavenegar').first()
if config:
    print(f"API Key: {config.api_key[:10]}...{config.api_key[-4:]}")
    print(f"Active: {config.is_active}")
else:
    print("API key not found")
exit()
```

---

## روش 2: استفاده از Emergency Endpoint (برای حالت اضطراری)

⚠️ **توجه**: این روش فقط برای حالت اضطراری است و باید در production غیرفعال شود.

### مراحل:

1. **Token امنیتی را در فایل `.env` تنظیم کنید** (اختیاری):

```env
EMERGENCY_API_KEY_TOKEN=YOUR_SECRET_TOKEN_HERE
```

اگر تنظیم نکنید، از token پیش‌فرض `EMERGENCY_RECOVERY_2024` استفاده می‌شود.

2. **درخواست POST ارسال کنید**:

با استفاده از Postman، curl، یا هر ابزار دیگری:

```bash
POST http://localhost:8000/api/emergency/set-kavenegar-api-key/
Content-Type: application/json

{
  "api_key": "YOUR_API_KEY_HERE",
  "secret_token": "EMERGENCY_RECOVERY_2024"
}
```

**مثال با curl:**
```bash
curl -X POST http://localhost:8000/api/emergency/set-kavenegar-api-key/ \
  -H "Content-Type: application/json" \
  -d '{"api_key": "YOUR_API_KEY_HERE", "secret_token": "EMERGENCY_RECOVERY_2024"}'
```

**مثال با PowerShell:**
```powershell
$body = @{
    api_key = "YOUR_API_KEY_HERE"
    secret_token = "EMERGENCY_RECOVERY_2024"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/emergency/set-kavenegar-api-key/" -Method POST -Body $body -ContentType "application/json"
```

---

## روش 3: استفاده از Django Admin Panel

اگر قبلاً یک کاربر admin دارید که می‌توانید با آن وارد شوید:

1. به `http://localhost:8000/admin/` بروید
2. وارد شوید
3. به بخش **API Configurations** بروید
4. یک رکورد جدید با این مشخصات ایجاد کنید:
   - **Provider**: `Kavenegar (SMS)`
   - **API Key**: کلید API شما
   - **Is Active**: ✅ (تیک بزنید)
5. **Save** کنید

---

## روش 4: تنظیم در فایل .env

اگر می‌خواهید API key را در فایل `.env` تنظیم کنید:

1. فایل `.env` را در ریشه پروژه باز کنید
2. این خط را اضافه یا ویرایش کنید:

```env
KAVENEGAR_API_KEY=YOUR_API_KEY_HERE
KAVENEGAR_SENDER=YOUR_SENDER_NUMBER  # اختیاری
```

3. **سرور را ری‌استارت کنید**

---

## دریافت API Key از پنل کاوهنگار

اگر API key ندارید:

1. به [پنل کاربری Kavenegar](https://panel.kavenegar.com/) بروید
2. وارد حساب کاربری خود شوید
3. به بخش **تنظیمات** > **API Key** بروید
4. API key خود را کپی کنید

---

## بررسی وضعیت API Key

بعد از تنظیم API key، می‌توانید وضعیت آن را بررسی کنید:

```bash
GET http://localhost:8000/api/test/kavenegar-config/
```

یا در terminal:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/test/kavenegar-config/" -Method GET
```

---

## نکات مهم

1. **اولویت**: سیستم ابتدا API key را از فایل `.env` می‌خواند، سپس از دیتابیس
2. **امنیت**: در production، endpoint اضطراری را غیرفعال کنید یا با امنیت بیشتری محافظت کنید
3. **ری‌استارت**: بعد از تنظیم API key در `.env`، حتماً سرور را ری‌استارت کنید
4. **بررسی**: همیشه بعد از تنظیم، با endpoint تست بررسی کنید که API key درست تنظیم شده است

---

## عیب‌یابی

### اگر هنوز نمی‌توانید وارد شوید:

1. **بررسی کنید که API key درست تنظیم شده است**:
   ```bash
   GET http://localhost:8000/api/test/kavenegar-config/
   ```

2. **بررسی لاگ‌های سرور** برای خطاهای دقیق‌تر

3. **تست ارسال پیامک**:
   ```bash
   POST http://localhost:8000/api/test/sms/
   Body: {"phone_number": "09123456789"}
   ```

4. **مطمئن شوید که ماژول kavenegar نصب شده است**:
   ```powershell
   pip install kavenegar
   ```

---

## امنیت در Production

⚠️ **مهم**: در محیط production:

1. Endpoint اضطراری را غیرفعال کنید یا با authentication قوی محافظت کنید
2. از management command استفاده کنید (روش 1)
3. Token امنیتی قوی برای endpoint اضطراری تنظیم کنید
4. لاگ‌های دسترسی به endpoint اضطراری را بررسی کنید

