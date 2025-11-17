# راهنمای تست Backend روی IP شبکه محلی

## 🎯 تست روی IP: 192.168.100.9:8000

### روش 1: استفاده از اسکریپت PowerShell (Windows)

```powershell
.\test_on_ip.ps1
```

این اسکریپت:
1. ✅ وضعیت Backend را بررسی می‌کند
2. ✅ تنظیمات Google OAuth را بررسی می‌کند
3. ✅ ارسال SMS را تست می‌کند

### روش 2: استفاده از دستورات curl

#### تست وضعیت Backend:
```powershell
curl http://192.168.100.9:8000/api/test/backend-status/
```

#### تست تنظیمات Google OAuth:
```powershell
curl http://192.168.100.9:8000/api/test/google-oauth/
```

#### تست ارسال SMS:
```powershell
curl -X POST http://192.168.100.9:8000/api/test/sms/ `
  -H "Content-Type: application/json" `
  -d '{\"phone_number\": \"09123456789\"}'
```

### روش 3: استفاده از مرورگر

می‌توانید این URLها را مستقیماً در مرورگر باز کنید:

1. **وضعیت Backend:**
   ```
   http://192.168.100.9:8000/api/test/backend-status/
   ```

2. **تنظیمات Google OAuth:**
   ```
   http://192.168.100.9:8000/api/test/google-oauth/
   ```

### روش 4: استفاده از Postman یا Insomnia

#### تست SMS:
- **Method:** POST
- **URL:** `http://192.168.100.9:8000/api/test/sms/`
- **Headers:** `Content-Type: application/json`
- **Body (JSON):**
  ```json
  {
    "phone_number": "09123456789"
  }
  ```

#### تست Google OAuth:
- **Method:** GET
- **URL:** `http://192.168.100.9:8000/api/test/google-oauth/`

#### وضعیت Backend:
- **Method:** GET
- **URL:** `http://192.168.100.9:8000/api/test/backend-status/`

---

## 📋 Endpoint های تست

### 1. `GET /api/test/backend-status/`
بررسی وضعیت Backend و تنظیمات

**Response:**
```json
{
  "success": true,
  "message": "وضعیت Backend",
  "config": {
    "backend_running": true,
    "hostname": "...",
    "local_ip": "192.168.100.9",
    "network_ips": ["192.168.100.9"],
    "google_client_id_configured": true,
    "kavenegar_api_key_configured": true,
    "kavenegar_sender_configured": true
  }
}
```

### 2. `GET /api/test/google-oauth/`
بررسی تنظیمات Google OAuth

**Query Parameters (اختیاری):**
- `frontend_client_id`: Client ID از Frontend

**Response:**
```json
{
  "success": true,
  "message": "وضعیت تنظیمات Google OAuth",
  "config": {
    "backend_google_client_id": "✅ تنظیم شده",
    "current_origin": "http://192.168.100.9:3000",
    "current_host": "192.168.100.9:8000"
  },
  "recommendations": [
    "مطمئن شوید که GOOGLE_CLIENT_ID در فایل .env تنظیم شده است",
    "مطمئن شوید که VITE_GOOGLE_CLIENT_ID در frontend/.env.local تنظیم شده است",
    "Origin فعلی باید در Google Cloud Console ثبت شود"
  ]
}
```

### 3. `POST /api/test/sms/`
تست ارسال SMS

**Body:**
```json
{
  "phone_number": "09123456789"
}
```

**Response (موفق):**
```json
{
  "success": true,
  "message": "پیامک با موفقیت ارسال شد",
  "test_otp": "123456",
  "phone_number": "09123456789"
}
```

**Response (خطا):**
```json
{
  "success": false,
  "message": "شماره فرستنده نامعتبر است...",
  "error": "..."
}
```

---

## ⚠️ نکات مهم

1. **Backend باید در حال اجرا باشد:**
   ```powershell
   cd backend
   python manage.py runserver 0.0.0.0:8000
   ```

2. **فایروال را بررسی کنید:**
   - پورت 8000 باید باز باشد
   - اگر از دستگاه دیگر تست می‌کنید، باید در همان شبکه باشید

3. **برای تست SMS:**
   - شماره موبایل باید به فرمت `09123456789` باشد
   - KAVENEGAR_API_KEY باید تنظیم شده باشد
   - KAVENEGAR_SENDER (اختیاری اما توصیه می‌شود)

4. **برای تست Google OAuth:**
   - GOOGLE_CLIENT_ID باید تنظیم شده باشد
   - Origin باید در Google Cloud Console ثبت شود

---

## 🔍 عیب‌یابی

### اگر Backend در دسترس نیست:
1. مطمئن شوید که Backend روی `0.0.0.0:8000` اجرا می‌شود
2. IP را بررسی کنید: `ipconfig` (Windows)
3. فایروال را بررسی کنید

### اگر SMS ارسال نمی‌شود:
1. لاگ‌های Backend را بررسی کنید: `backend/logs/api.log`
2. KAVENEGAR_API_KEY را بررسی کنید
3. KAVENEGAR_SENDER را تنظیم کنید (اگر خطای 412 می‌دهد)

### اگر Google OAuth کار نمی‌کند:
1. GOOGLE_CLIENT_ID را بررسی کنید
2. Origin را در Google Cloud Console اضافه کنید
3. راهنمای `راهنمای_گام_به_گام_رفع_بلاک_Google.md` را مطالعه کنید

---

## 📞 تست دستی با curl (مثال کامل)

```powershell
# 1. تست وضعیت
curl http://192.168.100.9:8000/api/test/backend-status/

# 2. تست Google OAuth
curl http://192.168.100.9:8000/api/test/google-oauth/

# 3. تست SMS
curl -X POST http://192.168.100.9:8000/api/test/sms/ `
  -H "Content-Type: application/json" `
  -d '{\"phone_number\": \"09123456789\"}'
```

---

## ✅ چک‌لیست

- [ ] Backend روی `0.0.0.0:8000` اجرا می‌شود
- [ ] IP محلی: `192.168.100.9`
- [ ] فایروال پورت 8000 را باز کرده است
- [ ] GOOGLE_CLIENT_ID تنظیم شده است
- [ ] KAVENEGAR_API_KEY تنظیم شده است
- [ ] KAVENEGAR_SENDER تنظیم شده است (اختیاری)
- [ ] تست‌ها را اجرا کرده‌ام

