# راهنمای تنظیم Google OAuth برای شبکه محلی

## مشکل
هنگام استفاده از Google Login از دستگاه‌های دیگر در شبکه محلی، خطای زیر نمایش داده می‌شود:
```
Error 400: origin_mismatch
Access blocked: Authorization Error
You can't sign in to this app because it doesn't comply with Google's OAuth 2.0 policy.
```

## راه حل

### مرحله 1: ورود به Google Cloud Console

1. به [Google Cloud Console](https://console.cloud.google.com/) بروید
2. با حساب Google خود وارد شوید (همان حسابی که Client ID را ساختید)
3. پروژه مربوطه را انتخاب کنید

### مرحله 2: پیدا کردن OAuth Client

1. در منوی سمت چپ، به **APIs & Services** > **Credentials** بروید
2. در لیست **OAuth 2.0 Client IDs**، Client ID مربوط به برنامه خود را پیدا کنید
3. روی نام Client ID کلیک کنید تا تنظیمات آن باز شود

### مرحله 3: اضافه کردن JavaScript Origins

در بخش **Authorized JavaScript origins**، این آدرس‌ها را اضافه کنید:

```
http://localhost:3000
http://127.0.0.1:3000
http://YOUR_LOCAL_IP:3000
```

**نکته مهم**: `YOUR_LOCAL_IP` را با IP محلی سیستم خود جایگزین کنید.

#### پیدا کردن IP محلی:

**Windows:**
```powershell
ipconfig | findstr IPv4
```

یا از PowerShell:
```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*"}
```

**Linux/Mac:**
```bash
hostname -I
# یا
ifconfig | grep "inet "
```

### مرحله 4: اضافه کردن Authorized Redirect URIs (اختیاری)

اگر از redirect URI استفاده می‌کنید، این آدرس‌ها را هم اضافه کنید:

```
http://localhost:3000
http://127.0.0.1:3000
http://YOUR_LOCAL_IP:3000
```

### مرحله 5: ذخیره تغییرات

1. روی دکمه **Save** کلیک کنید
2. چند دقیقه صبر کنید تا تغییرات اعمال شوند (معمولاً 1-2 دقیقه)

### مرحله 6: تست

1. از دستگاه دیگر در شبکه محلی به `http://YOUR_LOCAL_IP:3000` بروید
2. روی دکمه "Sign in with Google" کلیک کنید
3. باید بتوانید بدون خطا وارد شوید

## نکات مهم

1. **تغییرات فوری نیست**: گاهی اوقات تغییرات Google Cloud Console تا 5 دقیقه طول می‌کشد تا اعمال شوند.

2. **IP ثابت نیست**: اگر IP سیستم شما تغییر کند، باید دوباره origin جدید را اضافه کنید. برای حل این مشکل:
   - از IP ثابت (Static IP) استفاده کنید
   - یا همه IPهای ممکن شبکه را اضافه کنید (مثلاً `http://192.168.1.1:3000` تا `http://192.168.1.255:3000`)

3. **امنیت**: در production، فقط origins معتبر را اضافه کنید.

## راه حل موقت (اگر نمی‌توانید origin اضافه کنید)

اگر نمی‌توانید origin را اضافه کنید یا می‌خواهید از Google Login استفاده نکنید:

1. از روش ورود با شماره موبایل استفاده کنید
2. یا Google Login را موقتاً غیرفعال کنید

## مشکل رفع نشد؟

اگر بعد از انجام این مراحل مشکل حل نشد:

1. Cache مرورگر را پاک کنید
2. چند دقیقه صبر کنید و دوباره امتحان کنید
3. مطمئن شوید که Client ID درست است (بررسی فایل `.env` یا `env.example`)
4. لاگ‌های Console مرورگر را بررسی کنید

