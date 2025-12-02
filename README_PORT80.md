# راهنمای اجرای Frontend روی پورت 80

## خلاصه
این راهنما برای اجرای Frontend روی پورت 80 (برای دسترسی با دامنه بدون نیاز به پورت) است.

## پیش‌نیازها

1. IIS باید متوقف باشد (یا از پورت 80 استفاده نکند)
2. Backend باید روی پورت 8000 در حال اجرا باشد
3. Frontend باید build شده باشد (برای preview) یا از dev server استفاده کنید

## روش 1: استفاده از Preview Server (Production-like)

### مراحل:

1. **متوقف کردن IIS:**
   ```powershell
   iisreset /stop
   ```

2. **بررسی دسترسی پورت 80:**
   ```powershell
   .\check_port80.ps1
   ```

3. **راه‌اندازی Frontend:**
   ```powershell
   .\start_frontend_port80.ps1
   ```

4. **تست:**
   ```powershell
   .\test_port80.ps1
   ```

## روش 2: استفاده از Dev Server (Development)

برای توسعه و تست سریع‌تر:

```powershell
.\start_frontend_port80_dev.ps1
```

## دسترسی به سایت

بعد از راه‌اندازی، سایت در آدرس‌های زیر در دسترس است:

- `http://localhost`
- `http://191.101.113.163`
- `http://myaibaz.ir` (از طریق Cloudflare)

## تست‌ها

اسکریپت `test_port80.ps1` این موارد را تست می‌کند:

1. ✅ دسترسی پورت 80
2. ✅ پاسخ Frontend
3. ✅ دسترسی با IP address
4. ✅ Proxy API (اگر Backend در حال اجرا باشد)

## نکات مهم

- اگر IIS را متوقف کردید، برای راه‌اندازی مجدد: `iisreset /start`
- برای تغییر پورت IIS به 8080، در IIS Manager → Sites → MyWebsite → Bindings → Edit → Port: 8080
- Frontend به صورت خودکار درخواست‌های `/api/*` را به Backend روی پورت 8000 proxy می‌کند

## عیب‌یابی

### خطا: Port 80 is already in use
- IIS را متوقف کنید: `iisreset /stop`
- یا process دیگری که از پورت 80 استفاده می‌کند را پیدا و متوقف کنید

### خطا: Cannot find module
- در پوشه `frontend` اجرا کنید: `npm install`

### Frontend کار نمی‌کند
- بررسی کنید Backend روی پورت 8000 در حال اجرا است
- بررسی کنید فایروال پورت 80 را مسدود نکرده است

## فایل‌های ایجاد شده

- `setup_port80.ps1` - اسکریپت تنظیمات اولیه
- `start_frontend_port80.ps1` - راه‌اندازی Preview Server
- `start_frontend_port80_dev.ps1` - راه‌اندازی Dev Server
- `test_port80.ps1` - اسکریپت تست
- `check_port80.ps1` - بررسی دسترسی پورت 80



