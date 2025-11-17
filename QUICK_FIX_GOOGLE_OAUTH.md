# ⚡ راه حل سریع: مشکل Google OAuth

## مشکل: "Access blocked: Authorization Error" یا "origin_mismatch"

### ✅ راه حل در 3 دقیقه:

1. **به این آدرس بروید:**
   ```
   https://console.cloud.google.com/apis/credentials
   ```

2. **OAuth Client ID خود را باز کنید** (روی نام آن کلیک کنید)

3. **در بخش "Authorized JavaScript origins" این آدرس‌ها را اضافه کنید:**
   ```
   http://localhost:3000
   http://127.0.0.1:3000
   ```

4. **اگر از شبکه محلی استفاده می‌کنید، IP خود را هم اضافه کنید:**
   - IP را پیدا کنید: `ipconfig` (Windows) یا `hostname -I` (Linux)
   - مثال: `http://192.168.1.100:3000`

5. **Save کنید** و 1-2 دقیقه صبر کنید

6. **تست کنید** - باید کار کند! ✅

---

## 📝 اگر Client ID ندارید:

1. در همان صفحه، **"+ CREATE CREDENTIALS"** > **"OAuth client ID"** را بزنید
2. Application type: **"Web application"**
3. Name: هر نامی که می‌خواهید
4. Authorized JavaScript origins: `http://localhost:3000`
5. **CREATE** کنید
6. Client ID را کپی کنید
7. در فایل `.env` اضافه کنید:
   ```env
   GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE
   ```
8. در فایل `frontend/.env.local`:
   ```env
   VITE_GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE
   ```
9. Frontend و Backend را restart کنید

---

## 🆘 هنوز کار نمی‌کند؟

1. Cache مرورگر را پاک کنید (Ctrl+Shift+Delete)
2. چند دقیقه صبر کنید
3. Console مرورگر را بررسی کنید (F12)
4. راهنمای کامل را بخوانید: `راهنمای_گام_به_گام_رفع_بلاک_Google.md`

