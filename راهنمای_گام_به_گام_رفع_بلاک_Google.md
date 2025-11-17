# راهنمای گام به گام: رفع مشکل Google OAuth

## ⚠️ مهم: Google شما را بلاک نکرده!

خطای `origin_mismatch` یا `Access blocked` به این معنی است که:
- Google حساب شما را بلاک نکرده
- فقط تنظیمات OAuth در Google Cloud Console نیاز به به‌روزرسانی دارد
- این مشکل در چند دقیقه قابل حل است

---

## 🔧 راه حل: ثبت Origin در Google Cloud Console

### مرحله 1: ورود به Google Cloud Console

1. مرورگر را باز کنید
2. به این آدرس بروید: **https://console.cloud.google.com/**
3. با حساب Google خود وارد شوید (همان حسابی که Client ID را ساختید)
   - اگر Client ID ندارید، باید ابتدا آن را بسازید (مرحله 0)

### مرحله 2: انتخاب پروژه

1. در بالای صفحه، کنار "Google Cloud" یک منوی dropdown وجود دارد
2. پروژه مربوط به برنامه خود را انتخاب کنید
   - اگر پروژه ندارید، "New Project" را بزنید و یکی بسازید

### مرحله 3: رفتن به بخش Credentials

1. در منوی سمت چپ، روی **"APIs & Services"** کلیک کنید
2. سپس روی **"Credentials"** کلیک کنید

### مرحله 4: پیدا کردن OAuth Client ID

1. در صفحه Credentials، بخش **"OAuth 2.0 Client IDs"** را پیدا کنید
2. لیستی از Client IDs نمایش داده می‌شود
3. Client ID مربوط به برنامه خود را پیدا کنید (معمولاً نام آن "Web client" است)
4. روی **نام Client ID** کلیک کنید (نه روی خود Client ID)

### مرحله 5: اضافه کردن JavaScript Origins

1. در صفحه تنظیمات Client ID، بخش **"Authorized JavaScript origins"** را پیدا کنید
2. روی دکمه **"+ ADD URI"** کلیک کنید
3. این آدرس‌ها را یکی یکی اضافه کنید:

```
http://localhost:3000
http://127.0.0.1:3000
```

4. **برای دسترسی از شبکه محلی**، IP محلی خود را هم اضافه کنید:

```
http://YOUR_IP:3000
```

**نحوه پیدا کردن IP محلی:**

**Windows:**
```powershell
ipconfig
```
دنبال خطی بگردید که با `IPv4 Address` شروع می‌شود (مثلاً `192.168.1.100`)

**یا از PowerShell:**
```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*"}
```

**مثال:** اگر IP شما `192.168.1.100` است، این را اضافه کنید:
```
http://192.168.1.100:3000
```

### مرحله 6: اضافه کردن Redirect URIs (اختیاری)

اگر از Redirect URI استفاده می‌کنید:

1. بخش **"Authorized redirect URIs"** را پیدا کنید
2. همان آدرس‌ها را اینجا هم اضافه کنید:
   ```
   http://localhost:3000
   http://127.0.0.1:3000
   http://YOUR_IP:3000
   ```

### مرحله 7: ذخیره تغییرات

1. در پایین صفحه، روی دکمه **"SAVE"** کلیک کنید
2. پیام موفقیت نمایش داده می‌شود
3. **مهم:** 1-2 دقیقه صبر کنید تا تغییرات اعمال شوند

### مرحله 8: تست

1. به صفحه Login برنامه خود برگردید
2. روی دکمه "Sign in with Google" کلیک کنید
3. باید بدون خطا کار کند! ✅

---

## 🆘 اگر Client ID ندارید (مرحله 0)

اگر هنوز Client ID نساخته‌اید:

### مرحله 0.1: ایجاد OAuth Client ID

1. در Google Cloud Console، به **APIs & Services > Credentials** بروید
2. در بالای صفحه، روی **"+ CREATE CREDENTIALS"** کلیک کنید
3. **"OAuth client ID"** را انتخاب کنید
4. اگر اولین بار است، **"CONFIGURE CONSENT SCREEN"** را بزنید:
   - User Type: **External** را انتخاب کنید
   - App name: نام برنامه خود را وارد کنید
   - User support email: ایمیل خود را وارد کنید
   - Developer contact: ایمیل خود را وارد کنید
   - روی **"SAVE AND CONTINUE"** کلیک کنید
   - Scopes: پیش‌فرض را بگذارید و **"SAVE AND CONTINUE"** بزنید
   - Test users: در حال حاضر نیاز نیست، **"SAVE AND CONTINUE"** بزنید
   - Summary: **"BACK TO DASHBOARD"** بزنید

5. حالا دوباره **"+ CREATE CREDENTIALS > OAuth client ID** را بزنید
6. Application type: **"Web application"** را انتخاب کنید
7. Name: نامی برای Client ID بگذارید (مثلاً "AI Forex Strategy Manager")
8. Authorized JavaScript origins: 
   - `http://localhost:3000` را اضافه کنید
9. روی **"CREATE"** کلیک کنید
10. Client ID و Client Secret نمایش داده می‌شود
11. **Client ID** را کپی کنید
12. در فایل `.env` پروژه، این خط را اضافه/ویرایش کنید:
    ```env
    GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE
    ```
13. در فایل `frontend/.env` یا `frontend/.env.local`:
    ```env
    VITE_GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE
    ```
14. Frontend و Backend را راه‌اندازی مجدد کنید

---

## ❓ سوالات متداول

### Q: چرا باید IP شبکه محلی را اضافه کنم؟
**A:** چون وقتی از دستگاه دیگر در شبکه محلی به سایت دسترسی دارید، مرورگر از IP شبکه محلی استفاده می‌کند، نه localhost.

### Q: اگر IP من تغییر کند چه؟
**A:** باید origin جدید را اضافه کنید. یا می‌توانید از IP ثابت (Static IP) استفاده کنید.

### Q: چقدر طول می‌کشد تا تغییرات اعمال شود؟
**A:** معمولاً 1-2 دقیقه، اما گاهی تا 5 دقیقه هم طول می‌کشد.

### Q: بعد از تغییرات هنوز کار نمی‌کند؟
**A:** 
1. Cache مرورگر را پاک کنید (Ctrl+Shift+Delete)
2. چند دقیقه صبر کنید
3. مطمئن شوید که Client ID درست است
4. Console مرورگر را بررسی کنید (F12)

### Q: آیا می‌توانم همه IPها را یکجا اضافه کنم؟
**A:** نه، باید هر IP را جداگانه اضافه کنید. اما می‌توانید چند IP رایج شبکه محلی را اضافه کنید:
- `http://192.168.1.1:3000`
- `http://192.168.1.100:3000`
- `http://192.168.0.1:3000`
- و غیره

---

## 🔒 امنیت

- در production، فقط origins معتبر را اضافه کنید
- از HTTPS استفاده کنید
- Client Secret را محرمانه نگه دارید

---

## 📞 اگر مشکل حل نشد

1. Screenshot خطا را بگیرید
2. Console مرورگر (F12) را بررسی کنید
3. لاگ‌های Google Cloud Console را بررسی کنید
4. مطمئن شوید که:
   - Client ID درست است
   - Origins درست اضافه شده‌اند
   - تغییرات ذخیره شده‌اند

---

## ✅ چک‌لیست

- [ ] به Google Cloud Console وارد شده‌ام
- [ ] پروژه درست را انتخاب کرده‌ام
- [ ] به بخش Credentials رفته‌ام
- [ ] OAuth Client ID را پیدا کرده‌ام
- [ ] `http://localhost:3000` را اضافه کرده‌ام
- [ ] `http://127.0.0.1:3000` را اضافه کرده‌ام
- [ ] IP شبکه محلی را اضافه کرده‌ام
- [ ] تغییرات را ذخیره کرده‌ام
- [ ] 1-2 دقیقه صبر کرده‌ام
- [ ] Cache مرورگر را پاک کرده‌ام
- [ ] تست کرده‌ام و کار می‌کند ✅

